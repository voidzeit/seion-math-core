"""Finite-support compression bounds for fixed typed projected trees."""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np


@dataclass(frozen=True, slots=True)
class SupportBound:
    """Dimension/rank bound for one typed support space."""

    leaf_vectors: int
    node_vectors: int
    dimension_bound: int
    proper_projector_dimension_bound: int


def support_bound(
    leaf_vectors: int,
    internal_nodes: int,
    *,
    require_proper_projector: bool = False,
) -> SupportBound:
    """Return the deterministic support bound from the compression lemma.

    The generating set has one leaf vector and two node-output vectors per
    internal node (ambient and recursively projected raw output). Closing it
    under one orthogonal projector doubles the span dimension at most. Two
    dummy coordinates suffice if a proper nonzero projector is required after
    compression.
    """

    if leaf_vectors < 0 or internal_nodes < 0:
        raise ValueError("counts must be nonnegative")
    node_vectors = 2 * internal_nodes
    dimension_bound = 2 * (leaf_vectors + node_vectors)
    proper_bound = dimension_bound + (2 if require_proper_projector else 0)
    return SupportBound(
        leaf_vectors=leaf_vectors,
        node_vectors=node_vectors,
        dimension_bound=dimension_bound,
        proper_projector_dimension_bound=proper_bound,
    )


def invariant_span_basis(projector: np.ndarray, vectors: list[np.ndarray]) -> np.ndarray:
    """Return an orthonormal basis for span(vectors, P*vectors).

    This is a numerical realization of the support construction used in the
    proof. It is a diagnostic helper, not a replacement for the analytic
    theorem.
    """

    p = np.asarray(projector, dtype=float)
    if p.ndim != 2 or p.shape[0] != p.shape[1]:
        raise ValueError("projector must be square")
    if not vectors:
        return np.zeros((p.shape[0], 0), dtype=float)
    columns = [np.asarray(v, dtype=float) for v in vectors]
    if any(v.shape != (p.shape[0],) for v in columns):
        raise ValueError("every vector must match the projector dimension")
    generating = np.column_stack(columns + [p @ v for v in columns])
    u, singular, _ = np.linalg.svd(generating, full_matrices=False)
    rank = int(np.sum(singular > 1.0e-10))
    return u[:, :rank]


def invariant_span_residual(projector: np.ndarray, basis: np.ndarray) -> float:
    """Measure the residual of P-invariance for a computed basis."""

    p = np.asarray(projector, dtype=float)
    q = np.asarray(basis, dtype=float)
    if q.ndim != 2 or q.shape[0] != p.shape[0]:
        raise ValueError("basis and projector dimensions do not match")
    if q.shape[1] == 0:
        return 0.0
    coefficient = q.T @ p @ q
    return float(np.linalg.norm(p @ q - q @ coefficient))


def k3_binary_support_bound(*, require_proper_projector: bool = False) -> SupportBound:
    """Bound for a one-type k=3 binary chain or branching tree."""

    return support_bound(leaf_vectors=4, internal_nodes=3,
                         require_proper_projector=require_proper_projector)


if __name__ == "__main__":
    result = k3_binary_support_bound(require_proper_projector=True)
    assert result.dimension_bound == 20
    assert result.proper_projector_dimension_bound == 22
    print(
        "Support-compression checks passed: k=3 binary bound is "
        f"{result.dimension_bound} (or {result.proper_projector_dimension_bound} "
        "with a proper-projector padding pair)."
    )
