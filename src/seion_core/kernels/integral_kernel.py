"""Formal integral-kernel metadata plus finite quadrature realization."""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from .measure_space import FiniteMeasureSpace


@dataclass(frozen=True)
class IntegralKernelDefinition:
    """Formal definition; no claim of analytic convergence is implied."""

    kernel_name: str
    arity: int
    domain_description: str
    measure_description: str
    boundedness_assumptions: tuple[str, ...]

    def expression(self) -> str:
        return f"mu(f_1,...,f_{self.arity})(p)=integral K(p;q_1,...,q_{self.arity}) prod_j f_j(q_j) dnu"


def quadrature_apply(
    kernel: np.ndarray,
    inputs: tuple[np.ndarray, ...] | list[np.ndarray],
    measure: FiniteMeasureSpace,
) -> np.ndarray:
    """Apply a discrete kernel with weights in all integration variables.

    The kernel shape is ``(output, q_1, ..., q_n)`` and each input has shape
    ``(q_j,)``.  This is an exact finite model, not a continuous theorem.
    """
    kernel = np.asarray(kernel)
    values = tuple(np.asarray(v) for v in inputs)
    if kernel.ndim != len(values) + 1:
        raise ValueError("kernel rank and arity disagree")
    if any(v.shape != (measure.size,) for v in values):
        raise ValueError("each quadrature input must have one value per measure point")
    weighted = kernel
    for axis, (value, weight) in enumerate(zip(values, measure.weights)):
        weighted = np.tensordot(weighted, value * weight, axes=([1], [0]))
    return np.asarray(weighted)

