from __future__ import annotations

import numpy as np


def relative_error(value, reference, eps: float = 1e-15) -> float:
    value = np.asarray(value); reference = np.asarray(reference)
    return float(np.linalg.norm(value.ravel() - reference.ravel()) / max(np.linalg.norm(reference.ravel()), eps))


def scaled_residual(residual, scale, eps: float = 1e-15) -> float:
    return float(np.linalg.norm(np.asarray(residual).ravel()) / max(float(np.linalg.norm(np.asarray(scale).ravel())), eps))

