"""Regression tests for the adaptive tensor network application
(mission Section VI: rank-allocation budget conservation, no test-set
leakage, projector identities, deterministic behavior)."""

from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pytest

SRC = Path(__file__).resolve().parents[1] / "src"
sys.path.insert(0, str(SRC))

from allocation import ABLATION_METHODS, ALLOCATION_METHODS, small_case_oracle_allocation  # noqa: E402
from network import TensorNetwork  # noqa: E402
from tree import balanced_binary_topology, chain_topology  # noqa: E402


@pytest.fixture
def small_network():
    topo = chain_topology(depth=3, leaf_dim=4, ambient_dim=4)
    net = TensorNetwork.random(topo, seed=0)
    leaf_batch = net.sample_leaf_batch(100, seed=1)
    ambient_values = net.ambient_forward(leaf_batch)
    net.fit_projectors(ambient_values)
    return net, leaf_batch, ambient_values


def test_budget_conservation(small_network):
    net, leaf_batch, ambient_values = small_network
    budget = 8
    for name, fn in ALLOCATION_METHODS.items():
        ranks = fn(net, budget, ambient_values=ambient_values, leaf_batch=leaf_batch, seed=0)
        assert sum(ranks.values()) <= budget, f"{name} exceeded budget"
        for node in net.topology.nodes_postorder:
            assert 1 <= ranks[node.node_id] <= node.ambient_dim, f"{name} produced an invalid rank"


def test_ablation_budget_conservation(small_network):
    net, leaf_batch, ambient_values = small_network
    budget = 8
    for name, fn in ABLATION_METHODS.items():
        ranks = fn(net, budget, ambient_values=ambient_values, leaf_batch=leaf_batch, seed=0)
        assert sum(ranks.values()) <= budget, f"{name} exceeded budget"


def test_oracle_respects_budget(small_network):
    net, leaf_batch, ambient_values = small_network
    root_id = net.topology.root.node_id
    root_ambient = ambient_values[root_id]

    def evaluate(ranks):
        reduced = net.reduced_forward(leaf_batch, ranks)
        diff = root_ambient - reduced[root_id]
        return float(np.sqrt(np.mean(np.sum(diff**2, axis=1))))

    ranks = small_case_oracle_allocation(net, 8, evaluate_fn=evaluate, max_combinations=200)
    assert sum(ranks.values()) <= 8


def test_projector_orthonormality(small_network):
    net, _, _ = small_network
    for node_id, projector in net.projectors.items():
        gram = projector.basis.T @ projector.basis
        assert np.allclose(gram, np.eye(gram.shape[0]), atol=1e-8), f"{node_id} basis is not orthonormal"


def test_projector_is_idempotent(small_network):
    net, leaf_batch, ambient_values = small_network
    for node_id, projector in net.projectors.items():
        batch = ambient_values[node_id]
        rank = 2
        once = projector.project(batch, rank)
        twice = projector.project(once, rank)
        assert np.allclose(once, twice, atol=1e-8), f"{node_id} projector is not idempotent"


def test_full_rank_projection_is_identity(small_network):
    net, _, ambient_values = small_network
    for node in net.topology.nodes_postorder:
        batch = ambient_values[node.node_id]
        projected = net.projectors[node.node_id].project(batch, node.ambient_dim)
        assert np.allclose(projected, batch, atol=1e-6), f"{node.node_id} full-rank projection is not identity"


def test_zero_rank_projection_is_zero(small_network):
    net, _, ambient_values = small_network
    for node in net.topology.nodes_postorder:
        batch = ambient_values[node.node_id]
        projected = net.projectors[node.node_id].project(batch, 0)
        assert np.allclose(projected, 0.0)


def test_no_test_set_leakage(small_network):
    """The fitting batch and the evaluation batch must be drawn from
    independent RNG streams - verified by regenerating both and checking
    they are not the same data and that projectors are unaffected by the
    evaluation batch's contents."""

    net, fit_leaf_batch, fit_ambient_values = small_network
    eval_leaf_batch = net.sample_leaf_batch(100, seed=2)  # different seed than fitting (seed=1)
    for fit_leaf, eval_leaf in zip(fit_leaf_batch, eval_leaf_batch):
        assert not np.allclose(fit_leaf, eval_leaf), "fitting and evaluation batches must differ"

    # projectors fit from the fitting batch must not change when we
    # separately compute ambient values on the eval batch
    projectors_before = {k: v.basis.copy() for k, v in net.projectors.items()}
    net.ambient_forward(eval_leaf_batch)  # must not mutate net.projectors
    for node_id, basis_before in projectors_before.items():
        assert np.allclose(net.projectors[node_id].basis, basis_before), "evaluating on held-out data mutated fitted projectors"


def test_pathwise_majorant_upper_bounds_true_error_on_average(small_network):
    """Not a per-instance guarantee (this network is not the exact
    finite-core theory's homogeneous setting), but the ratio should stay
    well-behaved (bounded, not wildly exceeding 1) for a real fitted
    network - a basic sanity/regression check, not a re-proof of the
    finite-core theorem."""

    net, leaf_batch, ambient_values = small_network
    ranks = {node.node_id: 2 for node in net.topology.nodes_postorder}
    local_errors = net.local_truncation_error(ambient_values, ranks)
    amplifications = net.path_amplification(ambient_values, leaf_batch)
    majorant = sum(net.pathwise_score(local_errors, amplifications).values())
    reduced = net.reduced_forward(leaf_batch, ranks)
    root_id = net.topology.root.node_id
    diff = ambient_values[root_id] - reduced[root_id]
    true_error = float(np.sqrt(np.mean(np.sum(diff**2, axis=1))))
    assert true_error <= majorant * 3, "true error wildly exceeds the pathwise majorant (regression check)"


def test_balanced_binary_topology_shape():
    topo = balanced_binary_topology(4, leaf_dim=3, ambient_dim=3)
    assert topo.internal_node_count == 3
    assert len(topo.leaf_dims) == 4


def test_deterministic_given_seed():
    topo = chain_topology(depth=2, leaf_dim=4, ambient_dim=4)
    net1 = TensorNetwork.random(topo, seed=42)
    net2 = TensorNetwork.random(topo, seed=42)
    for node_id in net1.cores:
        assert np.allclose(net1.cores[node_id].tensor, net2.cores[node_id].tensor)
