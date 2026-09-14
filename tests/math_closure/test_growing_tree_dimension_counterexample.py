from __future__ import annotations

import pytest

from research.math_closure.dimension_rank.growing_tree_dimension_counterexample import (
    build_growing_chain_witness,
    verify_growing_chain_obstruction,
)


@pytest.mark.parametrize("depth", [1, 2, 5, 11])
def test_independent_law_chain_requires_growing_nodewise_support(depth: int):
    witness = verify_growing_chain_obstruction(depth)
    assert witness.support_rank == depth + 1
    assert witness.projector_rank == depth + 1
    assert witness.operator_norm == 1.0
    assert witness.closure_residual == 0.0


def test_depth_validation_is_explicit():
    with pytest.raises(ValueError, match="depth"):
        build_growing_chain_witness(0)
