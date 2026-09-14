"""F7: adversarial search for E_obs / B_R over small PMT-A networks (PyTorch, CPU, float64).

Network: k internal nodes, every value space R^chi, node laws are arbitrary real multilinear maps
W_v : (R^chi)^{m_v} -> R^chi (children first, then leaves), unit leaves, fixed orthogonal rank-r
projectors on non-root nodes, root P = I.  Topologies (arity of non-star nodes is 2):
  chain     node i attaches to node i-1
  balanced  node i attaches to node (i-1)//2
  random    node i attaches to a uniformly random earlier node with a free slot
  star      root has k-1 children (arity k-1, no leaves); each child has two leaves
Variants (preregistration Amendment 2):
  coiso   W_v has orthonormal-row flattening (chi, chi^m): M_hat = 1 rigorous (preregistered F7)
  opnorm  W_v normalised by its operator-norm estimate (block power iteration), so the witness
          (R^2 = C multiplication) is representable; used for the sharpness question H5
Optimisation: maximise log E - log G_k(smoothmax_v eta_v) with M = 1, 16 restarts batched, Adam.
Final evaluation (numpy): each restart becomes one PMT instance with a rigorous M_hat:
  M_up_v = min(flattening norm, net bound (arity 2 only)); the certificate in runs.jsonl uses max_v M_up_v.
  ratio_est uses M_low = max_v (128-restart power-iteration lower bound) and is descriptive only.
  d_span = max_v numerical rank (tol 1e-3 relative) of {F_v, mu_v(R_children), R_v}.
"""
from __future__ import annotations

import itertools
import math
import os

os.environ.setdefault("CUDA_VISIBLE_DEVICES", "")

import numpy as np
import torch

import certificate as cert
from pmt_eval import Node, evaluate
from seeding import stable_seed

torch.set_default_dtype(torch.float64)
DEV = torch.device("cpu")
LETTERS = "abcdefghijklmn"


# ----------------------------------------------------------------------------------------- topology
def topology(kind: str, k: int, rng) -> list:
    """List of nodes (index 0 = root) with fields children (list of ids) and n_leaves."""
    if kind == "star":
        nodes = [{"children": list(range(1, k)), "n_leaves": 0}] + [{"children": [], "n_leaves": 2} for _ in range(k - 1)]
        return nodes
    parent = [None]
    kids = {0: []}
    for i in range(1, k):
        if kind == "chain":
            p = i - 1
        elif kind == "balanced":
            p = (i - 1) // 2
        elif kind == "random":
            free = [j for j in range(i) if len(kids[j]) < 2]
            p = int(rng.choice(free))
        else:
            raise ValueError(kind)
        parent.append(p); kids[p].append(i); kids[i] = []
    return [{"children": kids[i], "n_leaves": 2 - len(kids[i])} for i in range(k)]


# ----------------------------------------------------------------------------------------- torch core
def t_apply(T, xs):
    """T: (B, o, d_1..d_m), xs: list of (B, d_i) -> (B, o)."""
    out = T
    for x in reversed(xs):
        out = (out * x.reshape(x.shape[0], *([1] * (out.dim() - 2)), x.shape[1])).sum(-1)
    return out


def t_contract_except(T, xs, i):
    m = T.dim() - 2
    sub = "z" + "y" + LETTERS[:m]
    ins = [sub] + ["z" + LETTERS[j] for j in range(m) if j != i]
    ops = [T] + [xs[j] for j in range(m) if j != i]
    return torch.einsum(",".join(ins) + "->zy" + LETTERS[i], *ops)


@torch.no_grad()
def t_power(T, xs, sweeps):
    xs = [x.clone() for x in xs]
    for _ in range(sweeps):
        for i in range(T.dim() - 2):
            A = t_contract_except(T, xs, i)
            _, _, Vh = torch.linalg.svd(A, full_matrices=False)
            xs[i] = Vh[:, 0, :]
    return xs


