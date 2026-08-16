"""Soundness gates for the M24/M25 certificates.

Tightness is the goal but soundness is the gate: a tighter bound that is
ever violated is wrong, not an improvement. These tests assert the bound
holds, and assert the structural inequality C <= B that makes the
Gram-aware refinement a refinement rather than a different bound.
"""

from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pytest

SRC = Path(__file__).resolve().parents[1] / "src"
sys.path.insert(0, str(SRC))

from geometric_certificate import gram_aware_certificate, restricted_gain_certificate  # noqa: E402
from network import TensorNetwork  # noqa: E402
from tree import balanced_binary_topology, chain_topology  # noqa: E402

AMBIENT = 5


def build(topology, seed: int):
    net = TensorNetwork.random(topology, seed=seed)
    fit = net.sample_leaf_batch(120, seed=seed * 31 + 1)
    net.fit_projectors(net.ambient_forward(fit))
    return net, net.sample_leaf_batch(120, seed=seed * 31 + 2)


TOPOLOGIES = [
    ("chain2", chain_topology(depth=2, leaf_dim=AMBIENT, ambient_dim=AMBIENT)),
    ("chain5", chain_topology(depth=5, leaf_dim=AMBIENT, ambient_dim=AMBIENT)),
    ("chain9", chain_topology(depth=9, leaf_dim=AMBIENT, ambient_dim=AMBIENT)),
    ("binary4", balanced_binary_topology(4, leaf_dim=AMBIENT, ambient_dim=AMBIENT)),
    ("binary8", balanced_binary_topology(8, leaf_dim=AMBIENT, ambient_dim=AMBIENT)),
]


@pytest.mark.parametrize("name,topology", TOPOLOGIES)
@pytest.mark.parametrize("rank", [1, 2, 4, AMBIENT])
@pytest.mark.parametrize("seed", [0, 1, 2])
def test_both_certificates_are_sound(name, topology, rank, seed):
    net, evaluation = build(topology, seed)
    ranks = {node.node_id: rank for node in topology.nodes_postorder}

    b = restricted_gain_certificate(net, evaluation, ranks)
    c = gram_aware_certificate(net, evaluation, ranks)

    assert b["bound_holds"], f"{name} r={rank} s={seed}: B violated"
    assert c["bound_holds"], f"{name} r={rank} s={seed}: C violated"
    assert b["root_actual_sup"] <= b["root_bound"] + 1e-9
    assert c["root_actual_sup"] <= c["root_bound"] + 1e-9


@pytest.mark.parametrize("name,topology", TOPOLOGIES)
@pytest.mark.parametrize("rank", [1, 2, 4])
def test_gram_aware_never_looser_than_restricted(name, topology, rank):
    """C replaces ||a||+||b|| with sqrt(||a||^2+||b||^2+2*cross*||b||) where
    cross <= ||a||, so C <= B identically. A regression that inverted this
    would mean the cross term was mis-bounded."""

    net, evaluation = build(topology, seed=3)
    ranks = {node.node_id: rank for node in topology.nodes_postorder}
    b = restricted_gain_certificate(net, evaluation, ranks)
    c = gram_aware_certificate(net, evaluation, ranks)
    assert c["root_bound"] <= b["root_bound"] * (1 + 1e-12)


def test_full_rank_gives_zero_error_and_zero_bound():
    """At full rank nothing is truncated, so both the true error and the
    certified bound must vanish -- a bound that stays positive here would be
    reporting error that cannot exist."""

    topology = chain_topology(depth=4, leaf_dim=AMBIENT, ambient_dim=AMBIENT)
    net, evaluation = build(topology, seed=7)
    ranks = {node.node_id: AMBIENT for node in topology.nodes_postorder}
    for certificate in (restricted_gain_certificate, gram_aware_certificate):
        result = certificate(net, evaluation, ranks)
        assert result["root_actual_sup"] == pytest.approx(0.0, abs=1e-10)
        assert result["root_bound"] == pytest.approx(0.0, abs=1e-10)


def test_tighter_than_the_scalar_frobenius_certificate_at_depth():
    """The whole point of M24: at depth the restricted-gain composition must
    beat the scalar/Frobenius one by orders of magnitude, not marginally."""

    topology = chain_topology(depth=9, leaf_dim=AMBIENT, ambient_dim=AMBIENT)
    net, evaluation = build(topology, seed=5)
    ranks = {node.node_id: 2 for node in topology.nodes_postorder}
    a = net.validated_error_certificate(evaluation, ranks)
    b = restricted_gain_certificate(net, evaluation, ranks)
    assert a["bound_holds"] and b["bound_holds"]
    assert b["root_bound"] < a["root_bound"] / 100.0
