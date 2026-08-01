"""Gauge-invariant comparison utilities for blocks J (tensor interscale) and
L (gauge canonicalization).

Mission diagnosis for J: the legacy comparison (`canonical_gauge_from_tensor`
+ `tensor_diff_rel`, legacy script ~line 433/1651) applies ONE specific
gauge-fixing heuristic (a Gram-matrix eigenbasis) and reports a single
normalized distance. That conflates "the two tensors are gauge-equivalent"
with "this one heuristic's canonical form happens to agree" — a tensor pair
related by a *different* unitary than the eigenbasis heuristic finds would
be wrongly reported as non-persistent.

This module reports the several distances the mission asks be kept
separate, at the matrix (single-mode-unfolding) level:

- raw_distance: no alignment at all.
- amplitude_ratio: ||M_b||/||M_a||, reported separately from any distance.
- procrustes_aligned_distance: the classic orthogonal Procrustes solution,
  Q* = argmin_{Q unitary} ||M_b - Q @ M_a||_F, solved in closed form via the
  SVD of M_b @ M_a^H (Q* = U @ V^H where M_b @ M_a^H = U @ S @ V^H). This is
  the actual gauge-invariant distance for a single mode unfolding.
- permutation_aligned_distance: best distance over the (small, exhaustively
  searched) permutation-only subgroup of the unitary group, relevant when
  the true residual gauge is a permutation of an orthonormal basis rather
  than a general rotation.

Scope note: the true reduced-tensor gauge freedom applies the SAME unitary
Q to every one of the tensor's `arity` legs simultaneously (not just one
mode unfolding independently) — a multilinear (not bilinear) Procrustes
problem. This module solves the single-mode-unfolding version, which is the
right invariant tool when comparing matrices (blocks A/D/L) and a
documented lower bound / diagnostic when comparing higher-arity tensors
mode-by-mode; the full same-Q-on-every-leg alternating-least-squares solver
is follow-up work (tracked in .ai/SPECTRAL_TRACK_ROADMAP.md), not silently
assumed solved here.

DO NOT apply `compare_with_gauge` to matrices whose COLUMNS are themselves
an orthonormal basis (e.g. HOSVD left singular vectors / subspace bases).
A free n x n unitary Q always exists mapping any orthonormal k-frame to any
other same-size orthonormal k-frame exactly (the unitary group acts
transitively on the Stiefel manifold), so Procrustes on such inputs is
mathematically vacuous — it will report near-zero distance even for
completely unrelated subspaces. This was caught by this suite's own
negative control during block M's development (see
`block_m_persistent_factorization.py`'s `principal_angles`, which is the
correct tool for comparing SUBSPACES; `compare_with_gauge` is for comparing
general matrices/tensor-unfoldings that are not themselves orthonormal
bases, e.g. an actual reduced-tensor mode unfolding).
"""

from __future__ import annotations

import itertools
from dataclasses import dataclass

import torch


@dataclass
class GaugeComparisonResult:
    raw_distance: float
    amplitude_ratio: float
    procrustes_aligned_distance: float
    permutation_aligned_distance: float | None
    permutation_search_exhaustive: bool


def _fro(x: torch.Tensor) -> torch.Tensor:
    return torch.linalg.norm(x.reshape(-1))


def orthogonal_procrustes(m_a: torch.Tensor, m_b: torch.Tensor) -> torch.Tensor:
    """Closed-form unitary Q minimizing ||m_b - Q @ m_a||_F."""
    cross = m_b @ m_a.conj().T
    u, _, vh = torch.linalg.svd(cross)
    return u @ vh


def compare_with_gauge(m_a: torch.Tensor, m_b: torch.Tensor, *, max_exhaustive_perm_dim: int = 8) -> GaugeComparisonResult:
    if m_a.shape != m_b.shape:
        raise ValueError(f"shape mismatch: {m_a.shape} vs {m_b.shape}")

    norm_a = _fro(m_a).item()
    norm_b = _fro(m_b).item()
    raw_distance = (_fro(m_b - m_a) / (norm_a + 1e-30)).item()
    amplitude_ratio = norm_b / (norm_a + 1e-30)

    q_star = orthogonal_procrustes(m_a, m_b)
    aligned = q_star @ m_a
    procrustes_distance = (_fro(m_b - aligned) / (norm_a + 1e-30)).item()

    perm_distance = None
    exhaustive = False
    dim = m_a.shape[0]
    if m_a.shape[0] == m_a.shape[1] and dim <= max_exhaustive_perm_dim:
        best = None
        for perm in itertools.permutations(range(dim)):
            permuted = m_a[list(perm), :]
            d = (_fro(m_b - permuted) / (norm_a + 1e-30)).item()
            if best is None or d < best:
                best = d
        perm_distance = best
        exhaustive = True

    return GaugeComparisonResult(
        raw_distance=raw_distance,
        amplitude_ratio=amplitude_ratio,
        procrustes_aligned_distance=procrustes_distance,
        permutation_aligned_distance=perm_distance,
        permutation_search_exhaustive=exhaustive,
    )
