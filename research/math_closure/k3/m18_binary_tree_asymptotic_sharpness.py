"""Repository-evaluator checks for M18 binary-tree asymptotic sharpness."""

from __future__ import annotations

import math
from typing import TypeAlias

import numpy as np

from seion_core.research_v3.exact_evaluation import evaluate_ambient_numpy
from seion_core.research_v3.local_constants import TypedLaw
from seion_core.research_v3.projected_evaluation import evaluate_projected_numpy
from seion_core.research_v3.typed_tree import Leaf, Node
from seion_core.research_v3.types import TypeSystem, TypedSpace


Shape: TypeAlias = None | tuple["Shape", "Shape"]


def full_binary_shapes(internal_nodes: int) -> list[Shape]:
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


def internal_nodes(shape: Shape) -> int:
    if shape is None:
        return 0
    return 1 + internal_nodes(shape[0]) + internal_nodes(shape[1])


def _to_tree(shape: Shape, labels: list[int], *, root: bool = True) -> Leaf | Node:
    if shape is None:
        leaf = Leaf(labels[0], "tau")
        labels[0] += 1
        return leaf
    law_id = "root" if root else "inner"
    return Node(
        law_id,
        "tau",
        (_to_tree(shape[0], labels, root=False), _to_tree(shape[1], labels, root=False)),
    )


def typed_tree(shape: Shape) -> Leaf | Node:
    return _to_tree(shape, [0])


def laws(theta: float) -> dict[str, TypedLaw]:
    c, s = math.cos(theta), math.sin(theta)
    inner = np.zeros((2, 2, 2), dtype=float)
    # Complex multiplication C(z,w)=(x0*y0-x1*y1, x0*y1+x1*y0),
    # followed by multiplication by exp(i theta).
    inner[0, 0, 0] = c
    inner[0, 1, 1] = -c
    inner[0, 0, 1] = -s
    inner[0, 1, 0] = -s
    inner[1, 0, 0] = s
    inner[1, 1, 1] = -s
    inner[1, 0, 1] = c
    inner[1, 1, 0] = c
    root = np.zeros((2, 2, 2), dtype=float)
    root[0, 1, 0] = 1.0
    root[0, 0, 1] = 1.0
    return {
        "inner": TypedLaw("inner", ("tau", "tau"), "tau", inner),
        "root": TypedLaw("root", ("tau", "tau"), "tau", root),
    }


def evaluate_witness(shape: Shape, eta: float) -> float:
    if not 0.0 < eta < 1.0:
        raise ValueError("eta must lie in (0,1) for the evaluator")
    theta = math.asin(eta)
    tree = typed_tree(shape)
    types = TypeSystem([TypedSpace.coordinate("tau", 2, 1, field="real")])
    leaves = {
        label: np.array([1.0 + 0.0j])
        for label in range(internal_nodes(shape) + 1)
    }
    ambient = evaluate_ambient_numpy(tree, laws(theta), types, leaves).root
    projected = evaluate_projected_numpy(tree, laws(theta), types, leaves).root
    return float(np.linalg.norm(types["tau"].project(ambient) - projected))


def closed_form(shape: Shape, eta: float) -> float:
    k = internal_nodes(shape)
    return abs(math.sin((k - 1) * math.asin(eta)))


def verify_formula(max_internal_nodes: int = 6) -> bool:
    for k in range(1, max_internal_nodes + 1):
        for shape in full_binary_shapes(k):
            for eta in (1.0e-5, 0.03, 0.2, 0.7):
                observed = evaluate_witness(shape, eta)
                if not math.isclose(observed, closed_form(shape, eta), rel_tol=0.0, abs_tol=2.0e-12):
                    return False
    return True


def verify_asymptotic(max_internal_nodes: int = 6) -> bool:
    for k in range(2, max_internal_nodes + 1):
        shape = full_binary_shapes(k)[0]
        for eta in (1.0e-6, 1.0e-7, 1.0e-8):
            ratio = closed_form(shape, eta) / eta
            if abs(ratio - (k - 1)) > 1.0e-5:
                return False
    return True


if __name__ == "__main__":
    assert verify_formula()
    assert verify_asymptotic()
    print("All checks passed: M18 binary-tree asymptotic sharpness.")
