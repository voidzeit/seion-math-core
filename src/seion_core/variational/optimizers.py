from __future__ import annotations

import numpy as np

from ..geometry.stiefel import orthonormalize
from ..projectors.closure import closure_leakage
from ..projectors.projector import Projector


def optimize_projector_closure(
    law, rank: int, samples: list[tuple[np.ndarray, ...]], seed: int = 0, steps: int = 40
) -> tuple[Projector, list[float]]:
    """Small deterministic stochastic-search baseline on the Stiefel manifold.

    This is an empirical optimizer.  It is intentionally not described as a
    global minimization result.
    """
    rng = np.random.default_rng(seed)
    q = orthonormalize(rng.normal(size=(law.output_dim, rank)), rank)
    current = closure_leakage(law, Projector(q), samples)
    history = [current]
    scale = 0.25
    for _ in range(steps):
        proposal = orthonormalize(q + scale * rng.normal(size=q.shape), rank)
        value = closure_leakage(law, Projector(proposal), samples)
        if value <= current:
            q, current = proposal, value
        else:
            scale *= 0.96
        history.append(float(current))
    return Projector(q, method="closure_minimizing_empirical"), history

