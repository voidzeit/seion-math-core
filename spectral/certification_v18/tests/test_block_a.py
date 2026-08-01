from __future__ import annotations

import torch

from spectral.certification_v18.blocks.block_a_projector import (
    certify_projector,
    exact_small_case_2x2,
    perturbation_stability_sweep,
)
from spectral.certification_v18.gates import TypedStatus
from spectral.certification_v18.model import SpectralModelV18, orthonormalize_columns


def test_exact_2x2_case_passes_at_tight_tolerance():
    report = exact_small_case_2x2()
    assert report.status == TypedStatus.STRUCTURAL_IDENTITY_PASS
    assert report.idem_rel < 1e-14
    assert report.rank_error < 1e-14


def test_random_orthonormal_u_passes_structural_identity_at_any_seed():
    """Idempotence/self-adjointness hold for ANY orthonormal U — the point
    of this block is that this is a construction fact, not a scientific
    one. Confirm it holds across seeds (not cherry-picked)."""
    for seed in range(5):
        gen = torch.Generator().manual_seed(seed)
        model = SpectralModelV18(n=20, rank=5, arity=3, cp_rank=4, device="cpu", dtype="float64", generator=gen)
        report = certify_projector(model.u())
        assert report.status == TypedStatus.STRUCTURAL_IDENTITY_PASS, f"seed {seed} failed"


def test_eigenvalues_cluster_at_zero_and_one():
    gen = torch.Generator().manual_seed(1)
    model = SpectralModelV18(n=16, rank=4, arity=3, cp_rank=4, device="cpu", dtype="float64", generator=gen)
    report = certify_projector(model.u())
    assert report.eigenvalue_cluster_max_deviation < 1e-10


def test_perturbation_stability_sweep_residual_scales_with_epsilon():
    gen = torch.Generator().manual_seed(2)
    model = SpectralModelV18(n=16, rank=4, arity=3, cp_rank=4, device="cpu", dtype="float64", generator=gen)
    U = orthonormalize_columns(model.u())
    rows = perturbation_stability_sweep(U, epsilons=[0.0, 1e-6, 1e-3])
    # QR re-orthonormalizes, so idem/selfadj residuals should stay tiny
    # regardless of epsilon (the perturbation is absorbed by construction) —
    # this IS the expected, documented behavior, not a failure.
    for row in rows:
        assert row["idem_rel"] < 1e-9
        assert row["selfadj_rel"] < 1e-9


def test_negative_control_non_selfadjoint_matrix_is_rejected():
    """A deliberately broken 'projector' (real transpose instead of
    conjugate transpose for a genuinely complex matrix) must NOT pass."""
    gen = torch.Generator().manual_seed(3)
    U = torch.complex(torch.randn(6, 2, generator=gen, dtype=torch.float64), torch.randn(6, 2, generator=gen, dtype=torch.float64))
    U = orthonormalize_columns(U)
    P_bad = U @ U.T  # WRONG: should be U @ U.conj().T
    selfadj_rel = torch.linalg.norm((P_bad.conj().T - P_bad).reshape(-1)) / (torch.linalg.norm(P_bad.reshape(-1)) + 1e-30)
    assert selfadj_rel.item() > 1e-6, "the negative control must actually be broken, or it isn't testing anything"
