from __future__ import annotations

import numpy as np

from ..algebra.nary_law import NaryLaw
from .projector import Projector


def reduced_law(law: NaryLaw, projector: Projector) -> NaryLaw:
    """Coordinate representation ``Q* mu(Qz_1,...,Qz_n)`` on ``Im(P)``."""
    if projector.dimension != law.output_dim or any(d != projector.dimension for d in law.input_dims):
        raise ValueError("reduced_law requires an internal law on the projector space")
    q = projector.q
    result = law.tensor
    # Contract output with Q* and each input index with Q.
    result = np.tensordot(q.conj().T, result, axes=([1], [0]))
    for reduced_count in range(law.arity):
        axis = 1 + reduced_count
        result = np.tensordot(result, q, axes=([axis], [0]))
        # Keep output first, then reduced input axes, then unreduced axes.
        result = np.moveaxis(result, -1, axis)
    return NaryLaw(result, law.arity, name=f"reduced({law.name})")


def lifted_reduced_output(law: NaryLaw, projector: Projector, reduced_inputs: tuple[np.ndarray, ...]) -> np.ndarray:
    return projector.q @ reduced_law(law, projector)(*reduced_inputs)
