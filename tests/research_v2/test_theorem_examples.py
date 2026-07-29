from __future__ import annotations

import json
from pathlib import Path

import numpy as np

from seion_core.research_v2.accelerated import apply_tensor_einsum
from seion_core.research_v2.reference import (
    Tree,
    compose_tensor_reference,
    exact_reduction_tensor,
    evaluate_tree_reference,
    tree_bound,
)


def _projected_tree(
    tensor: np.ndarray, tree: Tree, leaves: list[np.ndarray], p: np.ndarray
) -> np.ndarray:
    if tree.is_leaf:
        assert tree.leaf is not None
        return p @ leaves[tree.leaf]
    assert tree.children is not None
    child_values = [_projected_tree(tensor, child, leaves, p) for child in tree.children]
    return p @ apply_tensor_einsum(tensor, child_values)


def test_exact_invariant_reduction_and_composition_are_exact() -> None:
    # Rational block-supported ternary law on R^4, with W=span(e0,e1).
    tensor = np.zeros((4, 4, 4, 4), dtype=float)
    tensor[0, 0, 0, 0] = 1.0
    tensor[1, 1, 0, 1] = -2.0
    tensor[0, 1, 1, 0] = 3.0
    q = np.eye(4)[:, :2]
    reduced = exact_reduction_tensor(tensor, q)
    rng = np.random.default_rng(404)
    values = [rng.normal(size=2) for _ in range(3)]
    np.testing.assert_allclose(
        q @ apply_tensor_einsum(reduced, values),
        apply_tensor_einsum(tensor, [q @ value for value in values]),
        atol=1e-12,
    )
    for slot in range(3):
        composed_full = compose_tensor_reference(tensor, tensor, slot)
        composed_reduced = compose_tensor_reference(reduced, reduced, slot)
        shared = [rng.normal(size=2) for _ in range(5)]
        left = q @ apply_tensor_einsum(composed_reduced, shared)
        right = apply_tensor_einsum(composed_full, [q @ value for value in shared])
        np.testing.assert_allclose(left, right, atol=1e-12)


def test_approximate_tree_bound_is_respected() -> None:
    rng = np.random.default_rng(405)
    tensor = rng.normal(size=(3, 3, 3, 3)) / 5.0
    q = np.eye(3)[:, :2]
    p = q @ q.T
    leaves = [rng.normal(size=2) for _ in range(9)]
    tree = Tree.node(
        Tree.node(0, 1, 2, arity=3),
        Tree.node(3, 4, 5, arity=3),
        Tree.node(6, 7, 8, arity=3),
        arity=3,
    )
    lifted_leaves = [q @ value for value in leaves]
    full = evaluate_tree_reference(tensor, tree, lifted_leaves)
    projected = _projected_tree(tensor, tree, lifted_leaves, p)
    observed = float(np.linalg.norm(full - projected))
    operator_upper = float(np.linalg.norm(tensor.ravel()))
    projected_tensor = tensor.copy()
    for axis in range(1, tensor.ndim):
        projected_tensor = np.tensordot(projected_tensor, p, axes=([axis], [0]))
        projected_tensor = np.moveaxis(projected_tensor, -1, axis)
    leakage = projected_tensor - np.tensordot(p, projected_tensor, axes=([1], [0]))
    closure_upper = float(np.linalg.norm(leakage.ravel()))
    bound = tree_bound(tree, operator_upper, closure_upper, [np.linalg.norm(x) for x in leaves])
    assert observed <= bound + 1e-11


def test_no_invariance_counterexample_breaks_composition() -> None:
    # Binary law on R^2: mu(e0,e0)=e1 and mu(e1,e0)=e0.
    outer = np.zeros((2, 2, 2), dtype=float)
    outer[1, 0, 0] = 1.0
    outer[0, 1, 0] = 1.0
    inner = outer.copy()
    q = np.eye(2)[:, :1]
    reduced = exact_reduction_tensor(inner, q)
    reduced_composition = compose_tensor_reference(reduced, reduced, 0)
    full_composition = compose_tensor_reference(outer, inner, 0)
    assert np.allclose(reduced_composition, 0.0)
    assert full_composition[0, 0, 0, 0] == 1.0


def test_no_gap_counterexample_has_small_perturbation_but_large_snap_change() -> None:
    delta = 1e-8
    before = np.diag([0.5 - delta, 0.5 + delta])
    after = np.diag([0.5 + delta, 0.5 - delta])
    p_before = np.diag([0.0, 1.0])
    p_after = np.diag([1.0, 0.0])
    assert np.isclose(np.linalg.norm(after - before, 2), 2 * delta)
    assert np.linalg.norm(p_after - p_before, 2) == 1.0


def test_exact_example_artifact_is_json_serializable(tmp_path: Path) -> None:
    artifact = {
        "status": "passed",
        "tensor_shape": [4, 4, 4, 4],
        "reduction_rank": 2,
        "max_exact_residual": 0.0,
    }
    path = tmp_path / "example.json"
    path.write_text(json.dumps(artifact, indent=2), encoding="utf-8")
    assert json.loads(path.read_text(encoding="utf-8"))["status"] == "passed"
