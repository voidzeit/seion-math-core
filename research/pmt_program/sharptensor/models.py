"""Contract-then-truncate tree models used by the SharpTensor 0.1 benchmarks.

Every model realises, for each internal node ``v``,

  ``y_v = μ_v(R_children)``,  ``R_v = P_v y_v``,

with ``P_v`` the exact orthogonal projector onto the span of the top ``r_v`` left singular vectors of
``y_v`` (Frobenius inner product), so ``d_v = ‖y_v − P_v y_v‖ = √(Σ_{j>r_v} σ_j²)``. The root is not
truncated. Values are held in *canonical factored form* ``R = Q S`` with ``Q`` an isometry (explicit
or implicit), so the singular values of ``y_v`` are those of a small local matrix. A dense exact
reference is computed for validation on small instances.

Models:

* ``MatProdTree`` (B1): balanced binary tree, ``μ(X, Y) = (XY + s·YX)/(1+|s|)`` on ``d×d`` matrices.
  ``‖μ‖ ≤ 1`` analytically (submultiplicativity of the Frobenius norm). ``s = −1`` (commutator) with
  nearly commuting leaves produces controlled cancellation.
* ``MpoMpsChain`` (B2): application of an MPO to an MPS with bond truncation, as the chain
  ``L_k = μ_k(L_{k−1}, W_k)`` (contraction over one bond index; ``‖μ_k‖ ≤ 1`` by Cauchy–Schwarz).
* ``HTTree`` (B3): hierarchical-Tucker style contraction ``μ_v(U_l, U_r) = (U_l ⊗ U_r) B_v``;
  ``‖μ_v‖ ≤ ‖B_v‖₂`` (spectral norm of the transfer matrix, computed numerically).
"""

from __future__ import annotations

import math
import time
from dataclasses import dataclass, field

import numpy as np

from .certificate import Leaf, Node, Run

FLOAT_BYTES = 8


def _svd_cost(m: int, n: int) -> float:
    a, b = max(m, n), min(m, n)
    return 4.0 * a * b * b


def _qr_cost(m: int, n: int) -> float:
    a, b = max(m, n), min(m, n)
    return 2.0 * a * b * b


def truncate_small(M: np.ndarray, r: int | None):
    """Thin SVD of the local matrix and rank-``r`` truncation (``None`` keeps everything)."""
    U, s, Vt = np.linalg.svd(M, full_matrices=False)
    full = int(np.sum(s > 0)) if s.size else 0
    keep = len(s) if r is None else max(0, min(int(r), len(s)))
    resid = float(math.sqrt(float(np.sum(s[keep:] ** 2)))) if keep < len(s) else 0.0
    return U[:, :keep], s[:keep], Vt[:keep, :], resid, s, full


@dataclass
class Accounting:
    flops: float = 0.0
    stored: int = 0

    def matmul(self, a: int, b: int, c: int):
        self.flops += float(a) * b * c


@dataclass
class Result:
    run: Run
    accounting: Accounting
    actual_error: float | None
    singular_values: dict = field(default_factory=dict)
    child_norm_products: dict = field(default_factory=dict)
    full_ranks: dict = field(default_factory=dict)
    local_shapes: dict = field(default_factory=dict)
    seconds: float = 0.0


# ---------------------------------------------------------------------------
# B1 — mixed matrix-product tree
# ---------------------------------------------------------------------------


