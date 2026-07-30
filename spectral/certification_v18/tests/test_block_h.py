from __future__ import annotations

import torch

from spectral.certification_v18.blocks.block_h_associator import (
    ambient_projected_normal_split,
    associator_constant_report,
)
from spectral.certification_v18.model import SpectralModelV18, orthonormalize_columns


def test_associator_constant_report_runs_and_gives_a_verdict():
    report = associator_constant_report(seed=0, n=12, rank=3, cp_rank=3, trials=100, adversarial_steps=60)
    assert report.verdict in (
        "CONSTANT_2_EMPIRICALLY_SHARP",
        "CONSTANT_2_NOT_SHARP_TIGHTER_BOUND_AVAILABLE",
        "SHARPNESS_UNRESOLVED_GAP_MODERATE",
    )
    assert report.max_observed_ratio <= report.triangle_bound_constant + 1e-6, (
        "the naive triangle bound must never be violated by any observed (x,y,z) -- "
        "if it were, that would refute the bound itself, not just its sharpness"
    )


def test_ambient_projected_normal_split_is_pythagorean_consistent():
    gen = torch.Generator().manual_seed(1)
    model = SpectralModelV18(n=12, rank=3, arity=3, cp_rank=3, device="cpu", dtype="float64", generator=gen)
    U = orthonormalize_columns(model.u())
    x = torch.complex(torch.randn(12, generator=gen, dtype=torch.float64), torch.randn(12, generator=gen, dtype=torch.float64))
    y = torch.complex(torch.randn(12, generator=gen, dtype=torch.float64), torch.randn(12, generator=gen, dtype=torch.float64))
    z = torch.complex(torch.randn(12, generator=gen, dtype=torch.float64), torch.randn(12, generator=gen, dtype=torch.float64))
    result = ambient_projected_normal_split(model, U, x, y, z)
    # projected + normal are orthogonal components of ambient (P and I-P are
    # orthogonal projectors), so norms must satisfy the Pythagorean identity
    lhs = result["projected_norm"] ** 2 + result["normal_norm"] ** 2
    rhs = result["ambient_norm"] ** 2
    assert abs(lhs - rhs) / (rhs + 1e-30) < 1e-8
    assert 0.0 <= result["normal_leakage_fraction"] <= 1.0 + 1e-9
