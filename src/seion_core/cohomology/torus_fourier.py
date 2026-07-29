from __future__ import annotations

import numpy as np


def torus_fourier_differential(modes: int) -> np.ndarray:
    if modes <= 0:
        raise ValueError("modes must be positive")
    frequencies = np.arange(-modes, modes + 1)
    return np.diag(1j * frequencies)