class MatProdTree:
    name = "B1_matprod_tree"

    def __init__(self, depth: int = 4, d: int = 32, s: float = 1.0, decay: float = 3.0,
                 noise: float = 1e-3, seed: int = 0):
        self.depth, self.d, self.s = depth, d, float(s)
        rng = np.random.default_rng(seed)
        Q, _ = np.linalg.qr(rng.standard_normal((d, d)))
        self.leaves = []
        for _ in range(2 ** depth):
            lam = np.exp(-np.arange(d) / decay) * rng.choice([-1.0, 1.0], size=d) * rng.uniform(0.5, 1.5, d)
            Z = Q @ np.diag(lam) @ Q.T + noise * rng.standard_normal((d, d))
            self.leaves.append(Z)
        # node names: ("n", level, index); level 0 = parents of leaves
        self.internal = []
        for lev in range(depth):
            for i in range(2 ** (depth - lev - 1)):
                self.internal.append(f"n{lev}_{i}")
        self.root = f"n{depth - 1}_0"

    def children(self, name):
        lev, i = map(int, name[1:].split("_"))
        if lev == 0:
            return [f"z{2 * i}", f"z{2 * i + 1}"]
        return [f"n{lev - 1}_{2 * i}", f"n{lev - 1}_{2 * i + 1}"]

    def law(self, X, Y):
        return (X @ Y + self.s * (Y @ X)) / (1.0 + abs(self.s))

    def dense_exact(self):
        vals = {f"z{i}": Z for i, Z in enumerate(self.leaves)}
        for name in self.internal:
            a, b = self.children(name)
            vals[name] = self.law(vals[a], vals[b])
        return vals[self.root]

    def M_lower_estimate(self, iters: int = 6, seed: int = 1) -> float:
        """Lower bound on ‖μ‖ by alternating maximisation (rank-one search)."""
        d = self.d
        rng = np.random.default_rng(seed)
        X = rng.standard_normal((d, d))
        X /= np.linalg.norm(X)
        Y = rng.standard_normal((d, d))
        Y /= np.linalg.norm(Y)
        best = 0.0
        for _ in range(iters):
            # maximise over X for fixed Y: linear map X ↦ law(X, Y)
            A = np.stack([self.law(E.reshape(d, d), Y).ravel() for E in np.eye(d * d)], axis=1)
            u, sv, vt = np.linalg.svd(A, full_matrices=False)
            X = vt[0].reshape(d, d)
            B = np.stack([self.law(X, E.reshape(d, d)).ravel() for E in np.eye(d * d)], axis=1)
            u, sv, vt = np.linalg.svd(B, full_matrices=False)
            Y = vt[0].reshape(d, d)
            best = max(best, float(np.linalg.norm(self.law(X, Y))))
        return best

    def execute(self, ranks: dict | None = None, with_exact: bool = True) -> Result:
        d, s = self.d, self.s
        acc = Accounting()
        vals = {}  # name -> (Q, S)
        for i, Z in enumerate(self.leaves):
            vals[f"z{i}"] = (np.eye(d), Z)
        leaves = [Leaf(f"z{i}", float(np.linalg.norm(Z))) for i, Z in enumerate(self.leaves)]
        nodes, svals, cprods, fulls, shapes = [], {}, {}, {}, {}
        _t0 = time.perf_counter()
        for name in self.internal:
            a, b = self.children(name)
            Q1, S1 = vals[a]
            Q2, S2 = vals[b]
            k1, k2 = Q1.shape[1], Q2.shape[1]
            left = S1 @ Q2 @ S2  # XY = Q1 (S1 Q2 S2)
            acc.matmul(k1, d, k2)
            acc.matmul(k1, k2, d)
            parts_Q, parts_S = [Q1], [left]
            if s != 0.0:
                right = S2 @ Q1 @ S1  # YX = Q2 (S2 Q1 S1)
                acc.matmul(k2, d, k1)
                acc.matmul(k2, k1, d)
                parts_Q.append(Q2)
                parts_S.append(s * right)
            Qc = np.concatenate(parts_Q, axis=1)
            Sc = np.concatenate(parts_S, axis=0) / (1.0 + abs(s))
            Qy, Ry = np.linalg.qr(Qc)
            acc.flops += _qr_cost(*Qc.shape)
            Sy = Ry @ Sc
            acc.matmul(Ry.shape[0], Ry.shape[1], d)
            is_root = name == self.root
            r = None if (is_root or ranks is None) else ranks.get(name)
            U, sig, Vt, resid, s_all, full = truncate_small(Sy, r)
            acc.flops += _svd_cost(*Sy.shape)
            Qn = Qy @ U
            acc.matmul(d, U.shape[0], U.shape[1])
            Sn = sig[:, None] * Vt
            vals[name] = (Qn, Sn)
            acc.stored += FLOAT_BYTES * (Qn.size + Sn.size)
            cprod = math.prod(float(np.linalg.norm(vals[c][1])) if c.startswith("n") else
                              float(np.linalg.norm(self.leaves[int(c[1:])])) for c in (a, b))
            svals[name], cprods[name], fulls[name] = s_all, cprod, len(s_all)
            shapes[name] = Sy.shape
            k_op = [float(np.linalg.norm(S2, 2)), float(np.linalg.norm(S1, 2))]
            nodes.append(Node(name, [a, b], 1.0, "analytic: ‖XY+sYX‖_F ≤ (1+|s|)‖X‖_F‖Y‖_F", True,
                              0.0 if is_root else resid, float(np.linalg.norm(sig)), is_root,
                              rank=len(sig), rank_full=len(s_all), K_op=k_op,
                              K_op_method="analytic ‖XA‖_F ≤ ‖X‖_F‖A‖_2 with float64 spectral norms",
                              K_op_rigorous=True))
        run = Run(leaves, nodes, self.root, meta={"model": self.name, "d": d, "s": s, "depth": self.depth})
        actual = None
        if with_exact:
            F = self.dense_exact()
            Qr, Sr = vals[self.root]
            actual = float(np.linalg.norm(F - Qr @ Sr))
        return Result(run, acc, actual, svals, cprods, fulls, shapes, time.perf_counter() - _t0)

    def dense_cost(self) -> Accounting:
        acc = Accounting()
        for _ in self.internal:
            acc.matmul(self.d, self.d, self.d)
            if self.s != 0.0:
                acc.matmul(self.d, self.d, self.d)
            acc.stored += FLOAT_BYTES * self.d * self.d
        return acc


