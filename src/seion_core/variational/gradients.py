from __future__ import annotations

import numpy as np


def finite_difference_gradient(function, point: np.ndarray, step: float = 1e-6) -> np.ndarray:
    point = np.asarray(point, dtype=float)
    gradient = np.zeros_like(point)
    for index in np.ndindex(point.shape):
        plus = point.copy(); minus = point.copy()
        plus[index] += step; minus[index] -= step
        gradient[index] = (function(plus) - function(minus)) / (2 * step)
    return gradient


def gradient_check(function, gradient, point: np.ndarray, step: float = 1e-6) -> dict:
    analytic = np.asarray(gradient(point))
    numeric = finite_difference_gradient(function, point, step)
    return {"absolute_error": float(np.linalg.norm(analytic - numeric)), "analytic_norm": float(np.linalg.norm(analytic)), "numeric_norm": float(np.linalg.norm(numeric))}

