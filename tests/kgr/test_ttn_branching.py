"""Tests for the post-training branching TTN scorer and certificate bridge."""

from __future__ import annotations

import torch

from seion_kgr.data import tiny_kg
from seion_kgr.ttn_branching import BranchingTTNK3, branch_leaf_norm_bounds


def _model() -> BranchingTTNK3:
    torch.manual_seed(7)
    kg = tiny_kg()
    model = BranchingTTNK3(
        num_entities=kg.num_entities,
        num_relations_total=kg.num_relations_total,
        dim=8,
        branch_dim=6,
    )
    h = torch.tensor([x[0] for x in kg.train[:24]], dtype=torch.long)
    r = torch.tensor([x[1] for x in kg.train[:24]], dtype=torch.long)
    model.fit_projectors(h, r)
    return model


def test_full_rank_projected_execution_matches_full_score():
    model = _model()
    h = torch.tensor([0, 1, 2], dtype=torch.long)
    r = torch.tensor([0, 1, 2], dtype=torch.long)
    t = torch.tensor([1, 2, 3], dtype=torch.long)
    model.set_mode("full")
    full = model.score_positive(h, r, t)
    model.set_mode("projected")
    projected = model.score_positive(h, r, t)
    torch.testing.assert_close(projected, full, rtol=1e-5, atol=1e-6)


def test_reduced_core_execution_matches_ambient_projected_reference():
    model = _model()
    h = torch.tensor([0, 1, 2], dtype=torch.long)
    r = torch.tensor([0, 1, 2], dtype=torch.long)
    t = torch.tensor([1, 2, 3], dtype=torch.long)
    candidates = torch.arange(6, dtype=torch.long)
    model.set_ranks(2, 3)
    ambient_positive = model.score_positive_projected_ambient(h, r, t)
    ambient_candidates = model.score_tail_candidates_projected_ambient(h, r, candidates)
    model.set_mode("projected")
    reduced_positive = model.score_positive(h, r, t)
    reduced_candidates = model.score_tail_candidates(h, r, candidates)
    torch.testing.assert_close(reduced_positive, ambient_positive, rtol=1e-5, atol=1e-6)
    torch.testing.assert_close(reduced_candidates, ambient_candidates, rtol=1e-5, atol=1e-6)


def test_reduced_score_is_bounded_by_global_dag_certificate():
    model = _model()
    model.set_ranks(2, 3)
    h = torch.tensor([0, 1, 2, 3], dtype=torch.long)
    r = torch.tensor([0, 1, 2, 3], dtype=torch.long)
    t = torch.tensor([1, 2, 3, 4], dtype=torch.long)
    model.set_mode("full")
    full = model.score_positive(h, r, t)
    model.set_mode("projected")
    reduced = model.score_positive(h, r, t)
    bound = float(model.certificate(branch_leaf_norm_bounds(model), 2, 3)["root_bound"])
    assert float((full - reduced).abs().max().item()) <= bound + 1e-6


def test_candidate_scoring_shape_and_certificate_rank_allocator():
    model = _model()
    h = torch.tensor([0, 1], dtype=torch.long)
    r = torch.tensor([0, 1], dtype=torch.long)
    candidates = torch.arange(6, dtype=torch.long)
    scores = model.score_tail_candidates(h, r, candidates)
    assert scores.shape == (2, 6)
    allocation, objective = model.optimal_certificate_ranks(
        branch_leaf_norm_bounds(model), budget=5, rank_aware=True
    )
    assert set(allocation) == {"branch1", "branch2"}
    assert sum(allocation.values()) <= 5
    assert objective >= 0.0


def test_resource_proxy_decreases_projected_contraction_with_rank():
    model = _model()
    low = model.resource_proxy(1, 1)
    high = model.resource_proxy(model.branch_dim, model.branch_dim)
    assert low["projected_score_contraction_units"] < high["projected_score_contraction_units"]
    assert low["runtime_model_storage_bytes"] < high["runtime_model_storage_bytes"]


def test_output_compression_matches_ambient_output_projection():
    model = _model()
    h = torch.tensor([0, 1, 2], dtype=torch.long)
    r = torch.tensor([0, 1, 2], dtype=torch.long)
    t = torch.tensor([1, 2, 3], dtype=torch.long)
    candidates = torch.arange(6, dtype=torch.long)
    train_entities = torch.unique(torch.tensor([0, 1, 2, 3, 4, 5], dtype=torch.long))
    model.fit_output_projector(train_entities)
    model.set_output_rank(3)
    model.set_ranks(2, 3)
    ambient_positive = model.score_positive_projected_ambient(h, r, t)
    ambient_candidates = model.score_tail_candidates_projected_ambient(h, r, candidates)
    model.set_mode("projected")
    reduced_positive = model.score_positive(h, r, t)
    reduced_candidates = model.score_tail_candidates(h, r, candidates)
    torch.testing.assert_close(reduced_positive, ambient_positive, rtol=1e-5, atol=1e-6)
    torch.testing.assert_close(reduced_candidates, ambient_candidates, rtol=1e-5, atol=1e-6)


def test_output_certificate_and_candidate_proxy_decrease():
    model = _model()
    train_entities = torch.arange(model.entity.num_embeddings, dtype=torch.long)
    model.fit_output_projector(train_entities)
    full = model.resource_proxy(2, 3, output_rank=model.dim, candidate_count=6)
    model.set_output_rank(2)
    compressed = model.resource_proxy(2, 3, output_rank=2, candidate_count=6)
    certificate = model.output_certificate(branch_leaf_norm_bounds(model), 2, 3)
    assert compressed["projected_candidate_score_units"] < full["projected_candidate_score_units"]
    assert certificate["output_rank"] == 2
    assert certificate["total_error_bound"] >= certificate["internal_error_bound"]
