"""Accuracy-first discovery primitives for KGE experiments.

This module is deliberately separate from the certified confirmatory track.
It provides deterministic, model-agnostic pieces needed for discovery:

* top-k hard-negative mining from an already computed candidate score matrix;
* temperature-scaled InfoNCE over one positive and many negatives;
* weighted pairwise/listwise margin loss for top-ranking candidates;
* a small EMA state update and an entity-vector queue.

The queue stores snapshots, not live model parameters.  It therefore never
changes the frozen-confirmatory semantics and must be explicitly enabled by a
discovery runner.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable

import torch
import torch.nn as nn
import torch.nn.functional as F


def mine_hard_negatives(
    scores: torch.Tensor,
    candidate_ids: torch.Tensor,
    gold_ids: torch.Tensor,
    k: int,
    *,
    forbidden: torch.Tensor | None = None,
) -> tuple[torch.Tensor, torch.Tensor]:
    """Return the highest-scoring non-gold candidates per query.

    Parameters
    ----------
    scores:
        ``[B, N]`` candidate scores.
    candidate_ids:
        ``[N]`` shared IDs or ``[B, N]`` row-specific IDs.
    gold_ids:
        ``[B]`` positive entity IDs.
    k:
        Number of negatives to return.  It is clipped to ``N-1``.
    forbidden:
        Optional boolean mask with shape ``[B, N]``.  Forbidden candidates
        are excluded, except that the caller remains responsible for keeping
        the gold candidate available in the positive path.
    """
    if scores.ndim != 2:
        raise ValueError(f"scores must be [B,N], got {tuple(scores.shape)}")
    if candidate_ids.ndim not in (1, 2):
        raise ValueError("candidate_ids must be [N] or [B,N]")
    batch, n = scores.shape
    if candidate_ids.shape[-1] != n:
        raise ValueError("candidate_ids and scores disagree on N")
    if gold_ids.shape != (batch,):
        raise ValueError("gold_ids must have shape [B]")
    if k <= 0:
        raise ValueError("k must be positive")
    if forbidden is not None and forbidden.shape != scores.shape:
        raise ValueError("forbidden must have shape [B,N]")

    ids = candidate_ids if candidate_ids.ndim == 2 else candidate_ids.unsqueeze(0).expand(batch, -1)
    valid = torch.ones_like(scores, dtype=torch.bool)
    valid &= ids != gold_ids.unsqueeze(1)
    if forbidden is not None:
        valid &= ~forbidden
    masked = scores.masked_fill(~valid, -torch.inf)
    take = min(int(k), max(1, n - 1))
    hard_scores, positions = torch.topk(masked, k=take, dim=1)
    hard_ids = ids.gather(1, positions)
    return hard_ids, hard_scores


def info_nce_loss(
    positive: torch.Tensor,
    negatives: torch.Tensor,
    temperature: float = 0.07,
) -> torch.Tensor:
    """Compute stable InfoNCE for ``[B]`` positives and ``[B,K]`` negatives."""
    if positive.ndim != 1 or negatives.ndim != 2 or negatives.shape[0] != positive.shape[0]:
        raise ValueError("positive must be [B] and negatives must be [B,K]")
    if temperature <= 0:
        raise ValueError("temperature must be positive")
    logits = torch.cat((positive.unsqueeze(1), negatives), dim=1) / float(temperature)
    labels = torch.zeros(positive.shape[0], dtype=torch.long, device=positive.device)
    return F.cross_entropy(logits, labels)


def weighted_margin_loss(
    positive: torch.Tensor,
    negatives: torch.Tensor,
    margin: float = 1.0,
    *,
    decay: float = 0.0,
) -> torch.Tensor:
    """Top-weighted pairwise margin loss.

    ``decay=0`` gives equal weights.  Positive decay emphasizes earlier
    columns, which are expected to be ordered from hardest to easiest.
    """
    if positive.ndim != 1 or negatives.ndim != 2 or negatives.shape[0] != positive.shape[0]:
        raise ValueError("positive must be [B] and negatives must be [B,K]")
    if margin < 0 or decay < 0:
        raise ValueError("margin and decay must be non-negative")
    weights = torch.exp(-float(decay) * torch.arange(negatives.shape[1], device=negatives.device, dtype=negatives.dtype))
    weights = weights / weights.sum().clamp_min(torch.finfo(negatives.dtype).eps)
    violations = F.relu(float(margin) - positive.unsqueeze(1) + negatives)
    return (violations * weights.unsqueeze(0)).sum(dim=1).mean()


def update_ema_(target: nn.Module, online: nn.Module, momentum: float) -> None:
    """Update ``target`` parameters/buffers from ``online`` in-place."""
    if not 0.0 <= momentum < 1.0:
        raise ValueError("momentum must be in [0,1)")
    target_state = target.state_dict()
    online_state = online.state_dict()
    if target_state.keys() != online_state.keys():
        raise ValueError("target and online modules must have identical state keys")
    with torch.no_grad():
        for key, target_value in target_state.items():
            online_value = online_state[key]
            if target_value.shape != online_value.shape:
                raise ValueError(f"state shape mismatch for {key}")
            if target_value.is_floating_point():
                target_value.mul_(momentum).add_(online_value, alpha=1.0 - momentum)
            else:
                target_value.copy_(online_value)


@dataclass
class EntityVectorQueue:
    """Fixed-size FIFO queue of momentum/teacher entity snapshots."""

    capacity: int
    dim: int
    device: torch.device | str = "cpu"

    def __post_init__(self) -> None:
        if self.capacity <= 0 or self.dim <= 0:
            raise ValueError("capacity and dim must be positive")
        self.device = torch.device(self.device)
        self.ids = torch.full((self.capacity,), -1, dtype=torch.long, device=self.device)
        self.vectors = torch.zeros((self.capacity, self.dim), dtype=torch.float32, device=self.device)
        self.size = 0
        self.pointer = 0

    @torch.no_grad()
    def enqueue(self, ids: torch.Tensor, vectors: torch.Tensor) -> None:
        if ids.ndim != 1 or vectors.ndim != 2 or vectors.shape != (ids.numel(), self.dim):
            raise ValueError("ids must be [B] and vectors must be [B,dim]")
        if ids.numel() == 0:
            return
        ids = ids.detach().to(device=self.device, dtype=torch.long)
        vectors = vectors.detach().to(device=self.device, dtype=self.vectors.dtype)
        if ids.numel() >= self.capacity:
            ids = ids[-self.capacity :]
            vectors = vectors[-self.capacity :]
        count = int(ids.numel())
        end = min(self.capacity - self.pointer, count)
        self.ids[self.pointer : self.pointer + end] = ids[:end]
        self.vectors[self.pointer : self.pointer + end] = vectors[:end]
        if end < count:
            rest = count - end
            self.ids[:rest] = ids[end:]
            self.vectors[:rest] = vectors[end:]
        self.pointer = (self.pointer + count) % self.capacity
        self.size = min(self.capacity, self.size + count)

    def snapshot(self) -> tuple[torch.Tensor, torch.Tensor]:
        """Return valid queue entries in FIFO order."""
        if self.size < self.capacity:
            return self.ids[: self.size].clone(), self.vectors[: self.size].clone()
        order = torch.arange(self.capacity, device=self.device)
        order = (order + self.pointer) % self.capacity
        return self.ids[order].clone(), self.vectors[order].clone()

