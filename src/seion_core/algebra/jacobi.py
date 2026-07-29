"""Jacobi-type residuals with explicit convention names."""

from __future__ import annotations

import numpy as np


def commutator(product, x: np.ndarray, y: np.ndarray) -> np.ndarray:
    return product(x, y) - product(y, x)


def binary_jacobiator(product, x: np.ndarray, y: np.ndarray, z: np.ndarray) -> np.ndarray:
    bracket = lambda a, b: commutator(product, a, b)
    return bracket(x, bracket(y, z)) + bracket(y, bracket(z, x)) + bracket(z, bracket(x, y))


def generalized_jacobiator_ternary(law, x1, x2, x3, x4, x5) -> np.ndarray:
    """One named GJI variant: cyclic sum of outer slots.

    This is a convention, not a universal synonym for every generalized
    Jacobi identity in the literature.
    """
    return (
        law(law(x1, x2, x3), x4, x5)
        + law(law(x1, x2, x4), x5, x3)
        + law(law(x1, x2, x5), x3, x4)
    )

