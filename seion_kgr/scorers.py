"""Fase 3 expert base: reciprocal DistMult / ComplEx / CP / TuckER.

Contract §XI.1: "no necesariamente todos activos en producción. Su
función es proporcionar un piso predictivo fuerte y controles
estandarizados." Every expert exposes the same two-method interface so
``model.py`` can combine them uniformly:

    score_positive(h, r, t) -> [B]
    score_tail_candidates(h, r, candidates) -> [B, K]

Head-candidate scoring is never implemented separately: contract §II.3.2
makes it unnecessary — ``score_head_candidates(candidates, r, t)`` is
exactly ``score_tail_candidates(t, r_inverse, candidates)``. This is the
whole point of reciprocal closure and is wired once, centrally, in
``evaluate.py``, not duplicated per-expert.
"""
from __future__ import annotations

import math
from typing import Tuple

import torch
import torch.nn as nn
import torch.nn.functional as F


def _expand_candidates(candidates: torch.Tensor, batch: int) -> torch.Tensor:
    if candidates.ndim == 2:
        return candidates.unsqueeze(0).expand(batch, -1, -1)
    if candidates.ndim == 3 and candidates.shape[0] == batch:
        return candidates
    raise ValueError(f"candidates must be [K,D] or [B,K,D], got {tuple(candidates.shape)}")


class DistMultExpert(nn.Module):
    """``s(h,r,t) = sum(h*r*t)``. Deliberately weak baseline/control."""

    def score_positive(self, h: torch.Tensor, r: torch.Tensor, t: torch.Tensor) -> torch.Tensor:
        return (h * r * t).sum(dim=-1)

    def score_tail_candidates(self, h: torch.Tensor, r: torch.Tensor, candidates: torch.Tensor) -> torch.Tensor:
        cand = _expand_candidates(candidates, h.shape[0]).to(h.dtype)
        return torch.einsum("bd,bkd->bk", h * r, cand)


class ComplExExpert(nn.Module):
    """Reciprocal ComplEx (contract §XX.1). Embeddings are ``[..., 2*D]``
    with the first half real, second half imaginary — no complex dtype
    needed."""

    def _split(self, x: torch.Tensor) -> Tuple[torch.Tensor, torch.Tensor]:
        d = x.shape[-1] // 2
        return x[..., :d], x[..., d:]

    def score_positive(self, h: torch.Tensor, r: torch.Tensor, t: torch.Tensor) -> torch.Tensor:
        h_re, h_im = self._split(h)
        r_re, r_im = self._split(r)
        t_re, t_im = self._split(t)
        real = (h_re * r_re * t_re) + (h_im * r_re * t_im) + (h_re * r_im * t_im) - (h_im * r_im * t_re)
        return real.sum(dim=-1)

    def score_tail_candidates(self, h: torch.Tensor, r: torch.Tensor, candidates: torch.Tensor) -> torch.Tensor:
        cand = _expand_candidates(candidates, h.shape[0]).to(h.dtype)
        h_re, h_im = self._split(h)
        r_re, r_im = self._split(r)
        t_re, t_im = self._split(cand)
        # q = (h_re*r_re - h_im*r_im, h_re*r_im + h_im*r_re); score = <q, t>
        q_re = (h_re * r_re - h_im * r_im).unsqueeze(1)
        q_im = (h_re * r_im + h_im * r_re).unsqueeze(1)
        return (q_re * t_re + q_im * t_im).sum(dim=-1)


class CPExpert(nn.Module):
    """Reciprocal CP / canonical decomposition (Lacroix et al. 2018):
    asymmetric head-role/tail-role embeddings, unlike DistMult's shared
    table. ``t_tail`` must be passed already looked up from the
    tail-role table by the caller."""

    def score_positive(self, h_head: torch.Tensor, r: torch.Tensor, t_tail: torch.Tensor) -> torch.Tensor:
        return (h_head * r * t_tail).sum(dim=-1)

    def score_tail_candidates(self, h_head: torch.Tensor, r: torch.Tensor, candidates_tail: torch.Tensor) -> torch.Tensor:
        cand = _expand_candidates(candidates_tail, h_head.shape[0]).to(h_head.dtype)
        return torch.einsum("bd,bkd->bk", h_head * r, cand)


class TuckERExpert(nn.Module):
    """``s(h,r,t) = W x1 h x2 r x3 t`` with a learned core tensor.

    Contract §XI.1. ``dim_e``/``dim_r`` may differ from the shared model
    dimension; here they are equal for simplicity (Fase 3 baseline, not
    a hyperparameter-search target).
    """

    def __init__(self, dim_e: int, dim_r: int):
        super().__init__()
        self.W = nn.Parameter(torch.zeros(dim_r, dim_e, dim_e))
        nn.init.xavier_uniform_(self.W, gain=1.0)
        self.bn0 = nn.BatchNorm1d(dim_e, affine=False)
        self.bn1 = nn.BatchNorm1d(dim_e, affine=False)

    def _wr(self, r: torch.Tensor) -> torch.Tensor:
        return torch.einsum("bd,dij->bij", r, self.W)  # [B, dim_e, dim_e]

    def score_positive(self, h: torch.Tensor, r: torch.Tensor, t: torch.Tensor) -> torch.Tensor:
        h_bn = self.bn0(h) if h.shape[0] > 1 else h
        wr = self._wr(r)
        hw = torch.einsum("bi,bij->bj", h_bn, wr)
        hw = self.bn1(hw) if hw.shape[0] > 1 else hw
        return (hw * t).sum(dim=-1)

    def score_tail_candidates(self, h: torch.Tensor, r: torch.Tensor, candidates: torch.Tensor) -> torch.Tensor:
        cand = _expand_candidates(candidates, h.shape[0]).to(h.dtype)
        h_bn = self.bn0(h) if h.shape[0] > 1 else h
        wr = self._wr(r)
        hw = torch.einsum("bi,bij->bj", h_bn, wr)
        hw = self.bn1(hw) if hw.shape[0] > 1 else hw
        return torch.einsum("bd,bkd->bk", hw, cand)
