"""F4: exact Hierarchical Tucker of smooth functions, point evaluation with frozen HT-SVD projectors.

Construction (SVD selects projectors; the contraction is the PMT instance):
  1. f on the grid {0, 1/3, 2/3, 1}^8, normalised to unit Frobenius norm.
  2. Exact HT-SVD on the balanced binary dimension tree ((01)(23))((45)(67)). U_t holds the left singular
     vectors of the t-matricisation (all numerically nonzero ones, so the format is exact and nested).
     Transfer tensors: B_t = U_t^T (U_t1 kron U_t2), shape (r_t, r_t1, r_t2); root B = <vec f, U_t1 kron U_t2>.
  3. Point evaluation f(i) = contraction with leaf data z_l = U_l[i_l, :] (rows of the leaf bases).
  4. Frozen projectors P_t = diag(1_r, 0) on the node basis (ordered singular vectors); root P = I.
Nested orthonormal U_t make every non-root B_t a coisometry, and the root flattening norm is ||f|| = 1,
so M_hat = 1 by flattening. k = 7 internal nodes.
"""
from __future__ import annotations

import itertools

import numpy as np

from pmt_eval import Node
from seeding import stable_seed

GRID = np.array([0.0, 1 / 3, 2 / 3, 1.0])
FUNCS = {
    "inv_sum": lambda X: 1.0 / (1.0 + X.sum(-1)),
    "gauss_sum": lambda X: np.exp(-(X.sum(-1) ** 2) / 4.0),
    "sin_sum": lambda X: np.sin(X.sum(-1)) + 0.5 * np.cos(2.0 * X.sum(-1) + X[..., 0] * X[..., 7]),
}
TREE = {"t01": ("x0", "x1"), "t23": ("x2", "x3"), "t45": ("x4", "x5"), "t67": ("x6", "x7"),
        "t0123": ("t01", "t23"), "t4567": ("t45", "t67"), "root": ("t0123", "t4567")}
ORDER = ["t01", "t23", "t45", "t67", "t0123", "t4567", "root"]
VARS = {"x%d" % i: [i] for i in range(8)}
for t in ORDER:
    VARS[t] = VARS[TREE[t][0]] + VARS[TREE[t][1]]


def tensor(fname):
    mesh = np.stack(np.meshgrid(*[GRID] * 8, indexing="ij"), -1)
    F = FUNCS[fname](mesh)
    return F / np.linalg.norm(F)


def basis(F, dims, tol=1e-12):
    rest = [d for d in range(8) if d not in dims]
    M = np.transpose(F, dims + rest).reshape(4 ** len(dims), -1)
    U, s, _ = np.linalg.svd(M, full_matrices=False)
    keep = max(1, int(np.sum(s > tol * s[0])))
    return U[:, :keep]


def build_ht(F):
    U = {v: basis(F, VARS[v]) for v in list(VARS) if v != "root"}
    B = {}
    for t in ORDER:
        a, b = TREE[t]
        K = np.kron(U[a], U[b])                                   # row-major: vars(a) then vars(b)
        if t == "root":
            B[t] = (F.reshape(-1) @ K).reshape(1, U[a].shape[1], U[b].shape[1])
        else:
            B[t] = (U[t].T @ K).reshape(U[t].shape[1], U[a].shape[1], U[b].shape[1])
    return U, B


def flattening_norm3(T):
    a, b, c = T.shape
    return float(min(np.linalg.norm(T.reshape(a, b * c), 2),
                     np.linalg.norm(np.transpose(T, (1, 0, 2)).reshape(b, a * c), 2),
                     np.linalg.norm(np.transpose(T, (2, 0, 1)).reshape(c, a * b), 2)))


def diag_proj(dim, r):
    return np.diag((np.arange(dim) < r).astype(float))


def nodes_for_point(U, B, idx, r, M_hat):
    nodes = {}
    for t in ORDER:
        a, b = TREE[t]
        children, leaves, slots = [], [], []
        for c in (a, b):
            if c.startswith("x"):
                leaves.append(U[c][idx[int(c[1:])], :]); slots.append("l")
            else:
                children.append(c); slots.append("c")

        def law(cv, lv, T=B[t], slots=tuple(slots)):
            ci, li, ops = 0, 0, []
            for s in slots:
                if s == "c":
                    ops.append(np.asarray(cv[ci])); ci += 1
                else:
                    ops.append(np.asarray(lv[li])); li += 1
            return np.einsum("kij,i,j->k", T, ops[0], ops[1])

        is_root = t == "root"
        dim = B[t].shape[0]
        P = None if is_root else (lambda y, D=np.diag(diag_proj(dim, r)): D * np.asarray(y))
        nodes[t] = Node(children=children, leaves=leaves, law=law, M_hat=M_hat, M_provenance="flattening",
                        projector=P, is_root=is_root, extra={"output_shape": (dim,)})
    return nodes


def eta_full(B, r, M_hat):
    worst = 0.0
    for t in ORDER[:-1]:
        a, b = TREE[t]
        T = B[t]
        Q = np.eye(T.shape[0]) - diag_proj(T.shape[0], r)
        Pa = np.eye(T.shape[1]) if a.startswith("x") else diag_proj(T.shape[1], r)
        Pb = np.eye(T.shape[2]) if b.startswith("x") else diag_proj(T.shape[2], r)
        worst = max(worst, flattening_norm3(np.einsum("kc,cij,ia,jb->kab", Q, T, Pa, Pb)) / M_hat)
    return worst


def instances(family: str, quick: bool = False):
    fnames = ["inv_sum"] if quick else list(FUNCS)
    for fname in fnames:
        F = tensor(fname)
        U, B = build_ht(F)
        M_hat = max(flattening_norm3(B[t]) for t in ORDER)
        rng = np.random.default_rng(stable_seed("F4", fname))
        points = rng.integers(0, 4, size=(8 if quick else 128, 8))
        for r in [1, 2, 3]:
            ef = eta_full(B, r, M_hat)
            for p_i, idx in enumerate(points):
                meta = {"family": "F4", "variant": fname, "topology": "balanced_dimension_tree", "n_vars": 8,
                        "rank": r, "point_index": p_i, "exact_value": float(F[tuple(idx)]),
                        "node_ranks": {t: int(B[t].shape[0]) for t in ORDER}}
                yield {"nodes": nodes_for_point(U, B, idx, r, M_hat), "root": "root", "meta": meta,
                       "M_provenance": "flattening", "expected_violation": False, "eta_full": ef}
