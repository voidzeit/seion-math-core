"""Exact path constants for the nonnegative first-order DAG channel model.

The multilinear telescoping certificate produces nonnegative local sources and
nonnegative edge gains.  This module isolates that envelope as a mathematical
class in its own right: its optimal root coefficient is exactly the sum of
source bounds times all downstream path products.  It does not claim that the
full multilinear operator class always attains every channel simultaneously.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Mapping

from seion_core.research_v4.dag_certificate import (
    DAGNode,
    ScalarEdge,
    certify_dag_scalar,
)


@dataclass(frozen=True, slots=True)
class ExactDAGPathConstant:
    """Exact optimum for the declared nonnegative channel envelope."""

    root: str
    topological_order: tuple[str, ...]
    downstream_path_weights: Mapping[str, float]
    source_bounds: Mapping[str, float]
    source_contributions: Mapping[str, float]
    constant: float
    include_root_source: bool
    sharpness_scope: str = "exact for the declared nonnegative first-order channel class"


def exact_dag_path_constant(
    nodes: Mapping[str, DAGNode],
    edges: tuple[ScalarEdge, ...],
    root: str,
    *,
    include_root_source: bool = False,
) -> ExactDAGPathConstant:
    """Compute the exact worst-case root coefficient of a finite channel DAG.

    The declared class is

    ``d_v = s_v + sum_i g_(v,i) d_child_i``

    with ``0 <= s_v <= source_bounds[v]`` and nonnegative edge gains.  The
    supremum of ``d_root`` is attained by setting every source to its bound,
    and equals ``sum_v source_bounds[v] * downstream_path_weights[v]``.
    Parallel edges represent repeated multilinear input slots.
    """

    certificate = certify_dag_scalar(
        nodes,
        edges,
        root,
        include_root_source=include_root_source,
    )
    source_bounds = {
        node_id: float(node.local_source)
        for node_id, node in nodes.items()
        if include_root_source or node_id != root
    }
    return ExactDAGPathConstant(
        root=root,
        topological_order=certificate.topological_order,
        downstream_path_weights=certificate.reverse_weights,
        source_bounds=source_bounds,
        source_contributions=certificate.source_contributions,
        constant=float(certificate.root_bound),
        include_root_source=include_root_source,
    )


def channel_root_value(
    source_values: Mapping[str, float],
    nodes: Mapping[str, DAGNode],
    edges: tuple[ScalarEdge, ...],
    root: str,
    *,
    include_root_source: bool = False,
) -> float:
    """Evaluate one admissible nonnegative source realization exactly."""

    channel_nodes = {
        node_id: DAGNode(
            node_id,
            local_source=float(source_values.get(node_id, 0.0))
            if (include_root_source or node_id != root)
            else 0.0,
        )
        for node_id in nodes
    }
    return float(
        certify_dag_scalar(
            channel_nodes,
            edges,
            root,
            include_root_source=include_root_source,
        ).root_bound
    )

