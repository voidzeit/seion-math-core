"""Generic PMT evaluation engine for the PMT-TN benchmark.

A run is a finite rooted tree. Internal node v has
  * `children`: ids of internal children,
  * `leaves`:   leaf data (numpy arrays) in its remaining slots,
  * `law(child_values, leaf_values)`: multilinear map (trusted by the family, checked by validators),
  * `M_hat`, `M_provenance`: claimed upper bound on the multilinear operator norm of the law,
  * `projector`: callable value -> value; the ROOT must use the identity (certificate semantics),
  * `leak_measure` (optional): callable value -> vector whose norm is the measured leakage.
    Default: value - projector(value). Negative control F8b overrides it on purpose.
  * `law_sampler` (optional): callable rng -> (child_values, leaf_values) of unit vectors, used by the
    norm lower-bound validator.
  * `input_shapes` (optional): shapes of all slots, used by the orthogonality validator.

Adaptive projectors (chosen from the reduced intermediate during the run) are allowed: the family
passes `projector_factory(reduced_value) -> projector`, and the run is certified conditionally on the
frozen projector it produced.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Callable, Optional

import numpy as np


@dataclass
class Node:
    children: list
    leaves: list
    law: Callable
    M_hat: float
    M_provenance: str
    projector: Optional[Callable] = None
    projector_factory: Optional[Callable] = None
    leak_measure: Optional[Callable] = None
    is_root: bool = False
    extra: dict = field(default_factory=dict)


def _norm(x) -> float:
    return float(np.linalg.norm(np.asarray(x).ravel()))


def evaluate(nodes: dict, root: str) -> dict:
    """Bottom-up evaluation of ambient F and reduced R; returns per-node leakage records."""
    F, R, P_used, records = {}, {}, {}, {}

    def visit(v):
        nd = nodes[v]
        for c in nd.children:
            if c not in F:
                visit(c)
        Fc = [F[c] for c in nd.children]
        Rc = [R[c] for c in nd.children]
        Fv = nd.law(Fc, nd.leaves)
        Rraw = nd.law(Rc, nd.leaves)
        if nd.is_root:
            P = lambda x: x
        elif nd.projector_factory is not None:
            P = nd.projector_factory(Rraw)
        else:
            P = nd.projector
        Rv = P(Rraw)
        leak_vec = nd.leak_measure(Rraw) if nd.leak_measure is not None else (np.asarray(Rraw) - np.asarray(Rv))
        denom = float(np.prod([_norm(r) for r in Rc] + [_norm(z) for z in nd.leaves])) if (Rc or nd.leaves) else 1.0
        F[v], R[v], P_used[v] = Fv, Rv, P
        records[v] = {"leak": _norm(leak_vec) if not nd.is_root else 0.0, "input_norm_product": denom,
                      "M_hat": nd.M_hat, "M_provenance": nd.M_provenance, "is_root": nd.is_root,
                      "n_internal_children": len(nd.children), "n_leaf_slots": len(nd.leaves)}

    visit(root)
    internal = list(nodes.keys())
    k = len(internal)
    leaf_norms = [_norm(z) for nd in nodes.values() for z in nd.leaves]
    M_hat = max(nd.M_hat for nd in nodes.values())
    eta_nodes = {}
    for v, rec in records.items():
        if rec["is_root"] or rec["input_norm_product"] == 0.0:
            eta_nodes[v] = 0.0
        else:
            eta_nodes[v] = rec["leak"] / (M_hat * rec["input_norm_product"])
    return {"F_root": F[root], "R_root": R[root], "E_obs": _norm(np.asarray(F[root]) - np.asarray(R[root])),
            "F_norm": _norm(F[root]), "k": k, "M_hat": M_hat, "eta_hat": max(eta_nodes.values()) if eta_nodes else 0.0,
            "eta_nodes": eta_nodes, "leaf_product": float(np.prod(leaf_norms)) if leaf_norms else 1.0,
            "records": records, "projectors": P_used, "F": F, "R": R}


# ------------------------------------------------------------------------------ validators
def check_projector_orthogonal(P: Callable, shape, rng, trials: int = 8, tol: float = 1e-9) -> dict:
    """Idempotence and self-adjointness on random inputs (Frobenius inner product)."""
    worst_idem, worst_sym = 0.0, 0.0
    for _ in range(trials):
        x = rng.normal(size=shape); y = rng.normal(size=shape)
        Px, Py = np.asarray(P(x)), np.asarray(P(y))
        worst_idem = max(worst_idem, _norm(np.asarray(P(Px)) - Px) / max(_norm(x), 1e-300))
        worst_sym = max(worst_sym, abs(float(np.vdot(Px, y) - np.vdot(x, Py))) / max(_norm(x) * _norm(y), 1e-300))
    return {"idempotence_defect": worst_idem, "symmetry_defect": worst_sym,
            "orthogonal": bool(worst_idem < tol and worst_sym < tol)}


def law_norm_lower_bound(law: Callable, child_shapes: list, leaf_shapes: list, rng,
                         restarts: int = 16, iters: int = 60) -> float:
    """Alternating maximisation of ||law(x_1..x_m)|| over unit inputs: a LOWER bound on the norm."""
    shapes = list(child_shapes) + list(leaf_shapes)
    m_child = len(child_shapes)
    if not shapes:
        return _norm(law([], []))
    best = 0.0
    for _ in range(restarts):
        xs = [rng.normal(size=s) for s in shapes]
        xs = [x / _norm(x) for x in xs]
        for _ in range(iters):
            for j in range(len(shapes)):
                out = np.asarray(law(xs[:m_child], xs[m_child:]))
                if _norm(out) == 0.0:
                    break
                # gradient of <out_dir, law(x)> w.r.t. slot j by linearity: evaluate on basis
                basis_vals = []
                flat = np.zeros(int(np.prod(shapes[j])))
                u = out / _norm(out)
                grad = np.zeros_like(flat)
                for i in range(flat.size):
                    e = np.zeros_like(flat); e[i] = 1.0
                    trial = list(xs); trial[j] = e.reshape(shapes[j])
                    grad[i] = float(np.vdot(u, np.asarray(law(trial[:m_child], trial[m_child:]))))
                if _norm(grad) > 0:
                    xs[j] = (grad / _norm(grad)).reshape(shapes[j])
            best = max(best, _norm(law(xs[:m_child], xs[m_child:])))
    return best