# ---------------------------------------------------------------------------
# B2 — MPO applied to MPS with bond truncation
# ---------------------------------------------------------------------------


class MpoMpsChain:
    name = "B2_mpo_mps_chain"

    def __init__(self, sites: int = 12, phys: int = 2, chi: int = 6, wbond: int = 3, seed: int = 0,
                 eps: float = 0.1, gaussian: bool = False, entangle: float = 0.3):
        """`gaussian=True`: unnormalised Gaussian cores (exploratory control). Default: left-canonical
        MPS (isometric cores) and the MPO of `I + ε H` with `H = Σ_k h_k + Σ_k J_k (h'_k ⊗ h''_{k+1})`
        (bond dimension 3), a one-step linearised evolution."""
        self.N, self.p, self.chi, self.w = sites, phys, chi, wbond
        rng = np.random.default_rng(seed)
        self.W = []
        if not gaussian:
            self.w = 3
            chis = [1]
            for k in range(sites - 1):
                chis.append(min(chi, phys ** (k + 1), phys ** (sites - k - 1)))
            chis.append(1)
            I = np.eye(phys)
            for k in range(sites):
                G = entangle * rng.standard_normal((chis[k] * phys, chis[k + 1]))
                G[: min(G.shape), : min(G.shape)] += np.eye(min(G.shape))
                Q, _ = np.linalg.qr(G)
                A = Q.reshape(chis[k], phys, chis[k + 1])
                if k == sites - 1:
                    A = A / np.linalg.norm(A)
                h = rng.standard_normal((phys, phys)); h = (h + h.T) / 2; h /= np.linalg.norm(h, 2)
                g1 = rng.standard_normal((phys, phys)); g1 = (g1 + g1.T) / 2; g1 /= np.linalg.norm(g1, 2)
                g2 = rng.standard_normal((phys, phys)); g2 = (g2 + g2.T) / 2; g2 /= np.linalg.norm(g2, 2)
                Ob = np.zeros((3, phys, phys, 3))
                Ob[0, :, :, 0] = I
                Ob[0, :, :, 1] = math.sqrt(eps) * g1
                Ob[0, :, :, 2] = eps * h
                Ob[1, :, :, 2] = math.sqrt(eps) * g2
                Ob[2, :, :, 2] = I
                if k == 0:
                    O = Ob[0:1]
                elif k == sites - 1:
                    Ob[0, :, :, 2] = I + eps * h  # identity path completes at the last site
                    O = Ob[:, :, :, 2:3]
                else:
                    O = Ob
                if sites == 1:
                    O = Ob[0:1, :, :, 2:3]
                T = np.einsum("apqb,cqe->acpbe", O, A).reshape(O.shape[0] * A.shape[0], phys,
                                                                O.shape[3] * A.shape[2])
                self.W.append(T)
            self.internal = [f"L{k}" for k in range(1, sites + 1)]
            self.root = f"L{sites}"
            return
        chis = [1] + [chi] * (sites - 1) + [1]
        ws = [1] + [wbond] * (sites - 1) + [1]
        for k in range(sites):
            A = rng.standard_normal((chis[k], phys, chis[k + 1])) / math.sqrt(chis[k] * phys)
            O = rng.standard_normal((ws[k], phys, phys, ws[k + 1])) / math.sqrt(ws[k] * phys)
            # combined site tensor (a·c, p, b·e)
            T = np.einsum("apqb,cqe->acpbe", O, A).reshape(ws[k] * chis[k], phys, ws[k + 1] * chis[k + 1])
            self.W.append(T)
        self.internal = [f"L{k}" for k in range(1, sites + 1)]
        self.root = f"L{sites}"

    def children(self, name):
        k = int(name[1:])
        return [f"L{k - 1}" if k > 1 else "L0", f"W{k}"]

    def dense_exact(self):
        L = np.ones((1, 1))
        for T in self.W:
            L = np.einsum("pa,aqb->pqb", L, T).reshape(-1, T.shape[2])
        return L

    def execute(self, ranks: dict | None = None, with_exact: bool = True) -> Result:
        acc = Accounting()
        leaves = [Leaf("L0", 1.0)] + [Leaf(f"W{k + 1}", float(np.linalg.norm(T))) for k, T in enumerate(self.W)]
        cores = []  # implicit isometry: list of (r_prev, p, r) cores
        S = np.ones((1, 1))  # remainder (r × a)
        prevR = 1.0
        nodes, svals, cprods, fulls, shapes = [], {}, {}, {}, {}
        _t0 = time.perf_counter()
        for k, T in enumerate(self.W, start=1):
            name = f"L{k}"
            a, p, b = T.shape
            Mloc = np.einsum("ra,aqb->rqb", S, T)
            acc.flops += float(S.shape[0]) * a * p * b
            r_prev = S.shape[0]
            Mmat = Mloc.reshape(r_prev * p, b)
            is_root = name == self.root
            r = None if (is_root or ranks is None) else ranks.get(name)
            U, sig, Vt, resid, s_all, full = truncate_small(Mmat, r)
            acc.flops += _svd_cost(*Mmat.shape)
            cores.append(U.reshape(r_prev, p, U.shape[1]))
            S = sig[:, None] * Vt
            acc.stored += FLOAT_BYTES * (U.size + S.size)
            cprod = prevR * float(np.linalg.norm(T))
            svals[name], cprods[name], fulls[name] = s_all, cprod, len(s_all)
            shapes[name] = Mmat.shape
            k_op = [float(np.linalg.norm(T.reshape(a, p * b), 2)), None]
            nodes.append(Node(name, self.children(name), 1.0,
                              "analytic: contraction over one index, Cauchy–Schwarz", True,
                              0.0 if is_root else resid, float(np.linalg.norm(sig)), is_root,
                              rank=len(sig), rank_full=len(s_all), K_op=k_op,
                              K_op_method="analytic: x ↦ x·mat(W) has norm ‖mat(W)‖_2 (float64 SVD)",
                              K_op_rigorous=True))
            prevR = float(np.linalg.norm(sig))
        run = Run(leaves, nodes, self.root, meta={"model": self.name, "sites": self.N, "chi": self.chi, "w": self.w})
        actual = None
        if with_exact:
            F = self.dense_exact()
            Q = np.ones((1, 1))
            for C in cores:
                Q = np.einsum("pr,rqs->pqs", Q, C).reshape(-1, C.shape[2])
            actual = float(np.linalg.norm(F - Q @ S))
        return Result(run, acc, actual, svals, cprods, fulls, shapes, time.perf_counter() - _t0)

    def untruncated_bond_dims(self):
        return [T.shape[2] for T in self.W]


