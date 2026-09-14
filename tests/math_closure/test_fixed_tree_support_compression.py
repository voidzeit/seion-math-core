from __future__ import annotations

import numpy as np

from research.math_closure.dimension_rank.fixed_tree_support_compression import (
    invariant_span_basis,
    invariant_span_residual,
    k3_binary_support_bound,
    support_bound,
)


def test_support_bound_counts_node_and_leaf_generators():
    result = support_bound(leaf_vectors=4, internal_nodes=3)
    assert result.dimension_bound == 20
    assert k3_binary_support_bound(require_proper_projector=True).proper_projector_dimension_bound == 22


def test_projector_closed_span_is_invariant_and_has_the_doubled_bound():
    projector = np.diag([1.0, 1.0, 0.0, 0.0])
    vectors = [
        np.array([1.0, 2.0, 3.0, 4.0]),
        np.array([0.0, 1.0, 1.0, -2.0]),
        np.array([2.0, -1.0, 0.5, 3.0]),
    ]
    basis = invariant_span_basis(projector, vectors)
    assert basis.shape[1] <= 2 * len(vectors)
    assert invariant_span_residual(projector, basis) < 1e-10
