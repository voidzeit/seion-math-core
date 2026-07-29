from __future__ import annotations

import numpy as np


def spectral_truncate(matrix: np.ndarray, rank: int) -> tuple[np.ndarray, dict]:
    values, vectors = np.linalg.eigh(0.5 * (matrix + matrix.conj().T))
    selected = np.argsort(-np.abs(values))[:rank]
    return vectors[:, selected] @ np.diag(values[selected]) @ vectors[:, selected].conj().T, {"rank": rank, "status": "finite_spectral_truncation"}

