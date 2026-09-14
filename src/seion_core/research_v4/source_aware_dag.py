"""First-order source-aware vector certificates on finite DAGs.

This module deliberately models only the linearized, source-resolved layer of
the projected-tree theory.  Higher-order multilinear interactions are a
separate research track (P6B) and are not silently folded into this result.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Mapping

import numpy as np


Array = np.ndarray


def _as_matrix(value: Array, *, name: str) -> Array:
    matrix = np.asarray(value)
    if matrix.ndim != 2:
        raise ValueError(f"{name} must be a two-dimensional matrix")
    if not np.issubdtype(matrix.dtype, np.number):
        raise TypeError(f"{name} must have a numeric dtype")
    return np.array(matrix, copy=True)


def _matrix_norm(value: Array) -> float:
    return float(np.linalg.norm(value, ord=2))


@dataclass(frozen=True, slots=True)
class VectorDAGEdge:
    """A linearized dependency operator from ``source`` to ``target``."""

    source: str
    target: str
    operator: Array

    def __post_init__(self) -> None:
        if not self.source or not self.target:
            raise ValueError("DAG edge endpoints must be nonempty")
        object.__setattr__(self, "operator", _as_matrix(self.operator, name="edge operator"))


@dataclass(frozen=True, slots=True)
class VectorDAGNode:
    """A DAG node and its first-order local source operators.

    A local source operator maps a source error vector ``epsilon_s`` directly
    into the node's ambient linearized error space.  Its shape is
    ``(dimension, len(epsilon_s))``.
    """

    node_id: str
    dimension: int
    local_sources: Mapping[str, Array] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not self.node_id:
            raise ValueError("DAG node ids must be nonempty")
        if self.dimension <= 0:
            raise ValueError("DAG node dimensions must be positive")
        normalized: dict[str, Array] = {}
        for source_id, operator in self.local_sources.items():
            if not source_id:
                raise ValueError("source ids must be nonempty")
            matrix = _as_matrix(operator, name=f"local operator {source_id!r}")
            if matrix.shape[0] != self.dimension:
                raise ValueError(
                    f"local operator {source_id!r} has output dimension {matrix.shape[0]}, "
                    f"expected {self.dimension}"
                )
            normalized[source_id] = matrix
        object.__setattr__(self, "local_sources", normalized)


@dataclass(frozen=True, slots=True)
class SourceAwareDAGCertificate:
    """Result of the P6A first-order source-aware propagation."""

    root: str
    topological_order: tuple[str, ...]
    coefficient_maps: Mapping[str, Mapping[str, Array]]
    forward_error: Array
    source_vectors: Mapping[str, Array]
    source_contributions: Mapping[str, float]
    source_aware_bound: float
    pathwise_triangle_bound: float
    include_root_sources: bool
    complexity: str = "O(|V|+|E|)"

    @property
    def no_worse_than_pathwise(self) -> bool:
        return self.source_aware_bound <= self.pathwise_triangle_bound + 1.0e-12 * max(
            1.0, abs(self.pathwise_triangle_bound)
        )


def _topological_order(nodes: Mapping[str, VectorDAGNode], edges: tuple[VectorDAGEdge, ...]) -> tuple[str, ...]:
    if not nodes:
        raise ValueError("DAG must contain at least one node")
    indegree = {node_id: 0 for node_id in nodes}
    outgoing: dict[str, list[VectorDAGEdge]] = {node_id: [] for node_id in nodes}
    for edge in edges:
        if edge.source not in nodes or edge.target not in nodes:
            raise ValueError("edge endpoint is not present in nodes")
        expected_shape = (nodes[edge.target].dimension, nodes[edge.source].dimension)
        if edge.operator.shape != expected_shape:
            raise ValueError(
                f"edge {edge.source!r}->{edge.target!r} has shape {edge.operator.shape}, "
                f"expected {expected_shape}"
            )
        indegree[edge.target] += 1
        outgoing[edge.source].append(edge)

    ready = sorted(node_id for node_id, degree in indegree.items() if degree == 0)
    order: list[str] = []
    while ready:
        node_id = ready.pop(0)
        order.append(node_id)
        for edge in sorted(outgoing[node_id], key=lambda item: (item.target, item.source)):
            indegree[edge.target] -= 1
            if indegree[edge.target] == 0:
                ready.append(edge.target)
                ready.sort()
    if len(order) != len(nodes):
        raise ValueError("dependency graph contains a cycle")
    return tuple(order)


def _add_operator(target: dict[str, Array], source_id: str, value: Array) -> None:
    if source_id in target:
        target[source_id] = target[source_id] + value
    else:
        target[source_id] = np.array(value, copy=True)


def certify_source_aware_dag(
    nodes: Mapping[str, VectorDAGNode],
    edges: tuple[VectorDAGEdge, ...],
    root: str,
    source_vectors: Mapping[str, Array],
    *,
    include_root_sources: bool = True,
) -> SourceAwareDAGCertificate:
    """Propagate source-labelled first-order coefficients through a DAG.

    For every source ``s`` and node ``v`` this computes an operator
    ``A[v, s]`` such that the first-order error is

    ``Delta_v^(1) = sum_s A[v, s] @ epsilon_s``.

    Operators from all paths carrying the same source label are added before
    taking a norm.  The returned pathwise comparison instead propagates
    operator norms and therefore applies triangle inequality at each path
    merge.  Consequently the source-aware bound is never larger than that
    pathwise triangle certificate.
    """

    if root not in nodes:
        raise ValueError(f"unknown root {root!r}")
    order = _topological_order(nodes, edges)
    normalized_vectors: dict[str, Array] = {}
    for source_id, vector in source_vectors.items():
        value = np.asarray(vector)
        if value.ndim != 1:
            raise ValueError(f"source vector {source_id!r} must be one-dimensional")
        if not np.issubdtype(value.dtype, np.number):
            raise TypeError(f"source vector {source_id!r} must have a numeric dtype")
        normalized_vectors[source_id] = np.array(value, copy=True)

    incoming: dict[str, list[VectorDAGEdge]] = {node_id: [] for node_id in nodes}
    for edge in edges:
        incoming[edge.target].append(edge)

    coefficient_maps: dict[str, dict[str, Array]] = {}
    path_coefficients: dict[str, dict[str, float]] = {}
    for node_id in order:
        node = nodes[node_id]
        coefficients: dict[str, Array] = {}
        path_coeffs: dict[str, float] = {}

        if include_root_sources or node_id != root:
            for source_id, operator in node.local_sources.items():
                if source_id not in normalized_vectors:
                    raise ValueError(f"missing vector for local source {source_id!r}")
                if operator.shape[1] != normalized_vectors[source_id].shape[0]:
                    raise ValueError(
                        f"local operator {source_id!r} expects vector dimension {operator.shape[1]}, "
                        f"got {normalized_vectors[source_id].shape[0]}"
                    )
                _add_operator(coefficients, source_id, operator)
                path_coeffs[source_id] = path_coeffs.get(source_id, 0.0) + _matrix_norm(operator)

        for edge in incoming[node_id]:
            for source_id, predecessor_operator in coefficient_maps[edge.source].items():
                _add_operator(coefficients, source_id, edge.operator @ predecessor_operator)
            for source_id, predecessor_bound in path_coefficients[edge.source].items():
                path_coeffs[source_id] = path_coeffs.get(source_id, 0.0) + _matrix_norm(edge.operator) * predecessor_bound

        coefficient_maps[node_id] = coefficients
        path_coefficients[node_id] = path_coeffs

    root_coefficients = coefficient_maps[root]
    forward_error = np.zeros(nodes[root].dimension, dtype=np.result_type(*normalized_vectors.values(), float))
    source_contributions: dict[str, float] = {}
    source_aware_bound = 0.0
    pathwise_triangle_bound = 0.0
    for source_id, operator in root_coefficients.items():
        vector = normalized_vectors[source_id]
        contribution = _matrix_norm(operator) * float(np.linalg.norm(vector))
        source_contributions[source_id] = contribution
        source_aware_bound += contribution
        pathwise_triangle_bound += path_coefficients[root].get(source_id, 0.0) * float(np.linalg.norm(vector))
        forward_error = forward_error + operator @ vector

    tolerance = 1.0e-10 * max(1.0, abs(pathwise_triangle_bound))
    if source_aware_bound > pathwise_triangle_bound + tolerance:
        raise AssertionError("source-aware bound exceeds its pathwise triangle certificate")

    return SourceAwareDAGCertificate(
        root=root,
        topological_order=order,
        coefficient_maps=coefficient_maps,
        forward_error=forward_error,
        source_vectors=normalized_vectors,
        source_contributions=source_contributions,
        source_aware_bound=source_aware_bound,
        pathwise_triangle_bound=pathwise_triangle_bound,
        include_root_sources=include_root_sources,
    )
