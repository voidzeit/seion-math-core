from __future__ import annotations

import numpy as np

from .projector import Projector


def spectral_snap(near_projector: np.ndarray, threshold: float = 0.5) -> tuple[Projector, dict]:
    matrix = np.asarray(near_projector)
    hermitian = 0.5 * (matrix + matrix.conj().T)
    values, vectors = np.linalg.eigh(hermitian)
    selected = values >= threshold
    if not np.any(selected):
        # The zero-dimensional image is mathematically valid but Projector is
        # intentionally nonempty; return a rank-one explicit failure record.
        q = vectors[:, -1:]
        rank = 0
        p = np.zeros_like(matrix)
    else:
        q = vectors[:, selected]
        rank = int(np.sum(selected))
        p = q @ q.conj().T
    distances = np.abs(values - threshold)
    gap = float(np.min(distances)) if distances.size else 0.0
    report = {
        "threshold": threshold,
        "eigenvalues": values.tolist(),
        "spectral_gap_to_threshold": gap,
        "rank_before_threshold": int(np.sum(values > 0)),
        "rank_after_snapping": rank,
        "perturbation_size": float(np.linalg.norm(p - matrix)),
        "idempotence_error": float(np.linalg.norm(p @ p - p)),
        "selfadjoint_error": float(np.linalg.norm(p.conj().T - p)),
        "gap_condition_satisfied": bool(gap > 0),
    }
    return Projector(q, method="spectral_snap") if rank else Projector(np.zeros((matrix.shape[0], 1), dtype=matrix.dtype), method="spectral_snap_zero_record"), report


def snapping_counterexample_without_gap() -> dict:
    p_minus = np.diag([0.5 - 1e-12, 0.5 + 1e-12])
    p_plus = np.diag([0.5 + 1e-12, 0.5 - 1e-12])
    return {"before": p_minus.tolist(), "after_perturbation": p_plus.tolist(), "rank_flip": True, "status": "counterexample_to_continuity_without_uniform_gap"}

