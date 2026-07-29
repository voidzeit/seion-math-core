"""Slow, explicit reference implementation for the v2 theorem objects.

The reference evaluator uses coordinate loops rather than the production
``NaryLaw`` contraction path.  It is intentionally unsuitable for large
instances; its purpose is to make implementation parity falsifiable.
"""

from __future__ import annotations

from dataclasses import dataclass
from itertools import product
from typing import Sequence

import numpy as np


@dataclass(frozen=True)
class Tree:
    """A full ordered n-ary tree.

    Leaves are represented by nonnegative integer labels.  An internal node
    has exactly ``arity`` ordered children.  Repeated leaf labels are allowed
    and are useful for polynomial identities.
    """

    arity: int
    children: tuple["Tree | int", ...] | None = None
    leaf: int | None = None

    def __post_init__(self) -> None:
        if self.leaf is not None:
            if self.leaf < 0 or self.children is not None:
                raise ValueError("a leaf has only a nonnegative label")
            return
        if self.arity < 2:
            raise ValueError("arity must satisfy n >= 2")
        if self.children is None or len(self.children) != self.arity:
            raise ValueError("an internal tree must have exactly arity children")

    @classmethod
    def make_leaf(cls, label: int, arity: int = 2) -> "Tree":
        return cls(arity=arity, leaf=label)

    @classmethod
    def node(cls, *children: "Tree | int", arity: int | None = None) -> "Tree":
        if arity is None:
            arity = len(children)
        normalized = tuple(
            child if isinstance(child, Tree) else cls.make_leaf(int(child), arity=arity)
            for child in children
        )
        return cls(arity=arity, children=normalized)

    @property
    def is_leaf(self) -> bool:
        return self.leaf is not None

    @property
    def internal_nodes(self) -> int:
        return tree_internal_nodes(self)

    @property
    def height(self) -> int:
        return tree_height(self)


def _as_vectors(vectors: Sequence[np.ndarray], dims: Sequence[int]) -> tuple[np.ndarray, ...]:
    values = tuple(np.asarray(value) for value in vectors)
    if len(values) != len(dims):
        raise ValueError(f"expected {len(dims)} vectors, got {len(values)}")
    for index, (value, dim) in enumerate(zip(values, dims)):
        if value.ndim != 1 or value.shape[0] != dim:
            raise ValueError(f"vector {index} must have shape ({dim},), got {value.shape}")
    return values


def apply_tensor_reference(tensor: np.ndarray, vectors: Sequence[np.ndarray]) -> np.ndarray:
    """Evaluate an n-linear tensor with explicit coordinate summation."""

    tensor = np.asarray(tensor)
    if tensor.ndim < 3:
        raise ValueError("a law tensor must have an output axis and at least two input axes")
    arity = tensor.ndim - 1
    values = _as_vectors(vectors, tensor.shape[1:])
    dtype = np.result_type(tensor, *values)
    output = np.zeros(tensor.shape[0], dtype=dtype)
    for output_index in range(tensor.shape[0]):
        for input_indices in product(*[range(dim) for dim in tensor.shape[1:]]):
            coefficient = tensor[(output_index, *input_indices)]
            if coefficient == 0:
                continue
            term = coefficient
            for vector, coordinate in zip(values, input_indices):
                term = term * vector[coordinate]
            output[output_index] += term
    return output


def compose_tensor_reference(outer: np.ndarray, inner: np.ndarray, slot: int) -> np.ndarray:
    """Coordinate definition of the operadic partial composition ``outer o_i inner``."""

    outer = np.asarray(outer)
    inner = np.asarray(inner)
    if outer.ndim < 3 or inner.ndim < 3:
        raise ValueError("both laws must have arity at least two")
    outer_arity = outer.ndim - 1
    inner_arity = inner.ndim - 1
    if not 0 <= slot < outer_arity:
        raise ValueError("slot outside outer arity")
    if outer.shape[1 + slot] != inner.shape[0]:
        raise ValueError("inner output dimension must match the inserted slot")
    shape = outer.shape[: 1 + slot] + inner.shape[1:] + outer.shape[2 + slot :]
    result = np.zeros(shape, dtype=np.result_type(outer, inner))
    for result_index in np.ndindex(shape):
        output_index = result_index[0]
        inner_indices = result_index[1 + slot : 1 + slot + inner_arity]
        outer_input_indices: list[int] = []
        cursor = 1
        for outer_slot in range(outer_arity):
            if outer_slot == slot:
                cursor += inner_arity
            else:
                outer_input_indices.append(result_index[cursor])
                cursor += 1
        value = 0
        for inserted_index in range(inner.shape[0]):
            value += outer[(output_index, *outer_input_indices[:slot], inserted_index, *outer_input_indices[slot:])] * inner[(inserted_index, *inner_indices)]
        result[result_index] = value
    return result


