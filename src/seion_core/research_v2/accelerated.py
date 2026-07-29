"""Vectorized counterparts to :mod:`seion_core.research_v2.reference`."""

from __future__ import annotations

import string
from typing import Sequence

import numpy as np

from .reference import Tree


def _labels(arity: int) -> tuple[str, str]:
    alphabet = string.ascii_letters
    if arity + 1 > len(alphabet):
        raise ValueError("arity too large for the vectorized evaluator")
    return alphabet[0], alphabet[1 : arity + 1]


def apply_tensor_einsum(tensor: np.ndarray, vectors: Sequence[np.ndarray]) -> np.ndarray:
    """Evaluate an n-linear tensor with a single Einstein contraction."""

    tensor = np.asarray(tensor)
    arity = tensor.ndim - 1
    if arity != len(vectors):
        raise ValueError(f"expected {arity} vectors, got {len(vectors)}")
    output_label, input_labels = _labels(arity)
    operands: list[np.ndarray] = [tensor, *[np.asarray(vector) for vector in vectors]]
    subscripts = [output_label + "".join(input_labels), *input_labels]
    return np.einsum(",".join(subscripts) + "->" + output_label, *operands)


def compose_tensor_tensordot(outer: np.ndarray, inner: np.ndarray, slot: int) -> np.ndarray:
    """Vectorized partial composition, with output axes in canonical order."""

    outer = np.asarray(outer)
    inner = np.asarray(inner)
    outer_arity = outer.ndim - 1
    inner_arity = inner.ndim - 1
    if not 0 <= slot < outer_arity:
        raise ValueError("slot outside outer arity")
    if outer.shape[1 + slot] != inner.shape[0]:
        raise ValueError("inner output dimension must match the inserted slot")
    result = np.tensordot(outer, inner, axes=([1 + slot], [0]))
    # tensordot yields [out, outer-inputs-except-slot, inner-inputs].  Move
    # the inserted block immediately after the output axis so that the
    # canonical order is [out, outer-before, inner-inputs, outer-after].
    start = 1 + (outer_arity - 1)
    result = np.moveaxis(
        result,
        list(range(start, start + inner_arity)),
        list(range(1 + slot, 1 + slot + inner_arity)),
    )
    expected = (outer.shape[0], *outer.shape[1 : 1 + slot], *inner.shape[1:], *outer.shape[2 + slot :])
    if result.shape != expected:
        raise RuntimeError(f"unexpected composition shape {result.shape}, expected {expected}")
    return result


def evaluate_tree_einsum(tensor: np.ndarray, tree: Tree, leaves: Sequence[np.ndarray]) -> np.ndarray:
    if tree.is_leaf:
        if tree.leaf is None or tree.leaf >= len(leaves):
            raise ValueError("tree references an unavailable leaf")
        return np.asarray(leaves[tree.leaf])
    if tree.children is None:
        raise ValueError("internal tree has no children")
    return apply_tensor_einsum(tensor, [evaluate_tree_einsum(tensor, child, leaves) for child in tree.children])
