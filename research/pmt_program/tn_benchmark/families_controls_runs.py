"""Registered campaigns for F6 (positive control) and F8 (constructed negative controls)."""
from __future__ import annotations

import itertools
import math

import numpy as np

import certificate as cert
import families_controls as fc
from pmt_eval import check_projector_orthogonal, law_norm_lower_bound
from seeding import stable_seed


def eta_c(k: int) -> float:
    ts = np.linspace(1e-6, math.pi / 2, 40001)
    vals = [cert.g(t, k - 1) for t in ts]
    return math.sin(float(ts[int(np.argmax(vals))]))


def _shape_nodes(nodes):
    for nd in nodes.values():
        if "input_shape" in nd.extra and "output_shape" not in nd.extra:
            nd.extra["output_shape"] = nd.extra["input_shape"]
    return nodes


def instances(family: str, quick: bool = False):
    if family == "F6":
        n_eq = 20 if quick else 200
        for i in range(2 * n_eq):
            rng = np.random.default_rng(stable_seed("F6", i))
            k = int(rng.integers(2, 13))
            kids, leaves = fc.random_tree(rng, k)
            equal = i < n_eq
            if equal:
                frac = float(rng.uniform(0.01, 0.999))
                th = math.asin(frac * eta_c(k))
                thetas = {v: th for v in kids if v != "n0"}
                eta_nom = math.sin(th)
            else:
                eta_nom = float(rng.uniform(0.05, 1.0))
                thetas = {v: float(rng.uniform(0, math.asin(eta_nom))) for v in kids if v != "n0"}
            nodes = _shape_nodes(fc.witness_nodes(kids, leaves, thetas))
            yield {"nodes": nodes, "root": "n0", "M_provenance": "analytic", "expected_violation": False,
                   "meta": {"family": "F6", "variant": "equal_angles" if equal else "unequal_angles",
                            "topology": "random_tree", "n_internal": k, "index": i,
                            "arity_max": max(len(c) for c in kids.values())}}
    elif family == "F8":
        vr = np.random.default_rng(stable_seed("F8-validators"))
        for k, th, lam in itertools.product([2, 4, 6], [0.05, 0.1, 0.2], [1.2, 1.5, 2.0]):
            nodes = _shape_nodes(fc.f8a_nodes(k, th, lam))
            root = nodes["n0"]
            lb = law_norm_lower_bound(root.law, [(2,)] * len(root.children), [(2,)] * len(root.leaves), vr, restarts=6, iters=30)
            yield {"nodes": nodes, "root": "n0", "M_provenance": "DELIBERATELY_UNDERESTIMATED",
                   "expected_violation": True, "check_projectors": True,
                   "meta": {"family": "F8a", "k_param": k, "theta": th, "lambda": lam, "analytic_ratio": lam,
                            "validator_flag": bool(lb > root.M_hat * (1 + 1e-6)), "validator_value": lb}}
        for th, c in itertools.product([0.1, 0.3], [1.0, 3.0]):
            nodes = _shape_nodes(fc.f8b_nodes(th, c))
            chk = check_projector_orthogonal(nodes["n1"].projector, (2,), vr)
            yield {"nodes": nodes, "root": "n0", "M_provenance": "analytic", "expected_violation": True,
                   "meta": {"family": "F8b", "theta": th, "c": c, "analytic_ratio": math.sqrt(1 + c * c),
                            "validator_flag": not chk["orthogonal"], "validator_value": chk["symmetry_defect"]}}
        for th, d in itertools.product([0.1, 0.2], [4, 9]):
            nodes = fc.f8c_nodes(th, d)
            nodes["n1"].extra["output_shape"] = (d, d)
            lb = law_norm_lower_bound(nodes["n0"].law, [(d, d)], [], vr, restarts=4, iters=20)
            yield {"nodes": nodes, "root": "n0", "M_provenance": "DELIBERATELY_UNDERESTIMATED",
                   "expected_violation": True,
                   "meta": {"family": "F8c", "theta": th, "d": d, "analytic_ratio": math.sqrt(d),
                            "validator_flag": bool(lb > 1 + 1e-6), "validator_value": lb}}
