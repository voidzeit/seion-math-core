from __future__ import annotations

import numpy as np

from .chain_complex import ChainComplex


def descends_to_cohomology(operator: np.ndarray, complex_: ChainComplex, tolerance: float = 1e-10) -> dict:
    operator = np.asarray(operator)
    defects = []
    for d in complex_.differentials:
        if operator.shape == d.shape:
            defects.append(float(np.linalg.norm(operator @ d - d @ operator)))
    passed = bool(defects) and all(value <= tolerance for value in defects)
    return {"commutator_defects": defects, "tolerance": tolerance, "descends": passed, "status": "proved_under_finite_dimensional_commutation" if passed else "incompatible_control"}


def cohomology_action(operator: np.ndarray, harmonic_basis: np.ndarray) -> np.ndarray:
    q = np.asarray(harmonic_basis)
    return q.conj().T @ np.asarray(operator) @ q

