"""Exact evaluator for finite ordered trees with arity-compatible gated rotations."""

from __future__ import annotations

import sys
from itertools import product
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


Shape: TypeAlias = None | tuple["Shape", ...]


def _compositions(total: int, parts: int) -> list[tuple[int, ...]]:
    if parts == 1:
        return [(total,)]
    return [
        (head,) + tail
        for head in range(total + 1)
        for tail in _compositions(total - head, parts - 1)
    ]


def rooted_shapes(internal_nodes: int, max_arity: int = 3) -> list[Shape]:
    """Enumerate ordered rooted shapes with arity in [2, max_arity]."""

    if internal_nodes < 0 or max_arity < 2:
        raise ValueError("internal_nodes >= 0 and max_arity >= 2 are required")
    if internal_nodes == 0:
        return [None]
    result: list[Shape] = []
    for arity in range(2, max_arity + 1):
        for allocation in _compositions(internal_nodes - 1, arity):
            children = [rooted_shapes(count, max_arity) for count in allocation]
            for choice in product(*children):
                result.append(tuple(choice))
    return result


def _to_typed_tree(shape: Shape, next_leaf: list[int]) -> Leaf | Node:
    if shape is None:
        label = next_leaf[0]
        next_leaf[0] += 1
        return Leaf(label, "tau")
    arity = len(shape)
    return Node(
        f"mu{arity}",
        "tau",
        tuple(_to_typed_tree(child, next_leaf) for child in shape),
    )


def typed_tree(shape: Shape) -> Leaf | Node:
    next_leaf = [0]
    return _to_typed_tree(shape, next_leaf)


def internal_nodes(shape: Shape) -> int:
    if shape is None:
        return 0
    return 1 + sum(internal_nodes(child) for child in shape)


def leaf_count(shape: Shape) -> int:
    if shape is None:
        return 1
    return sum(leaf_count(child) for child in shape)


def left_spine_depth(shape: Shape) -> int:
    if shape is None:
        return 0
    return 1 + left_spine_depth(shape[0])


def ambient_amplitude(shape: Shape, theta: sp.Expr) -> sp.Expr:
    if shape is None:
        return sp.Integer(1)
    value = ambient_amplitude(shape[0], theta)
    for child in shape[1:]:
        value *= ambient_amplitude(child, theta) * sp.cos(
            left_spine_depth(child) * theta
        )
    return sp.simplify(value)


def closed_form_error_squared(shape: Shape, theta: sp.Expr) -> sp.Expr:
    alpha = ambient_amplitude(shape, theta)
    depth = left_spine_depth(shape)
    projected_scalar = sp.cos(theta) ** internal_nodes(shape)
    return sp.expand((alpha * sp.cos(depth * theta) - projected_scalar) ** 2)


def _symbolic_rotation_law(
    law_id: str, arity: int, dimension: int, projector_rank: int, theta: sp.Expr
) -> TypedLaw:
    c = sp.cos(theta)
    s = sp.sin(theta)
    rotation = sp.Matrix([[c, -s], [s, c]])
    tensor = np.zeros((dimension,) + (dimension,) * arity, dtype=object)
    active = (0, projector_rank)
    for out_local, out_index in enumerate(active):
        for first_local, first_index in enumerate(active):
            index = (out_index, first_index) + (0,) * (arity - 1)
            tensor[index] = rotation[out_local, first_local]
    return TypedLaw(law_id, ("tau",) * arity, "tau", tensor)


def symbolic_projected_error_squared(
    shape: Shape, *, dimension: int = 2, projector_rank: int = 1
) -> sp.Expr:
    if not 1 <= projector_rank < dimension:
        raise ValueError("require 1 <= projector_rank < dimension")
    theta = sp.Symbol("theta", real=True)
    types = TypeSystem([TypedSpace.coordinate("tau", dimension, projector_rank, field="real")])
    tree = typed_tree(shape)
    arities = set()

    def collect(current: Shape) -> None:
        if current is not None:
            arities.add(len(current))
            for child in current:
                collect(child)

    collect(shape)
    laws = {
        f"mu{arity}": _symbolic_rotation_law(
            f"mu{arity}", arity, dimension, projector_rank, theta
        )
        for arity in arities
    }
    leaves = {
        label: np.array(
            [sp.Integer(1)] + [sp.Integer(0)] * (projector_rank - 1), dtype=object
        )
        for label in range(leaf_count(shape))
    }
    ambient = evaluate_ambient_numpy(tree, laws, types, leaves).root
    projected = evaluate_projected_numpy(tree, laws, types, leaves).root
    difference = types["tau"].project(ambient) - projected
    return sp.expand(sum(sp.simplify(value) ** 2 for value in difference))


def _identity_zero(observed: sp.Expr, expected: sp.Expr, theta: sp.Symbol) -> bool:
    identity = sp.expand_trig(observed - expected)
    identity = identity.subs(sp.sin(theta) ** 2, 1 - sp.cos(theta) ** 2)
    return sp.simplify(identity) == 0


def verify_closed_form(max_internal_nodes: int = 3, max_arity: int = 3) -> bool:
    theta = sp.Symbol("theta", real=True)
    for node_count in range(1, max_internal_nodes + 1):
        for shape in rooted_shapes(node_count, max_arity):
            expected = closed_form_error_squared(shape, theta)
            for dimension, rank in ((2, 1), (3, 1), (3, 2), (4, 2)):
                observed = symbolic_projected_error_squared(
                    shape, dimension=dimension, projector_rank=rank
                )
                if not _identity_zero(observed, expected, theta):
                    return False
    return True


if __name__ == "__main__":
    assert verify_closed_form()
    print(
        "All checks passed: arity-compatible gated-rotation formula verified "
        "through three internal nodes."
    )
