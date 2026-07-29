from __future__ import annotations

import numpy as np

from ..algebra.cp_law import CPLaw


def rank_one_law(dimension: int = 3, dtype=np.float64) -> CPLaw:
    output = np.arange(1, dimension + 1, dtype=dtype)
    factors = [np.linspace(1.0, 2.0, dimension, dtype=dtype), np.linspace(2.0, 1.0, dimension, dtype=dtype), np.ones(dimension, dtype=dtype)]
    return CPLaw.from_rank_one_factors(output, factors, weight=0.25, name="rank_one_ternary")

