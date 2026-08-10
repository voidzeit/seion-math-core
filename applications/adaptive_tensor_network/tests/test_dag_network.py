"""Numerical validation of shared-subexpression DAG tensor networks."""

from __future__ import annotations

import itertools
import sys
from pathlib import Path

import numpy as np
import pytest

APP_SRC = Path(__file__).resolve().parents[1] / "src"
REPO_SRC = Path(__file__).resolve().parents[2] / ".." / "src"
sys.path.insert(0, str(APP_SRC))
sys.path.insert(0, str(REPO_SRC))

from dag import shared_diamond_topology  # noqa: E402
from dag_network import DAGTensorNetwork  # noqa: E402


def _network() -> DAGTensorNetwork:
    topology = shared_diamond_topology(leaf_dim=3, ambient_dim=3)
    network = DAGTensorNetwork.random(topology, seed=17)
    fit = [
        values / np.maximum(np.linalg.norm(values, axis=1, keepdims=True), 1.0)
        for values in network.sample_leaf_batch(100, seed=18)
    ]
    network.fit_projectors(network.ambient_forward(fit))
    return network


def test_dag_held_out_root_error_is_bounded_by_global_certificate():
    network = _network()
    held_out = [
        values / np.maximum(np.linalg.norm(values, axis=1, keepdims=True), 1.0)
        for values in network.sample_leaf_batch(300, seed=19)
    ]
    ranks = {"u": 2, "left": 1, "right": 2, "root": 1}
    certificate = network.global_error_certificate([1.0, 1.0, 1.0], ranks)
    actual = network.root_error_sup(held_out, ranks)
    assert actual <= certificate["root_bound"] + 1.0e-10
    assert certificate["downstream_gains"]["u"] > certificate["downstream_gains"]["left"]


def test_dag_full_rank_has_zero_global_certificate_and_error():
    network = _network()
    ranks = {node_id: 3 for node_id in network.topology.topological_order}
    certificate = network.global_error_certificate([1.0, 1.0, 1.0], ranks)
    assert certificate["root_bound"] == pytest.approx(0.0, abs=1.0e-12)
    held_out = network.sample_leaf_batch(40, seed=20)
    assert network.root_error_sup(held_out, ranks) == pytest.approx(0.0, abs=1.0e-10)


def test_rank_aware_dag_certificate_is_sound_and_tracks_projected_values():
    network = _network()
    held_out = [
        values / np.maximum(np.linalg.norm(values, axis=1, keepdims=True), 1.0)
        for values in network.sample_leaf_batch(200, seed=21)
    ]
    ranks = {"u": 1, "left": 2, "right": 1, "root": 1}
    certificate = network.rank_aware_error_certificate([1.0, 1.0, 1.0], ranks)
    actual = network.root_error_sup(held_out, ranks)
    assert actual <= certificate["root_bound"] + 1.0e-10
    assert certificate["approximate_value_bounds"]["u"] <= certificate["exact_value_bounds"]["u"] + 1.0e-12


def test_rank_aware_allocator_matches_small_exhaustive_search():
    network = _network()
    budget = 7
    allocation = network.optimal_rank_aware_certificate_allocation(
        budget, leaf_norm_bounds=[1.0, 1.0, 1.0]
    )
    selected = network.rank_aware_error_certificate([1.0, 1.0, 1.0], allocation)["root_bound"]
    best = float("inf")
    for values in itertools.product((1, 2, 3), repeat=3):
        candidate = {"root": 1, **dict(zip(("u", "left", "right"), values))}
        if sum(candidate.values()) <= budget:
            bound = network.rank_aware_error_certificate([1.0, 1.0, 1.0], candidate)["root_bound"]
            best = min(best, bound)
    assert selected == pytest.approx(best, abs=1.0e-10)


def test_compressed_coordinate_forward_matches_projected_ambient_forward():
    network = _network()
    leaves = network.sample_leaf_batch(25, seed=23)
    ranks = {"u": 1, "left": 2, "right": 1, "root": 1}
    ambient_projected = network.reduced_forward(leaves, ranks)
    compressed = network.compressed_forward(leaves, ranks)
    for node_id in network.topology.topological_order:
        if node_id == network.topology.root_id:
            reconstructed = compressed[node_id]
            expected = ambient_projected[node_id]
        else:
            rank = ranks[node_id]
            basis = network.projectors[node_id].basis[:, :rank]
            reconstructed = compressed[node_id] @ basis.T
            expected = network.projectors[node_id].project(
                ambient_projected[node_id], rank
            )
        assert reconstructed == pytest.approx(expected, abs=1.0e-10)


def test_resource_proxy_counts_shared_node_once_and_tracks_rank_dependence():
    network = _network()
    low = network.resource_proxy({"u": 1, "left": 1, "right": 1, "root": 1})
    high = network.resource_proxy({"u": 3, "left": 3, "right": 3, "root": 1})
    assert low["node_contraction_units"]["u"] == 1 * 3 * 3
    assert low["contraction_units_per_sample"] < high["contraction_units_per_sample"]
    assert low["parameter_storage_bytes"] < high["parameter_storage_bytes"]
    assert low["peak_activation_units_per_sample"] > 0


def test_dag_certificate_allocator_matches_exhaustive_rank_search():
    network = _network()
    budget = 7
    allocation = network.optimal_certificate_allocation(
        budget, leaf_norm_bounds=[1.0, 1.0, 1.0]
    )
    assert sum(allocation.values()) <= budget
    selected = network.global_error_certificate([1.0, 1.0, 1.0], allocation)["root_bound"]

    best = float("inf")
    for values in itertools.product((1, 2, 3), repeat=3):
        candidate = {"root": 1, **dict(zip(("u", "left", "right"), values))}
        if sum(candidate.values()) <= budget:
            bound = network.global_error_certificate([1.0, 1.0, 1.0], candidate)["root_bound"]
            best = min(best, bound)
    assert selected == pytest.approx(best, abs=1.0e-10)


def test_dag_topology_rejects_cycles_and_disconnected_nodes():
    from dag import DAGNodeSpec, DAGTopology

    with pytest.raises(ValueError, match="cycle"):
        DAGTopology(
            nodes={
                "a": DAGNodeSpec("a", ("b",), 2),
                "b": DAGNodeSpec("b", ("a",), 2),
            },
            root_id="a",
            leaf_dims=(2,),
        )
    with pytest.raises(ValueError, match="feed"):
        DAGTopology(
            nodes={
                "root": DAGNodeSpec("root", (0,), 2),
                "unused": DAGNodeSpec("unused", (0,), 2),
            },
            root_id="root",
            leaf_dims=(2,),
        )
