"""Tree topology for the adaptive hierarchical tensor network (mission AI1).

Purpose-built for this application (arbitrary arity, per-node ambient
dimension and reduced rank) rather than reusing
src/seion_core/research_v3/typed_tree.py, which is specialized to the
finite-core math theory's fixed-type, homogeneous-arity trees.
"""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(frozen=True)
class NodeSpec:
    """One internal vertex: its children (leaves are ints = leaf index,
    internal nodes are NodeSpec, recursively), ambient output dimension,
    and current reduced rank (mutable via rank allocation, tracked
    separately in RankAllocation - this dataclass only fixes topology and
    ambient dimension, which do not change across rank-allocation trials).
    """

    node_id: str
    children: tuple["NodeSpec | int", ...]
    ambient_dim: int

    @property
    def arity(self) -> int:
        return len(self.children)


@dataclass(frozen=True)
class TreeTopology:
    """A fixed tree: root NodeSpec, leaf dimensions, and a flat list of
    all internal nodes in a canonical post-order (children before
    parents) for iteration.
    """

    root: NodeSpec
    leaf_dims: tuple[int, ...]
    nodes_postorder: tuple[NodeSpec, ...] = field(default_factory=tuple)

    def __post_init__(self) -> None:
        if not self.nodes_postorder:
            object.__setattr__(self, "nodes_postorder", tuple(_postorder(self.root)))

    @property
    def internal_node_count(self) -> int:
        return len(self.nodes_postorder)

    def path_to_root(self, node_id: str) -> list[str]:
        """Return the list of node ids from `node_id` up to (and
        including) the root, in child-to-root order."""

        parent_of = {}
        for node in self.nodes_postorder:
            for child in node.children:
                if isinstance(child, NodeSpec):
                    parent_of[child.node_id] = node.node_id
        path = [node_id]
        current = node_id
        while current in parent_of:
            current = parent_of[current]
            path.append(current)
        return path


def _postorder(node: NodeSpec):
    for child in node.children:
        if isinstance(child, NodeSpec):
            yield from _postorder(child)
    yield node


def chain_topology(depth: int, leaf_dim: int = 4, ambient_dim: int = 4) -> TreeTopology:
    """A chain: node_0 = f(leaf_0, leaf_1), node_1 = f(node_0, leaf_2), ...
    `depth` internal nodes, `depth+1` leaves."""

    if depth < 1:
        raise ValueError("depth must be >= 1")
    current: NodeSpec | int = 0
    node = None
    for i in range(depth):
        left = current if i > 0 else 0
        right = i + 1
        node = NodeSpec(node_id=f"n{i}", children=(left, right), ambient_dim=ambient_dim)
        current = node
    leaf_dims = tuple(leaf_dim for _ in range(depth + 1))
    return TreeTopology(root=node, leaf_dims=leaf_dims)


def balanced_binary_topology(n_leaves: int, leaf_dim: int = 4, ambient_dim: int = 4) -> TreeTopology:
    """A balanced binary tree over `n_leaves` leaves (n_leaves must be a
    power of 2)."""

    if n_leaves < 2 or (n_leaves & (n_leaves - 1)) != 0:
        raise ValueError("n_leaves must be a power of 2, >= 2")

    counter = [0]

    def build(leaf_range: tuple[int, int]) -> "NodeSpec | int":
        lo, hi = leaf_range
        if hi - lo == 1:
            return lo
        mid = (lo + hi) // 2
        left = build((lo, mid))
        right = build((mid, hi))
        node_id = f"n{counter[0]}"
        counter[0] += 1
        return NodeSpec(node_id=node_id, children=(left, right), ambient_dim=ambient_dim)

    root = build((0, n_leaves))
    leaf_dims = tuple(leaf_dim for _ in range(n_leaves))
    return TreeTopology(root=root, leaf_dims=leaf_dims)


def unbalanced_topology(n_leaves: int, leaf_dim: int = 4, ambient_dim: int = 4) -> TreeTopology:
    """A maximally unbalanced (left-comb) tree: node_0=f(leaf0,leaf1),
    node_1=f(node_0,leaf2), ... identical shape to chain_topology but
    named separately for clarity in experiment configs."""

    return chain_topology(n_leaves - 1, leaf_dim=leaf_dim, ambient_dim=ambient_dim)
