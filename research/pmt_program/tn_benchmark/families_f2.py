"""F2 (+ F5 Gaussian-W variant): binary tree tensor network with fixed PCA projectors.

Translation W. Leaves: unit vectors x_l in R^4, drawn as normalize(mu_l + 0.5 noise) with a fixed
mean direction per leaf. Internal node v: bilinear law mu_v(a, b) = W_v(a, b, .), with
W_v in R^{chi_out x chi_l x chi_r} and chi_out = min(chi, chi_l chi_r).
  canonical: the flattening (chi_out, chi_l chi_r) has orthonormal rows -> operator norm <= 1 (exact bound);
  gaussian (F5): random W normalised by its flattening spectral norm -> operator norm <= 1.
M_hat_v = min over the three flattenings of the spectral norm (certified upper bound); M_hat = max_v.
Projectors: fixed before testing. Bottom-up PCA (uncentered second moment) of the REDUCED node outputs
on 512 training inputs, keeping the top-r eigenvectors. Root: identity.
Full-subspace leakage bound: eta_full_v = ||Q_v W_v (P_l x P_r)||_flattening / M_hat.
"""
from __future__ import annotations

import itertools

import numpy as np

from pmt_eval import Node, law_norm_lower_bound
from seeding import stable_seed


def tree_shape(n: int, kind: str, rng):
    def balanced(lo, hi):
        if hi - lo == 1:
            return lo
        mid = (lo + hi) // 2
        return (balanced(lo, mid), balanced(mid, hi))

    def caterpillar(lo, hi):
        t = lo
        for i in range(lo + 1, hi):
            t = (t, i)
        return t

    def random_split(lo, hi):
        if hi - lo == 1:
            return lo
        mid = int(rng.integers(lo + 1, hi))
        return (random_split(lo, mid), random_split(mid, hi))

    return {"balanced": balanced, "caterpillar": caterpillar, "random": random_split}[kind](0, n)


def flattening_norm(T: np.ndarray) -> float:
    a, b, c = T.shape
    return float(min(np.linalg.norm(T.reshape(a, b * c), 2),
                     np.linalg.norm(np.transpose(T, (1, 0, 2)).reshape(b, a * c), 2),
                     np.linalg.norm(np.transpose(T, (2, 0, 1)).reshape(c, a * b), 2)))


def make_W(rng, chi_out, chi_l, chi_r, kind):
    if kind == "canonical":
        Q, _ = np.linalg.qr(rng.normal(size=(chi_l * chi_r, chi_out)))
        return Q.T.reshape(chi_out, chi_l, chi_r)
    W = rng.normal(size=(chi_out, chi_l, chi_r))
    return W / flattening_norm(W)


def build_network(tree, chi, rng, Wkind):
    """Return node specs (children ids, leaf indices, W) in post-order, root last."""
    specs, dims, counter = [], {}, [0]

    def rec(t):
        if not isinstance(t, tuple):
            return ("leaf", t), 4
        (lspec, ldim), (rspec, rdim) = rec(t[0]), rec(t[1])
        vid = f"v{counter[0]}"; counter[0] += 1
        chi_out = min(chi, ldim * rdim)
        specs.append({"id": vid, "left": lspec, "right": rspec, "W": make_W(rng, chi_out, ldim, rdim, Wkind)})
        return ("node", vid), chi_out

    rec(tree)
    specs[-1]["id_root"] = True
    return specs


def contract(W, a, b):
    return np.einsum("kij,i,j->k", W, a, b)


def fit_projectors(specs, train_X, r):
    """Bottom-up PCA on reduced outputs; returns dict id -> projector matrix (root: None)."""
    P, reduced = {}, {}
    for s in specs:
        outs = []
        reduced[s["id"]] = []
        for i, x in enumerate(train_X):
            a = x[s["left"][1]] if s["left"][0] == "leaf" else reduced[s["left"][1]][i]
            b = x[s["right"][1]] if s["right"][0] == "leaf" else reduced[s["right"][1]][i]
            outs.append(contract(s["W"], a, b))
        Y = np.array(outs)
        if s.get("id_root") or r >= Y.shape[1]:
            P[s["id"]] = None if s.get("id_root") else np.eye(Y.shape[1])
        else:
            evals, evecs = np.linalg.eigh(Y.T @ Y)
            U = evecs[:, ::-1][:, :r]
            P[s["id"]] = U @ U.T
        Pm = P[s["id"]]
        reduced[s["id"]] = [y if Pm is None else Pm @ y for y in outs]
    return P


