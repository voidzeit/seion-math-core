from __future__ import annotations

import numpy as np


def row_markov_normalize(matrix: np.ndarray, eps: float = 1e-15) -> tuple[np.ndarray, dict]:
    a = np.asarray(matrix, dtype=float)
    row_sums = np.sum(np.maximum(a, 0.0), axis=1)
    valid = bool(np.all(row_sums > eps))
    if not valid:
        return a, {"markovian": False, "reason": "zero or negative row mass"}
    result = np.maximum(a, 0.0) / row_sums[:, None]
    return result, {"markovian": True, "row_sum_error": float(np.max(np.abs(result.sum(axis=1) - 1.0)))}

