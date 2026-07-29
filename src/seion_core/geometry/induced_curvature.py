from __future__ import annotations

import numpy as np


def commutator(left: np.ndarray, right: np.ndarray) -> np.ndarray:
    return left @ right - right @ left


def curvature_operator(left_x: np.ndarray, left_y: np.ndarray, left_bracket: np.ndarray) -> np.ndarray:
    """Standard operator convention ``[L_x,L_y] - L_[x,y]``."""
    return commutator(left_x, left_y) - left_bracket


def standard_curvature_residual(product, x, y, z):
    """Return ``R_standard(x,y)z - (A(y,x,z)-A(x,y,z))``.

    This identity is proved by expansion for every bilinear product.  It is
    a finite-dimensional algebraic identity, not a geometric curvature claim.
    """
    bracket = lambda a, b: product(a, b) - product(b, a)
    left = lambda a: np.column_stack([product(a, np.eye(len(a))[:, j]) for j in range(len(a))])
    lx, ly = left(x), left(y)
    lb = left(bracket(x, y))
    r = curvature_operator(lx, ly, lb) @ z
    assoc = lambda a, b, c: product(product(a, b), c) - product(a, product(b, c))
    return r - (assoc(y, x, z) - assoc(x, y, z))

