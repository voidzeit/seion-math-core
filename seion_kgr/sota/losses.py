"""Discovery losses kept separate from certified training losses."""

from __future__ import annotations

import torch
import torch.nn.functional as F


def listwise_loss(positive: torch.Tensor, negatives: torch.Tensor, temperature: float = 0.07) -> torch.Tensor:
    if temperature <= 0:
        raise ValueError("temperature must be positive")
    logits = torch.cat((positive.unsqueeze(1), negatives), dim=1) / temperature
    labels = torch.zeros(positive.shape[0], dtype=torch.long, device=positive.device)
    return F.cross_entropy(logits, labels)


def margin_distillation_loss(teacher_positive: torch.Tensor, teacher_negative: torch.Tensor, student_positive: torch.Tensor, student_negative: torch.Tensor, *, weights: torch.Tensor | None = None) -> torch.Tensor:
    teacher_margin = teacher_positive.unsqueeze(1) - teacher_negative
    student_margin = student_positive.unsqueeze(1) - student_negative
    error = (student_margin - teacher_margin.detach()).pow(2)
    if weights is not None:
        if weights.shape != (teacher_negative.shape[1],):
            raise ValueError("weights must be [K]")
        error = error * (weights / weights.sum().clamp_min(torch.finfo(error.dtype).eps)).unsqueeze(0)
    return error.mean()
