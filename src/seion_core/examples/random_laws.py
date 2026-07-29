from __future__ import annotations

import numpy as np

from ..algebra.ternary_law import TernaryLaw
from ..algebra.symmetry import cyclic_symmetrize


def random_ternary_law(dimension: int = 3, seed: int = 0, dtype=np.float64, scale_match: bool = False) -> TernaryLaw:
    rng = np.random.default_rng(seed)
    tensor = rng.normal(size=(dimension,) * 4).astype(dtype)
    if scale_match:
        tensor /= max(np.linalg.norm(tensor), np.finfo(float).eps)
        tensor *= np.sqrt(dimension)
    return TernaryLaw(tensor, f"random_ternary_{seed}")


def cyclic_random_law(dimension: int = 3, seed: int = 0, dtype=np.float64) -> TernaryLaw:
    return TernaryLaw(cyclic_symmetrize(random_ternary_law(dimension, seed, dtype)).tensor, f"cyclic_random_{seed}")


def ill_conditioned_law(dimension: int = 3, dtype=np.float64) -> TernaryLaw:
    tensor = np.zeros((dimension,) * 4, dtype=dtype)
    for i in range(dimension):
        tensor[i, i, i, i] = 10.0 ** (-6 * i)
    return TernaryLaw(tensor, "ill_conditioned_ternary")

