from __future__ import annotations

import numpy as np
import pytest

from seion_core.algebra.cp_law import CPLaw
from seion_core.algebra.nary_law import NaryLaw
from seion_core.research_v2.accelerated import (
    apply_tensor_einsum,
    compose_tensor_tensordot,
    evaluate_tree_einsum,
)
from seion_core.research_v2.reference import (
    Tree,
    apply_tensor_reference,
    compose_tensor_reference,
    evaluate_tree_reference,
)


@pytest.mark.parametrize("arity", [2, 3, 4])
def test_reference_and_einsum_evaluation_match_for_complex_laws(arity: int) -> None:
    rng = np.random.default_rng(100 + arity)
    dimension = 3
    tensor = rng.normal(size=(dimension,) * (arity + 1)) + 1j * rng.normal(
        size=(dimension,) * (arity + 1)
    )
    vectors = [
        rng.normal(size=dimension) + 1j * rng.normal(size=dimension)
        for _ in range(arity)
    ]
    np.testing.assert_allclose(
        apply_tensor_reference(tensor, vectors),
        apply_tensor_einsum(tensor, vectors),
        rtol=1e-12,
        atol=1e-12,
    )


@pytest.mark.parametrize("slot", [0, 1, 2])
def test_reference_and_tensordot_partial_compositions_match(slot: int) -> None:
    rng = np.random.default_rng(200 + slot)
    outer = rng.normal(size=(3, 3, 3, 3))
    inner = rng.normal(size=(3, 3, 3, 3))
    expected = compose_tensor_reference(outer, inner, slot)
    actual = compose_tensor_tensordot(outer, inner, slot)
    assert actual.shape == (3, 3, 3, 3, 3, 3)
    np.testing.assert_allclose(actual, expected, rtol=1e-12, atol=1e-12)


def test_tree_evaluation_parity_for_repeated_leaf_labels() -> None:
    rng = np.random.default_rng(303)
    tensor = rng.normal(size=(2, 2, 2, 2))
    leaves = [rng.normal(size=2) for _ in range(5)]
    tree = Tree.node(Tree.node(0, 1, 2, arity=3), 2, 3, arity=3)
    np.testing.assert_allclose(
        evaluate_tree_reference(tensor, tree, leaves),
        evaluate_tree_einsum(tensor, tree, leaves),
        rtol=1e-12,
        atol=1e-12,
    )


def test_invalid_tree_leaf_is_rejected() -> None:
    with pytest.raises(ValueError):
        Tree.make_leaf(-1)


def test_rank_one_cp_factorization_matches_dense_and_einsum_paths() -> None:
    rng = np.random.default_rng(505)
    output = rng.normal(size=3) + 1j * rng.normal(size=3)
    inputs = [
        rng.normal(size=3) + 1j * rng.normal(size=3),
        rng.normal(size=2) + 1j * rng.normal(size=2),
        rng.normal(size=4) + 1j * rng.normal(size=4),
    ]
    law = CPLaw.from_rank_one_factors(output, inputs, weight=0.7 - 0.2j)
    dense = law.to_dense()
    vectors = [
        rng.normal(size=3) + 1j * rng.normal(size=3),
        rng.normal(size=2) + 1j * rng.normal(size=2),
        rng.normal(size=4) + 1j * rng.normal(size=4),
    ]
    expected = law(*vectors)
    np.testing.assert_allclose(expected, dense(*vectors), rtol=1e-12, atol=1e-12)
    np.testing.assert_allclose(
        expected,
        apply_tensor_einsum(dense.tensor, vectors),
        rtol=1e-12,
        atol=1e-12,
    )
    assert isinstance(dense, NaryLaw)
