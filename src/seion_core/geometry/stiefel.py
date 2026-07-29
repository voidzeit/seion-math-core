from __future__ import annotations

import numpy as np


def orthonormalize(matrix: np.ndarray, rank: int | None = None) -> np.ndarray:
    q, _ = np.linalg.qr(np.asarray(matrix))
    return q[:, :rank] if rank is not None else q


def project_tangent(q: np.ndarray, gradient: np.ndarray) -> np.ndarray:
    q = np.asarray(q)
    gradient = np.asarray(gradient)
    sym = 0.5 * (q.conj().T @ gradient + gradient.conj().T @ q)
    return gradient - q @ sym

