"""Gate 13.5 standalone scorer microtests.

These tests are intentionally small and test-closed. They verify that the
standalone branches receive internal gradients from the first optimization
step, rather than only updating their learned scale parameters.
"""
from __future__ import annotations

import torch

from seion_kgr.losses import negative_sampling_loss
from seion_kgr.model import SeionKGRv26
from seion_kgr.reasoner import Adjacency
from seion_kgr.train import build_optimizer_param_groups


def _triples():
    h = torch.tensor([0, 1, 2, 3], dtype=torch.long)
    r = torch.tensor([0, 1, 0, 1], dtype=torch.long)
    t = torch.tensor([1, 2, 3, 0], dtype=torch.long)
    return h, r, t


def _adjacency():
    # Keep an alternate outgoing edge for every query head.  The queried
    # positive edge is excluded by the leakage guard, so a one-edge cycle
    # would exercise only ``unreached_state`` and cannot certify gradients
    # through the internal Path law.
    return Adjacency({0: [(0, 1), (1, 2)], 1: [(1, 2), (0, 3)], 2: [(0, 3), (1, 0)], 3: [(1, 0), (0, 1)]})


def _one_step(model, adjacency=None):
    h, r, t = _triples()
    negatives = torch.tensor([[2, 3], [0, 3], [0, 1], [1, 2]], dtype=torch.long)
    optimizer = torch.optim.AdamW(build_optimizer_param_groups(model, lr=0.01, router_lr_multiplier=5.0))
    optimizer.zero_grad(set_to_none=True)
    positive = model.score_positive(h, r, t, adjacency, seed=0, training=True)
    negative = model.score_tail_candidates(h, r, negatives, adjacency, seed=0, training=True, gold_tail_ids=t)
    loss = negative_sampling_loss(positive, negative, adversarial_temperature=1.0)
    loss.backward()
    return loss, model


def test_standalone_path_internal_gradient_is_nonzero_on_first_batch():
    torch.manual_seed(7)
    model = SeionKGRv26(
        num_entities=4, num_relations_total=4, dim=8, base_expert="tucker",
        enable_path=True, path_rank=4, path_layers=1, path_max_neighbors=4,
        path_selector_mode="full_neighborhood", standalone_mode="end_to_end",
    )
    loss, model = _one_step(model, _adjacency())
    assert torch.isfinite(loss)
    assert model.use_base_scorer is False
    assert model.base.W.requires_grad is False
    assert model.path_reasoner.mu.A.weight.grad is not None
    assert model.path_reasoner.mu.A.weight.grad.norm().item() > 0.0
    assert model.path_scale_raw.weight.grad is not None
    assert torch.allclose(model._positive_scale(model.path_scale_raw, torch.tensor([0])), torch.ones(1), atol=1e-4)


def test_standalone_seion_internal_gradient_is_nonzero_on_first_batch():
    torch.manual_seed(11)
    model = SeionKGRv26(
        num_entities=4, num_relations_total=4, dim=8, base_expert="tucker",
        enable_seion=True, seion_rank=4, standalone_mode="end_to_end",
    )
    loss, model = _one_step(model)
    assert torch.isfinite(loss)
    assert model.use_base_scorer is False
    assert model.base.W.requires_grad is False
    assert model.seion_scorer.A.weight.grad is not None
    assert model.seion_scorer.A.weight.grad.norm().item() > 0.0
    assert model.seion_scale_raw.weight.grad is not None


def test_warm_started_decoder_mode_has_zero_base_contribution_and_finite_scores():
    torch.manual_seed(13)
    model = SeionKGRv26(
        num_entities=4, num_relations_total=4, dim=8, base_expert="tucker",
        enable_seion=True, seion_rank=4, standalone_mode="warm_started_decoder",
    )
    h, r, t = _triples()
    scores, breakdown = model.score_positive(h, r, t, return_breakdown=True)
    assert torch.isfinite(scores).all()
    assert torch.allclose(breakdown["s_base"], torch.zeros_like(breakdown["s_base"]))
    assert torch.isfinite(breakdown["eta_seion"]).all()
    assert float(scores.std().item()) > 0.0
