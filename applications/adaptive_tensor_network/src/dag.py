"""Finite DAG topologies for the adaptive tensor-network backend."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Mapping


InputRef = int | str


@dataclass(frozen=True, slots=True)
class DAGNodeSpec:
    """One internal DAG vertex; integer references are leaves."""

    node_id: str
    inputs: tuple[InputRef, ...]
    ambient_dim: int

    @property
    def arity(self) -> int:
        return len(self.inputs)


@dataclass(frozen=True, slots=True)
class DAGTopology:
    """A finite acyclic multilinear DAG with one designated root."""

    nodes: Mapping[str, DAGNodeSpec]
    root_id: str
    leaf_dims: tuple[int, ...]
    topological_order: tuple[str, ...] = field(default_factory=tuple)

    def __post_init__(self) -> None:
        if not self.nodes:
            raise ValueError("DAG topology must contain at least one internal node")
        if self.root_id not in self.nodes:
            raise ValueError(f"unknown root {self.root_id!r}")
        if any(dim <= 0 for dim in self.leaf_dims):
            raise ValueError("leaf dimensions must be positive")
        if set(self.nodes) != {node.node_id for node in self.nodes.values()}:
            raise ValueError("DAG mapping keys must match node_id fields")
        indegree = {node_id: 0 for node_id in self.nodes}
        outgoing: dict[str, list[str]] = {node_id: [] for node_id in self.nodes}
        for node in self.nodes.values():
            if node.ambient_dim <= 0 or not node.inputs:
                raise ValueError("internal nodes need positive dimension and at least one input")
            for ref in node.inputs:
                if isinstance(ref, bool):
                    raise ValueError("leaf references must be integer indices, not booleans")
                if isinstance(ref, int):
                    if ref < 0 or ref >= len(self.leaf_dims):
                        raise ValueError(f"leaf index {ref} is out of range")
                elif isinstance(ref, str):
                    if ref not in self.nodes:
                        raise ValueError(f"unknown input node {ref!r}")
                    indegree[node.node_id] += 1
                    outgoing[ref].append(node.node_id)
                else:
                    raise TypeError("DAG inputs must be integer leaf indices or node ids")
        ready = sorted(node_id for node_id, degree in indegree.items() if degree == 0)
        order: list[str] = []
        while ready:
            node_id = ready.pop(0)
            order.append(node_id)
            for target in sorted(outgoing[node_id]):
                indegree[target] -= 1
                if indegree[target] == 0:
                    ready.append(target)
                    ready.sort()
        if len(order) != len(self.nodes):
            raise ValueError("DAG topology contains a cycle")

        ancestors: set[str] = set()
        frontier = [self.root_id]
        while frontier:
            node_id = frontier.pop()
            if node_id in ancestors:
                continue
            ancestors.add(node_id)
            frontier.extend(ref for ref in self.nodes[node_id].inputs if isinstance(ref, str))
        if ancestors != set(self.nodes):
            raise ValueError("every internal DAG node must feed the designated root")
        object.__setattr__(self, "topological_order", tuple(order))

    @property
    def internal_node_count(self) -> int:
        return len(self.topological_order)

    @property
    def root(self) -> DAGNodeSpec:
        return self.nodes[self.root_id]


def shared_diamond_topology(leaf_dim: int = 4, ambient_dim: int = 4) -> DAGTopology:
    """Return a four-node DAG with one shared intermediate subexpression.

    ``u`` is evaluated once and feeds both ``left`` and ``right``; leaf zero
    is also reused across the two branches.  The root is unprojected.
    """

    nodes = {
        "u": DAGNodeSpec("u", (0, 1), ambient_dim),
        "left": DAGNodeSpec("left", ("u", 2), ambient_dim),
        "right": DAGNodeSpec("right", (0, "u"), ambient_dim),
        "root": DAGNodeSpec("root", ("left", "right"), ambient_dim),
    }
    return DAGTopology(nodes=nodes, root_id="root", leaf_dims=(leaf_dim, leaf_dim, leaf_dim))

