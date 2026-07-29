"""Symmetry constraints are evaluated separately and never conflated."""

from __future__ import annotations

from itertools import permutations

import numpy as np

from .nary_law import NaryLaw


def permutation_residual(law: NaryLaw, vectors: tuple[np.ndarray, ...], permutation: tuple[int, ...]) -> np.ndarray:
    return law(*vectors) - law(*[vectors[i] for i in permutation])


def symmetry_defect(
    law: NaryLaw, vectors: tuple[np.ndarray, ...], permutations_to_test: list[tuple[int, ...]] | None = None
) -> float:
    if permutations_to_test is None:
        permutations_to_test = list(permutations(range(law.arity)))
    values = [np.linalg.norm(permutation_residual(law, vectors, p)) ** 2 for p in permutations_to_test]
    return float(np.mean(values))


def cyclic_defect(law: NaryLaw, vectors: tuple[np.ndarray, ...]) -> float:
    if law.arity < 2:
        return 0.0
    rotated = vectors[1:] + vectors[:1]
    return float(np.linalg.norm(law(*vectors) - law(*rotated)) ** 2)


def antisymmetry_defect(law: NaryLaw, vectors: tuple[np.ndarray, ...]) -> float:
    if law.arity != 2:
        raise ValueError("antisymmetry_defect currently targets binary laws")
    return float(np.linalg.norm(law(*vectors) + law(vectors[1], vectors[0])) ** 2)


def cyclic_symmetrize(law: NaryLaw) -> NaryLaw:
    if law.arity == 1:
        return law
    tensor = law.tensor.copy()
    result = np.zeros_like(tensor)
    for shift in range(law.arity):
        result += np.transpose(tensor, axes=(0, *([1 + ((i + shift) % law.arity) for i in range(law.arity)])))
    return NaryLaw(result / law.arity, law.arity, name=f"cyclic({law.name})")


def full_symmetrize(law: NaryLaw) -> NaryLaw:
    result = np.zeros_like(law.tensor)
    for permutation in permutations(range(law.arity)):
        axes = (0, *[1 + p for p in permutation])
        result += np.transpose(law.tensor, axes=axes)
    return NaryLaw(result / np.math.factorial(law.arity), law.arity, name=f"symmetric({law.name})")

