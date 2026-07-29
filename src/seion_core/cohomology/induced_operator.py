from __future__ import annotations

import numpy as np


def induced_operator(operator: np.ndarray, degree: int | None = None) -> np.ndarray:
    return np.asarray(operator)


def commutator_defect(operator: np.ndarray, differential: np.ndarray) -> float:
    return float(np.linalg.norm(np.asarray(operator) @ np.asarray(differential) - np.asarray(differential) @ np.asarray(operator)))