# ---------------------------------------------------------------------------
# B3 — hierarchical Tucker style contraction
# ---------------------------------------------------------------------------


def _random_ht(rng, depth, n, k_leaf, k_int, decay, orthogonal=True, scale=1.0):
    """A random HT tensor. `orthogonal`: orthonormal leaf bases and orthonormal-column transfer
    matrices below the root (orthogonal HT format), root core with decaying entries and norm `scale`."""
    U = [np.linalg.qr(rng.standard_normal((n, k_leaf)))[0] for _ in range(2 ** depth)]
    B = {}
    for lev in range(depth):
        for i in range(2 ** (depth - lev - 1)):
            kin = k_leaf if lev == 0 else k_int
            is_root = lev == depth - 1
            kout = 1 if is_root else k_int
            G = rng.standard_normal((kin * kin, kout))
            if orthogonal and not is_root:
                B[f"h{lev}_{i}"] = np.linalg.qr(G)[0]
            elif orthogonal and is_root:
                core = rng.standard_normal((kin, kin)) * np.exp(-np.add.outer(np.arange(kin), np.arange(kin)) / decay)
                v = core.reshape(-1, 1)
                B[f"h{lev}_{i}"] = scale * v / np.linalg.norm(v)
            else:
                Ub, sb, Vb = np.linalg.svd(G, full_matrices=False)
                sb = np.exp(-np.arange(len(sb)) / decay)
                B[f"h{lev}_{i}"] = (Ub * sb) @ Vb
    return U, B


