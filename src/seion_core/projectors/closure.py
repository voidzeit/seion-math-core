from __future__ import annotations

import numpy as np

from ..algebra.nary_law import NaryLaw
from .projector import Projector


def closure_leakage(
    law: NaryLaw,
    projector: Projector,
    samples: list[tuple[np.ndarray, ...]] | tuple[tuple[np.ndarray, ...], ...],
    eps: float = 1e-15,
) -> float:
    if projector.dimension != law.output_dim or any(d != projector.dimension for d in law.input_dims):
        raise ValueError("closure leakage currently requires an internal law on one common space")
    p = projector.matrix
    complement = np.eye(projector.dimension, dtype=p.dtype) - p
    values = []
    for sample in samples:
        projected = tuple(p @ np.asarray(x) for x in sample)
        output = law(*projected)
        values.append(np.linalg.norm(complement @ output) ** 2 / (np.linalg.norm(output) ** 2 + eps))
    return float(np.mean(values)) if values else 0.0


def closure_residual(law: NaryLaw, projector: Projector, sample: tuple[np.ndarray, ...]) -> np.ndarray:
    p = projector.matrix
    return (np.eye(projector.dimension, dtype=p.dtype) - p) @ law(*[p @ x for x in sample])

