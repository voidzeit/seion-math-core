from __future__ import annotations

from dataclasses import dataclass

import numpy as np


@dataclass(frozen=True)
class FiniteMeasureSpace:
    """Exact finite discrete measure used as a kernel approximation."""

    points: np.ndarray
    weights: np.ndarray
    name: str = "finite_measure_space"

    def __post_init__(self) -> None:
        points = np.asarray(self.points)
        weights = np.asarray(self.weights, dtype=float)
        if points.ndim == 0:
            points = points.reshape(1)
        if weights.ndim != 1 or weights.shape[0] != points.shape[0]:
            raise ValueError("measure weights must match the number of points")
        if np.any(weights < 0) or not np.any(weights > 0):
            raise ValueError("measure weights must be nonnegative and not all zero")
        object.__setattr__(self, "points", points)
        object.__setattr__(self, "weights", weights)

    @property
    def size(self) -> int:
        return int(self.weights.shape[0])

    @property
    def total_mass(self) -> float:
        return float(np.sum(self.weights))

