from __future__ import annotations

import itertools
import sys
from pathlib import Path

import numpy as np

SRC = Path(__file__).resolve().parents[1] / "src"
sys.path.insert(0, str(SRC))

from allocation import global_certificate_optimal_allocation  # noqa: E402
from network import TensorNetwork  # noqa: E402
from tree import chain_topology  # noqa: E402


def _unit_batch(values):
    return [value / np.maximum(np.linalg.norm(value, axis=1, keepdims=True), 1.0) for value in values]


def test_global_domain_certificate_dominates_arbitrary_bounded_batch():
    topology = chain_topology(depth=3, leaf_dim=3, ambient_dim=3)
    net = TensorNetwork.random(topology, seed=31)
    fit_leaves = _unit_batch(net.sample_leaf_batch(30, seed=32))
    net.fit_projectors(net.ambient_forward(fit_leaves))
    test_leaves = _unit_batch(net.sample_leaf_batch(45, seed=33))
    ranks = {node.node_id: 2 for node in topology.nodes_postorder}
    certificate = net.global_error_certificate([1.0] * len(test_leaves), ranks)
    reduced = net.reduced_forward(test_leaves, ranks)
    ambient = net.ambient_forward(test_leaves)
    actual = max(np.linalg.norm(ambient[topology.root.node_id] - reduced[topology.root.node_id], axis=1))
    assert actual <= certificate["root_bound"] + 1e-10


def test_global_certificate_allocator_matches_exhaustive_certificate_minimum():
    topology = chain_topology(depth=3, leaf_dim=3, ambient_dim=3)
    net = TensorNetwork.random(topology, seed=34)
    leaves = _unit_batch(net.sample_leaf_batch(25, seed=35))
    net.fit_projectors(net.ambient_forward(leaves))
    budget = 6
    ranks = global_certificate_optimal_allocation(
        net, budget, leaf_norm_bounds=[1.0] * len(leaves)
    )
    ids = [node.node_id for node in topology.nodes_postorder if node != topology.root]
    best = float("inf")
    for values in itertools.product(range(1, 4), repeat=len(ids)):
        candidate = {topology.root.node_id: 1, **dict(zip(ids, values))}
        if sum(candidate.values()) > budget:
            continue
        best = min(best, net.global_error_certificate([1.0] * len(leaves), candidate)["root_bound"])
    observed = net.global_error_certificate([1.0] * len(leaves), ranks)["root_bound"]
    assert observed == pytest_approx(best)


def pytest_approx(value: float):
    class _Approx:
        def __eq__(self, other: object) -> bool:
            return isinstance(other, (int, float, np.floating)) and np.isclose(
                other, value, atol=1e-12, rtol=1e-12
            )

    return _Approx()
