"""No-gradient EMA teacher wrapper."""

from __future__ import annotations

import copy

import torch
import torch.nn as nn

from ..sota_discovery import update_ema_


class MomentumEncoder(nn.Module):
    def __init__(self, online: nn.Module, momentum: float = 0.999):
        super().__init__()
        if not 0.0 <= momentum < 1.0:
            raise ValueError("momentum must be in [0,1)")
        self.momentum = float(momentum)
        self.encoder = copy.deepcopy(online)
        for parameter in self.encoder.parameters():
            parameter.requires_grad_(False)
        self.encoder.eval()

    @torch.no_grad()
    def update(self, online: nn.Module) -> None:
        update_ema_(self.encoder, online, self.momentum)
        self.encoder.eval()

    def forward(self, *args, **kwargs):
        with torch.no_grad():
            return self.encoder(*args, **kwargs)
