"""Joint representation/projection/closure error budgets."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class CPProjectionBudget:
    representation: float
    projection_and_closure: float
    interaction: float
    recursive_amplification: float
    total: float
    inequality: str


def homogeneous_cp_projection_budget(
    *,
    internal_nodes: int,
    exact_norm: float,
    representation_error: float,
    closure_residual: float,
    leaf_product: float = 1.0,
    projected_root: bool = False,
) -> CPProjectionBudget:
    """A transparent two-stage bound for ``mu`` versus projected ``hat mu``.

    If ``||mu-hat_mu||<=delta`` and ``||mu||<=M``, then
    ``||hat_mu||<=M+delta``.  The representation tree contributes
    ``k delta (M+delta)^(k-1)``.  Projection is split into a base term using
    ``M`` and the extra amplification caused by ``delta``; that extra is
    reported as interaction instead of being hidden inside ``rho``.
    """

    k = internal_nodes
    if k < 0 or min(exact_norm, representation_error, closure_residual, leaf_product) < 0:
        raise ValueError("budget parameters must be nonnegative")
    if k == 0:
        return CPProjectionBudget(0.0, 0.0, 0.0, 0.0, 0.0, "zero-node identity")
    approximate_norm = exact_norm + representation_error
    projection_coefficient = max(0, k - 1) if projected_root else k
    representation = k * representation_error * approximate_norm ** (k - 1) * leaf_product
    projection_base = (
        projection_coefficient
        * closure_residual
        * exact_norm ** (k - 1)
        * leaf_product
    )
    interaction = (
        projection_coefficient
        * closure_residual
        * (approximate_norm ** (k - 1) - exact_norm ** (k - 1))
        * leaf_product
    )
    recursive = representation + projection_base + interaction
    return CPProjectionBudget(
        representation=float(representation),
        projection_and_closure=float(projection_base),
        interaction=float(interaction),
        recursive_amplification=float(recursive),
        total=float(recursive),
        inequality="total <= representation + projection/closure + representation-projection interaction",
    )
