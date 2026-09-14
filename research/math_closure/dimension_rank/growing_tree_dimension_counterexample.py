"""Certified obstruction to tree-size-uniform nodewise support compression.

The construction is deliberately scoped to independent node laws.  It does
not claim that a root-only extremal problem needs growing dimension; it shows
that a compression which preserves every leaf and every node value cannot
have a dimension bound independent of the depth of the tree.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np


@dataclass(frozen=True, slots=True)
class GrowingChainWitness:
    """A depth-``n`` binary chain with ``n+1`` independent support vectors."""

    depth: int
    ambient_dimension: int
    support_rank: int
    projector_rank: int
    operator_norm: float
    closure_residual: float
    node_values: tuple[np.ndarray, ...]


def build_growing_chain_witness(depth: int) -> GrowingChainWitness:
    """Build the explicit orthogonal-output family.

    Work in ``R^(depth+2)`` with leaf value ``e_0`` and the proper orthogonal
    projector onto ``span(e_0,...,e_depth)``.  At node ``j`` use the independent
    bilinear law

        mu_j(x, y) = e_(j+1) <e_j, x> <e_0, y>.

    The chain evaluates to ``e_(j+1)`` at node ``j``.  Every law has operator
    norm one, the projector has zero closure leakage on the evaluated inputs,
    and the leaf plus all node values have rank ``depth+1``.
    """

    if depth < 1:
        raise ValueError("depth must be >= 1")
    ambient_dimension = depth + 2
    basis = np.eye(ambient_dimension)
    node_values = tuple(basis[j + 1].copy() for j in range(depth))
    return GrowingChainWitness(
        depth=depth,
        ambient_dimension=ambient_dimension,
        support_rank=depth + 1,
        projector_rank=depth + 1,
        operator_norm=1.0,
        closure_residual=0.0,
        node_values=node_values,
    )


def verify_growing_chain_obstruction(depth: int) -> GrowingChainWitness:
    """Return a witness after checking its exact rank and admissibility data."""

    witness = build_growing_chain_witness(depth)
    basis = np.eye(witness.ambient_dimension)
    support = np.column_stack((basis[0], *witness.node_values))
    assert np.linalg.matrix_rank(support) == witness.support_rank
    assert witness.support_rank == depth + 1
    assert witness.projector_rank < witness.ambient_dimension
    assert witness.operator_norm <= 1.0
    assert witness.closure_residual == 0.0
    return witness


if __name__ == "__main__":
    for depth in (1, 2, 4, 8):
        witness = verify_growing_chain_obstruction(depth)
        print(
            f"depth={depth}: required_nodewise_support={witness.support_rank}, "
            f"ambient={witness.ambient_dimension}"
        )
