from __future__ import annotations

import numpy as np

from .measure_space import FiniteMeasureSpace


def periodic_grid(size: int, period: float = 2 * np.pi) -> FiniteMeasureSpace:
    if size < 2:
        raise ValueError("periodic quadrature requires at least two points")
    points = np.linspace(0.0, period, size, endpoint=False)
    weights = np.full(size, period / size)
    return FiniteMeasureSpace(points, weights, name=f"periodic_grid_{size}")


def trapezoidal_interval(size: int, left: float = 0.0, right: float = 1.0) -> FiniteMeasureSpace:
    if size < 2:
        raise ValueError("interval quadrature requires at least two points")
    points = np.linspace(left, right, size)
    h = (right - left) / (size - 1)
    weights = np.full(size, h)
    weights[[0, -1]] *= 0.5
    return FiniteMeasureSpace(points, weights, name=f"trapezoid_{size}")

