from __future__ import annotations

import numpy as np


def convergence_errors(values: list[np.ndarray], reference: np.ndarray) -> np.ndarray:
    ref = np.asarray(reference)
    return np.asarray([np.linalg.norm(np.asarray(v) - ref) for v in values])


def loglog_slope(resolutions: list[int], errors: list[float]) -> float:
    x = np.log(np.asarray(resolutions, dtype=float))
    y = np.log(np.maximum(np.asarray(errors, dtype=float), np.finfo(float).tiny))
    return float(np.polyfit(x, y, 1)[0])