def eta_full(specs, P, M_hat):
    worst = 0.0
    for s in specs:
        if s.get("id_root"):
            continue
        W = s["W"]
        Pl = np.eye(W.shape[1]) if s["left"][0] == "leaf" else P[s["left"][1]]
        Pr = np.eye(W.shape[2]) if s["right"][0] == "leaf" else P[s["right"][1]]
        Q = np.eye(W.shape[0]) - P[s["id"]]
        T = np.einsum("ka,aij,ib,jc->kbc", Q, W, Pl, Pr)
        worst = max(worst, flattening_norm(T) / M_hat)
    return worst


def nodes_for_input(specs, P, x, M_hat):
    nodes = {}
    for s in specs:
        vid = "root" if s.get("id_root") else s["id"]
        children, leaves, slots = [], [], []
        for side in ("left", "right"):
            spec = s[side]
            if spec[0] == "leaf":
                leaves.append(x[spec[1]]); slots.append("l")
            else:
                children.append(spec[1]); slots.append("c")

        def law(child_vals, leaf_vals, W=s["W"], slots=tuple(slots)):
            ci, li, ops = 0, 0, []
            for sl in slots:
                if sl == "c":
                    ops.append(np.asarray(child_vals[ci])); ci += 1
                else:
                    ops.append(np.asarray(leaf_vals[li])); li += 1
            return contract(W, ops[0], ops[1])

        Pm = P[s["id"]]
        nodes[vid] = Node(children=children, leaves=leaves, law=law, M_hat=M_hat,
                          M_provenance="flattening", projector=None if Pm is None else (lambda y, Pm=Pm: Pm @ np.asarray(y)),
                          is_root=bool(s.get("id_root")), extra={"output_shape": (s["W"].shape[0],)})
    return nodes


def instances(family: str, quick: bool = False):
    ns = [8] if quick else [8, 16, 32]
    chis = [8] if quick else [8, 16]
    ranks = [2, 4] if quick else [2, 4, 6]
    Wkinds = ["canonical", "gaussian"]
    seeds = [0] if quick else [0, 1]
    n_train, n_test = (128, 8) if quick else (512, 64)
    kinds = [("balanced", None), ("caterpillar", None)] + [("random", i) for i in range(1 if quick else 3)]
    for n, chi, r, Wk, seed, (kind, idx) in itertools.product(ns, chis, ranks, Wkinds, seeds, kinds):
        rng = np.random.default_rng(stable_seed("F2", n, chi, Wk, seed, kind, idx))
        tree = tree_shape(n, kind, rng)
        specs = build_network(tree, chi, rng, Wk)
        M_hat = max(flattening_norm(s["W"]) for s in specs)
        mus = rng.normal(size=(n, 4))

        def sample(m):
            X = mus[None, :, :] + 0.5 * rng.normal(size=(m, n, 4))
            return X / np.linalg.norm(X, axis=2, keepdims=True)

        P = fit_projectors(specs, sample(n_train), r)
        ef = eta_full(specs, P, M_hat)
        # validator: sampled lower bound of the operator norm of two node laws vs M_hat
        vrng = np.random.default_rng(seed)
        lows = []
        for s in (specs[0], specs[-1]):
            law = lambda cv, lv, W=s["W"]: contract(W, lv[0], lv[1])
            lows.append(law_norm_lower_bound(law, [], [(s["W"].shape[1],), (s["W"].shape[2],)], vrng, restarts=4, iters=20))
        for t, x in enumerate(sample(n_test)):
            meta = {"family": "F5" if Wk == "gaussian" else "F2", "variant": Wk,
                    "topology": kind if idx is None else f"random{idx}", "n": n, "chi": chi, "rank": r,
                    "seed": seed, "test_index": t, "M_lower_sampled_max": max(lows)}
            yield {"nodes": nodes_for_input(specs, P, x, M_hat), "root": "root", "meta": meta,
                   "M_provenance": "flattening", "expected_violation": False, "eta_full": ef}
