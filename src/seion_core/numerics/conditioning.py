from __future__ import annotations

import numpy as np


def condition_number(matrix: np.ndarray, eps: float = 1e-15) -> float:
    values = np.linalg.svd(np.asarray(matrix), compute_uv=False)
    if not len(values) or values[-1] <= eps:
        return float("inf")
    return float(values[0] / values[-1])

