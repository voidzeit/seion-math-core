"""First-order signed source certificates for cancellation-aware forests."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Mapping

import numpy as np

from .source_aware_dag import _as_matrix, _matrix_norm


@dataclass(frozen=True, slots=True)
class SignedSourceTerm:
    """One signed first-order term with source-labelled coefficient operators."""

    term_id: str
    coefficient: complex
    source_operators: Mapping[str, np.ndarray] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not self.term_id:
            raise ValueError("signed term ids must be nonempty")
        normalized: dict[str, np.ndarray] = {}
        for source_id, operator in self.source_operators.items():
            if not source_id:
                raise ValueError("source ids must be nonempty")
            normalized[source_id] = _as_matrix(operator, name=f"term operator {source_id!r}")
        object.__setattr__(self, "source_operators", normalized)


@dataclass(frozen=True, slots=True)
class SignedSourceCertificate:
    """Signed source aggregation and its treewise triangle comparison."""

    aggregated_operators: Mapping[str, np.ndarray]
    source_contributions: Mapping[str, float]
    signed_bound: float
    naive_treewise_bound: float
    strict_improvement: bool
    tolerance: float


def certify_signed_source_forest(
    terms: tuple[SignedSourceTerm, ...],
    source_vectors: Mapping[str, np.ndarray],
) -> SignedSourceCertificate:
    """Aggregate signed source operators before taking norms.

    The result is a first-order certificate for a signed forest such as an
    associator.  It proves only the linear source-labelled statement; it does
    not claim a nonlinear universal associator constant.
    """

    if not terms:
        raise ValueError("signed forest must contain at least one term")
    vectors: dict[str, np.ndarray] = {}
    for source_id, vector in source_vectors.items():
        value = np.asarray(vector)
        if value.ndim != 1:
            raise ValueError(f"source vector {source_id!r} must be one-dimensional")
        if not np.issubdtype(value.dtype, np.number):
            raise TypeError(f"source vector {source_id!r} must have a numeric dtype")
        vectors[source_id] = np.array(value, copy=True)

    aggregated: dict[str, np.ndarray] = {}
    naive_treewise_bound = 0.0
    for term in terms:
        for source_id, operator in term.source_operators.items():
            if source_id not in vectors:
                raise ValueError(f"missing vector for source {source_id!r}")
            if operator.shape[1] != vectors[source_id].shape[0]:
                raise ValueError(
                    f"term operator {source_id!r} expects vector dimension {operator.shape[1]}, "
                    f"got {vectors[source_id].shape[0]}"
                )
            scaled = term.coefficient * operator
            if source_id in aggregated:
                if aggregated[source_id].shape != scaled.shape:
                    raise ValueError(f"incompatible output dimensions for source {source_id!r}")
                aggregated[source_id] = aggregated[source_id] + scaled
            else:
                aggregated[source_id] = np.array(scaled, copy=True)
            naive_treewise_bound += (
                abs(term.coefficient)
                * _matrix_norm(operator)
                * float(np.linalg.norm(vectors[source_id]))
            )

    contributions = {
        source_id: _matrix_norm(operator) * float(np.linalg.norm(vectors[source_id]))
        for source_id, operator in aggregated.items()
    }
    signed_bound = sum(contributions.values())
    tolerance = 1.0e-10 * max(1.0, abs(naive_treewise_bound))
    if signed_bound > naive_treewise_bound + tolerance:
        raise AssertionError("signed source certificate exceeds the treewise triangle certificate")
    return SignedSourceCertificate(
        aggregated_operators=aggregated,
        source_contributions=contributions,
        signed_bound=signed_bound,
        naive_treewise_bound=naive_treewise_bound,
        strict_improvement=signed_bound < naive_treewise_bound - tolerance,
        tolerance=tolerance,
    )
