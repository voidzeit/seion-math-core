"""M20 evaluator: exact k=3 constants for arbitrary finite arity profiles."""

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


def rooted_shapes(internal_nodes: int = 3, max_arity: int = 4) -> list[Shape]:
    """Enumerate the finite k=3 arity atlas used by the deterministic gate."""

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


def internal_child_slots(shape: Shape) -> tuple[int, ...]:
    if shape is None:
        return ()
    return tuple(index for index, child in enumerate(shape) if child is not None)


def topology_kind(shape: Shape) -> str:
    """Return the internal-child skeleton for a three-node tree."""

    if internal_nodes(shape) != 3 or shape is None:
        raise ValueError("topology_kind requires a tree with exactly three nodes")
    slots = internal_child_slots(shape)
    if len(slots) == 2:
        if all(internal_nodes(shape[index]) == 1 for index in slots):
            return "branch"
    if len(slots) == 1:
        child = shape[slots[0]]
        if (
            child is not None
            and internal_nodes(child) == 2
            and len(internal_child_slots(child)) == 1
            and internal_nodes(child[internal_child_slots(child)[0]]) == 1
        ):
            return "chain"
    raise AssertionError("unexpected k=3 internal-child skeleton")


def _node_tensor(arity: int, internal_slots: tuple[int, ...], base: np.ndarray) -> np.ndarray:
    """Insert a linear/bilinear effective tensor behind unit e0 leaf gates."""

    base = np.asarray(base, dtype=float)
    tensor = np.zeros((2,) + (2,) * arity, dtype=float)
    if len(internal_slots) == 0:
        tensor[(slice(None),) + (0,) * arity] = base
        return tensor
    if len(internal_slots) == 1:
        if base.shape != (2, 2):
            raise ValueError("one internal slot requires a 2x2 effective matrix")
        slot = internal_slots[0]
        for out_index in range(2):
            for in_index in range(2):
                indices = [0] * arity
                indices[slot] = in_index
                tensor[(out_index, *indices)] = base[out_index, in_index]
        return tensor
    if len(internal_slots) == 2:
        if base.shape != (2, 2, 2):
            raise ValueError("two internal slots require a 2x2x2 effective tensor")
        first, second = internal_slots
        for out_index, first_index, second_index in product(range(2), repeat=3):
            indices = [0] * arity
            indices[first] = first_index
            indices[second] = second_index
            tensor[(out_index, *indices)] = base[out_index, first_index, second_index]
        return tensor
    raise AssertionError("k=3 has at most two internal children")


def _m14_bases(eta: float) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    t = min(eta, math.sqrt(2.0 / 3.0))
    p = math.sqrt(1.0 - t * t)
    c = p
    f = np.array([p, t])
    n = np.array([[-c, t], [t, c]])
    x = n @ np.array([0.0, 1.0])
    v = t * x + p * t * np.array([0.0, 1.0])
    a = np.zeros((2, 2), dtype=float)
    a[0, :] = v / np.linalg.norm(v)
    return f, n, a


def _m15_bases(eta: float) -> tuple[np.ndarray, np.ndarray]:
    t = min(eta, math.sqrt(2.0 / 3.0))
    p = math.sqrt(1.0 - t * t)
    f = np.array([p, t])
    d = np.array([0.0, 1.0])
    k = t * np.outer(d, f) + p * t * np.outer(np.array([1.0, 0.0]), d)
    u, _, vt = np.linalg.svd(k)
    a = u @ vt
    base = np.zeros((2, 2, 2), dtype=float)
    base[0, :, :] = a
    return f, base


def _to_tree(
    shape: Shape,
    labels: list[int],
    family: str,
    eta: float,
    path: tuple[int, ...] = (),
) -> tuple[Leaf | Node, dict[str, TypedLaw]]:
    laws: dict[str, TypedLaw] = {}

    def visit(current: Shape, current_path: tuple[int, ...], depth: int) -> Leaf | Node:
        if current is None:
            leaf = Leaf(labels[0], "tau")
            labels[0] += 1
            return leaf
        arity = len(current)
        law_id = "v" + ("_".join(map(str, current_path)) or "root")
        slots = internal_child_slots(current)
        if family == "chain":
            f, n, a = _m14_bases(eta)
            base = f if len(slots) == 0 else n if depth == 1 else a
        else:
            f, root_base = _m15_bases(eta)
            base = f if len(slots) == 0 else root_base
        tensor = _node_tensor(arity, slots, base)
        laws[law_id] = TypedLaw(law_id, ("tau",) * arity, "tau", tensor)
        children = tuple(
            visit(child, (*current_path, index), depth + 1)
            for index, child in enumerate(current)
        )
        return Node(law_id, "tau", children)

    return visit(shape, path, 0), laws


def evaluate_witness(shape: Shape, eta: float) -> float:
    if not 0.0 < eta <= 1.0:
        raise ValueError("eta must lie in (0,1]")
    family = topology_kind(shape)
    tree, laws = _to_tree(shape, [0], family, eta)
    types = TypeSystem([TypedSpace.coordinate("tau", 2, 1, field="real")])
    leaves = {label: np.array([1.0]) for label in range(leaf_count(shape))}
    ambient = evaluate_ambient_numpy(tree, laws, types, leaves).root
    projected = evaluate_projected_numpy(tree, laws, types, leaves).root
    return float(np.linalg.norm(types["tau"].project(ambient) - projected))


def W3(eta: float) -> float:
    if eta <= math.sqrt(2.0 / 3.0):
        return math.sqrt(4.0 - 3.0 * eta * eta)
    return 2.0 / (math.sqrt(3.0) * eta)


def verify_all_finite_arity_k3(max_arity: int = 4) -> bool:
    for shape in rooted_shapes(3, max_arity):
        for eta in (1.0e-4, 0.2, 0.7, 1.0):
            observed = evaluate_witness(shape, eta)
            if not math.isclose(observed / eta, W3(eta), rel_tol=0.0, abs_tol=2.0e-10):
                return False
    return True


if __name__ == "__main__":
    assert verify_all_finite_arity_k3()
    print("All checks passed: M20 exact k=3 arbitrary-arity witnesses.")
