from __future__ import annotations

import numpy as np

from ..algebra.ternary_law import TernaryLaw
from ..projectors.projector import Projector


def invariant_subspace_law(dimension: int = 4, invariant_rank: int = 2, seed: int = 0, dtype=np.float64) -> tuple[TernaryLaw, Projector]:
    if not 0 < invariant_rank < dimension:
        raise ValueError("invariant_rank must be strictly between zero and dimension")
    rng = np.random.default_rng(seed)
    tensor = np.zeros((dimension,) * 4, dtype=dtype)
    block = rng.normal(size=(invariant_rank,) * 4).astype(dtype)
    tensor[:invariant_rank, :invariant_rank, :invariant_rank, :invariant_rank] = block
    return TernaryLaw(tensor, "known_invariant_subspace"), Projector(np.eye(dimension, invariant_rank), method="known_invariant")


def no_nontrivial_closed_subspace_control(dimension: int = 4, seed: int = 0, dtype=np.float64) -> TernaryLaw:
    rng = np.random.default_rng(seed)
    return TernaryLaw(rng.normal(size=(dimension,) * 4).astype(dtype), "random_no_closed_subspace_control")

