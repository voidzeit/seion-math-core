"""Regression tests for the least-squares root-fitting machinery (Levels
2/3) and the Burgers solver, including a regression test for the
rank-degeneracy bug caught during Level 3 development."""

from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pytest

SRC = Path(__file__).resolve().parents[1] / "src"
EXPERIMENTS = Path(__file__).resolve().parents[1] / "experiments"
sys.path.insert(0, str(SRC))
sys.path.insert(0, str(EXPERIMENTS))

from network import NodeCore, TensorNetwork  # noqa: E402
from tree import NodeSpec, TreeTopology  # noqa: E402
from burgers_solver import generate_dataset, solve_burgers  # noqa: E402


def test_burgers_solver_bounded_no_nan():
    u = solve_burgers(0.1, np.array([1.0, 0.3, -0.2]))
    assert np.isfinite(u).all()
    assert np.max(np.abs(u)) < 10.0  # sanity bound, not a tight physical claim


def test_burgers_dataset_shapes():
    nu, fc, states = generate_dataset(10, seed=0, grid_size=16, n_fourier_modes=3)
    assert nu.shape == (10,)
    assert fc.shape == (10, 3)
    assert states.shape == (10, 16)
    assert np.isfinite(states).all()


def test_fit_root_reduces_training_error():
    """A basic sanity check: fitting the root via least squares should
    substantially reduce training error compared to the unfitted random
    root, on a task the linear model can actually solve (a genuinely
    linear target of the leaf features)."""

    node0 = NodeSpec(node_id="n0", children=(0, 1), ambient_dim=4)
    root = NodeSpec(node_id="root", children=(node0, 2), ambient_dim=3)
    topology = TreeTopology(root=root, leaf_dims=(2, 2, 1))
    net = TensorNetwork.random(topology, seed=0)

    leaf_batch = net.sample_leaf_batch(200, seed=1)
    ambient = net.ambient_forward(leaf_batch)
    net.fit_projectors(ambient)

    ranks = {"n0": 4}
    # A target actually IN the model's span (the outer product of the
    # reduced children contracted with a random target tensor) - unlike
    # pure i.i.d. noise, this is something the closed-form least-squares
    # solve can fit almost exactly, so a strong error reduction is the
    # correct expectation to test for.
    reduced_children = net.reduced_children_of_root(leaf_batch, ranks)
    rng = np.random.default_rng(2)
    true_tensor = rng.standard_normal((root.ambient_dim, *[c.shape[1] for c in reduced_children]))
    target = np.einsum("dab,na,nb->nd", true_tensor, *reduced_children)

    pred_before = net.predict_root(leaf_batch, ranks)
    error_before = np.mean((pred_before - target) ** 2)

    net.fit_root_via_least_squares(leaf_batch, ranks, target)
    pred_after = net.predict_root(leaf_batch, ranks)
    error_after = np.mean((pred_after - target) ** 2)

    assert error_after < error_before / 10, "least-squares fit did not substantially reduce training error"


def test_rank_degeneracy_regression():
    """Regression test for the Level 3 design bug: if BOTH children of
    an intermediate node are 1-dimensional, that node's ambient output is
    mathematically rank-1 regardless of its declared ambient_dim, so
    varying its allocated rank from 1 to ambient_dim must have NO effect
    on the fitted root's predictions. This test both documents and
    detects that specific degeneracy (so a future change that
    accidentally reintroduces it - e.g. in a new experiment topology -
    fails loudly)."""

    node0 = NodeSpec(node_id="n0", children=(0, 1), ambient_dim=6)
    root = NodeSpec(node_id="root", children=(node0, 2), ambient_dim=8)
    topology = TreeTopology(root=root, leaf_dims=(1, 1, 2))  # degenerate: both node0 children are 1-dim
    net = TensorNetwork.random(topology, seed=0)

    train_leaf = net.sample_leaf_batch(100, seed=1)
    ambient = net.ambient_forward(train_leaf)
    net.fit_projectors(ambient)
    rng = np.random.default_rng(3)
    target = rng.standard_normal((100, 8))

    predictions = []
    for rank in [1, 3, 6]:
        ranks = {"n0": rank}
        net.fit_root_via_least_squares(train_leaf, ranks, target)
        predictions.append(net.predict_root(train_leaf, ranks))

    for p in predictions[1:]:
        assert np.allclose(p, predictions[0], atol=1e-8), (
            "expected the known 1-dim/1-dim degeneracy to make rank irrelevant; "
            "if this now fails, the degeneracy no longer holds and this test "
            "(and its docstring) should be updated, not silently ignored"
        )


def test_non_degenerate_topology_rank_matters():
    """Companion to the regression test above: with genuinely
    multi-dimensional children (the FIX applied in Level 3), rank
    SHOULD affect predictions."""

    node0 = NodeSpec(node_id="n0", children=(0, 1), ambient_dim=6)
    root = NodeSpec(node_id="root", children=(node0, 2), ambient_dim=8)
    topology = TreeTopology(root=root, leaf_dims=(3, 2, 1))  # 3*2=6, matches ambient_dim
    net = TensorNetwork.random(topology, seed=0)

    train_leaf = net.sample_leaf_batch(100, seed=1)
    ambient = net.ambient_forward(train_leaf)
    net.fit_projectors(ambient)
    rng = np.random.default_rng(3)
    target = rng.standard_normal((100, 8))

    net.fit_root_via_least_squares(train_leaf, {"n0": 1}, target)
    pred_rank1 = net.predict_root(train_leaf, {"n0": 1})
    net.fit_root_via_least_squares(train_leaf, {"n0": 6}, target)
    pred_rank6 = net.predict_root(train_leaf, {"n0": 6})

    assert not np.allclose(pred_rank1, pred_rank6, atol=1e-6), (
        "expected rank to matter for a non-degenerate topology"
    )
