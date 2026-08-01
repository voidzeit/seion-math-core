"""Negative-sampling loss (contract §XXII) and N3 regularization (§XXIII)."""
from __future__ import annotations

import torch
import torch.nn.functional as F


def negative_sampling_loss(positive: torch.Tensor, negative: torch.Tensor, adversarial_temperature: float) -> torch.Tensor:
    """Self-adversarial logistic loss (contract §XXII, BCE variant)."""
    positive_loss = F.softplus(-positive)
    if adversarial_temperature > 0:
        weights = F.softmax(negative.detach() * float(adversarial_temperature), dim=1)
        negative_loss = (weights * F.softplus(negative)).sum(dim=1)
    else:
        negative_loss = F.softplus(negative).mean(dim=1)
    return (positive_loss + negative_loss).mean()


def n3_regularizer(*embeddings: torch.Tensor) -> torch.Tensor:
    """Contract §XXIII: ``sum ||e||_3^3`` over the given embedding batches."""
    total = embeddings[0].new_zeros(())
    for e in embeddings:
        total = total + e.float().abs().pow(3).sum(dim=-1).mean()
    return total
