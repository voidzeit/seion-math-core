"""Validation-fitted score normalization and convex ensembles."""

from __future__ import annotations

import torch


def normalize_relation_scores(scores: torch.Tensor, relation_ids: torch.Tensor, eps: float = 1e-6) -> torch.Tensor:
    if scores.ndim != 3 or relation_ids.shape != (scores.shape[1],):
        raise ValueError("scores must be [M,B,N] and relation_ids must be [B]")
    result = torch.empty_like(scores)
    for relation in torch.unique(relation_ids):
        rows = relation_ids == relation
        values = scores[:, rows, :]
        mean = values.mean(dim=(1, 2), keepdim=True)
        std = values.std(dim=(1, 2), keepdim=True, unbiased=False)
        result[:, rows, :] = (values - mean) / (std + eps)
    return result


def weighted_score_ensemble(scores: torch.Tensor, weights: torch.Tensor) -> torch.Tensor:
    if scores.ndim != 3 or weights.shape != (scores.shape[0],):
        raise ValueError("scores must be [M,B,N] and weights must be [M]")
    if torch.any(weights < 0) or not torch.isfinite(weights).all():
        raise ValueError("weights must be finite and non-negative")
    normalized = weights / weights.sum().clamp_min(torch.finfo(weights.dtype).eps)
    return torch.einsum("m,mbn->bn", normalized, scores)
