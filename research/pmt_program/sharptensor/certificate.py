"""Certificates for a single tree execution.

A run is a rooted tree. Leaves carry inputs (optionally approximate: ``dev = ‖z − z̃‖``). Every internal
node ``v`` computes a value ``R_v`` from its children and records:

* ``M``          a bound ``‖μ_v‖ ≤ M_v`` (method and rigour recorded),
* ``residual``   ``d_v = ‖μ_v(R_children) − R_v‖``; for exact orthogonal truncation this is
                 ``‖(I − P_v) μ_v(R_children)‖ = √(Σ_{j>r} σ_j²)``,
* ``R_norm``     ``‖R_v‖``,
* ``K_op``       optional per-slot bounds ``‖x ↦ μ_v(R_1, …, x, …, R_m)‖ ≤ K_op[i]``,
* ``orthogonal`` whether ``R_v = P_v μ_v(R_children)`` with an exact orthogonal projector.

Three certificates, each an upper bound on ``‖F_r − R_r‖`` under the recorded assumptions; their
minimum is also an upper bound.

1. **Theorem R (trajectory)** — ``PMT.heterogeneous_scaled_upper_of_admTC_nonneg``
   (requires exact leaves, orthogonal truncations, untruncated root):
   ``E_R = Λ_T · gBox(η)``, ``Λ_T = ∏_v M_v ∏_ℓ ‖z_ℓ‖``, ``η_v = d_v / (M_v ∏_i ‖R_i‖)``,
   ``gBox`` enclosed rigorously (H3, ``PMT.gBox_eq_capped``).
2. **Compact amplitude bound** — ``PMT.ATree.err_le_abound``:
   ``A_v = d_v + M_v (∏_i (‖R_i‖ + A_i) − ∏_i ‖R_i‖)``, ``A_ℓ = dev_ℓ``.
3. **Slot-wise bound** — ``PMT.KTree.err_le_sbound`` with slot constants from
   ``PMT.slot_const_general`` (``K_i = M_v ∏_{j<i}(‖R_j‖ + S_j) ∏_{j>i} ‖R_j‖``) or, for the first
   slot of a telescoping order (empty exact prefix, ``PMT.slot_args_eq_update``), ``K_op``.
   Every slot order of the law is a valid multilinear map, so the best order per node is used.

Assumption recorded in every certificate: exact arithmetic (float64 values treated as exact) and,
for certificate 1, exact orthogonal projectors (APPLICATIONS_BOUNDARY §3, §10).
"""

from __future__ import annotations

import hashlib
import itertools
import json
import math
from dataclasses import asdict, dataclass, field

from .gbox import additive_bound, gbox_certified

LEAN_THEOREMS = {
    "theorem_r_trajectory": "PMT.heterogeneous_scaled_upper_of_admTC_nonneg",
    "h3": "PMT.capped_equal_angle / PMT.gBox_eq_capped",
    "amplitude_compact": "PMT.ATree.err_le_abound",
    "slotwise": "PMT.KTree.err_le_sbound + PMT.slot_const_general + PMT.slot_args_eq_update",
}


@dataclass
class Leaf:
    name: str
    norm: float
    dev: float = 0.0


@dataclass
class Node:
    name: str
    children: list[str]
    M: float
    M_method: str
    M_rigorous: bool
    residual: float
    R_norm: float
    is_root: bool = False
    rank: int | None = None
    rank_full: int | None = None
    K_op: list | None = None
    K_op_method: str = ""
    K_op_rigorous: bool = False
    orthogonal: bool = True


@dataclass
class Run:
    """Execution record of one tree computation."""

    leaves: list[Leaf]
    nodes: list[Node]
    root: str
    meta: dict = field(default_factory=dict)

    def index(self):
        return {l.name: l for l in self.leaves}, {n.name: n for n in self.nodes}

    def tree_hash(self) -> str:
        shape = {n.name: n.children for n in self.nodes}
        return hashlib.sha256(json.dumps(shape, sort_keys=True).encode()).hexdigest()[:16]


def _norm_of(name, leaves, nodes):
    return leaves[name].norm if name in leaves else nodes[name].R_norm


def _check_run(run: Run):
    for n in run.nodes:
        if not (n.M >= 0 and n.residual >= 0 and n.R_norm >= 0):
            raise ValueError(f"node {n.name}: M, residual and R_norm must be nonnegative")
        if n.K_op is not None and len(n.K_op) != len(n.children):
            raise ValueError(f"node {n.name}: K_op must have one entry per child")
    for l in run.leaves:
        if not (l.norm >= 0 and l.dev >= 0):
            raise ValueError(f"leaf {l.name}: norm and dev must be nonnegative")


