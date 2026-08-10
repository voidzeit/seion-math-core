"""Query-dependent convex expert gate."""

from __future__ import annotations

import torch
import torch.nn as nn


class QueryGate(nn.Module):
    def __init__(self, input_dim: int, experts: int, hidden_dim: int = 64):
        super().__init__()
        if input_dim <= 0 or experts <= 0 or hidden_dim <= 0:
            raise ValueError("gate dimensions must be positive")
        self.network = nn.Sequential(nn.Linear(input_dim, hidden_dim), nn.GELU(), nn.Linear(hidden_dim, experts))

    def forward(self, features: torch.Tensor) -> torch.Tensor:
        if features.ndim != 2:
            raise ValueError("features must be [B,F]")
        return torch.softmax(self.network(features), dim=-1)