def _function_tensor(n: int, dims: int, kind: str) -> np.ndarray:
    grid = (np.arange(n) + 0.5) / n
    mesh = np.meshgrid(*([grid] * dims), indexing="ij")
    s = sum(mesh)
    if kind == "inverse":
        X = 1.0 / (1.0 + s)
    elif kind == "gauss":
        X = np.exp(-sum(m ** 2 for m in mesh))
    else:
        raise ValueError(kind)
    return X / np.linalg.norm(X)


def _hsvd_weighted(X: np.ndarray, depth: int, n: int, k: int):
    """Weighted-gauge HT of a dense tensor (balanced dimension tree, rank cap ``k``).

    Node basis ``W_t = U_t diag(σ_t)`` (left singular vectors scaled by the singular values of the
    matricisation), transfer ``B_t = (W_l ⊗ W_r)^+ W_t``. Used only to *construct* inputs.
    """
    dims = 2 ** depth
    W = {}
    # leaves
    for i in range(dims):
        Xm = np.moveaxis(X, i, 0).reshape(n, -1)
        U, s, _ = np.linalg.svd(Xm, full_matrices=False)
        r = min(k, len(s))
        W[f"u{i}"] = U[:, :r] * s[:r]
    B = {}
    for lev in range(depth):
        span = 2 ** (lev + 1)
        for i in range(2 ** (depth - lev - 1)):
            modes = list(range(i * span, (i + 1) * span))
            Xm = np.moveaxis(X, modes, list(range(len(modes)))).reshape(n ** len(modes), -1)
            name = f"h{lev}_{i}"
            left = f"u{2 * i}" if lev == 0 else f"h{lev - 1}_{2 * i}"
            right = f"u{2 * i + 1}" if lev == 0 else f"h{lev - 1}_{2 * i + 1}"
            K = np.kron(W[left], W[right])
            if lev == depth - 1:
                target = Xm.reshape(-1, 1)
            else:
                U, s, _ = np.linalg.svd(Xm, full_matrices=False)
                r = min(k, len(s))
                target = U[:, :r] * s[:r]
            Bt, *_ = np.linalg.lstsq(K, target, rcond=None)
            B[name] = Bt
            W[name] = K @ Bt
    U = [W[f"u{i}"] for i in range(dims)]
    return U, B


def _block_kron_embedding(ka1, ka2, kb1, kb2):
    """Column index maps of blocks U⊗U' and V⊗V' inside [U,V] ⊗ [U',V'] (sizes ka1+kb1, ka2+kb2)."""
    w2 = ka2 + kb2
    uu = [i * w2 + j for i in range(ka1) for j in range(ka2)]
    vv = [(ka1 + i) * w2 + (ka2 + j) for i in range(kb1) for j in range(kb2)]
    return uu, vv


