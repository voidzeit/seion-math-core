"""Fase 6: projection audit — periodic Gate 1 checks + closure-leakage logging.

``StiefelProjector`` itself lives in ``kernels.py`` (it is used by both
the reasoner's message-passing layer and, in principle, any future
scorer branch that needs a reduced subspace). This module only adds the
audit/logging layer the contract's reproducibility section requires:
``projection_audit.json`` per run (contract §XV).
"""
from __future__ import annotations

from typing import Any, Dict, Mapping

import torch

from .kernels import StiefelProjector, closure_leakage


def audit_projectors(projectors: Mapping[str, StiefelProjector]) -> Dict[str, Any]:
    """Gate 1 identities for every named projector in the model, in FP32/64
    as stored (this is a training-time spot check, not the FP64 oracle's
    definitive certificate — see ``seion_kgr_reference_fp64.py`` for that)."""
    out: Dict[str, Any] = {}
    for name, proj in projectors.items():
        if not proj.enabled:
            out[name] = {"enabled": False}
            continue
        out[name] = {
            "enabled": True,
            "rank": proj.rank,
            "dim": proj.dim,
            "isometry_residual": proj.isometry_residual(),
            "idempotent_residual": proj.idempotent_residual(),
        }
    return out


@torch.no_grad()
def measure_closure_leakage_sample(
    projector: StiefelProjector, ambient_samples: torch.Tensor
) -> Dict[str, float]:
    """Sample-mean closure leakage ratio (contract §VI): a training-time
    proxy, NOT a certified bound on ``rho_mu`` (operator norm) — see
    ``docs/definitions/projectors.md`` and CLM_KGR_009's limitation."""
    if not projector.enabled or ambient_samples.numel() == 0:
        return {"mean_ratio": 0.0, "samples": 0}
    leak = closure_leakage(projector, ambient_samples)
    numerator = leak.float().pow(2).sum(dim=-1)
    denominator = ambient_samples.float().pow(2).sum(dim=-1).clamp_min(1e-12)
    ratio = (numerator / denominator).mean().item()
    return {"mean_ratio": float(ratio), "samples": int(ambient_samples.shape[0])}
