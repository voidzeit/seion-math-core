from __future__ import annotations

import numpy as np

from ..algebra.nary_law import NaryLaw


def zero_law(dimension: int = 3, dtype=np.float64) -> NaryLaw:
    return NaryLaw(np.zeros((dimension, dimension, dimension, dimension), dtype=dtype), 3, "zero_ternary")

