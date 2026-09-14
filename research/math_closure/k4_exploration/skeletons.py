"""Tree skeletons and exact projected-error evaluation, float64 throughout.

A skeleton is the shape that remains after deleting leaves. For k=3 there are
two; for k=4 there are four. Leaf slots are filled with unit vectors, so a
skeleton plus an arity assignment determines the computation completely.

Everything here is deterministic and exact given the laws: the optimizer lives
in ``optimizer.py`` and the feasibility certification in ``certify_candidate.py``.
"""

from __future__ import annotations

from dataclasses import dataclass

import torch

LEAF = "leaf"


@dataclass(frozen=True)
class Node:
    """An internal vertex: an ordered list of children, each LEAF or a Node."""
    children: tuple

    @property
    def arity(self) -> int:
        return len(self.children)


def internal_count(node) -> int:
    if node is LEAF:
        return 0
    return 1 + sum(internal_count(c) for c in node.children)


def internal_nodes(node, acc=None) -> list:
    """Post-order list of internal vertices; index i is the i-th law."""
    if acc is None:
        acc = []
    if node is LEAF:
        return acc
    for c in node.children:
        internal_nodes(c, acc)
    acc.append(node)
    return acc


# --- k = 3 -----------------------------------------------------------------
_v1 = Node((LEAF, LEAF))
K3_CHAIN = Node((Node((_v1, LEAF)), LEAF))
K3_BRANCH = Node((Node((LEAF, LEAF)), Node((LEAF, LEAF))))

# --- k = 4 -----------------------------------------------------------------
# T41 chain:            v1 -> v2 -> v3 -> r
K4_CHAIN = Node((Node((Node((Node((LEAF, LEAF)), LEAF)), LEAF)), LEAF))
# T42 branch below:     v1, v2 -> v3 -> r
K4_BRANCH_BELOW = Node((Node((Node((LEAF, LEAF)), Node((LEAF, LEAF)))), LEAF))
# T43 chain + sibling:  (v1 -> v2) and v3 both feed r
K4_MIXED = Node((Node((Node((LEAF, LEAF)), LEAF)), Node((LEAF, LEAF))))
# T44 three-way star:   v1, v2, v3 -> r   (root is ternary)
K4_STAR = Node((Node((LEAF, LEAF)), Node((LEAF, LEAF)), Node((LEAF, LEAF))))

SKELETONS = {
    "k3_chain": K3_CHAIN,
    "k3_branch": K3_BRANCH,
    "k4_chain": K4_CHAIN,
    "k4_branch_below": K4_BRANCH_BELOW,
    "k4_mixed": K4_MIXED,
    "k4_star": K4_STAR,
}


def contract(tensor: torch.Tensor, inputs: list[torch.Tensor]) -> torch.Tensor:
    """out[a] = sum T[i1,...,im,a] x1[i1] ... xm[im]."""
    out = tensor
    for x in inputs:
        out = torch.tensordot(x, out, dims=([0], [0]))
    return out


def evaluate(node, laws: dict, projectors: dict, leaf: torch.Tensor):
    """Return (F, R) at ``node``: ambient and recursively projected values."""
    if node is LEAF:
        return leaf, leaf
    fs, rs = [], []
    for c in node.children:
        f, r = evaluate(c, laws, projectors, leaf)
        fs.append(f)
        rs.append(r)
    mu = laws[id(node)]
    F = contract(mu, fs)
    R = projectors[id(node)] @ contract(mu, rs)
    return F, R


def projected_root_error(node, laws: dict, projectors: dict, leaf: torch.Tensor) -> torch.Tensor:
    """E_T^P = || P_r F_r - R_r ||."""
    F, R = evaluate(node, laws, projectors, leaf)
    return torch.linalg.norm(projectors[id(node)] @ F - R)