def theorem_r_certificate(run: Run, tol: float = 1e-9) -> dict:
    """Theorem R trajectory certificate ``E ≤ Λ_T · gBox(η)``."""
    _check_run(run)
    leaves, nodes = run.index()
    root = nodes[run.root]
    reasons = []
    if any(l.dev > 0 for l in run.leaves):
        reasons.append("approximate leaves")
    if any(not n.orthogonal for n in run.nodes):
        reasons.append("non-orthogonal local operation")
    if root.residual != 0.0:
        reasons.append("truncated root")
    if reasons:
        return {"lean": LEAN_THEOREMS["theorem_r_trajectory"], "applicable": False,
                "reason": ", ".join(reasons), "absolute_error_upper": math.inf}
    lam = math.prod(n.M for n in run.nodes) * math.prod(l.norm for l in run.leaves)
    rho, eta = {}, {}
    for n in run.nodes:
        if n.is_root:
            continue
        denom = math.prod(_norm_of(c, leaves, nodes) for c in n.children)
        if denom == 0.0:
            if n.residual != 0.0:
                raise ValueError(f"node {n.name}: nonzero residual with a zero child")
            r = 0.0
        else:
            r = n.residual / denom
        rho[n.name] = r
        eta[n.name] = (r / n.M) if n.M > 0 else 0.0
    etas = list(eta.values())
    if any(n.M == 0 for n in run.nodes):
        lo = up = err = 0.0
        cells = 0
    else:
        enc = gbox_certified(etas, tol=tol)
        lo, cells = enc.lower, enc.cells
        # gBox ≤ Σ η (PMT.gBox_le_sum): use the smaller of the two rigorous upper bounds
        sum_up = math.nextafter(math.fsum(etas), math.inf) if etas else 0.0
        up = min(enc.upper, sum_up)
        lo = min(lo, up)
        err = lam * up
    return {
        "lean": LEAN_THEOREMS["theorem_r_trajectory"],
        "applicable": True,
        "lambda_T": lam,
        "prod_M": math.prod(n.M for n in run.nodes),
        "prod_leaf_norms": math.prod(l.norm for l in run.leaves),
        "rho": rho,
        "eta": eta,
        "sum_eta": additive_bound(etas),
        "gbox_lower": lo,
        "gbox_upper": up,
        "gbox_cells": cells,
        "absolute_error_upper": err,
    }


def amplitude_compact_certificate(run: Run) -> dict:
    """``A_v = d_v + M_v (∏(‖R_i‖ + A_i) − ∏ ‖R_i‖)`` (``PMT.ATree.err_le_abound``)."""
    _check_run(run)
    leaves, nodes = run.index()
    memo: dict[str, float] = {}

    def A(name):
        if name in leaves:
            return leaves[name].dev
        if name in memo:
            return memo[name]
        n = nodes[name]
        rs = [_norm_of(c, leaves, nodes) for c in n.children]
        As = [A(c) for c in n.children]
        val = n.residual + n.M * (math.prod(r + a for r, a in zip(rs, As)) - math.prod(rs))
        memo[name] = max(val, n.residual)
        return memo[name]

    return {"lean": LEAN_THEOREMS["amplitude_compact"], "absolute_error_upper": A(run.root),
            "node_bounds": dict(memo)}


def _slot_value(n: Node, order, rs, Ss):
    """``Σ_k K_k S_{order[k]}`` for one telescoping order (first slot may use ``K_op``)."""
    total = 0.0
    for k, i in enumerate(order):
        before = order[:k]
        after = order[k + 1:]
        k_gen = n.M * math.prod(rs[j] + Ss[j] for j in before) * math.prod(rs[j] for j in after)
        K = k_gen
        # exact prefix (every earlier slot has zero certified error): slot map = x ↦ μ(update R i x)
        if n.K_op is not None and n.K_op[i] is not None and all(Ss[j] == 0.0 for j in before):
            K = min(K, n.K_op[i])
        total += K * Ss[i]
    return total


