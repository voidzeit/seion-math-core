"""DAG-native scalar source-resolved error certificates."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Mapping


@dataclass(frozen=True, slots=True)
class ScalarEdge:
    """One dependency edge ``source -> target`` with nonnegative gain."""

    source: str
    target: str
    gain: float

    def __post_init__(self) -> None:
        if not self.source or not self.target:
            raise ValueError("DAG edge endpoints must be nonempty")
        if self.gain < 0.0:
            raise ValueError("DAG gains must be nonnegative")


@dataclass(frozen=True, slots=True)
class DAGNode:
    """A node-local source magnitude."""

    node_id: str
    local_source: float = 0.0

    def __post_init__(self) -> None:
        if not self.node_id:
            raise ValueError("DAG node ids must be nonempty")
        if self.local_source < 0.0:
            raise ValueError("local source magnitudes must be nonnegative")


@dataclass(frozen=True, slots=True)
class DAGCertificate:
    root: str
    topological_order: tuple[str, ...]
    forward_bounds: Mapping[str, float]
    reverse_weights: Mapping[str, float]
    source_contributions: Mapping[str, float]
    root_bound: float
    include_root_source: bool
    complexity: str = "O(|V|+|E|)"


def _validate_graph(nodes: Mapping[str, DAGNode], edges: tuple[ScalarEdge, ...], root: str) -> tuple[str, ...]:
    if not nodes:
        raise ValueError("DAG must contain at least one node")
    if root not in nodes:
        raise ValueError(f"unknown root {root!r}")
    indegree = {node_id: 0 for node_id in nodes}
    outgoing: dict[str, list[ScalarEdge]] = {node_id: [] for node_id in nodes}
    for edge in edges:
        if edge.source not in nodes or edge.target not in nodes:
            raise ValueError("edge endpoint is not present in nodes")
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


def certify_dag_scalar(
    nodes: Mapping[str, DAGNode],
    edges: tuple[ScalarEdge, ...],
    root: str,
    *,
    include_root_source: bool = True,
) -> DAGCertificate:
    """Compute a source-resolved scalar certificate in linear graph time."""

    order = _validate_graph(nodes, edges, root)
    incoming: dict[str, list[ScalarEdge]] = {node_id: [] for node_id in nodes}
    outgoing: dict[str, list[ScalarEdge]] = {node_id: [] for node_id in nodes}
    for edge in edges:
        incoming[edge.target].append(edge)
        outgoing[edge.source].append(edge)

    forward: dict[str, float] = {}
    for node_id in order:
        local = nodes[node_id].local_source
        if node_id == root and not include_root_source:
            local = 0.0
        forward[node_id] = local + sum(edge.gain * forward[edge.source] for edge in incoming[node_id])

    weights = {node_id: 0.0 for node_id in nodes}
    weights[root] = 1.0
    for node_id in reversed(order):
        for edge in outgoing[node_id]:
            weights[node_id] += edge.gain * weights[edge.target]

    contributions = {
        node_id: nodes[node_id].local_source * weights[node_id]
        for node_id in nodes
        if include_root_source or node_id != root
    }
    root_bound = forward[root]
    if abs(root_bound - sum(contributions.values())) > 1.0e-12 * max(1.0, abs(root_bound)):
        raise AssertionError("forward and source-resolved DAG certificates disagree")
    return DAGCertificate(root, order, forward, weights, contributions, root_bound, include_root_source)
