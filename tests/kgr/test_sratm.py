from __future__ import annotations

import torch

from seion_kgr.data import tiny_kg
from seion_kgr.sota.sratm import SpectralRelationAdaptiveTensorMixture


def _model() -> SpectralRelationAdaptiveTensorMixture:
    kg = tiny_kg()
    torch.manual_seed(3)
    return SpectralRelationAdaptiveTensorMixture(
        kg.num_entities,
        kg.num_relations_total,
        entity_dim=8,
        relation_dim=8,
        experts=2,
        active_per_relation=1,
        expert_rank=4,
        core_basis=2,
    )


def test_sratm_positive_and_candidate_shapes_are_finite():
    model = _model()
    h = torch.tensor([0, 1])
    r = torch.tensor([0, 1])
    t = torch.tensor([1, 2])
    positive = model.score_positive(h, r, t)
    candidates = model.score_tail_candidates(h, r, torch.arange(4))
    assert positive.shape == (2,)
    assert candidates.shape == (2, 4)
    assert torch.isfinite(positive).all()
    assert torch.isfinite(candidates).all()


def test_sratm_relation_prediction_and_fusion_are_well_formed():
    model = _model()
    h = torch.tensor([0, 1])
    r = torch.tensor([0, 1])
    t = torch.tensor([1, 2])
    logits = model.relation_logits(h, t)
    fusion = model.fusion_probabilities(r)
    assert logits.shape == (2, 4)
    assert fusion.shape == (2, 3)
    assert torch.allclose(fusion.sum(dim=-1), torch.ones(2), atol=1e-6)


def test_sratm_gradients_reach_all_three_paths():
    model = _model()
    h = torch.tensor([0, 1])
    r = torch.tensor([0, 1])
    t = torch.tensor([1, 2])
    loss = model.score_positive(h, r, t).sum() + model.relation_logits(h, t).square().mean()
    loss.backward()
    assert model.global_core.grad is not None
    assert model.fusion_logits.grad is not None
    assert model.complex_entity_real.weight.grad is not None
    assert model.relation_head.weight.grad is not None
