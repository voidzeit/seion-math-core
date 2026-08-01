"""Fase 8: associator + Filippov-identity diagnostics with a weight-gated curriculum.

Contract §V/§VII (source design note), CLM_KGR_006/CLM_KGR_008. These
are diagnostics, not certificates (`docs/definitions/associators.md`
keeps the two associator objects distinct; reducing FI energy does not
by itself establish a 3-Lie algebra, per assumption A10).

Fixes the specific v25 performance bug documented in
`SEION_V25_DESIGN.md` §3/§4: `filippov_embedding_loss` and
`associator_embedding_loss` there are gated on `samples <= 0`, not on
effective weight, so with the CLI defaults (`fi_samples=16`,
`fi_weight=0.0`) every batch still pays for 7 ternary-law evaluations
with zero loss contribution. Here every energy function takes the
*already-resolved effective weight* and returns an exact zero tensor
without evaluating `ternary_fn` at all when that weight is `<= 0`.
"""
from __future__ import annotations

from typing import Callable

import torch

TernaryFn = Callable[[torch.Tensor, torch.Tensor, torch.Tensor], torch.Tensor]


def effective_weight(base: float, epoch: int, warmup_epochs: int) -> float:
    if base <= 0:
        return 0.0
    if warmup_epochs <= 0:
        return float(base)
    return float(base) * min(1.0, float(epoch + 1) / float(warmup_epochs))


def _sample_rows(pool: torch.Tensor, count: int, generator: torch.Generator) -> torch.Tensor:
    idx = torch.randint(0, pool.shape[0], (count,), generator=generator, device=pool.device)
    return pool[idx]


def filippov_energy(
    ternary_fn: TernaryFn,
    pool: torch.Tensor,
    samples: int,
    effective_w: float,
    generator: torch.Generator,
) -> torch.Tensor:
    """Contract §VIII (source note): five-slot Filippov-identity residual energy.
    Returns an exact zero WITHOUT calling ``ternary_fn`` when
    ``effective_w <= 0`` — this is the fix for the v25 perf bug."""
    if effective_w <= 0 or samples <= 0:
        return pool.new_zeros(())
    s = min(int(samples), max(1, pool.shape[0]))
    a, b, x, c, d = (_sample_rows(pool, s, generator) for _ in range(5))
    xcd = ternary_fn(x, c, d)
    abx = ternary_fn(a, b, x)
    abc = ternary_fn(a, b, c)
    abd = ternary_fn(a, b, d)
    lhs = ternary_fn(a, b, xcd)
    rhs = ternary_fn(abx, c, d) + ternary_fn(x, abc, d) + ternary_fn(x, c, abd)
    numerator = (lhs - rhs).float().pow(2).sum(dim=-1)
    denominator = lhs.float().pow(2).sum(dim=-1) + rhs.float().pow(2).sum(dim=-1)
    return (numerator / denominator.clamp_min(1e-12)).mean()


def associator_energy(
    ternary_fn: TernaryFn,
    pool: torch.Tensor,
    samples: int,
    effective_w: float,
    generator: torch.Generator,
) -> torch.Tensor:
    """Contract §V / `docs/definitions/associators.md`: the FIVE-input
    associator ``A^(5)``, kept distinct from the anchored binary
    associator (not implemented here — different object, different domain)."""
    if effective_w <= 0 or samples <= 0:
        return pool.new_zeros(())
    s = min(int(samples), max(1, pool.shape[0]))
    x1, x2, x3, x4, x5 = (_sample_rows(pool, s, generator) for _ in range(5))
    inner_left = ternary_fn(x1, x2, x3)
    inner_right = ternary_fn(x3, x4, x5)
    left = ternary_fn(inner_left, x4, x5)
    right = ternary_fn(x1, x2, inner_right)
    numerator = (left - right).float().pow(2).sum(dim=-1)
    denominator = left.float().pow(2).sum(dim=-1) + right.float().pow(2).sum(dim=-1)
    return (numerator / denominator.clamp_min(1e-12)).mean()


def geometric_curriculum_weights(
    epoch: int,
    assoc_weight: float, assoc_warmup: int,
    fi_weight: float, fi_warmup: int,
    closure_weight: float, closure_warmup: int,
) -> dict:
    """Contract §IV (curriculum): closure -> associator -> FI, staggered.
    Per the source note's schedule (epochs 0-5 KGE+path, 6-10 tiny
    closure, 11-15 tiny associator, 16+ FI only if validation holds),
    this returns the *effective* weight for the current epoch; the
    caller is responsible for gating FI on validation not regressing —
    that requires the training loop's own state, not this pure function.
    """
    return {
        "closure": effective_weight(closure_weight, epoch, closure_warmup),
        "assoc": effective_weight(assoc_weight, epoch, assoc_warmup),
        "fi": effective_weight(fi_weight, epoch, fi_warmup),
    }
