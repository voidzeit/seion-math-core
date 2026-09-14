from __future__ import annotations

import sys
from pathlib import Path

import numpy as np

SRC = Path(__file__).resolve().parents[1] / "src"
sys.path.insert(0, str(SRC))

from network import TensorNetwork  # noqa: E402
from tree import balanced_binary_topology, chain_topology  # noqa: E402
from allocation import small_case_validated_certificate_allocation  # noqa: E402


def test_finite_batch_certificate_dominates_real_root_error():
    for topology in (
        chain_topology(depth=3, leaf_dim=4, ambient_dim=4),
        balanced_binary_topology(4, leaf_dim=4, ambient_dim=4),
    ):
        for seed in range(4):
            net = TensorNetwork.random(topology, seed=seed)
            leaves = net.sample_leaf_batch(35, seed=100 + seed)
            net.ambient_forward(leaves)
            net.fit_projectors(net.ambient_forward(leaves))
            ranks = {node.node_id: 2 for node in topology.nodes_postorder}
            certificate = net.validated_error_certificate(leaves, ranks)
            assert certificate["bound_holds"] is True
            assert certificate["root_actual_sup"] <= certificate["root_bound"] + 1e-10
            assert all(
                value >= -1e-12
                for value in certificate["operator_norm_enclosures"].values()
            )


def test_full_rank_certificate_is_zero():
    topology = chain_topology(depth=2, leaf_dim=3, ambient_dim=3)
    net = TensorNetwork.random(topology, seed=13)
    leaves = net.sample_leaf_batch(20, seed=14)
    net.fit_projectors(net.ambient_forward(leaves))
    ranks = {node.node_id: node.ambient_dim for node in topology.nodes_postorder}
    certificate = net.validated_error_certificate(leaves, ranks)
    assert certificate["root_actual_sup"] == pytest_approx(0.0)
    assert certificate["root_bound"] == pytest_approx(0.0)


def test_certificate_allocator_uses_only_the_finite_batch_certificate():
    topology = chain_topology(depth=2, leaf_dim=3, ambient_dim=3)
    net = TensorNetwork.random(topology, seed=21)
    leaves = net.sample_leaf_batch(16, seed=22)
    net.fit_projectors(net.ambient_forward(leaves))
    ranks = small_case_validated_certificate_allocation(
        net, 4, leaf_batch=leaves, max_combinations=500
    )
    assert sum(ranks.values()) <= 4
    certificate = net.validated_error_certificate(leaves, ranks)
    assert certificate["bound_holds"] is True


def pytest_approx(value: float):
    class _Approx:
        def __eq__(self, other: object) -> bool:
            return isinstance(other, (int, float, np.floating)) and np.isclose(
                other, value, atol=1e-12, rtol=1e-12
            )

    return _Approx()
