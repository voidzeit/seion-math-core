"""Closed-form PMT bounds and the exact three-node ``W_3`` contract."""

from __future__ import annotations

import math


W3_BREAKPOINT = math.sqrt(2.0 / 3.0)


def _nonnegative_parameters(k: int, M: float, rho: float, leaf_product: float) -> None:
    if k < 0 or M < 0.0 or rho < 0.0 or leaf_product < 0.0:
        raise ValueError("k, M, rho, and leaf_product must be nonnegative")
    if M == 0.0 and rho > 0.0:
        raise ValueError("rho cannot exceed a zero operator bound")
    if M > 0.0 and rho > M + 1.0e-12:
        raise ValueError("rho must satisfy rho <= M")


def ambient_root_bound(k: int, M: float, rho: float, leaf_product: float = 1.0) -> float:
    """Universal ambient discrepancy bound ``k rho M^(k-1) L_T``."""

    _nonnegative_parameters(k, M, rho, leaf_product)
    return float(k * rho * M ** max(k - 1, 0) * leaf_product) if k else 0.0


def projected_root_bound(k: int, M: float, rho: float, leaf_product: float = 1.0) -> float:
    """Universal projected-root bound ``(k-1) rho M^(k-1) L_T``."""

    _nonnegative_parameters(k, M, rho, leaf_product)
    if k <= 1:
        return 0.0
    return float((k - 1) * rho * M ** (k - 1) * leaf_product)


def w3(eta: float) -> float:
    """Exact independent-law finite-dimensional ``k=3`` constant contract."""

    if not 0.0 < eta <= 1.0:
        raise ValueError("eta must satisfy 0 < eta <= 1")
    if eta <= W3_BREAKPOINT:
        return math.sqrt(4.0 - 3.0 * eta * eta)
    return 2.0 / (math.sqrt(3.0) * eta)


def w3_absolute(eta: float) -> float:
    """Absolute normalized ``k=3`` extremal error ``eta W_3(eta)``."""

    return eta * w3(eta)


def w3_sos_residual(xi: float, zeta: float) -> float:
    """Return the nonnegative SOS residual behind the ``4/3`` bound.

    The identity is
    ``4(1+xi^2)(1+zeta^2)-3((xi+zeta)^2+xi^2 zeta^2)``.
    """

    left = 4.0 * (1.0 + xi * xi) * (1.0 + zeta * zeta)
    middle = 3.0 * ((xi + zeta) ** 2 + xi * xi * zeta * zeta)
    return left - middle
