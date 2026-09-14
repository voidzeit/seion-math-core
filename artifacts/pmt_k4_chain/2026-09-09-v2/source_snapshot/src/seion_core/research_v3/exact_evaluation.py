"""Explicit-coordinate ambient evaluation of typed composition trees."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Mapping, Sequence

import numpy as np

from .local_constants import TypedLaw, validate_law_family
from .typed_tree import Leaf, Node, Tree, validate_tree
from .types import TypeSystem


Path = tuple[int, ...]


@dataclass(frozen=True, slots=True)
class EvaluationTrace:
    root: np.ndarray
    values: Mapping[Path, np.ndarray]


def _leaf_value(
    leaf: Leaf, reduced_inputs: Mapping[int, np.ndarray] | Sequence[np.ndarray], types: TypeSystem
) -> np.ndarray:
    try:
        reduced = reduced_inputs[leaf.label]
    except (KeyError, IndexError) as exc:
        raise ValueError(f"missing reduced input for leaf {leaf.label}") from exc
    return types[leaf.type_name].lift(np.asarray(reduced))


def evaluate_ambient_reference(
    tree: Tree,
    laws: Mapping[str, TypedLaw],
    types: TypeSystem,
    reduced_inputs: Mapping[int, np.ndarray] | Sequence[np.ndarray],
) -> EvaluationTrace:
    """Evaluate ``F_T`` with explicit coordinate loops at every node."""

    validate_law_family(laws, types)
    validate_tree(tree, types, laws)
    values: dict[Path, np.ndarray] = {}

    def visit(item: Tree, path: Path) -> np.ndarray:
        if isinstance(item, Leaf):
            value = _leaf_value(item, reduced_inputs, types)
        else:
            children = [visit(child, (*path, slot)) for slot, child in enumerate(item.children)]
            value = laws[item.law_id].apply_reference(children)
        values[path] = np.asarray(value)
        return values[path]

    root = visit(tree, ())
    return EvaluationTrace(root=root, values=values)


def evaluate_ambient_numpy(
    tree: Tree,
    laws: Mapping[str, TypedLaw],
    types: TypeSystem,
    reduced_inputs: Mapping[int, np.ndarray] | Sequence[np.ndarray],
) -> EvaluationTrace:
    """Evaluate ``F_T`` through independent NumPy contractions."""

    validate_law_family(laws, types)
    validate_tree(tree, types, laws)
    values: dict[Path, np.ndarray] = {}

    def visit(item: Tree, path: Path) -> np.ndarray:
        if isinstance(item, Leaf):
            value = _leaf_value(item, reduced_inputs, types)
        else:
            children = [visit(child, (*path, slot)) for slot, child in enumerate(item.children)]
            value = laws[item.law_id].apply(children)
        values[path] = np.asarray(value)
        return values[path]

    root = visit(tree, ())
    return EvaluationTrace(root=root, values=values)
