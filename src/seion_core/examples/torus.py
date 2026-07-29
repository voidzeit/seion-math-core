from __future__ import annotations

import numpy as np

from ..algebra.ternary_law import TernaryLaw


def torus_fourier_law(modes: int = 3, dtype=np.complex128) -> TernaryLaw:
    dimension = modes
    tensor = np.zeros((dimension,) * 4, dtype=dtype)
    for i in range(dimension):
        tensor[i, i, i, i] = 1.0
    return TernaryLaw(tensor, f"torus_fourier_{modes}")