def slotwise_certificate(run: Run, max_perm_arity: int = 4) -> dict:
    """``S_v = d_v + min_order Σ_k K_k S_{order[k]}`` (``PMT.KTree.err_le_sbound``)."""
    _check_run(run)
    leaves, nodes = run.index()
    memo: dict[str, float] = {}
    orders_used: dict[str, list[int]] = {}

    def S(name):
        if name in leaves:
            return leaves[name].dev
        if name in memo:
            return memo[name]
        n = nodes[name]
        rs = [_norm_of(c, leaves, nodes) for c in n.children]
        Ss = [S(c) for c in n.children]
        m = len(n.children)
        if m <= max_perm_arity:
            candidates = itertools.permutations(range(m))
        else:
            candidates = [tuple(range(m)), tuple(reversed(range(m)))]
        best, best_order = math.inf, list(range(m))
        for order in candidates:
            v = _slot_value(n, list(order), rs, Ss)
            if v < best:
                best, best_order = v, list(order)
        memo[name] = n.residual + best
        orders_used[name] = best_order
        return memo[name]

    return {"lean": LEAN_THEOREMS["slotwise"], "absolute_error_upper": S(run.root),
            "node_bounds": dict(memo), "orders": orders_used,
            "K_op_methods": sorted({n.K_op_method for n in run.nodes if n.K_op is not None}),
            "K_op_all_rigorous": all(n.K_op_rigorous for n in run.nodes if n.K_op is not None)}


def _relative(err: float, r_norm: float):
    return err / (r_norm - err) if math.isfinite(err) and r_norm - err > 0 else "VACUOUS"


def certify(run: Run, tol: float = 1e-9, actual_error: float | None = None) -> dict:
    """Full certificate for one run."""
    _, nodes = run.index()
    thr = theorem_r_certificate(run, tol=tol)
    amp = amplitude_compact_certificate(run)
    slot = slotwise_certificate(run)
    r_norm = nodes[run.root].R_norm
    bounds = {
        "theorem_r": thr["absolute_error_upper"],
        "amplitude_compact": amp["absolute_error_upper"],
        "slotwise": slot["absolute_error_upper"],
    }
    best_kind = min(bounds, key=bounds.get)
    best = bounds[best_kind]
    cert = {
        "sharptensor": "0.1",
        "tree_hash": run.tree_hash(),
        "arithmetic_model": "float64 treated as exact; exact orthogonal projectors for theorem_r "
                            "(APPLICATIONS_BOUNDARY §3, §10)",
        "M_methods": sorted({f"{n.M_method}{'' if n.M_rigorous else ' (numeric)'}" for n in run.nodes}),
        "M_all_rigorous": all(n.M_rigorous for n in run.nodes),
        "M": {n.name: n.M for n in run.nodes},
        "absolute_residuals": {n.name: n.residual for n in run.nodes},
        "R_root_norm": r_norm,
        "theorem_r": thr,
        "amplitude_compact": amp,
        "slotwise": slot,
        "bounds": bounds,
        "best": best_kind,
        "absolute_error_upper": best,
        "relative_error_upper": _relative(best, r_norm),
        "relative_by_certificate": {k: _relative(v, r_norm) for k, v in bounds.items()},
        "meta": run.meta,
    }
    if actual_error is not None:
        cert["actual_error"] = actual_error
        cert["tightness"] = {k: (v / actual_error if actual_error > 0 else math.inf)
                             for k, v in bounds.items()}
        cert["sound"] = bool(actual_error <= best * (1 + 1e-9) + 1e-12)
    return cert


def verify(cert: dict, run: Run, tol: float = 1e-9) -> bool:
    """Recompute the certificate from the run record and check internal consistency."""
    again = certify(run, tol=tol)
    for k in ("theorem_r", "amplitude_compact", "slotwise"):
        a, b = cert["bounds"][k], again["bounds"][k]
        if math.isinf(a) and math.isinf(b):
            continue
        if not math.isclose(a, b, rel_tol=1e-9, abs_tol=1e-15):
            return False
    thr = again["theorem_r"]
    if thr.get("applicable"):
        if thr["gbox_upper"] + 1e-12 < thr["gbox_lower"]:
            return False
        if thr["gbox_lower"] > thr["sum_eta"] * (1 + 1e-9) + 1e-15:
            return False
    return math.isclose(cert["absolute_error_upper"], min(again["bounds"].values()), rel_tol=1e-9,
                        abs_tol=1e-15)


def run_to_json(run: Run) -> dict:
    return {"leaves": [asdict(l) for l in run.leaves], "nodes": [asdict(n) for n in run.nodes],
            "root": run.root, "meta": run.meta}