@torch.no_grad()
def t_power_global(T, xs_warm, restarts, sweeps, gen):
    B, m, d = T.shape[0], T.dim() - 2, T.shape[2]
    TT = T.repeat_interleave(restarts, 0)
    xs = [torch.nn.functional.normalize(torch.randn(B * restarts, d, generator=gen), dim=1) for _ in range(m)]
    xs = t_power(TT, xs, sweeps)
    val = t_apply(TT, xs).norm(dim=1).reshape(B, restarts)
    best = val.argmax(1)
    idx = torch.arange(B) * restarts + best
    cand = [x[idx] for x in xs]
    if xs_warm is not None:
        warm = t_power(T, xs_warm, sweeps)
        use_warm = t_apply(T, warm).norm(dim=1) >= t_apply(T, cand).norm(dim=1)
        cand = [torch.where(use_warm[:, None], w, c) for w, c in zip(warm, cand)]
    return cand


def t_G(eta, k, grid=1025):
    n = k - 1
    t = torch.linspace(0.0, 1.0, grid)
    th = t[None, :] * torch.asin(eta.clamp(0.0, 1.0))[:, None]
    c = torch.cos(th)
    g2 = (1 - 2 * c ** n * torch.cos(n * th) + c ** (2 * n)).clamp_min(1e-300)
    return g2.sqrt().max(1).values


class Adversary:
    def __init__(self, topo, chi, r, variant, B, gen):
        self.topo, self.chi, self.r, self.variant, self.B, self.k = topo, chi, r, variant, B, len(topo)
        self.W, self.U, self.Z = [], [], []
        for v, nd in enumerate(topo):
            m = len(nd["children"]) + nd["n_leaves"]
            self.W.append(torch.randn(B, chi, chi ** m, generator=gen).requires_grad_())
            self.U.append(torch.randn(B, chi, r, generator=gen).requires_grad_() if v != 0 else None)
            self.Z.append([torch.randn(B, chi, generator=gen).requires_grad_() for _ in range(nd["n_leaves"])])
        self.xs = [None] * self.k

    def params(self):
        ps = list(self.W) + [u for u in self.U if u is not None]
        return ps + [z for zs in self.Z for z in zs]

    def arity(self, v):
        nd = self.topo[v]
        return len(nd["children"]) + nd["n_leaves"]

    def tensors(self, gen=None, refresh=False):
        out = []
        for v in range(self.k):
            m, raw = self.arity(v), self.W[v]
            if self.variant == "coiso":
                Q = torch.linalg.qr(raw.transpose(1, 2)).Q            # (B, chi^m, chi)
                T = Q.transpose(1, 2).reshape(self.B, self.chi, *([self.chi] * m))
            else:
                T0 = raw.reshape(self.B, self.chi, *([self.chi] * m))
                with torch.no_grad():
                    if refresh or self.xs[v] is None:
                        self.xs[v] = t_power_global(T0.detach(), self.xs[v], 16, 25, gen)
                    else:
                        self.xs[v] = t_power(T0.detach(), self.xs[v], 2)
                M = t_apply(T0, self.xs[v]).norm(dim=1)
                T = T0 / M.reshape(self.B, *([1] * (m + 1)))
            out.append(T)
        return out

    def forward(self, gen=None, refresh=False, beta=200.0):
        Ts = self.tensors(gen, refresh)
        F, R, leaks = {}, {}, []
        for v in reversed(range(self.k)):
            nd = self.topo[v]
            z = [torch.nn.functional.normalize(zz, dim=1) for zz in self.Z[v]]
            F[v] = t_apply(Ts[v], [F[c] for c in nd["children"]] + z)
            y = t_apply(Ts[v], [R[c] for c in nd["children"]] + z)
            if v == 0:
                R[v] = y
            else:
                Q = torch.linalg.qr(self.U[v]).Q
                Ry = Q @ (Q.transpose(1, 2) @ y[:, :, None])
                R[v] = Ry[:, :, 0]
                denom = torch.stack([R[c].norm(dim=1) for c in nd["children"]] + [torch.ones(self.B)], 0).prod(0)
                leaks.append((y - R[v]).norm(dim=1) / denom.clamp_min(1e-300))
        E = (F[0] - R[0]).norm(dim=1)
        L = torch.stack(leaks, 1)
        eta = torch.logsumexp(beta * L, 1) / beta
        return E, eta, L.max(1).values

    def export(self, b):
        """Numpy instance data for restart b (tensors as used, orthonormal projector bases, unit leaves)."""
        with torch.no_grad():
            Ts = self.tensors()
            W = [Ts[v][b].numpy().copy() for v in range(self.k)]
            U = [None if v == 0 else torch.linalg.qr(self.U[v][b:b + 1]).Q[0].numpy().copy() for v in range(self.k)]
            Z = [[torch.nn.functional.normalize(z[b:b + 1], dim=1)[0].numpy().copy() for z in self.Z[v]] for v in range(self.k)]
        return W, U, Z


