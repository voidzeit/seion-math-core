from __future__ import annotations

import torch

from spectral.certification_v18.blocks.block_l_gauge_canonicalization import (
    canonicalize,
    certify_canonicalization,
    make_exactly_degenerate_tensor,
)
from spectral.certification_v18.blocks.block_m_persistent_factorization import principal_angles
from spectral.certification_v18.model import SpectralModelV18, orthonormalize_columns


def test_simple_spectrum_is_stable_under_tiny_perturbation():
    gen = torch.Generator().manual_seed(0)
    model = SpectralModelV18(n=12, rank=4, arity=3, cp_rank=4, device="cpu", dtype="float64", generator=gen)
    U = orthonormalize_columns(model.u())
    T = model.reduced_law_tensor_einsum(U)
    report = certify_canonicalization(T, perturbation_eps=1e-9)
    assert report.status in ("CANONICAL", "CANONICAL_MODULO_RESIDUAL_GAUGE")
    assert report.stability_max_principal_angle < 1e-2


def test_exactly_degenerate_tensor_is_detected_as_such():
    T = make_exactly_degenerate_tensor(n=3, seed=0)
    result = canonicalize(T)
    assert result["regime"] == "partially_degenerate"
    assert 2 in result["residual_gauge_dims"]


def test_arbitrary_rotation_within_degenerate_eigenspace_is_the_same_subspace():
    """The real content of 'residual gauge': two DIFFERENT (pointwise
    unequal) bases of the same degenerate eigenspace, related by an
    ARBITRARY (not infinitesimal) unitary rotation within that eigenspace,
    must still be reported as the same subspace via principal angles —
    this is what 'canonical only modulo residual gauge' actually means."""
    T = make_exactly_degenerate_tensor(n=3, seed=1)
    result = canonicalize(T)
    # find the 2-dim degenerate cluster
    deg_cluster = next((i, j) for i, j in result["clusters"] if j - i == 2)
    u_a = result["eigenvectors"][:, deg_cluster[0] : deg_cluster[1]]

    gen = torch.Generator().manual_seed(2)
    rand2 = torch.complex(torch.randn(2, 2, generator=gen, dtype=torch.float64), torch.randn(2, 2, generator=gen, dtype=torch.float64))
    q2, _ = torch.linalg.qr(rand2)
    u_b = u_a @ q2  # arbitrary rotation WITHIN the degenerate eigenspace

    # pointwise, these are very different bases:
    pointwise_diff = torch.linalg.norm((u_a - u_b).reshape(-1)).item()
    assert pointwise_diff > 0.1, "the rotation must actually change the basis pointwise, or this tests nothing"

    # but as SUBSPACES they must be identical:
    pa = principal_angles(u_a, u_b)
    assert pa.max_angle_rad < 1e-8
