from __future__ import annotations

import numpy as np


def hilbert_schmidt_bound(kernel: np.ndarray, measure_weights: np.ndarray | None = None) -> float:
    """Finite-grid Hilbert-Schmidt-style upper bound.

    The returned quantity is a discrete bound estimate.  It is not an
    assertion about an unbounded continuous operator.
    """
    value = np.asarray(kernel)
    bound = np.linalg.norm(value.ravel())
    if measure_weights is not None:
        weights = np.asarray(measure_weights, dtype=float)
        bound *= float(np.prod(np.sqrt(weights)))
    return float(bound)

