"""Exact k=2 saturation construction for the general independent-law class."""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np


@dataclass(frozen=True, slots=True)
class K2SaturationResult:
    eta: float
    M: float
    rho: float
    inner_operator_norm: float
    outer_operator_norm: float
    inner_closure_norm: float
    outer_closure_norm: float
    projected_error: float
    universal_projected_bound: float
    normalized_ratio: float


def construct_k2_independent_map_saturation(eta: float, *, M: float = 1.0) -> K2SaturationResult:
    """Evaluate an exact real 2D chain saturating the k=2 projected bound.

    Let ``P`` project onto ``e0`` and ``N`` onto ``e1``. With ``rho=eta*M``:

    ``mu_inner(x,y) = M*x1*y1*e0 + rho*x0*y0*e1``
    ``mu_outer(x,y) = M*x1*y0*e0``.

    Both laws have operator norm ``M``. The inner closure norm is ``rho`` and
    the outer closure norm is zero. For unit leaves ``e0,e0,e0``, the inner
    projected state is zero while its ambient state is ``rho*e1``; the outer
    law maps that normal error to ``M*rho*e0``. Therefore the projected-root
    error equals ``rho*M`` exactly.
    """

    if not 0.0 < eta <= 1.0 or M <= 0.0:
        raise ValueError("require 0 < eta <= 1 and M > 0")
    rho = eta * M
    e0 = np.array([1.0, 0.0])
    e1 = np.array([0.0, 1.0])
    leaves = (e0, e0, e0)

    def inner(x: np.ndarray, y: np.ndarray) -> np.ndarray:
        return M * x[1] * y[1] * e0 + rho * x[0] * y[0] * e1

    def outer(x: np.ndarray, y: np.ndarray) -> np.ndarray:
        return M * x[1] * y[0] * e0

    inner_ambient = inner(leaves[0], leaves[1])
    inner_projected = np.array([inner_ambient[0], 0.0])
    root_ambient = outer(inner_ambient, leaves[2])
    root_projected = outer(inner_projected, leaves[2])
    projected_error = float(np.linalg.norm(root_ambient - root_projected))
    bound = rho * M
    return K2SaturationResult(
        eta=eta,
        M=M,
        rho=rho,
        inner_operator_norm=M,
        outer_operator_norm=M,
        inner_closure_norm=rho,
        outer_closure_norm=0.0,
        projected_error=projected_error,
        universal_projected_bound=bound,
        normalized_ratio=projected_error / bound,
    )
