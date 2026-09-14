from __future__ import annotations

import torch

from seion_kgr.sota.spectral_mixture import SpectralConditionalTensorMixture


def _model() -> SpectralConditionalTensorMixture:
    return SpectralConditionalTensorMixture(11, 5, entity_dim=8, relation_dim=8, experts=3, active_per_relation=2, expert_rank=4, core_basis=2)


def test_spectral_mixture_shapes_and_positive_candidate_parity():
    model = _model()
    h, r, t = torch.tensor([0, 1, 2]), torch.tensor([0, 1, 2]), torch.tensor([3, 4, 5])
    positive = model.score_positive(h, r, t)
    candidates = torch.stack((t, torch.tensor([6, 7, 8]), torch.tensor([9, 10, 0])), dim=1)
    scores = model.score_tail_candidates(h, r, candidates)
    assert positive.shape == (3,)
    assert scores.shape == (3, 3)
    assert torch.allclose(positive, scores[:, 0], atol=1e-5, rtol=1e-5)


def test_bases_are_orthonormal_and_routing_is_convex():
    model = _model()
    assert float(model.orthonormality_error().detach()) < 1e-5
    weights = model.routing_probabilities(torch.tensor([0, 1, 2]))
    assert torch.allclose(weights.sum(dim=1), torch.ones(3))


def test_mixture_is_lipschitz_infinity_norm_for_fixed_expert_scores():
    weights, tau = torch.tensor([0.2, 0.8]), torch.tensor(0.7)
    a, b = torch.tensor([1.2, -0.3]), torch.tensor([0.8, -0.1])
    f = lambda x: tau * torch.logsumexp(torch.log(weights) + x / tau, dim=0)
    assert abs(float(f(a) - f(b))) <= float((a - b).abs().max()) + 1e-6


def test_mixture_has_finite_gradients():
    model = _model()
    loss = model.score_positive(torch.tensor([0, 1, 2, 3]), torch.tensor([0, 1, 2, 3]), torch.tensor([4, 5, 6, 7])).sum()
    loss.backward()
    assert all(parameter.grad is None or torch.isfinite(parameter.grad).all() for parameter in model.parameters())
