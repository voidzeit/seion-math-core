"""Fase 7: adaptive rank allocation policies + comparison harness.

Contract §XXVII/§XXVIII. Per `applications/adaptive_tensor_network/results/LEVEL1_FINDINGS.md`
(confirmatory, preregistered), a pathwise-score-alone policy LOSES to
`uniform` and `local_error_greedy` at equal budget. Per A12/CLM_KGR_017,
this file must never expose "pathwise alone" as the recommended default
— ``hybrid_feature_policy`` (a weighted combination) is the one meant
for actual use; the single-signal policies exist for comparison, not
production.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Callable, Dict, List, Mapping

import numpy as np


@dataclass
class ModuleDiagnostics:
    """One row of the feature vector ``phi_v`` from contract §XXVII."""

    name: str
    closure_leakage: float  # lambda_v
    singular_energy_uncaptured: float  # in [0,1], higher = more rank needed
    gradient_sensitivity: float
    pathwise_score: float  # lambda_v * prod(path gains) -- see warning above
    current_rank: int
    max_rank: int
    cost_per_rank: float = 1.0


Allocation = Dict[str, int]


def _normalize(values: List[float]) -> np.ndarray:
    arr = np.asarray(values, dtype=np.float64)
    total = arr.sum()
    if total <= 0:
        return np.full(arr.shape, 1.0 / max(len(arr), 1))
    return arr / total


def uniform_policy(modules: List[ModuleDiagnostics], budget: int) -> Allocation:
    n = len(modules)
    base = budget // max(n, 1)
    extra = budget - base * n
    out: Allocation = {}
    for i, m in enumerate(modules):
        r = base + (1 if i < extra else 0)
        out[m.name] = int(min(r, m.max_rank))
    return out


def singular_energy_policy(modules: List[ModuleDiagnostics], budget: int) -> Allocation:
    weights = _normalize([m.singular_energy_uncaptured for m in modules])
    return {m.name: int(min(round(w * budget), m.max_rank)) for m, w in zip(modules, weights)}


def gradient_sensitivity_policy(modules: List[ModuleDiagnostics], budget: int) -> Allocation:
    weights = _normalize([m.gradient_sensitivity for m in modules])
    return {m.name: int(min(round(w * budget), m.max_rank)) for m, w in zip(modules, weights)}


def pathwise_policy(modules: List[ModuleDiagnostics], budget: int) -> Allocation:
    """Included for comparison ONLY — see module docstring; do not ship as default."""
    weights = _normalize([m.pathwise_score for m in modules])
    return {m.name: int(min(round(w * budget), m.max_rank)) for m, w in zip(modules, weights)}


def local_error_greedy_policy(modules: List[ModuleDiagnostics], budget: int) -> Allocation:
    """Greedily spend one unit of rank at a time on whichever module has
    the highest current closure leakage, respecting each module's max_rank."""
    ranks = {m.name: 0 for m in modules}
    remaining = {m.name: m.max_rank for m in modules}
    leakage = {m.name: m.closure_leakage for m in modules}
    for _ in range(budget):
        candidates = [m for m in modules if remaining[m.name] > 0]
        if not candidates:
            break
        best = max(candidates, key=lambda m: leakage[m.name] / max(ranks[m.name] + 1, 1))
        ranks[best.name] += 1
        remaining[best.name] -= 1
    return ranks


def random_policy(modules: List[ModuleDiagnostics], budget: int, seed: int) -> Allocation:
    rng = np.random.default_rng(seed)
    weights = rng.dirichlet(np.ones(len(modules)))
    return {m.name: int(min(round(w * budget), m.max_rank)) for m, w in zip(modules, weights)}


def hybrid_feature_policy(
    modules: List[ModuleDiagnostics],
    budget: int,
    feature_weights: Mapping[str, float] | None = None,
) -> Allocation:
    """Contract §XXVII ``phi_v`` combiner — the recommended default
    (CLM_KGR_017). Combines closure leakage, pathwise score, gradient
    sensitivity, and singular energy into one score, rather than trusting
    any single signal (explicitly required after A12: pathwise alone is
    known to lose to simpler baselines in the confirmatory evidence)."""
    fw = {"closure": 0.3, "pathwise": 0.2, "gradient": 0.25, "singular": 0.25}
    if feature_weights:
        fw.update(feature_weights)
    scores = []
    for m in modules:
        s = (
            fw["closure"] * m.closure_leakage
            + fw["pathwise"] * m.pathwise_score
            + fw["gradient"] * m.gradient_sensitivity
            + fw["singular"] * m.singular_energy_uncaptured
        )
        scores.append(max(s, 0.0))
    weights = _normalize(scores)
    return {m.name: int(min(round(w * budget), m.max_rank)) for m, w in zip(modules, weights)}


POLICIES: Dict[str, Callable[..., Allocation]] = {
    "uniform": uniform_policy,
    "singular_energy": singular_energy_policy,
    "gradient_sensitivity": gradient_sensitivity_policy,
    "pathwise": pathwise_policy,
    "local_error_greedy": local_error_greedy_policy,
    "hybrid": hybrid_feature_policy,
    "random": random_policy,
}


def compare_policies(
    modules: List[ModuleDiagnostics],
    budget: int,
    objective_fn: Callable[[Allocation], float],
    seed: int = 0,
) -> Dict[str, Dict[str, float]]:
    """Runs every registered policy through ``objective_fn`` (lower is
    better, e.g. a proxy error) and reports each vs. the empirical best
    observed (NOT a proven oracle — regret here is only regret against
    the other policies tried, matching the honest framing already used
    for the Level 1/2/3 campaign results this contract cites)."""
    results: Dict[str, Dict[str, float]] = {}
    for name, fn in POLICIES.items():
        alloc = fn(modules, budget, seed) if name == "random" else fn(modules, budget)
        results[name] = {"allocation": alloc, "objective": objective_fn(alloc)}
    best = min(results.values(), key=lambda r: r["objective"])["objective"]
    for r in results.values():
        r["regret_vs_best_tried"] = r["objective"] - best
    return results
