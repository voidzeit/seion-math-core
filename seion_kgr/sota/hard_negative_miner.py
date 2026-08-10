"""Leakage-aware hard-negative selection."""

from __future__ import annotations

import torch

from ..sota_discovery import mine_hard_negatives


def mine_filtered_hard_negatives(scores: torch.Tensor, candidate_ids: torch.Tensor, gold_ids: torch.Tensor, known_positive_mask: torch.Tensor, k: int) -> tuple[torch.Tensor, torch.Tensor]:
    if known_positive_mask.dtype is not torch.bool:
        raise ValueError("known_positive_mask must be boolean")
    return mine_hard_negatives(scores, candidate_ids, gold_ids, k, forbidden=known_positive_mask)
