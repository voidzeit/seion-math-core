"""Small-instance discrete error-budget allocation.

This is intentionally an auditable exhaustive optimizer.  It is appropriate
for prototype studies and produces a conservative feasible plan by using the
uniform Theorem R certificate.  A larger production planner can replace the
enumeration with dynamic programming or mixed-integer search without changing
the certificate interface.
"""

from __future__ import annotations

import itertools
import math
from dataclasses import dataclass
from typing import Iterable, Sequence

from .certificate import HeterogeneousCertificate, make_certificate


@dataclass(frozen=True)
class NodeChoice:
    """One admissible rank/truncation choice for a non-root node."""

    label: str
    operator_norm: float
    normalized_defect: float
    cost: float

    def __post_init__(self) -> None:
        if not self.label:
            raise ValueError("choice label cannot be empty")
        if not math.isfinite(self.operator_norm) or self.operator_norm <= 0:
            raise ValueError("operator_norm must be positive and finite")
        if not math.isfinite(self.normalized_defect) or not 0 <= self.normalized_defect <= 1:
            raise ValueError("normalized_defect must lie in [0, 1]")
        if not math.isfinite(self.cost) or self.cost < 0:
            raise ValueError("cost must be finite and nonnegative")


@dataclass(frozen=True)
class AllocationResult:
    choices: tuple[NodeChoice, ...]
    certificate: HeterogeneousCertificate
    total_cost: float
    feasible_under_safe_bound: bool
    explored_combinations: int


def optimize_allocation(
    root_operator_norm: float,
    choices_by_node: Sequence[Sequence[NodeChoice]],
    leaf_product: float,
    target_error: float,
    *,
    max_combinations: int = 100_000,
) -> AllocationResult:
    """Find the cheapest safe plan by exhaustive enumeration.

    The returned plan is feasible only if the conservative uniform bound is at
    most ``target_error``.  The heterogeneous expression is reported inside
    the certificate for comparison but is never used to claim feasibility.
    """
    if not math.isfinite(root_operator_norm) or root_operator_norm <= 0:
        raise ValueError("root_operator_norm must be positive and finite")
    if not math.isfinite(target_error) or target_error < 0:
        raise ValueError("target_error must be finite and nonnegative")
    if not choices_by_node or any(not choices for choices in choices_by_node):
        raise ValueError("every non-root node must have at least one choice")

    total = 1
    for choices in choices_by_node:
        total *= len(choices)
    if total > max_combinations:
        raise ValueError(f"{total} combinations exceed max_combinations={max_combinations}")

    best: AllocationResult | None = None
    explored = 0
    for choices in itertools.product(*choices_by_node):
        explored += 1
        cert = make_certificate(
            [root_operator_norm] + [choice.operator_norm for choice in choices],
            [choice.normalized_defect * choice.operator_norm for choice in choices],
            leaf_product,
            seed=0,
            maxiter=80,
        )
        cost = sum(choice.cost for choice in choices)
        feasible = cert.uniform_safe_bound <= target_error * (1.0 + 1e-12)
        candidate = AllocationResult(tuple(choices), cert, cost, feasible, explored)
        if feasible and (best is None or cost < best.total_cost):
            best = candidate

    if best is None:
        # Return the least expensive infeasible plan to make failure
        # diagnosable, but keep the feasibility flag explicit.
        candidates = []
        for choices in itertools.product(*choices_by_node):
            cert = make_certificate(
                [root_operator_norm] + [choice.operator_norm for choice in choices],
                [choice.normalized_defect * choice.operator_norm for choice in choices],
                leaf_product,
                seed=0,
                maxiter=40,
            )
            candidates.append(AllocationResult(tuple(choices), cert, sum(c.cost for c in choices), False, explored))
        best = min(candidates, key=lambda item: item.total_cost)
    return best

