from __future__ import annotations

import itertools
import sys
from pathlib import Path

import numpy as np

SRC = Path(__file__).resolve().parents[1] / "src"
sys.path.insert(0, str(SRC))

from allocation import (  # noqa: E402
    pathwise_majorant_optimal_allocation,
    pathwise_majorant_value,
)
from network import TensorNetwork  # noqa: E402
from tree import chain_topology  # noqa: E402


def test_dynamic_program_minimizes_declared_majorant_without_projecting_root():
    topology = chain_topology(depth=3, leaf_dim=4, ambient_dim=4)
    net = TensorNetwork.random(topology, seed=7)
    leaf_batch = net.sample_leaf_batch(40, seed=8)
    ambient_values = net.ambient_forward(leaf_batch)
    net.fit_projectors(ambient_values)
    budget = 7

    ranks = pathwise_majorant_optimal_allocation(
        net,
        budget,
        ambient_values=ambient_values,
        leaf_batch=leaf_batch,
    )
    assert sum(ranks.values()) <= budget
    assert ranks[topology.root.node_id] == 1

    ids = [node.node_id for node in topology.nodes_postorder if node != topology.root]
    best = float("inf")
    for candidate_values in itertools.product(range(1, 5), repeat=len(ids)):
        candidate = {topology.root.node_id: 1, **dict(zip(ids, candidate_values))}
        if sum(candidate.values()) > budget:
            continue
        best = min(
            best,
            pathwise_majorant_value(
                net,
                candidate,
                ambient_values=ambient_values,
                leaf_batch=leaf_batch,
            ),
        )
    assert pathwise_majorant_value(
        net,
        ranks,
        ambient_values=ambient_values,
        leaf_batch=leaf_batch,
    ) == pytest_approx(best)


def pytest_approx(value: float):
    class _Approx:
        def __eq__(self, other: object) -> bool:
            return isinstance(other, (float, int)) and np.isclose(other, value, atol=1e-12, rtol=1e-12)

    return _Approx()
