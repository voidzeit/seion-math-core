from __future__ import annotations

import numpy as np

from ..algebra.nary_law import NaryLaw
from .measure_space import FiniteMeasureSpace


class DiscreteKernel(NaryLaw):
    """A finite discrete kernel; its finite sum is exact for the declared grid."""

    def __init__(self, tensor: np.ndarray, measure: FiniteMeasureSpace, name: str = "discrete_kernel") -> None:
        tensor = np.asarray(tensor)
        if tensor.ndim < 3 or any(d != measure.size for d in tensor.shape[1:]):
            raise ValueError("a discrete kernel uses the measure grid in every input slot")
        super().__init__(tensor, arity=tensor.ndim - 1, name=name)
        self.measure = measure

    def weighted_law(self, inputs: tuple[np.ndarray, ...]) -> np.ndarray:
        weighted = self.tensor
        for value in inputs:
            weighted = np.tensordot(weighted, np.asarray(value) * self.measure.weights, axes=([1], [0]))
        return np.asarray(weighted)

