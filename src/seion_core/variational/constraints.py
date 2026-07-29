from __future__ import annotations

import numpy as np


def orthogonality_violation(q: np.ndarray) -> float:
    q = np.asarray(q)
    return float(np.linalg.norm(q.conj().T @ q - np.eye(q.shape[1])))


def project_to_stiefel(q: np.ndarray) -> np.ndarray:
    return np.linalg.qr(np.asarray(q))[0][:, :q.shape[1]]

