"""Asymptotic path sharpness for fixed independent-law multilinear DAGs."""

from __future__ import annotations

import cmath
import math
from dataclasses import dataclass

from seion_core.research_v4.dag_certificate import DAGNode, ScalarEdge, certify_dag_scalar


@dataclass(frozen=True, slots=True)
class DAGAsymptoticSharpness:
    root: str
    projected_nodes: tuple[str, ...]
    path_weights: dict[str, float]
    asymptotic_constant: float
    topological_order: tuple[str, ...]


def exact_dag_asymptotic_path_constant(
    nodes: dict[str, DAGNode],
    edges: tuple[ScalarEdge, ...],
    root: str,
    *,
    projected_nodes: tuple[str, ...] | None = None,
) -> DAGAsymptoticSharpness:
    """Return the exact first-order path count for a fixed finite DAG.

    ``nodes`` and ``edges`` include leaves and all internal dependencies.  A
    projected internal node contributes one local source; leaves contribute
    zero.  Parallel edges are retained, so repeated input slots have their
    correct multiplicity.  The returned constant is the exact coefficient of
    the universal ``eta`` upper bound for the independent-law asymptotic
    construction described in ``dag_asymptotic_sharpness.tex``.
    """

    selected = tuple(projected_nodes or (node_id for node_id in nodes if node_id != root))
    selected_set = set(selected)
    if root in selected_set:
        raise ValueError("the unprojected root cannot be a projected source")
    if not selected_set <= set(nodes):
        raise ValueError("projected_nodes contains an unknown node")
    source_nodes = {
        node_id: DAGNode(node_id, 1.0 if node_id in selected_set else 0.0)
        for node_id in nodes
    }
    certificate = certify_dag_scalar(source_nodes, edges, root, include_root_source=False)
    return DAGAsymptoticSharpness(
        root=root,
        projected_nodes=selected,
        path_weights={node_id: certificate.reverse_weights[node_id] for node_id in selected},
        asymptotic_constant=float(certificate.root_bound),
        topological_order=certificate.topological_order,
    )


def complex_product_witness_error(asymptotic_constant: int | float, eta: float) -> float:
    """Exact planar witness error for the path-count construction."""

    if asymptotic_constant < 0 or not float(asymptotic_constant).is_integer():
        raise ValueError("asymptotic_constant must be a nonnegative integer")
    if not 0.0 < eta <= 1.0:
        raise ValueError("eta must lie in (0, 1]")
    count = int(asymptotic_constant)
    theta = math.asin(eta)
    return abs(cmath.exp(1j * count * theta) - math.cos(theta) ** count)


def complex_product_witness_ratio(asymptotic_constant: int | float, eta: float) -> float:
    return complex_product_witness_error(asymptotic_constant, eta) / eta

