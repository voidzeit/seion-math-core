from __future__ import annotations

import numpy as np


def matrix_commutator(left: np.ndarray, right: np.ndarray) -> np.ndarray:
    return np.asarray(left) @ np.asarray(right) - np.asarray(right) @ np.asarray(left)


def normal_tangential_decomposition(matrix: np.ndarray, basis: np.ndarray) -> dict[str, np.ndarray]:
    q = np.asarray(basis)
    p = q @ q.conj().T
    a = np.asarray(matrix)
    return {"tangential": p @ a @ p, "normal": (np.eye(a.shape[0]) - p) @ a @ (np.eye(a.shape[0]) - p)}

