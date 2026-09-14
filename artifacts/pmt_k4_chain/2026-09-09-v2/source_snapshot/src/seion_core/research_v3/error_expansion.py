"""Exact local subset expansion before any norm inequality is applied."""

from __future__ import annotations

from dataclasses import dataclass
from itertools import combinations
from typing import Mapping, Sequence

import numpy as np

from .local_constants import TypedLaw


Subset = tuple[int, ...]


@dataclass(frozen=True, slots=True)
class LocalErrorExpansion:
    local_residual: np.ndarray
    subset_terms: Mapping[Subset, np.ndarray]
    ambient_delta: np.ndarray
    reconstructed_delta: np.ndarray
    projected_delta: np.ndarray
    normal_delta: np.ndarray
    identity_residual: float


def nonempty_subsets(size: int) -> tuple[Subset, ...]:
    return tuple(
        subset for cardinality in range(1, size + 1) for subset in combinations(range(size), cardinality)
    )


def exact_local_expansion(
    law: TypedLaw,
    child_ambient: Sequence[np.ndarray],
    child_projected: Sequence[np.ndarray],
    output_projector: np.ndarray,
) -> LocalErrorExpansion:
    """Expand ``F_v-R_v`` over every nonempty erroneous-child subset.

    With ``Delta_i=F_i-R_i`` the exact identity is

    ``Delta_v = (I-P) mu(R_1,...,R_a) + sum_{S!=empty} mu(y^S)``,

    where ``y_i^S=Delta_i`` for ``i in S`` and ``R_i`` otherwise.
    """

    if len(child_ambient) != law.arity or len(child_projected) != law.arity:
        raise ValueError("child list length must equal the law arity")
    f_values = tuple(np.asarray(value) for value in child_ambient)
    r_values = tuple(np.asarray(value) for value in child_projected)
    deltas = tuple(f_value - r_value for f_value, r_value in zip(f_values, r_values))
    p = np.asarray(output_projector)
    identity = np.eye(p.shape[0], dtype=p.dtype)
    mu_r = law.apply(r_values)
    local = (identity - p) @ mu_r
    terms: dict[Subset, np.ndarray] = {}
    for subset in nonempty_subsets(law.arity):
        chosen = set(subset)
        arguments = [deltas[index] if index in chosen else r_values[index] for index in range(law.arity)]
        terms[subset] = law.apply(arguments)
    ambient_delta = law.apply(f_values) - p @ mu_r
    reconstructed = local + sum(terms.values(), np.zeros_like(local))
    projected = p @ ambient_delta
    normal = (identity - p) @ ambient_delta
    return LocalErrorExpansion(
        local_residual=local,
        subset_terms=terms,
        ambient_delta=ambient_delta,
        reconstructed_delta=reconstructed,
        projected_delta=projected,
        normal_delta=normal,
        identity_residual=float(np.linalg.norm(ambient_delta - reconstructed)),
    )


def symbolic_subset_expansion(arity: int) -> str:
    """Return a stable symbolic rendering used by exact artifacts/tests."""

    if arity < 2:
        raise ValueError("arity must be at least two")
    terms = ["r_v(R_1,...,R_a)"]
    for subset in nonempty_subsets(arity):
        mask = "".join("D" if index in subset else "R" for index in range(arity))
        terms.append(f"mu_v[{mask}]")
    return "Delta_v = " + " + ".join(terms)
