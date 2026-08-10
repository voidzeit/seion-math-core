"""Exact evaluator for every finite ordered full-binary gated-rotation tree."""

from __future__ import annotations

import sys
from pathlib import Path
from typing import TypeAlias

import numpy as np
import sympy as sp

REPO_ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(REPO_ROOT / "src"))

from seion_core.research_v3.exact_evaluation import evaluate_ambient_numpy  # noqa: E402
from seion_core.research_v3.local_constants import TypedLaw  # noqa: E402
from seion_core.research_v3.projected_evaluation import evaluate_projected_numpy  # noqa: E402
from seion_core.research_v3.typed_tree import Leaf, Node  # noqa: E402
from seion_core.research_v3.types import TypeSystem, TypedSpace  # noqa: E402


Shape: TypeAlias = None | tuple["Shape", "Shape"]


def full_binary_shapes(internal_nodes: int) -> list[Shape]:
    """Enumerate all ordered full-binary shapes with the given node count."""

    if internal_nodes < 0:
        raise ValueError("internal_nodes must be nonnegative")
    if internal_nodes == 0:
        return [None]
    result: list[Shape] = []
    for left_nodes in range(internal_nodes):
        right_nodes = internal_nodes - 1 - left_nodes
        result.extend(
            (left, right)
            for left in full_binary_shapes(left_nodes)
            for right in full_binary_shapes(right_nodes)
        )
    return result


def _to_typed_tree(shape: Shape, next_leaf: list[int]) -> Leaf | Node:
    if shape is None:
        label = next_leaf[0]
        next_leaf[0] += 1
        return Leaf(label, "tau")
    left, right = shape
    return Node(
        "mu",
        "tau",
        (_to_typed_tree(left, next_leaf), _to_typed_tree(right, next_leaf)),
    )


def typed_tree(shape: Shape) -> Leaf | Node:
    next_leaf = [0]
    return _to_typed_tree(shape, next_leaf)


def internal_nodes(shape: Shape) -> int:
    if shape is None:
        return 0
    left, right = shape
    return 1 + internal_nodes(left) + internal_nodes(right)


def left_spine_depth(shape: Shape) -> int:
    """Number of internal nodes on the path obtained by taking left slots."""

    if shape is None:
        return 0
    return 1 + left_spine_depth(shape[0])


def ambient_amplitude(shape: Shape, theta: sp.Expr) -> sp.Expr:
    """Return alpha in z_shape = alpha * R(theta)^d * e0."""

    if shape is None:
        return sp.Integer(1)
    left, right = shape
    return sp.simplify(
        ambient_amplitude(left, theta)
        * ambient_amplitude(right, theta)
        * sp.cos(left_spine_depth(right) * theta)
    )


def closed_form_error_squared(shape: Shape, theta: sp.Expr) -> sp.Expr:
    """Return the exact normalized projected-root error squared."""

    alpha = ambient_amplitude(shape, theta)
    depth = left_spine_depth(shape)
    projected_scalar = sp.cos(theta) ** internal_nodes(shape)
    return sp.expand((alpha * sp.cos(depth * theta) - projected_scalar) ** 2)


def _symbolic_rotation_law(
    dimension: int, projector_rank: int, theta: sp.Expr
) -> TypedLaw:
    c = sp.cos(theta)
    s = sp.sin(theta)
    rotation = sp.Matrix([[c, -s], [s, c]])
    tensor = np.zeros((dimension, dimension, dimension), dtype=object)
    active = (0, projector_rank)
    for out_local, out_index in enumerate(active):
        for first_local, first_index in enumerate(active):
            tensor[(out_index, first_index, 0)] = rotation[out_local, first_local]
    return TypedLaw("mu", ("tau", "tau"), "tau", tensor)


def symbolic_projected_error_squared(
    shape: Shape, *, dimension: int = 2, projector_rank: int = 1
) -> sp.Expr:
    if not 1 <= projector_rank < dimension:
        raise ValueError("require 1 <= projector_rank < dimension")
    theta = sp.Symbol("theta", real=True)
    types = TypeSystem([TypedSpace.coordinate("tau", dimension, projector_rank, field="real")])
    tree = typed_tree(shape)
    leaf_count = internal_nodes(shape) + 1
    leaves = {
        label: np.array(
            [sp.Integer(1)] + [sp.Integer(0)] * (projector_rank - 1), dtype=object
        )
        for label in range(leaf_count)
    }
    law = _symbolic_rotation_law(dimension, projector_rank, theta)
    ambient = evaluate_ambient_numpy(tree, {"mu": law}, types, leaves).root
    projected = evaluate_projected_numpy(tree, {"mu": law}, types, leaves).root
    difference = types["tau"].project(ambient) - projected
    return sp.expand(sum(sp.simplify(value) ** 2 for value in difference))


def verify_closed_form(max_internal_nodes: int = 4) -> bool:
    theta = sp.Symbol("theta", real=True)
    for node_count in range(1, max_internal_nodes + 1):
        for shape in full_binary_shapes(node_count):
            expected = closed_form_error_squared(shape, theta)
            for dimension, rank in ((2, 1), (3, 1), (3, 2), (4, 2)):
                observed = symbolic_projected_error_squared(
                    shape, dimension=dimension, projector_rank=rank
                )
                identity = sp.expand_trig(observed - expected)
                identity = identity.subs(sp.sin(theta) ** 2, 1 - sp.cos(theta) ** 2)
                if sp.simplify(identity) != 0:
                    return False
    return True


if __name__ == "__main__":
    assert verify_closed_form()
    print(
        "All checks passed: full ordered-binary gated-rotation formula verified "
        "through four internal nodes."
    )
