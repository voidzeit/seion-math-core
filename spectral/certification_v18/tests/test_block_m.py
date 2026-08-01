from __future__ import annotations

import math

import pytest
import torch

from spectral.certification_v18.blocks.block_m_persistent_factorization import (
    hosvd_signature,
    hosvd_signature_distance,
    persistence_across_resolutions,
    principal_angles,
)


def _low_rank_tensor(seed: int, n: int = 8, true_rank: int = 2) -> torch.Tensor:
    gen = torch.Generator().manual_seed(seed)
    factors = [torch.randn(n, true_rank, generator=gen, dtype=torch.float64) for _ in range(3)]
    core = torch.randn(true_rank, true_rank, true_rank, generator=gen, dtype=torch.float64)
    return torch.einsum("ia,jb,kc,abc->ijk", factors[0], factors[1], factors[2], core)


def test_requires_at_least_three_resolutions():
    tensors = {0: _low_rank_tensor(0), 1: _low_rank_tensor(1)}
    with pytest.raises(ValueError, match="at least three"):
        persistence_across_resolutions(tensors)


def test_hosvd_mode_energy_recovers_true_low_rank():
    t = _low_rank_tensor(0, n=10, true_rank=2)
    sig = hosvd_signature(t, energy_threshold=0.999)
    for mode in sig.mode_energies:
        assert mode["rank_needed"] <= 3, "a true rank-2 tensor should need a small mode rank to hit 99.9% energy"


def test_identical_tensor_has_near_zero_principal_angle_to_itself():
    t = _low_rank_tensor(0, n=8, true_rank=2)
    sig_a = hosvd_signature(t, seed=0)
    sig_b = hosvd_signature(t, seed=0)
    distances = hosvd_signature_distance(sig_a, sig_b)
    for d in distances:
        assert d.max_angle_rad < 1e-6


def test_persistence_across_three_resolutions_reports_full_pairwise_matrix():
    tensors = {s: _low_rank_tensor(s, n=10, true_rank=2) for s in (0, 1, 2)}
    result = persistence_across_resolutions(tensors)
    assert set(result["pairwise"].keys()) == {"0_vs_1", "0_vs_2", "1_vs_2"}
    assert result["mean_max_principal_angle_rad_across_all_pairs"] is not None


def test_genuinely_different_random_subspaces_show_large_principal_angles():
    """The negative control this block's development actually caught: an
    earlier version of this comparison used free-unitary Procrustes on the
    left-singular-vector bases directly, which is exactly satisfiable for
    ANY two same-size orthonormal k-frames (the unitary group acts
    transitively on them) regardless of whether the subspaces are related
    — it silently reported near-zero distance even for independent random
    subspaces. Principal angles do not have that failure mode."""
    gen = torch.Generator().manual_seed(42)
    u_a, _ = torch.linalg.qr(torch.randn(8, 2, generator=gen, dtype=torch.float64))
    gen2 = torch.Generator().manual_seed(99)
    u_b, _ = torch.linalg.qr(torch.randn(8, 2, generator=gen2, dtype=torch.float64))
    result = principal_angles(u_a.to(torch.complex128), u_b.to(torch.complex128))
    assert result.max_angle_rad > 0.3, "independent random 2-dim subspaces of an 8-dim space should not appear aligned"


def test_principal_angle_is_zero_for_the_same_subspace_under_a_within_subspace_rotation():
    """Principal angles must be invariant to re-choosing the orthonormal
    basis WITHIN the same subspace (unlike raw column-wise comparison)."""
    gen = torch.Generator().manual_seed(7)
    u_a, _ = torch.linalg.qr(torch.randn(8, 3, generator=gen, dtype=torch.float64))
    # rotate the 3 basis columns among themselves (still spans the same subspace)
    rot = torch.tensor(
        [[math.cos(0.7), -math.sin(0.7), 0.0], [math.sin(0.7), math.cos(0.7), 0.0], [0.0, 0.0, 1.0]],
        dtype=torch.float64,
    )
    u_b = u_a @ rot
    result = principal_angles(u_a.to(torch.complex128), u_b.to(torch.complex128))
    assert result.max_angle_rad < 1e-8
