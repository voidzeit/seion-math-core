"""Finite topology metrics and non-sharp topology-aware bound records."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Mapping


@dataclass(frozen=True, slots=True)
class TopologyMetrics:
    node_count: int
    edge_count: int
    root: str
    source_count: int
    depth: int
    max_fan_in: int
    max_fan_out: int
    path_count_to_root: int
    signature: str


def compute_topology_metrics(nodes: Mapping[str, tuple[str, ...]], root: str) -> TopologyMetrics:
    if not nodes or root not in nodes:
        raise ValueError("topology must contain the root and at least one node")
    children = {node_id: tuple(inputs) for node_id, inputs in nodes.items()}
    for node_id, inputs in children.items():
        for input_id in inputs:
            if input_id not in children:
                raise ValueError(f"unknown topology input {input_id!r}")

    visiting: set[str] = set()
    memo_depth: dict[str, int] = {}
    memo_paths: dict[str, int] = {}

    def visit(node_id: str) -> tuple[int, int]:
        if node_id in visiting:
            raise ValueError("topology contains a cycle")
        if node_id in memo_depth:
            return memo_depth[node_id], memo_paths[node_id]
        visiting.add(node_id)
        if not children[node_id]:
            result = (0, 1)
        else:
            child_results = [visit(input_id) for input_id in children[node_id]]
            result = (1 + max(depth for depth, _ in child_results), sum(paths for _, paths in child_results))
        visiting.remove(node_id)
        memo_depth[node_id], memo_paths[node_id] = result
        return result

    depth, paths = visit(root)
    fan_in = max(len(inputs) for inputs in children.values())
    outgoing = {node_id: 0 for node_id in children}
    for inputs in children.values():
        for input_id in inputs:
            outgoing[input_id] += 1
    signature = ";".join(f"{node_id}:{','.join(children[node_id])}" for node_id in sorted(children))
    return TopologyMetrics(
        node_count=len(children),
        edge_count=sum(len(inputs) for inputs in children.values()),
        root=root,
        source_count=sum(1 for inputs in children.values() if not inputs),
        depth=depth,
        max_fan_in=fan_in,
        max_fan_out=max(outgoing.values(), default=0),
        path_count_to_root=paths,
        signature=signature,
    )


def universal_topology_bound(
    *,
    internal_nodes: int,
    closure_residual: float,
    operator_norm: float,
    leaf_product: float = 1.0,
    projected_root: bool = True,
) -> float:
    if min(internal_nodes, closure_residual, operator_norm, leaf_product) < 0.0:
        raise ValueError("bound parameters must be nonnegative")
    coefficient = max(0, internal_nodes - 1) if projected_root else internal_nodes
    return float(coefficient * closure_residual * operator_norm ** max(0, internal_nodes - 1) * leaf_product)
