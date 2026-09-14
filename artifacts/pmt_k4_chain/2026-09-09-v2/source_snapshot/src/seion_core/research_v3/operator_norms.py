"""Lower estimates and rigorous finite-dimensional upper bounds for laws."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Sequence

import numpy as np

from .local_constants import apply_tensor_numpy


@dataclass(frozen=True, slots=True)
class OperatorNormBracket:
    lower: float
    upper: float
    method: str
    iterations: int
    converged: bool

    def __post_init__(self) -> None:
        if self.lower < -1.0e-15 or self.upper + 1.0e-15 < self.lower:
            raise ValueError("invalid operator-norm bracket")


def frobenius_upper_bound(tensor: np.ndarray) -> float:
    """Return the rigorous ``||T||_op <= ||T||_F`` certificate."""

    return float(np.linalg.norm(np.asarray(tensor).ravel()))


def _contract_except(
    tensor: np.ndarray,
    vectors: Sequence[np.ndarray],
    output_direction: np.ndarray,
    free_slot: int,
) -> np.ndarray:
    """Adjoint contraction giving the gradient in one input slot."""

    data = np.asarray(tensor)
    result = np.tensordot(output_direction.conj(), data, axes=([0], [0]))
    current_axes = list(range(len(vectors)))
    for slot in reversed(range(len(vectors))):
        if slot == free_slot:
            continue
        axis = current_axes.index(slot)
        result = np.tensordot(result, vectors[slot], axes=([axis], [0]))
        current_axes.pop(axis)
    return np.asarray(result).conj()


def multilinear_power_lower_bound(
    tensor: np.ndarray,
    *,
    restarts: int = 8,
    maximum_iterations: int = 200,
    tolerance: float = 1.0e-12,
    seed: int = 0,
) -> OperatorNormBracket:
    """Alternating maximization lower bound, paired with a Frobenius upper bound.

    The returned ``lower`` is an attained value and is therefore rigorous up
    to the recorded floating-point evaluation.  It is never presented as a
    certified global optimum.  ``upper`` is the Frobenius certificate.
    """

    data = np.asarray(tensor)
    if data.ndim < 3:
        raise ValueError("a multilinear law must have arity at least two")
    rng = np.random.default_rng(seed)
    best = 0.0
    any_converged = False
    total_iterations = 0
    complex_data = np.iscomplexobj(data)
    for _ in range(max(1, restarts)):
        vectors: list[np.ndarray] = []
        for dimension in data.shape[1:]:
            value = rng.normal(size=dimension)
            if complex_data:
                value = value + 1j * rng.normal(size=dimension)
            value = value / np.linalg.norm(value)
            vectors.append(value)
        previous = -1.0
        for iteration in range(1, maximum_iterations + 1):
            output = apply_tensor_numpy(data, vectors)
            output_norm = float(np.linalg.norm(output))
            if output_norm == 0.0:
                break
            direction = output / output_norm
            for slot in range(len(vectors)):
                update = _contract_except(data, vectors, direction, slot)
                update_norm = float(np.linalg.norm(update))
                if update_norm > 0.0:
                    vectors[slot] = update / update_norm
            value = float(np.linalg.norm(apply_tensor_numpy(data, vectors)))
            total_iterations += 1
            if abs(value - previous) <= tolerance * max(1.0, value):
                any_converged = True
                break
            previous = value
        best = max(best, float(np.linalg.norm(apply_tensor_numpy(data, vectors))))
    return OperatorNormBracket(
        lower=best,
        upper=frobenius_upper_bound(data),
        method="alternating_multilinear_power/Frobenius",
        iterations=total_iterations,
        converged=any_converged,
    )


def rank_one_exact_norm(weight: complex, factors: Sequence[np.ndarray]) -> float:
    return float(abs(weight) * np.prod([np.linalg.norm(np.asarray(factor)) for factor in factors]))
