from __future__ import annotations

import numpy as np


def laplacian_from_curried(operators: list[np.ndarray], symmetrize: bool = True) -> tuple[np.ndarray, dict]:
    if not operators:
        raise ValueError("at least one operator is required")
    laplacian = sum(op.conj().T @ op for op in operators)
    if symmetrize:
        laplacian = 0.5 * (laplacian + laplacian.conj().T)
    eigenvalues = np.linalg.eigvalsh(laplacian)
    metadata = {
        "construction": "sum of adjoint-compositions of declared curried operators",
        "self_adjoint": bool(np.allclose(laplacian, laplacian.conj().T)),
        "positive_semidefinite_numerical": bool(np.min(eigenvalues) >= -1e-10),
        "markovian": False,
        "intrinsic": False,
        "minimum_eigenvalue": float(np.min(eigenvalues)),
    }
    return laplacian, metadata


def dirichlet_form(laplacian: np.ndarray, vector: np.ndarray) -> float:
    return float(np.real(np.vdot(vector, np.asarray(laplacian) @ vector)))

