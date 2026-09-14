"""Evaluator for M19: asymptotic ``k-1`` sharpness at arbitrary finite arity."""

from __future__ import annotations

import math
from itertools import product
from typing import TypeAlias

import numpy as np

from seion_core.research_v3.exact_evaluation import evaluate_ambient_numpy
from seion_core.research_v3.local_constants import TypedLaw
from seion_core.research_v3.projected_evaluation import evaluate_projected_numpy
from seion_core.research_v3.typed_tree import Leaf, Node
from seion_core.research_v3.types import TypeSystem, TypedSpace


Shape: TypeAlias = None | tuple["Shape", ...]


def _compositions(total: int, parts: int) -> list[tuple[int, ...]]:
    if parts == 1:
        return [(total,)]
    return [
        (head,) + tail
        for head in range(total + 1)
        for tail in _compositions(total - head, parts - 1)
    ]


def rooted_shapes(internal_nodes: int, max_arity: int = 4) -> list[Shape]:
    """Enumerate ordered finite rooted shapes with arity 2 through max_arity."""

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


def internal_nodes(shape: Shape) -> int:
    if shape is None:
        return 0
    return 1 + sum(internal_nodes(child) for child in shape)


def leaf_count(shape: Shape) -> int:
    if shape is None:
        return 1
    return sum(leaf_count(child) for child in shape)


def _to_tree(shape: Shape, labels: list[int], *, root: bool = True) -> Leaf | Node:
    if shape is None:
        leaf = Leaf(labels[0], "tau")
        labels[0] += 1
        return leaf
    arity = len(shape)
    law_id = f"root{arity}" if root else f"inner{arity}"
    return Node(
        law_id,
        "tau",
        tuple(_to_tree(child, labels, root=False) for child in shape),
    )


def typed_tree(shape: Shape) -> Leaf | Node:
    return _to_tree(shape, [0])


def _rotated_product_tensor(arity: int, theta: float) -> np.ndarray:
    """Real-coordinate tensor for ``exp(i theta) prod_j z_j`` on R^2 ~= C."""

    tensor = np.zeros((2,) + (2,) * arity, dtype=float)
    phase = complex(math.cos(theta), math.sin(theta))
    for bits in product((0, 1), repeat=arity):
        coefficient = phase * (1j ** sum(bits))
        tensor[(0, *bits)] = coefficient.real
        tensor[(1, *bits)] = coefficient.imag
    return tensor


def _imaginary_product_tensor(arity: int) -> np.ndarray:
    """Real-coordinate tensor for ``Im(prod_j z_j) e0`` on R^2 ~= C."""

    tensor = np.zeros((2,) + (2,) * arity, dtype=float)
    for bits in product((0, 1), repeat=arity):
        tensor[(0, *bits)] = (1j ** sum(bits)).imag
    return tensor


def laws(shape: Shape, theta: float) -> dict[str, TypedLaw]:
    arities: set[int] = set()

    def collect(current: Shape) -> None:
        if current is None:
            return
        arities.add(len(current))
        for child in current:
            collect(child)

    collect(shape)
    result: dict[str, TypedLaw] = {}
    for arity in arities:
        result[f"inner{arity}"] = TypedLaw(
            f"inner{arity}", ("tau",) * arity, "tau", _rotated_product_tensor(arity, theta)
        )
        result[f"root{arity}"] = TypedLaw(
            f"root{arity}", ("tau",) * arity, "tau", _imaginary_product_tensor(arity)
        )
    return result


def evaluate_witness(shape: Shape, eta: float) -> float:
    if not 0.0 < eta < 1.0:
        raise ValueError("eta must lie in (0,1) for the evaluator")
    theta = math.asin(eta)
    tree = typed_tree(shape)
    types = TypeSystem([TypedSpace.coordinate("tau", 2, 1, field="real")])
    leaves = {label: np.array([1.0]) for label in range(leaf_count(shape))}
    family = laws(shape, theta)
    ambient = evaluate_ambient_numpy(tree, family, types, leaves).root
    projected = evaluate_projected_numpy(tree, family, types, leaves).root
    return float(np.linalg.norm(types["tau"].project(ambient) - projected))


def closed_form(shape: Shape, eta: float) -> float:
    return abs(math.sin((internal_nodes(shape) - 1) * math.asin(eta)))


def _canonical_shape(internal_node_count: int, max_arity: int) -> Shape:
    """Build one finite shape without enumerating the full topology atlas."""

    if internal_node_count == 0:
        return None
    arity = min(max_arity, internal_node_count + 1)
    return (_canonical_shape(internal_node_count - 1, max_arity),) + (
        (None,) * (arity - 1)
    )


def verify_formula(max_internal_nodes: int = 3, max_arity: int = 4) -> bool:
    for k in range(1, max_internal_nodes + 1):
        for shape in rooted_shapes(k, max_arity):
            for eta in (1.0e-5, 0.03, 0.2, 0.7):
                observed = evaluate_witness(shape, eta)
                if not math.isclose(
                    observed, closed_form(shape, eta), rel_tol=0.0, abs_tol=2.0e-12
                ):
                    return False
    return True


def verify_asymptotic(max_internal_nodes: int = 7, max_arity: int = 4) -> bool:
    for k in range(2, max_internal_nodes + 1):
        shape = _canonical_shape(k, max_arity)
        for eta in (1.0e-6, 1.0e-7, 1.0e-8):
            ratio = closed_form(shape, eta) / eta
            if abs(ratio - (k - 1)) > 1.0e-5:
                return False
    return True


if __name__ == "__main__":
    assert verify_formula()
    assert verify_asymptotic()
    print("All checks passed: M19 finite-arity asymptotic sharpness.")
