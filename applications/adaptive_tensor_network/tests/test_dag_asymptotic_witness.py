"""Numerical real-tensor verification of the fixed-DAG complex witness."""

from __future__ import annotations

import math
import sys
from pathlib import Path

import numpy as np
import pytest

APP_SRC = Path(__file__).resolve().parents[1] / "src"
REPO_SRC = Path(__file__).resolve().parents[2] / ".." / "src"
sys.path.insert(0, str(APP_SRC))
sys.path.insert(0, str(REPO_SRC))

from dag import DAGNodeSpec, DAGTopology, shared_diamond_topology  # noqa: E402
from dag_network import DAGTensorNetwork  # noqa: E402
from network import NodeCore, NodeProjector  # noqa: E402
from seion_core.research_v4.dag_certificate import DAGNode, ScalarEdge  # noqa: E402
from seion_core.research_v5.dag_asymptotic_sharpness import (  # noqa: E402
    complex_product_witness_error,
    exact_dag_asymptotic_path_constant,
)


def _chain_topology(depth: int = 4) -> DAGTopology:
    nodes: dict[str, DAGNodeSpec] = {}
    current: int | str = 0
    for index in range(depth):
        node_id = f"n{index}"
        nodes[node_id] = DAGNodeSpec(node_id, (current, index + 1), 2)
        current = node_id
    return DAGTopology(nodes=nodes, root_id=f"n{depth - 1}", leaf_dims=(2,) * (depth + 1))


def _repeated_slot_topology() -> DAGTopology:
    nodes = {
        "u": DAGNodeSpec("u", (0, 1), 2),
        "square": DAGNodeSpec("square", ("u", "u"), 2),
        "root": DAGNodeSpec("root", ("square", 2), 2),
    }
    return DAGTopology(nodes=nodes, root_id="root", leaf_dims=(2, 2, 2))


def _complex_product_core(arity: int, theta: float) -> NodeCore:
    phase = complex(math.cos(theta), math.sin(theta))
    tensor = np.zeros((2,) * (arity + 1), dtype=float)
    basis = (1.0 + 0.0j, 0.0 + 1.0j)
    for indices in np.ndindex(tensor.shape):
        output_index, *input_indices = indices
        value = phase
        for input_index in input_indices:
            value *= basis[input_index]
        tensor[indices] = value.real if output_index == 0 else value.imag
    return NodeCore(tensor=tensor)


def _witness_network(topology: DAGTopology, theta: float) -> DAGTensorNetwork:
    cores = {
        node_id: _complex_product_core(topology.nodes[node_id].arity, theta)
        for node_id in topology.topological_order
    }
    projectors = {
        node_id: NodeProjector(basis=np.eye(2), singular_values=np.ones(2))
        for node_id in topology.topological_order
    }
    return DAGTensorNetwork(topology=topology, cores=cores, projectors=projectors)


def _path_constant(topology: DAGTopology) -> float:
    nodes = {
        node_id: DAGNode(node_id, 0.0)
        for node_id in topology.topological_order
    }
    edges: list[ScalarEdge] = []
    for node_id in topology.topological_order:
        for ref in topology.nodes[node_id].inputs:
            if isinstance(ref, str):
                edges.append(ScalarEdge(ref, node_id, 1.0))
    projected = tuple(node_id for node_id in topology.topological_order if node_id != topology.root_id)
    return exact_dag_asymptotic_path_constant(
        nodes, tuple(edges), topology.root_id, projected_nodes=projected
    ).asymptotic_constant


@pytest.mark.parametrize("topology", [
    shared_diamond_topology(leaf_dim=2, ambient_dim=2),
    _chain_topology(),
    _repeated_slot_topology(),
])
def test_real_tensor_backend_matches_general_dag_witness_formula(topology):
    eta = 0.01
    theta = math.asin(eta)
    network = _witness_network(topology, theta)
    leaves = [np.array([[1.0, 0.0]]) for _ in topology.leaf_dims]
    root_id = topology.root_id
    ambient = network.ambient_forward(leaves)[root_id]
    reduced = network.reduced_forward(
        leaves,
        {node_id: 1 for node_id in topology.topological_order},
    )[root_id]
    observed = float(np.linalg.norm(ambient - reduced))
    expected = complex_product_witness_error(_path_constant(topology), eta)
    assert observed == pytest.approx(expected, abs=1.0e-10)

