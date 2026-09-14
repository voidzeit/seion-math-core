"""F6 (positive control) and F8 (constructed negative controls) for the PMT-TN benchmark.

F6: the universal sharp witness of THEOREM_R_v2, Theorem 8.1, on random trees. All spaces are R^2,
    read as C. Non-root law: e^{i theta} * prod(internal children) * prod Re(leaf slots); projector
    Re; root: plain product, P = I. Analytic M = 1. With every theta equal to asin(eta) and
    eta <= eta_c(k), the certificate is attained: E_obs / B_R = 1.

F8: constructed instances that are known in advance to violate the certificate, each with an
    analytic ratio:
  F8a  M underestimated: F6 chain with the root law scaled by lam > 1 while M_hat = 1 is claimed.
       Ratio = lam.
  F8b  Oblique projector P = [[1, c], [0, 0]] at a leaf-only node, with the pipeline measuring leakage
       as the distance to Ran P. Ratio = sqrt(1 + c^2).
  F8c  Self-trace law tr(X) on d x d matrices (true norm sqrt(d)) with M_hat = 1 claimed.
       Ratio = sqrt(d).
"""
from __future__ import annotations

import math

import numpy as np

from pmt_eval import Node


def _c(x):
    x = np.asarray(x, dtype=float).ravel()
    return complex(x[0], x[1])


def _v(z):
    return np.array([z.real, z.imag])


def re_projector(x):
    x = np.asarray(x, dtype=float).ravel()
    return np.array([x[0], 0.0])


def random_tree(rng, k: int, max_arity: int = 3):
    """Random rooted tree on k internal nodes (ids 'n0' = root). Returns children lists and leaf counts."""
    while True:
        parent = [None] + [int(rng.integers(0, i)) for i in range(1, k)]
        kids = {f"n{i}": [] for i in range(k)}
        for i in range(1, k):
            kids[f"n{parent[i]}"].append(f"n{i}")
        if all(len(c) <= max_arity for c in kids.values()):
            break
    leaves = {v: int(rng.integers(0 if kids[v] else 1, 3)) for v in kids}
    return kids, leaves


def witness_nodes(kids: dict, leaves: dict, thetas: dict, root: str = "n0", root_scale: float = 1.0,
                  root_M_claim: float = 1.0) -> dict:
    e0 = np.array([1.0, 0.0])
    nodes = {}
    for v, cs in kids.items():
        is_root = v == root
        th = 0.0 if is_root else thetas[v]
        scale = root_scale if is_root else 1.0

        def law(child_vals, leaf_vals, th=th, scale=scale):
            z = complex(math.cos(th), math.sin(th)) * scale
            for c in child_vals:
                z *= _c(c)
            for l in leaf_vals:
                z *= float(np.asarray(l).ravel()[0])          # Re(leaf) gate
            return _v(z)

        nodes[v] = Node(children=list(cs), leaves=[e0.copy() for _ in range(leaves[v])], law=law,
                        M_hat=root_M_claim if is_root else 1.0,
                        M_provenance="analytic: |prod z| = prod |z|, |Re x| <= |x|" if scale == 1.0
                        else "DELIBERATELY UNDERESTIMATED (F8a)",
                        projector=None if is_root else re_projector, is_root=is_root,
                        extra={"theta": th, "input_shape": (2,)})
    return nodes


# ------------------------------------------------------------------------------ F8 constructions
def f8a_nodes(k: int, theta: float, lam: float) -> dict:
    kids = {f"n{i}": ([f"n{i+1}"] if i + 1 < k else []) for i in range(k)}
    leaves = {v: (0 if kids[v] else 1) for v in kids}
    thetas = {v: theta for v in kids if v != "n0"}
    return witness_nodes(kids, leaves, thetas, root_scale=lam, root_M_claim=1.0)


def f8b_nodes(theta: float, c: float) -> dict:
    P_obl = np.array([[1.0, c], [0.0, 0.0]])
    Pi_range = np.array([[1.0, 0.0], [0.0, 0.0]])            # orthogonal projector onto Ran P_obl
    f = np.array([math.cos(theta), math.sin(theta)])
    n1 = Node(children=[], leaves=[np.array([1.0])], law=lambda cv, lv: f * float(lv[0][0]),
              M_hat=1.0, M_provenance="analytic",
              projector=lambda x: P_obl @ np.asarray(x),
              leak_measure=lambda x: np.asarray(x) - Pi_range @ np.asarray(x),   # careless measurement
              extra={"input_shape": (2,), "construction": "oblique projector, leakage measured orthogonally to its range"})
    root = Node(children=["n1"], leaves=[], law=lambda cv, lv: np.asarray(cv[0]), M_hat=1.0,
                M_provenance="analytic", is_root=True, extra={"input_shape": (2,)})
    return {"n0": root, "n1": n1}


def f8c_nodes(theta: float, d: int) -> dict:
    A = np.zeros((d, d)); A[0, 0], A[1, 1] = 1 / math.sqrt(2), -1 / math.sqrt(2)   # trace 0, unit Frobenius
    Iu = np.eye(d) / math.sqrt(d)
    f = math.cos(theta) * A + math.sin(theta) * Iu
    n1 = Node(children=[], leaves=[np.array([1.0])], law=lambda cv, lv: f * float(lv[0][0]),
              M_hat=1.0, M_provenance="analytic",
              projector=lambda X: float(np.sum(np.asarray(X) * A)) * A,
              extra={"input_shape": (d, d)})
    root = Node(children=["n1"], leaves=[], law=lambda cv, lv: np.array([np.trace(np.asarray(cv[0]))]),
                M_hat=1.0, M_provenance="DELIBERATELY UNDERESTIMATED (F8c): true norm sqrt(d)", is_root=True,
                extra={"input_shape": (d, d)})
    return {"n0": root, "n1": n1}
