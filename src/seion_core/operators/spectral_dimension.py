from __future__ import annotations

import numpy as np


def spectral_dimension_estimate(times: np.ndarray, traces: np.ndarray) -> float:
    times = np.asarray(times, dtype=float)
    traces = np.maximum(np.asarray(traces, dtype=float), np.finfo(float).tiny)
    slope = np.polyfit(np.log(times), np.log(traces), 1)[0]
    return float(-2 * slope)

