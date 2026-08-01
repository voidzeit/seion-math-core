"""Fase 5/6: batched CP ternary law, Stiefel-parametrized projector, seionic scorer.

Vectorized ``nn.Module`` counterparts of the explicit-loop objects in
``seion_kgr_reference_fp64.py`` — same mathematics (contract §III, §XI,
§XXV), different implementation, so a divergence between the two would
be a real bug, not just a style difference. There is no code sharing
between the two paths — that is the point (independent implementation,
per the repo's existing discipline in `src/seion_core/research_v3`).
"""
from __future__ import annotations

import torch
import torch.nn as nn
import torch.nn.functional as F


class CPTernaryLaw(nn.Module):
    """``mu(x,a,q) = O[(Ax) o (Ba) o (Cq)]`` — contract §III, batched.

    Accepts ``x,a,q`` of shape ``[..., dim]`` (broadcastable), so it
    works for both a single positive triple ``[B,D]`` and a candidate
    block ``[B,K,D]``.
    """

    def __init__(self, dim_x: int, dim_a: int, dim_q: int, dim_out: int, rank: int):
        super().__init__()
        self.rank = rank
        self.A = nn.Linear(dim_x, rank, bias=False)
        self.B = nn.Linear(dim_a, rank, bias=False)
        self.C = nn.Linear(dim_q, rank, bias=False)
        self.O = nn.Linear(rank, dim_out, bias=False)
        for layer in (self.A, self.B, self.C, self.O):
            nn.init.xavier_uniform_(layer.weight)

    def forward(self, x: torch.Tensor, a: torch.Tensor, q: torch.Tensor) -> torch.Tensor:
        z = self.A(x) * self.B(a) * self.C(q)
        return self.O(z)

    def dense_equivalent(self) -> torch.Tensor:
        """``K[d,i,j,k] = sum_alpha O[d,alpha] A[alpha,i] B[alpha,j] C[alpha,k]``
        — for gauge/equivalence tests only (Gate 1), not for training."""
        return torch.einsum(
            "da,ai,aj,ak->dijk",
            self.O.weight, self.A.weight, self.B.weight, self.C.weight,
        )

    @torch.no_grad()
    def permute_components_(self, perm: list[int]) -> None:
        """In-place permutation of the rank/component axis (contract §V
        gauge group, permutation half — the batched counterpart of
        ``seion_kgr_reference_fp64.CPTernaryLaw.permute_components``).
        Must leave ``dense_equivalent()`` unchanged."""
        if sorted(perm) != list(range(self.rank)):
            raise ValueError(f"perm must be a permutation of range({self.rank}), got {perm}")
        idx = torch.tensor(perm, dtype=torch.long)
        self.A.weight.copy_(self.A.weight[idx])
        self.B.weight.copy_(self.B.weight[idx])
        self.C.weight.copy_(self.C.weight[idx])
        self.O.weight.copy_(self.O.weight[:, idx])


class StiefelProjector(nn.Module):
    """``Q`` on the Stiefel manifold via QR retraction (contract §XXV),
    ``P = Q Q^T``. ``rank=0`` disables projection (acts as identity)."""

    def __init__(self, dim: int, rank: int):
        super().__init__()
        self.dim = dim
        self.rank = rank
        if rank > 0:
            raw = torch.randn(dim, rank) / (dim ** 0.5)
            self.raw = nn.Parameter(raw)
        else:
            self.raw = None

    @property
    def enabled(self) -> bool:
        return self.rank > 0

    def Q(self) -> torch.Tensor:
        """``torch.linalg.qr`` always returns ``Q`` with orthonormal
        columns regardless of the sign convention on ``R``'s diagonal —
        no sign correction is needed (or should be attempted) for
        ``Q^T Q = I`` to hold; an earlier version here "fixed" the sign
        with ``torch.sign(...).clamp_min(1e-12)``, which silently
        replaced any negative sign with ``1e-12`` and shrank that
        column to near zero, breaking orthonormality after training."""
        if not self.enabled:
            raise RuntimeError("projector disabled (rank=0)")
        q, _ = torch.linalg.qr(self.raw)
        return q

    def P(self) -> torch.Tensor:
        q = self.Q()
        return q @ q.T

    def apply(self, x: torch.Tensor) -> torch.Tensor:
        if not self.enabled:
            return x
        return x @ self.P().T

    @torch.no_grad()
    def isometry_residual(self) -> float:
        if not self.enabled:
            return 0.0
        q = self.Q()
        return float(torch.linalg.norm(q.T @ q - torch.eye(self.rank, device=q.device)).item())

    @torch.no_grad()
    def idempotent_residual(self) -> float:
        if not self.enabled:
            return 0.0
        p = self.P()
        return float(torch.linalg.norm(p @ p - p).item())


def closure_leakage(projector: StiefelProjector, ambient_output: torch.Tensor) -> torch.Tensor:
    """``r_mu = (I-P) mu(...)`` — contract §VI/§IX, retyped for messages."""
    if not projector.enabled:
        return torch.zeros_like(ambient_output[..., :0])
    return ambient_output - projector.apply(ambient_output)


class SeionicScalarScorer(nn.Module):
    """``s_seion(h,r,t) = <q_seion(h,r), T e_t>`` — contract §XI/§XX.2.

    ``score_tail_candidates`` uses the batched-matrix form
    ``S(h,r,:) = q_seion (TE)^T``, never materializing a ``[B,K,rank]``
    intermediate — the exact inefficiency flagged in the v25 postmortem
    (`SEION_V25_DESIGN.md` §4) for the CP branch's head-candidate path.
    """

    def __init__(self, dim_e: int, dim_r: int, dim_q: int, rank: int):
        super().__init__()
        self.A = nn.Linear(dim_e, rank, bias=False)
        self.B = nn.Linear(dim_r, rank, bias=False)
        self.C = nn.Linear(dim_r, rank, bias=False)
        self.O = nn.Linear(rank, dim_q, bias=False)
        self.T = nn.Linear(dim_e, dim_q, bias=False)
        for layer in (self.A, self.B, self.C, self.O, self.T):
            nn.init.xavier_uniform_(layer.weight)

    def q_seion(self, h: torch.Tensor, r: torch.Tensor, c: torch.Tensor) -> torch.Tensor:
        z = self.A(h) * self.B(r) * self.C(c)
        return self.O(z)

    def score_positive(self, h: torch.Tensor, r: torch.Tensor, c: torch.Tensor, t: torch.Tensor) -> torch.Tensor:
        q = self.q_seion(h, r, c)
        return (q * self.T(t)).sum(dim=-1)

    def score_tail_candidates(self, h: torch.Tensor, r: torch.Tensor, c: torch.Tensor, candidates: torch.Tensor) -> torch.Tensor:
        q = self.q_seion(h, r, c)  # [B, dim_q]
        if candidates.ndim == 2:
            TE = self.T(candidates)  # [K, dim_q] — shared across the batch
            return q @ TE.T
        if candidates.ndim == 3:
            TE = self.T(candidates)  # [B, K, dim_q]
            return torch.einsum("bd,bkd->bk", q, TE)
        raise ValueError(f"candidates must be [K,D] or [B,K,D], got {tuple(candidates.shape)}")
