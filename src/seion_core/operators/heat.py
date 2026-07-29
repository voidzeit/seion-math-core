from __future__ import annotations

import numpy as np
from scipy.linalg import expm


def heat_kernel(laplacian: np.ndarray, time: float) -> np.ndarray:
    if time < 0:
        raise ValueError("heat time must be nonnegative")
    return expm(-time * np.asarray(laplacian))


def heat_trace(laplacian: np.ndarray, times: np.ndarray) -> np.ndarray:
    values = np.linalg.eigvalsh(0.5 * (laplacian + laplacian.conj().T))
    return np.asarray([np.sum(np.exp(-float(t) * values)) for t in times])

