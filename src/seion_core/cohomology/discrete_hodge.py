from __future__ import annotations

import numpy as np

from .chain_complex import ChainComplex


def hodge_laplacian(complex_: ChainComplex, degree: int) -> np.ndarray:
    d_prev = complex_.differentials[degree - 1] if degree > 0 else np.zeros((complex_.dimensions[degree], 0))
    d_next = complex_.differentials[degree] if degree < len(complex_.differentials) else np.zeros((0, complex_.dimensions[degree]))
    return d_prev @ d_prev.conj().T + d_next.conj().T @ d_next

