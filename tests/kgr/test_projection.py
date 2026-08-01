"""Gate 1 / CLM_KGR_009,011: projector identities and closure leakage, property-based."""
import pytest
import torch
from hypothesis import given, settings
from hypothesis import strategies as st

from seion_kgr_reference_fp64 import CPTernaryLaw, MessagePassingLayer, Projector, closure_residual

pytestmark = pytest.mark.symbolic

dims_ranks = st.tuples(st.integers(2, 8), st.integers(1, 6)).filter(lambda dr: dr[1] <= dr[0])
seed = st.integers(min_value=0, max_value=2**31 - 1)


@settings(deadline=None, max_examples=40)
@given(dim_rank=dims_ranks, seed=seed)
def test_projector_identities_hold_in_fp64(dim_rank, seed):
    dim, rank = dim_rank
    proj = Projector.random_rank(dim=dim, rank=rank, seed=seed)
    assert proj.isometry_residual() < 1e-10
    assert proj.idempotent_residual() < 1e-10
    assert proj.selfadjoint_residual() < 1e-10


def test_identity_projector_has_full_rank_and_zero_residuals():
    proj = Projector.identity(5)
    assert proj.dim_W == 5
    assert proj.isometry_residual() < 1e-12
    assert proj.idempotent_residual() < 1e-12


def test_projector_rejects_rank_out_of_range():
    with pytest.raises(ValueError):
        Projector.random_rank(dim=4, rank=0, seed=1)
    with pytest.raises(ValueError):
        Projector.random_rank(dim=4, rank=5, seed=1)


def test_projector_rejects_non_2d_Q():
    with pytest.raises(ValueError):
        Projector(torch.randn(3, 3, 3, dtype=torch.float64))


def test_closure_leakage_zero_at_full_rank_projector():
    dim = 6
    proj = Projector.identity(dim)
    mu_out = torch.randn(dim, dtype=torch.float64)
    residual = closure_residual(proj, mu_out)
    assert torch.linalg.norm(residual).item() < 1e-12


@settings(deadline=None, max_examples=15)
@given(seed=seed)
def test_closure_leakage_generically_nonzero_at_reduced_rank(seed):
    """Numerical observation (NUMERICALLY_TESTED, not a proof): a strictly
    rank-reduced random projector generically leaks nonzero energy for a
    random ambient vector. This is expected to fail only on a
    probability-zero event (mu_out already lying in ran(P))."""
    dim, rank = 6, 3
    proj = Projector.random_rank(dim=dim, rank=rank, seed=seed)
    g = torch.Generator().manual_seed(seed + 999)
    mu_out = torch.randn(dim, generator=g, dtype=torch.float64)
    residual = closure_residual(proj, mu_out)
    assert torch.linalg.norm(residual).item() > 1e-8


def test_message_passing_layer_closure_leakage_matches_manual_formula():
    dim = 4
    cp = CPTernaryLaw(
        A=torch.randn(2, dim, dtype=torch.float64),
        B=torch.randn(2, dim, dtype=torch.float64),
        C=torch.randn(2, dim, dtype=torch.float64),
        O=torch.randn(dim, 2, dtype=torch.float64),
    )
    proj = Projector.random_rank(dim=dim, rank=2, seed=3)
    layer = MessagePassingLayer(
        mu=cp,
        U=torch.zeros(dim, dim, dtype=torch.float64),
        V=torch.zeros(dim, dim, dtype=torch.float64),
        W=torch.zeros(dim, dim, dtype=torch.float64),
        P_out=proj,
    )
    x = torch.randn(dim, dtype=torch.float64)
    a = torch.randn(dim, dtype=torch.float64)
    q = torch.randn(dim, dtype=torch.float64)
    m_tilde = layer.message_ambient(x, a, q)
    expected = m_tilde - proj.apply(m_tilde)
    got = layer.closure_leakage(x, a, q)
    assert torch.allclose(expected, got, atol=1e-10)