class HTTree:
    """HT arithmetic with intermediate truncation: the sum of two HT tensors, then rounding.

    Sum representation: leaf bases ``W_ℓ = [U_ℓ, V_ℓ]``; at an internal node the transfer matrix
    ``B_v^sum`` maps the ``U⊗U'`` block through ``B_v`` and the ``V⊗V'`` block through ``B'_v``
    (block diagonal, ranks add). The root sums the two scalars-per-column outputs, so the root output is
    ``F₁ + F₂``. Truncation at every non-root node reduces the doubled rank.
    """

    name = "B3_ht_sum_arithmetic"

    def __init__(self, depth: int = 3, n: int = 4, k_leaf: int = 3, k_int: int = 4, decay: float = 1.5,
                 seed: int = 0, alpha: float = 0.1, orthogonal: bool = True, functions: bool = True):
        """`x + α·d` with `x`, `d` random HT tensors (orthogonal format by default; `‖x‖ = 1`,
        `‖d‖ = 1`), followed by rounding. `orthogonal=False` gives the exploratory Gaussian control."""
        self.depth, self.n = depth, n
        rng = np.random.default_rng(seed)
        if functions:
            U1, B1 = _hsvd_weighted(_function_tensor(n, 2 ** depth, "inverse"), depth, n, k_int)
            U2, B2 = _hsvd_weighted(alpha * _function_tensor(n, 2 ** depth, "gauss"), depth, n, k_int)
            k_leaf = U1[0].shape[1]
        else:
            U1, B1 = _random_ht(rng, depth, n, k_leaf, k_int, decay, orthogonal, 1.0)
            U2, B2 = _random_ht(rng, depth, n, k_leaf, k_int, decay, orthogonal, alpha)
        self.U = [np.concatenate([a, b], axis=1) for a, b in zip(U1, U2)]
        self.parts = (U1, B1, U2, B2)
        self.internal, self.B = [], {}
        for lev in range(depth):
            for i in range(2 ** (depth - lev - 1)):
                name = f"h{lev}_{i}"
                self.internal.append(name)
                b1, b2 = B1[name], B2[name]
                ch_a, ch_b = self.children(name)
                ka1 = (U1[int(ch_a[1:])].shape[1] if lev == 0 else B1[ch_a].shape[1])
                kb1 = (U1[int(ch_b[1:])].shape[1] if lev == 0 else B1[ch_b].shape[1])
                ka2 = (U2[int(ch_a[1:])].shape[1] if lev == 0 else B2[ch_a].shape[1])
                kb2 = (U2[int(ch_b[1:])].shape[1] if lev == 0 else B2[ch_b].shape[1])
                is_root = lev == depth - 1
                kout = b1.shape[1] if is_root else b1.shape[1] + b2.shape[1]
                S = np.zeros(((ka1 + ka2) * (kb1 + kb2), kout))
                uu, vv = _block_kron_embedding(ka1, kb1, ka2, kb2)
                if is_root:
                    S[uu, :] = b1
                    S[vv, :] += b2
                else:
                    S[uu, : b1.shape[1]] = b1
                    S[vv, b1.shape[1]:] = b2
                self.B[name] = S
        self.root = f"h{depth - 1}_0"

    def dense_parts_exact(self):
        U1, B1, U2, B2 = self.parts

        def ev(U, B):
            vals = {f"u{i}": u for i, u in enumerate(U)}
            for name in self.internal:
                a, b = self.children(name)
                vals[name] = np.kron(vals[a], vals[b]) @ B[name]
            return vals[self.root]

        return ev(U1, B1) + ev(U2, B2)

    def children(self, name):
        lev, i = map(int, name[1:].split("_"))
        if lev == 0:
            return [f"u{2 * i}", f"u{2 * i + 1}"]
        return [f"h{lev - 1}_{2 * i}", f"h{lev - 1}_{2 * i + 1}"]

    def M_bound(self, name):
        return float(np.linalg.norm(self.B[name], 2))

    def _width(self, child):
        return self.U[int(child[1:])].shape[1] if child.startswith("u") else self.B[child].shape[1]

    def M_lower_estimate(self, name, iters: int = 8, seed: int = 1) -> float:
        """Lower bound on the multilinear norm of `(X, Y) ↦ (X ⊗ Y) B` (alternating maximisation;
        one input row suffices since the map acts row-pair-wise)."""
        B = self.B[name]
        a, b = self.children(name)
        kl, kr = self._width(a), self._width(b)
        rng = np.random.default_rng(seed)
        x = rng.standard_normal(kl); x /= np.linalg.norm(x)
        y = rng.standard_normal(kr); y /= np.linalg.norm(y)
        Bt = B.reshape(kl, kr, B.shape[1])
        best = 0.0
        for _ in range(iters):
            Ax = np.einsum("b,abc->ca", y, Bt)
            x = np.linalg.svd(Ax, full_matrices=False)[2][0]
            Ay = np.einsum("a,abc->cb", x, Bt)
            y = np.linalg.svd(Ay, full_matrices=False)[2][0]
            best = max(best, float(np.linalg.norm(np.einsum("a,b,abc->c", x, y, Bt))))
        return best

    def dense_exact(self):
        vals = {f"u{i}": U for i, U in enumerate(self.U)}
        for name in self.internal:
            a, b = self.children(name)
            vals[name] = np.kron(vals[a], vals[b]) @ self.B[name]
        return vals[self.root]

    def execute(self, ranks: dict | None = None, with_exact: bool = True) -> Result:
        acc = Accounting()
        leaves = [Leaf(f"u{i}", float(np.linalg.norm(U))) for i, U in enumerate(self.U)]
        vals = {f"u{i}": (None, U) for i, U in enumerate(self.U)}  # (Q implicit or None=identity, S)
        Qexp = {f"u{i}": np.eye(self.n) for i in range(len(self.U))}
        nodes, svals, cprods, fulls, shapes = [], {}, {}, {}, {}
        _t0 = time.perf_counter()
        for name in self.internal:
            a, b = self.children(name)
            _, Sa = vals[a]
            _, Sb = vals[b]
            B = self.B[name]
            K = np.kron(Sa, Sb)
            acc.flops += float(K.size)
            Mloc = K @ B
            acc.matmul(K.shape[0], K.shape[1], B.shape[1])
            is_root = name == self.root
            r = None if (is_root or ranks is None) else ranks.get(name)
            U, sig, Vt, resid, s_all, full = truncate_small(Mloc, r)
            acc.flops += _svd_cost(*Mloc.shape)
            S = sig[:, None] * Vt
            vals[name] = (U, S)
            acc.stored += FLOAT_BYTES * (U.size + S.size)
            if with_exact:
                Qexp[name] = np.kron(Qexp[a], Qexp[b]) @ U
            cprod = float(np.linalg.norm(Sa)) * float(np.linalg.norm(Sb))
            svals[name], cprods[name], fulls[name] = s_all, cprod, len(s_all)
            shapes[name] = Mloc.shape
            kl, kr = Sa.shape[1], Sb.shape[1]
            Bt = B.reshape(kl, kr, B.shape[1])
            T0 = np.einsum("qb,abc->qca", Sb, Bt).reshape(-1, kl)
            T1 = np.einsum("pa,abc->pcb", Sa, Bt).reshape(-1, kr)
            k_op = [float(np.linalg.norm(T0, 2)), float(np.linalg.norm(T1, 2))]
            nodes.append(Node(name, [a, b], self.M_bound(name),
                              "analytic ‖(U_l⊗U_r)B‖_F ≤ ‖B‖_2‖U_l‖_F‖U_r‖_F with float64 ‖B‖_2",
                              True, 0.0 if is_root else resid, float(np.linalg.norm(sig)), is_root,
                              rank=len(sig), rank_full=len(s_all), K_op=k_op,
                              K_op_method="exact slot operator norm via isometric reduction (float64 SVD)",
                              K_op_rigorous=True))
        run = Run(leaves, nodes, self.root, meta={"model": self.name, "depth": self.depth, "n": self.n})
        actual = None
        if with_exact:
            F = self.dense_exact()
            _, S = vals[self.root]
            actual = float(np.linalg.norm(F - Qexp[self.root] @ S))
        return Result(run, acc, actual, svals, cprods, fulls, shapes, time.perf_counter() - _t0)
