"""Deterministic multi-retriever candidate unions."""

from __future__ import annotations

import torch


def union_topk(score_matrices: list[torch.Tensor], k: int) -> torch.Tensor:
    if not score_matrices:
        raise ValueError("at least one score matrix is required")
    if k <= 0:
        raise ValueError("k must be positive")
    shape = score_matrices[0].shape
    if len(shape) != 2 or any(score.shape != shape for score in score_matrices):
        raise ValueError("score matrices must all have shape [B,N]")
    n = shape[1]
    top = min(k, n)
    pieces: list[torch.Tensor] = []
    values: list[torch.Tensor] = []
    for score in score_matrices:
        value, index = torch.topk(score, top, dim=1)
        pieces.append(index)
        values.append(value)
    merged = torch.full_like(score_matrices[0], -torch.inf)
    merged.scatter_reduce_(1, torch.cat(pieces, dim=1), torch.cat(values, dim=1), reduce="amax", include_self=True)
    return torch.topk(merged, min(n, len(score_matrices) * top), dim=1).indices


def recall_at_k(candidate_ids: torch.Tensor, gold_ids: torch.Tensor) -> float:
    if candidate_ids.ndim != 2 or gold_ids.shape != (candidate_ids.shape[0],):
        raise ValueError("candidate_ids must be [B,K] and gold_ids must be [B]")
    return float((candidate_ids == gold_ids.unsqueeze(1)).any(dim=1).float().mean().item())