# ----------------------------------------------------------------------------------------- numpy evaluation
def np_apply(T, xs):
    out = T
    for x in reversed(xs):
        out = out @ x
    return out


def flattening_norm_nd(T):
    return float(min(np.linalg.norm(np.moveaxis(T, a, 0).reshape(T.shape[a], -1), 2) for a in range(T.ndim)))


def opnorm_lower(T, rng, restarts=128, sweeps=60):
    m, d = T.ndim - 1, T.shape[1]
    Tt = torch.from_numpy(T)[None].repeat(restarts, *([1] * T.ndim))
    gen = torch.Generator().manual_seed(int(rng.integers(0, 2 ** 31)))
    xs = [torch.nn.functional.normalize(torch.randn(restarts, d, generator=gen), dim=1) for _ in range(m)]
    xs = t_power(Tt, xs, sweeps)
    return float(t_apply(Tt, xs).norm(dim=1).max())


def cube_net(d, h):
    """Points p/||p|| on the upper faces of the cube [-1,1]^d (antipodal symmetry), covering radius <= h*sqrt(d-1)/2."""
    g = np.arange(-1.0, 1.0 + 1e-12, h)
    pts = []
    for face in range(d):
        grids = np.meshgrid(*([g] * (d - 1)), indexing="ij")
        P = np.empty((grids[0].size, d))
        cols = [c.ravel() for c in grids]
        j = 0
        for a in range(d):
            if a == face:
                P[:, a] = 1.0
            else:
                P[:, a] = cols[j]; j += 1
        pts.append(P)
    P = np.concatenate(pts)
    return P / np.linalg.norm(P, axis=1, keepdims=True), h * math.sqrt(d - 1) / 2


