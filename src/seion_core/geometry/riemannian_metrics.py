from __future__ import annotations

import numpy as np


def stiefel_metric(q: np.ndarray, tangent_a: np.ndarray, tangent_b: np.ndarray) -> float:
    return float(np.real(np.trace(tangent_a.conj().T @ tangent_b)))


def principal_angles(q: np.ndarray, r: np.ndarray) -> np.ndarray:
    singular_values = np.linalg.svd(np.asarray(q).conj().T @ np.asarray(r), compute_uv=False)
    return np.arccos(np.clip(np.real(singular_values), -1.0, 1.0))

