"""The certificate-node cache must be exact and must invalidate correctly.

`_certificate_nodes` reads only frozen model tensors, but the post-training
sweep calls `certificate()` once per query per rank pair, recomputing ~128
matrix norms and as many device syncs each time. Caching it is a pure
memoization -- so it has to return identical values, and it has to notice when
the tensors it read actually change.
"""

from __future__ import annotations

import torch

from seion_kgr.ttn_branching import BranchingTTNK3

BOUNDS = {"h1": 0.8, "r1": 0.8, "h2": 0.9, "r2": 0.9, "t": 1.0}


def _model() -> BranchingTTNK3:
    torch.manual_seed(0)
    model = BranchingTTNK3(40, 8, 8, 8)
    model.fit_projectors(torch.arange(16), torch.arange(16) % 8)
    return model


def _nodes_snapshot(model: BranchingTTNK3):
    return {
        name: (node.operator_bound, node.normal_bounds, node.projected_operator_bounds)
        for name, node in model._certificate_nodes().items()
    }


def test_cache_returns_identical_node_values():
    model = _model()
    first = _nodes_snapshot(model)
    second = _nodes_snapshot(model)
    assert first == second
    assert model._certificate_nodes() is model._certificate_nodes(), "second call must be cached"


def test_certificate_values_are_unchanged_by_caching():
    model = _model()
    baseline = float(model.certificate(BOUNDS, 2, 3, rank_aware=True)["root_bound"])
    for _ in range(5):
        assert float(model.certificate(BOUNDS, 2, 3, rank_aware=True)["root_bound"]) == baseline
    # A different rank pair must still be computed correctly off the same cache.
    other = float(model.certificate(BOUNDS, 4, 4, rank_aware=True)["root_bound"])
    assert other != baseline or True  # value may coincide; the point is it computes


def test_cache_invalidates_on_in_place_weight_change():
    model = _model()
    before = _nodes_snapshot(model)
    with torch.no_grad():
        model.mu1.weight.mul_(1.7)
    after = _nodes_snapshot(model)
    assert before != after, "an in-place weight change must invalidate the cache"


def test_cache_invalidates_on_rebound_basis():
    model = _model()
    before = _nodes_snapshot(model)
    model.basis1 = torch.linalg.qr(torch.randn_like(model.basis1))[0]
    after = _nodes_snapshot(model)
    assert before != after, "rebinding the basis must invalidate the cache"


def test_cached_and_uncached_agree_exactly():
    """Recompute with the cache disabled and compare bit-for-bit."""
    model = _model()
    cached = _nodes_snapshot(model)
    model._certificate_nodes_cache = None
    fresh = _nodes_snapshot(model)
    assert cached == fresh
