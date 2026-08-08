"""Separate closure, representation, and interaction error budgets."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Sequence


@dataclass(frozen=True, slots=True)
class ApproximateLawBudget:
    closure_contribution: float
    representation_contribution: float
    interaction_contribution: float
    total: float
    internal_nodes: int
    projected_root: bool
    certified: bool = True


def homogeneous_approximate_law_budget(
    *,
    internal_nodes: int,
    exact_norm: float,
    representation_error: float,
    closure_residual: float,
    leaf_product: float = 1.0,
    projected_root: bool = False,
) -> ApproximateLawBudget:
    """Certified two-stage homogeneous budget with separate mechanisms."""

    values = (exact_norm, representation_error, closure_residual, leaf_product)
    if internal_nodes < 0 or min(values) < 0.0:
        raise ValueError("budget parameters must be nonnegative")
    if internal_nodes == 0:
        return ApproximateLawBudget(0.0, 0.0, 0.0, 0.0, 0, projected_root)
    approximate_norm = exact_norm + representation_error
    coefficient = max(0, internal_nodes - 1) if projected_root else internal_nodes
    representation = internal_nodes * representation_error * approximate_norm ** (internal_nodes - 1) * leaf_product
    closure = coefficient * closure_residual * exact_norm ** (internal_nodes - 1) * leaf_product
    interaction = coefficient * closure_residual * (
        approximate_norm ** (internal_nodes - 1) - exact_norm ** (internal_nodes - 1)
    ) * leaf_product
    total = representation + closure + interaction
    return ApproximateLawBudget(float(closure), float(representation), float(interaction), float(total), internal_nodes, projected_root)


def nodewise_approximate_law_budget(
    exact_norms: Sequence[float],
    representation_errors: Sequence[float],
    closure_residuals: Sequence[float],
    *,
    leaf_product: float = 1.0,
    projected_root: bool = False,
) -> ApproximateLawBudget:
    """Conservative nodewise reduction to homogeneous maxima.

    This records the nodewise inputs and uses their maxima in the proved
    homogeneous budget. It is sound but may be loose; a future nodewise
    telescoping budget can improve it without changing the decomposition.
    """

    if not (len(exact_norms) == len(representation_errors) == len(closure_residuals)):
        raise ValueError("nodewise budget sequences must have equal length")
    if not exact_norms:
        return homogeneous_approximate_law_budget(
            internal_nodes=0,
            exact_norm=0.0,
            representation_error=0.0,
            closure_residual=0.0,
            leaf_product=leaf_product,
            projected_root=projected_root,
        )
    return homogeneous_approximate_law_budget(
        internal_nodes=len(exact_norms),
        exact_norm=max(exact_norms),
        representation_error=max(representation_errors),
        closure_residual=max(closure_residuals),
        leaf_product=leaf_product,
        projected_root=projected_root,
    )
