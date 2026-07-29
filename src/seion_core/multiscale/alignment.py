from __future__ import annotations

import numpy as np


def align_bases(left: np.ndarray, right: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    """Orthogonal Procrustes alignment and aligned right basis."""
    cross = np.asarray(left).conj().T @ np.asarray(right)
    u, _, vh = np.linalg.svd(cross)
    rotation = vh.conj().T @ u.conj().T
    return rotation, np.asarray(right) @ rotation