def evaluate_tree_reference(
    tensor: np.ndarray, tree: Tree, leaves: Sequence[np.ndarray]
) -> np.ndarray:
    """Evaluate a tree using the coordinate-loop law evaluator."""

    tensor = np.asarray(tensor)
    if tree.is_leaf:
        if tree.leaf is None or tree.leaf >= len(leaves):
            raise ValueError("tree references an unavailable leaf")
        return np.asarray(leaves[tree.leaf])
    if tree.children is None:
        raise ValueError("internal tree has no children")
    child_values = tuple(evaluate_tree_reference(tensor, child, leaves) for child in tree.children)
    return apply_tensor_reference(tensor, child_values)


def tree_internal_nodes(tree: Tree) -> int:
    if tree.is_leaf:
        return 0
    if tree.children is None:
        raise ValueError("internal tree has no children")
    return 1 + sum(tree_internal_nodes(child) for child in tree.children)


def tree_height(tree: Tree) -> int:
    if tree.is_leaf:
        return 0
    if tree.children is None:
        raise ValueError("internal tree has no children")
    return 1 + max(tree_height(child) for child in tree.children)


def tree_bound(
    tree: Tree,
    operator_norm: float,
    closure_residual: float,
    leaf_norms: Sequence[float] | None = None,
) -> float:
    """Return the proved homogeneous approximate-closure tree bound.

    For ``k`` internal nodes the bound is
    ``k * epsilon * M**(k-1) * product(leaf_norms)``.  ``M`` is the operator
    norm of the law and epsilon is the operator norm of ``(I-P) mu(P.,...)``.
    """

    k = tree_internal_nodes(tree)
    if leaf_norms is None:
        product_norm = 1.0
    else:
        product_norm = float(np.prod(np.asarray(leaf_norms, dtype=float)))
    if k == 0:
        return 0.0
    return float(k * closure_residual * (operator_norm ** (k - 1)) * product_norm)


def _contract_output(tensor: np.ndarray, q_star: np.ndarray) -> np.ndarray:
    return np.tensordot(q_star, tensor, axes=([1], [0]))


def project_tensor_inputs(tensor: np.ndarray, q: np.ndarray, output_projected: bool = False) -> np.ndarray:
    """Apply ``P=QQ*`` on every input mode and optionally on the output mode."""

    tensor = np.asarray(tensor)
    q = np.asarray(q)
    if q.ndim != 2 or q.shape[0] != tensor.shape[0]:
        raise ValueError("Q must have shape (ambient_dimension, reduced_rank)")
    p = q @ q.conj().T
    result = tensor
    for axis in range(1, tensor.ndim):
        result = np.tensordot(result, p, axes=([axis], [0]))
        result = np.moveaxis(result, -1, axis)
    if output_projected:
        result = np.tensordot(p, result, axes=([1], [0]))
    return result


def exact_reduction_tensor(tensor: np.ndarray, q: np.ndarray) -> np.ndarray:
    """Return ``Q* mu(Q.,...,Q.)`` for an internal law."""

    tensor = np.asarray(tensor)
    q = np.asarray(q)
    if q.ndim != 2 or q.shape[0] != tensor.shape[0]:
        raise ValueError("Q must have shape (ambient_dimension, reduced_rank)")
    result = _contract_output(tensor, q.conj().T)
    for axis in range(1, tensor.ndim):
        result = np.tensordot(result, q, axes=([axis], [0]))
        result = np.moveaxis(result, -1, axis)
    return result


def closure_residual_tensor(tensor: np.ndarray, q: np.ndarray) -> np.ndarray:
    """Return the ambient tensor ``(I-P) mu(P.,...,P.)``."""

    tensor = np.asarray(tensor)
    q = np.asarray(q)
    if q.ndim != 2 or q.shape[0] != tensor.shape[0]:
        raise ValueError("Q must have shape (ambient_dimension, reduced_rank)")
    p = q @ q.conj().T
    return project_tensor_inputs(tensor, q, output_projected=False) - np.tensordot(
        p, project_tensor_inputs(tensor, q, output_projected=False), axes=([1], [0])
    )
