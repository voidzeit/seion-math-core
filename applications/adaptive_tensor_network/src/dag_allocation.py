"""Allocation entry points for the finite DAG tensor-network backend."""

from __future__ import annotations

from dag_network import DAGTensorNetwork


def global_certificate_optimal_dag_allocation(
    net: DAGTensorNetwork,
    budget: int,
    *,
    leaf_norm_bounds: list[float] | tuple[float, ...],
) -> dict[str, int]:
    """Delegate to the exact finite-DAG bounded-domain certificate DP."""

    return net.optimal_certificate_allocation(budget, leaf_norm_bounds=leaf_norm_bounds)


def rank_aware_certificate_optimal_dag_allocation(
    net: DAGTensorNetwork,
    budget: int,
    *,
    leaf_norm_bounds: list[float] | tuple[float, ...],
) -> dict[str, int]:
    """Small-DAG exhaustive oracle using rank-dependent value bounds."""

    return net.optimal_rank_aware_certificate_allocation(
        budget, leaf_norm_bounds=leaf_norm_bounds
    )
