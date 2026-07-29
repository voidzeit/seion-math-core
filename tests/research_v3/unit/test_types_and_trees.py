import numpy as np
import pytest

from seion_core.research_v3.local_constants import TypedLaw
from seion_core.research_v3.typed_tree import Leaf, Node, tree_hash, tree_statistics, validate_tree
from seion_core.research_v3.types import TypeSystem, TypedSpace


def test_coordinate_space_has_orthogonal_projector():
    space = TypedSpace.coordinate("x", 4, 2)
    assert np.allclose(space.projector @ space.projector, space.projector)
    assert np.allclose(space.q.conj().T @ space.q, np.eye(2))
    value = np.array([2.0, -1.0])
    assert np.allclose(space.reduce(space.lift(value)), value)


def test_space_rejects_nonisometric_embedding():
    with pytest.raises(ValueError, match="orthonormal"):
        TypedSpace("x", 2, np.array([[2.0], [0.0]]))


def test_typed_tree_rejects_invalid_edge_before_evaluation():
    types = TypeSystem(
        [TypedSpace.coordinate("a", 2, 1), TypedSpace.coordinate("b", 3, 1)]
    )
    law = TypedLaw("mu", ("a", "a"), "a", np.zeros((2, 2, 2)))
    invalid = Node("mu", "a", (Leaf(0, "a"), Leaf(1, "b")))
    with pytest.raises(ValueError, match="type-invalid edge"):
        validate_tree(invalid, types, {"mu": law})


def test_tree_hash_and_statistics_are_deterministic():
    tree = Node(
        "root",
        "tau",
        (Node("child", "tau", (Leaf(0, "tau"), Leaf(1, "tau"))), Leaf(2, "tau")),
    )
    stats = tree_statistics(tree)
    assert stats["node_count"] == 2
    assert stats["leaf_count"] == 3
    assert stats["depth"] == 2
    assert stats["strahler_number"] == 2
    assert stats["tree_hash"] == tree_hash(tree)
    assert tree_hash(tree) == tree_hash(tree)