def opnorm_net_upper(T, h=None):
    """Rigorous upper bound for arity-2 T (o, d, d): M <= max_net sigma_max(T(y, .)) / (1 - delta)."""
    if T.ndim != 3:
        return None
    d = T.shape[1]
    h = h if h is not None else (0.0005 if d == 2 else 0.004)
    Y, delta = cube_net(d, h)
    best = 0.0
    for chunk in np.array_split(Y, max(1, len(Y) // 200000)):
        A = np.einsum("oab,na->nob", T, chunk)
        best = max(best, float(np.linalg.svd(A, compute_uv=False)[:, 0].max()))
    return best / (1 - delta)


def build_nodes(topo, W, U, Z, M_hat, provenance):
    nodes = {}
    for v, nd in enumerate(topo):
        vid = "root" if v == 0 else f"v{v}"
        children = [f"v{c}" for c in nd["children"]]
        P = None if v == 0 else (lambda y, Q=U[v]: Q @ (Q.T @ np.asarray(y)))
        nodes[vid] = Node(children=children, leaves=list(Z[v]),
                          law=lambda cv, lv, T=W[v]: np_apply(T, [np.asarray(c) for c in cv] + [np.asarray(l) for l in lv]),
                          M_hat=M_hat, M_provenance=provenance, projector=P, is_root=(v == 0),
                          extra={"output_shape": (W[v].shape[0],)})
    return nodes


def d_span(topo, W, U, Z, tol=1e-3):
    F, R, worst = {}, {}, 0
    for v in reversed(range(len(topo))):
        nd = topo[v]
        F[v] = np_apply(W[v], [F[c] for c in nd["children"]] + list(Z[v]))
        y = np_apply(W[v], [R[c] for c in nd["children"]] + list(Z[v]))
        R[v] = y if v == 0 else U[v] @ (U[v].T @ y)
        s = np.linalg.svd(np.stack([F[v], y, R[v]]), compute_uv=False)
        worst = max(worst, int(np.sum(s > tol * s[0])) if s[0] > 0 else 0)
    return worst


def mp_replay_factory(topo, W, U, Z, M_hat):
    def replay(out, c):
        import mpmath as mp
        mp.mp.dps = 50
        conv = lambda a: np.vectorize(mp.mpf, otypes=[object])(a)
        Wm = [conv(w) for w in W]; Um = [None if u is None else conv(u) for u in U]
        Zm = [[conv(z) for z in zs] for zs in Z]

        def app(T, xs):
            o = T
            for x in reversed(xs):
                o = np.tensordot(o, x, axes=([o.ndim - 1], [0]))
            return o
        F, R, etas = {}, {}, []
        for v in reversed(range(len(topo))):
            nd = topo[v]
            F[v] = app(Wm[v], [F[c] for c in nd["children"]] + Zm[v])
            y = app(Wm[v], [R[c] for c in nd["children"]] + Zm[v])
            if v == 0:
                R[v] = y
            else:
                R[v] = Um[v].dot(Um[v].T.dot(y))
                den = mp.mpf(M_hat)
                for cc in nd["children"]:
                    den *= mp.sqrt(sum(t * t for t in R[cc]))
                etas.append(mp.sqrt(sum(t * t for t in (y - R[v]))) / den)
        E = mp.sqrt(sum(t * t for t in (F[0] - R[0])))
        eta = max(etas)
        G = cert.G_k_mp(len(topo), eta) if eta <= 1 else mp.mpf(2)
        B = G * mp.mpf(M_hat) ** len(topo)
        ratio = E / B
        return {"mp_E": str(E), "mp_eta": str(eta), "mp_BR": str(B), "mp_ratio": str(ratio),
                "survives_replay": bool(ratio > 1),
                "label_after_replay": "THEOREM_R_COUNTEREXAMPLE_CANDIDATE" if ratio > 1 else "WITHIN_CERTIFICATE_AFTER_REPLAY"}
    return replay


# ----------------------------------------------------------------------------------------- campaigns
def optimise(topo, chi, r, variant, B, steps, seed, objective="ratio", eta_target=None, lam=1e3):
    gen = torch.Generator().manual_seed(seed)
    adv = Adversary(topo, chi, r, variant, B, gen)
    opt = torch.optim.Adam(adv.params(), lr=0.03)
    sched = torch.optim.lr_scheduler.CosineAnnealingLR(opt, steps, eta_min=0.002)
    k = len(topo)
    for step in range(steps):
        refresh = (step % 100 == 0)
        E, eta_s, _ = adv.forward(gen, refresh=refresh)
        if objective == "ratio":
            loss = -(torch.log(E + 1e-30) - torch.log(t_G(eta_s, k) + 1e-30)).sum()
        else:
            loss = (-E + lam * torch.relu(eta_s - eta_target) ** 2).sum()
        opt.zero_grad(); loss.backward(); opt.step(); sched.step()
    adv.tensors(gen, refresh=True)
    return adv


def estimate(adv, b, rng):
    topo = adv.topo
    W, U, Z = adv.export(b)
    low = [opnorm_lower(T, rng) for T in W]
    M_low = max(low)
    o = evaluate(build_nodes(topo, W, U, Z, M_low, "power_iteration_lower_bound"), "root")
    c_est = cert.certificate(o["k"], min(o["eta_hat"], 1.0), M_low, o["leaf_product"], o["E_obs"], o["F_norm"], "estimate")
    return {"W": W, "U": U, "Z": Z, "low": low, "M_low": M_low, "ratio_est": c_est.ratio_obs_to_BR,
            "eta_hat_est": o["eta_hat"], "E_obs": o["E_obs"]}


def finalize(adv, b, est, meta, use_net):
    """One PMT instance with rigorous M_hat. The arity-2 net bound is computed when use_net (always for chi = 2)."""
    topo, W, U, Z = adv.topo, est["W"], est["U"], est["Z"]
    flat = [flattening_norm_nd(T) for T in W]
    net = [opnorm_net_upper(T) if (use_net or T.shape[0] == 2) else None for T in W]
    up = [min(f, n) if n is not None else f for f, n in zip(flat, net)]
    M_up = max(up)
    prov = "flattening (coisometric)" if adv.variant == "coiso" else (
        "flattening+net" if all(n is not None for n in net) else "flattening")
    meta = dict(meta)
    meta.update({"restart": b, "M_up_nodes": up, "M_low_nodes": est["low"], "M_flat_nodes": flat, "M_net_nodes": net,
                 "M_up": M_up, "M_low": est["M_low"], "M_gap_rel": (M_up - est["M_low"]) / est["M_low"],
                 "ratio_est": est["ratio_est"], "eta_hat_est": est["eta_hat_est"], "d_span": d_span(topo, W, U, Z),
                 "arities": [len(nd["children"]) + nd["n_leaves"] for nd in topo], "net_bound_computed": bool(use_net)})
    return {"nodes": build_nodes(topo, W, U, Z, M_up, prov), "root": "root", "meta": meta, "M_provenance": prov,
            "expected_violation": False, "replay": mp_replay_factory(topo, W, U, Z, M_up),
            "frozen": {"topology": topo, "W": [w.tolist() for w in W], "U": [None if u is None else u.tolist() for u in U],
                       "Z": [[z.tolist() for z in zs] for zs in Z]}}


def config_instances(adv, meta, rng, key):
    ests = [estimate(adv, b, rng) for b in range(adv.B)]
    best = int(np.argmax([e[key] for e in ests]))
    for b, est in enumerate(ests):
        inst = finalize(adv, b, est, dict(meta, best_restart_by=key, is_best_restart=(b == best)), use_net=(b == best))
        inst["save_frozen"] = b == best
        yield inst


TOPOLOGIES = ["chain", "balanced", "star", "random"]


def instances(family: str, quick: bool = False):
    B, steps = (4, 200) if quick else (16, 1500)
    rng_np = np.random.default_rng(stable_seed("F7-final", family))
    if family == "F7":
        ks = [3, 4] if quick else [3, 4, 5, 7]
        grid = [(v, t, k, chi, r) for v in ("coiso", "opnorm") for t in TOPOLOGIES for k in ks
                for chi in (2, 3) for r in range(1, chi)]
        for variant, kind, k, chi, r in grid:
            seed = stable_seed("F7", variant, kind, k, chi, r)
            topo = topology(kind, k, np.random.default_rng(seed))
            adv = optimise(topo, chi, r, variant, B, steps, seed)
            yield from config_instances(adv, {"family": "F7", "variant": variant, "topology": kind, "k_param": k,
                                              "chi": chi, "rank": r, "seed": seed}, rng_np, "ratio_est")
    elif family == "F7R":
        ks = [3] if quick else [3, 5, 7]
        etas = [0.3, 0.9] if quick else [round(0.1 * i, 1) for i in range(1, 11)]
        for kind, k, et in itertools.product(["chain", "balanced"], ks, etas):
            seed = stable_seed("F7R", kind, k, et)
            topo = topology(kind, k, np.random.default_rng(seed))
            adv = optimise(topo, 2, 1, "opnorm", B, steps, seed, objective="abs_error", eta_target=et)
            yield from config_instances(adv, {"family": "F7R", "variant": "opnorm", "topology": kind, "k_param": k,
                                              "chi": 2, "rank": 1, "seed": seed, "eta_target": et,
                                              "G_k_eta_target": cert.G_k(k, et)}, rng_np, "E_obs")
    else:
        raise ValueError(family)
