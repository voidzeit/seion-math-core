"""Typed ordered composition-tree data model and canonical statistics."""

from __future__ import annotations

from collections import Counter
from dataclasses import dataclass
import hashlib
import json
import math
from typing import Iterator, Mapping, TypeAlias

from .types import TypeSystem


@dataclass(frozen=True, slots=True)
class Leaf:
    label: int
    type_name: str

    def __post_init__(self) -> None:
        if self.label < 0:
            raise ValueError("leaf labels must be nonnegative")
        if not self.type_name:
            raise ValueError("a leaf type must be nonempty")


@dataclass(frozen=True, slots=True)
class Node:
    law_id: str
    output_type: str
    children: tuple["Tree", ...]

    def __post_init__(self) -> None:
        if not self.law_id:
            raise ValueError("an internal node requires a law id")
        if not self.output_type:
            raise ValueError("an internal node requires an output type")
        if len(self.children) < 2:
            raise ValueError("internal-node arity must be at least two")

    @property
    def arity(self) -> int:
        return len(self.children)


Tree: TypeAlias = Leaf | Node


def iter_nodes(tree: Tree) -> Iterator[Tree]:
    yield tree
    if isinstance(tree, Node):
        for child in tree.children:
            yield from iter_nodes(child)


def iter_internal(tree: Tree) -> Iterator[Node]:
    if isinstance(tree, Node):
        yield tree
        for child in tree.children:
            yield from iter_internal(child)


def iter_leaves(tree: Tree) -> Iterator[Leaf]:
    if isinstance(tree, Leaf):
        yield tree
    else:
        for child in tree.children:
            yield from iter_leaves(child)


def tree_to_dict(tree: Tree) -> dict[str, object]:
    if isinstance(tree, Leaf):
        return {"kind": "leaf", "label": tree.label, "type": tree.type_name}
    return {
        "kind": "node",
        "law_id": tree.law_id,
        "output_type": tree.output_type,
        "children": [tree_to_dict(child) for child in tree.children],
    }


def canonical_json(tree: Tree) -> str:
    return json.dumps(tree_to_dict(tree), sort_keys=True, separators=(",", ":"))


def tree_hash(tree: Tree) -> str:
    return hashlib.sha256(canonical_json(tree).encode("utf-8")).hexdigest()


def shape_signature(tree: Tree, *, ordered: bool = True) -> str:
    if isinstance(tree, Leaf):
        return "L"
    children = [shape_signature(child, ordered=ordered) for child in tree.children]
    if not ordered:
        children.sort()
    return f"N{tree.arity}[{','.join(children)}]"


def validate_tree(tree: Tree, types: TypeSystem, laws: Mapping[str, object]) -> None:
    """Reject unknown colors, type-invalid edges, and law/arity mismatches.

    Law objects are structurally required to expose ``input_types``,
    ``output_type``, and ``arity``.  Avoiding a concrete import keeps this
    module free of a circular dependency on ``local_constants``.
    """

    if isinstance(tree, Leaf):
        if tree.type_name not in types:
            raise ValueError(f"unknown leaf type {tree.type_name!r}")
        return
    if tree.output_type not in types:
        raise ValueError(f"unknown output type {tree.output_type!r}")
    if tree.law_id not in laws:
        raise ValueError(f"unknown law {tree.law_id!r}")
    law = laws[tree.law_id]
    input_types = tuple(getattr(law, "input_types"))
    output_type = str(getattr(law, "output_type"))
    arity = int(getattr(law, "arity"))
    if arity != tree.arity:
        raise ValueError(f"law {tree.law_id!r} has arity {arity}, tree uses {tree.arity}")
    if output_type != tree.output_type:
        raise ValueError(
            f"law {tree.law_id!r} outputs {output_type!r}, node declares {tree.output_type!r}"
        )
    for slot, (child, expected) in enumerate(zip(tree.children, input_types)):
        validate_tree(child, types, laws)
        actual = child.type_name if isinstance(child, Leaf) else child.output_type
        if actual != expected:
            raise ValueError(
                f"type-invalid edge at slot {slot}: expected {expected!r}, got {actual!r}"
            )


def _leaf_depths(tree: Tree, depth: int = 0) -> list[int]:
    if isinstance(tree, Leaf):
        return [depth]
    result: list[int] = []
    for child in tree.children:
        result.extend(_leaf_depths(child, depth + 1))
    return result


def _strahler(tree: Tree) -> int:
    if isinstance(tree, Leaf):
        return 1
    values = [_strahler(child) for child in tree.children]
    maximum = max(values)
    return maximum + 1 if values.count(maximum) >= 2 else maximum


def _automorphisms(tree: Tree) -> int:
    if isinstance(tree, Leaf):
        return 1
    signatures = [shape_signature(child, ordered=False) for child in tree.children]
    multiplicity = math.prod(math.factorial(value) for value in Counter(signatures).values())
    return multiplicity * math.prod(_automorphisms(child) for child in tree.children)


def tree_statistics(tree: Tree) -> dict[str, object]:
    """Return the complete topology record required by the v3 atlas."""

    nodes = list(iter_nodes(tree))
    internal = [item for item in nodes if isinstance(item, Node)]
    leaves = [item for item in nodes if isinstance(item, Leaf)]
    depths = _leaf_depths(tree)
    subtree_signatures = [shape_signature(item) for item in nodes]
    unique_subtrees = len(set(subtree_signatures))
    repeated = sum(count - 1 for count in Counter(subtree_signatures).values() if count > 1)
    arities = Counter(node.arity for node in internal)
    types = Counter(
        [leaf.type_name for leaf in leaves] + [node.output_type for node in internal]
    )
    return {
        "tree_hash": tree_hash(tree),
        "ordered_shape_id": shape_signature(tree, ordered=True),
        "unordered_shape_id": shape_signature(tree, ordered=False),
        "node_count": len(internal),
        "total_vertex_count": len(nodes),
        "leaf_count": len(leaves),
        "arity_profile": dict(sorted(arities.items())),
        "depth": max(depths, default=0),
        "minimum_leaf_depth": min(depths, default=0),
        "maximum_leaf_depth": max(depths, default=0),
        "average_leaf_depth": sum(depths) / len(depths) if depths else 0.0,
        "imbalance": (max(depths) - min(depths)) if depths else 0,
        "strahler_number": _strahler(tree),
        "path_length_sum": sum(depths),
        "automorphism_count": _automorphisms(tree),
        "type_signature": dict(sorted(types.items())),
        "repeated_subtree_count": repeated,
        "expression_dag_compression_ratio": len(nodes) / unique_subtrees,
    }
