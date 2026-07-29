from __future__ import annotations

import numpy as np


def minibatch_mean(values: np.ndarray, batch_size: int, seed: int = 0) -> tuple[float, dict]:
    values = np.asarray(values)
    if batch_size <= 0:
        raise ValueError("batch_size must be positive")
    rng = np.random.default_rng(seed)
    indices = rng.choice(values.shape[0], size=min(batch_size, values.shape[0]), replace=False)
    return float(np.mean(values[indices])), {"seed": seed, "batch_size": int(len(indices)), "population": int(values.shape[0])}

