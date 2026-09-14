"""F1 (+ F5 data variants): matrix products under bracketing trees with adaptive two-sided truncation.

Translation L. Leaves are matrices A_i in R^{chi x chi} with unit Frobenius norm. An internal node
multiplies its two ordered operands: mu(X, Y) = X Y, a bilinear map with operator norm exactly 1
in Frobenius norms (||XY||_F <= ||X||_op ||Y||_F <= ||X||_F ||Y||_F, attained by rank-one matrices).
Non-root node projector: two-sided rank-r truncation P(Z) = U_r U_r^T Z V_r V_r^T with (U_r, V_r) the
top-r singular pairs of the REDUCED intermediate mu(R_children). It is chosen adaptively, and the
run is certified conditionally on the frozen projector (preregistration §2.1).
Root: P = I, so E_obs is the ordinary truncated-product error.
"""
from __future__ import annotations

import itertools

import numpy as np

from pmt_eval import Node
from seeding import stable_seed


def make_matrix(rng, chi: int, data: str) -> np.ndarray:
    if data.startswith("decay_"):
        alpha = float(data.split("_")[1])
        U, _ = np.linalg.qr(rng.normal(size=(chi, chi)))
        V, _ = np.linalg.qr(rng.normal(size=(chi, chi)))
        A = U @ np.diag(np.exp(-alpha * np.arange(chi))) @ V.T
    elif data == "gaussian":
        A = rng.normal(size=(chi, chi))
    elif data == "orthogonal":
        A, _ = np.linalg.qr(rng.normal(size=(chi, chi)))
    else:
        raise ValueError(data)
    return A / np.linalg.norm(A)


def bracketing(n: int, kind: str, rng):
    """Binary tree over leaves 0..n-1 as nested tuples."""
    def left(lo, hi):
        t = lo
        for i in range(lo + 1, hi):
            t = (t, i)
        return t

    def right(lo, hi):
        t = hi - 1
        for i in range(hi - 2, lo - 1, -1):
            t = (i, t)
        return t

    def balanced(lo, hi):
        if hi - lo == 1:
            return lo
        mid = (lo + hi) // 2
        return (balanced(lo, mid), balanced(mid, hi))

    def random_split(lo, hi):
        if hi - lo == 1:
            return lo
        mid = int(rng.integers(lo + 1, hi))
        return (random_split(lo, mid), random_split(mid, hi))

    return {"left": left, "right": right, "balanced": balanced, "random": random_split}[kind](0, n)


def truncation_factory(r: int):
    def factory(Z):
        Z = np.asarray(Z)
        if r >= min(Z.shape):
            return lambda X: np.asarray(X)
        U, s, Vt = np.linalg.svd(Z)
        Ur, Vr = U[:, :r], Vt[:r, :].T
        PL, PR = Ur @ Ur.T, Vr @ Vr.T
        return lambda X: PL @ np.asarray(X) @ PR
    return factory


def build_nodes(tree, mats, r):
    nodes, counter = {}, [0]

    def rec(t, is_root):
        vid = "root" if is_root else f"v{counter[0]}"
        counter[0] += 1
        slots, children, leaves = [], [], []
        for sub in t:
            if isinstance(sub, tuple):
                cid = rec(sub, False)
                children.append(cid); slots.append("c")
            else:
                leaves.append(mats[sub]); slots.append("l")

        def law(child_vals, leaf_vals, slots=tuple(slots)):
            ci, li, ops = 0, 0, []
            for s in slots:
                if s == "c":
                    ops.append(np.asarray(child_vals[ci])); ci += 1
                else:
                    ops.append(np.asarray(leaf_vals[li])); li += 1
            return ops[0] @ ops[1]

        nodes[vid] = Node(children=children, leaves=leaves, law=law, M_hat=1.0,
                          M_provenance="analytic: ||XY||_F <= ||X||_F ||Y||_F",
                          projector_factory=None if is_root else truncation_factory(r),
                          is_root=is_root, extra={"output_shape": mats[0].shape})
        return vid

    rec(tree, True)
    return nodes


def exact_product(mats):
    P = mats[0]
    for A in mats[1:]:
        P = P @ A
    return P


def instances(family: str, quick: bool = False):
    ns = [4, 8] if quick else [4, 8, 16, 32]
    chis = [8] if quick else [8, 16, 32]
    datas = ["decay_0.3", "decay_1.0", "gaussian", "orthogonal"]
    seeds = [0] if quick else [0, 1, 2]
    for n, chi, data, seed in itertools.product(ns, chis, datas, seeds):
        rng = np.random.default_rng(stable_seed("F1", n, chi, data, seed))
        mats = [make_matrix(rng, chi, data) for _ in range(n)]
        ranks = sorted({1, 2, 4, chi // 2})
        topologies = [("left", None), ("right", None), ("balanced", None)] + [("random", i) for i in range(2 if quick else 5)]
        for r, (kind, idx) in itertools.product(ranks, topologies):
            tree = bracketing(n, kind, np.random.default_rng(stable_seed("F1-topology", n, seed, kind, idx)))
            nodes = build_nodes(tree, mats, r)
            meta = {"family": "F5" if data in ("gaussian", "orthogonal") else "F1", "variant": data,
                    "topology": kind if idx is None else f"random{idx}", "n": n, "chi": chi, "rank": r,
                    "seed": seed, "cost_proxy_factored": int((n - 1) * r * chi * chi)}
            yield {"nodes": nodes, "root": "root", "meta": meta, "M_provenance": "analytic",
                   "expected_violation": False}
