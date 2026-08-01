"""Gate 1 / CLM_KGR_002-005: CP ternary law algebra, property-based.

Cross-checks the vectorized ``CPTernaryLaw.forward`` against the
independent nested-loop reconstruction, and the CP/cyclic gauge groups,
across many random seeds and shapes instead of the single fixed example
in ``seion_kgr_reference_fp64.py``'s self-test.
"""
import pytest
import torch
from hypothesis import given, settings
from hypothesis import strategies as st

from seion_kgr_reference_fp64 import CPTernaryLaw, cyclic_projector

pytestmark = pytest.mark.symbolic

small_dim = st.integers(min_value=1, max_value=4)
small_rank = st.integers(min_value=1, max_value=4)
seed = st.integers(min_value=0, max_value=2**31 - 1)


def _random_cp(dim: int, rank: int, seed: int) -> CPTernaryLaw:
    g = torch.Generator().manual_seed(seed)
    return CPTernaryLaw(
        A=torch.randn(rank, dim, generator=g, dtype=torch.float64),
        B=torch.randn(rank, dim, generator=g, dtype=torch.float64),
        C=torch.randn(rank, dim, generator=g, dtype=torch.float64),
        O=torch.randn(dim, rank, generator=g, dtype=torch.float64),
    )


@settings(deadline=None, max_examples=30)
@given(dim=small_dim, rank=small_rank, seed=seed)
def test_cp_forward_equals_dense_contraction(dim, rank, seed):
    cp = _random_cp(dim, rank, seed)
    g = torch.Generator().manual_seed(seed + 1)
    x = torch.randn(dim, generator=g, dtype=torch.float64)
    a = torch.randn(dim, generator=g, dtype=torch.float64)
    q = torch.randn(dim, generator=g, dtype=torch.float64)
    direct = cp.forward(x, a, q)
    via_dense = cp.forward_via_dense(x, a, q)
    assert torch.allclose(direct, via_dense, atol=1e-9), (direct, via_dense)


@settings(deadline=None, max_examples=20)
@given(dim=small_dim, rank=small_rank, seed=seed)
def test_cp_batched_matches_per_row_loop(dim, rank, seed):
    """Batched forward over a stack of rows must equal one call per row."""
    cp = _random_cp(dim, rank, seed)
    g = torch.Generator().manual_seed(seed + 2)
    n = 5
    X = torch.randn(n, dim, generator=g, dtype=torch.float64)
    Aa = torch.randn(n, dim, generator=g, dtype=torch.float64)
    Qq = torch.randn(n, dim, generator=g, dtype=torch.float64)
    batched = cp.forward(X, Aa, Qq)
    for i in range(n):
        single = cp.forward(X[i], Aa[i], Qq[i])
        assert torch.allclose(batched[i], single, atol=1e-10)


@settings(deadline=None, max_examples=20)
@given(dim=small_dim, rank=small_rank, seed=seed)
def test_cp_gauge_group_leaves_tensor_invariant(dim, rank, seed):
    cp = _random_cp(dim, rank, seed)
    g = torch.Generator().manual_seed(seed + 3)
    scales = []
    for _ in range(rank):
        c0 = float(torch.rand(1, generator=g).item()) + 0.5
        c1 = float(torch.rand(1, generator=g).item()) + 0.5
        c2 = float(torch.rand(1, generator=g).item()) + 0.5
        c3 = 1.0 / (c0 * c1 * c2)
        scales.append((c0, c1, c2, c3))
    gauged = cp.gauge_transform(scales)
    K0 = cp.dense_tensor_explicit_loops()
    K1 = gauged.dense_tensor_explicit_loops()
    assert torch.allclose(K0, K1, atol=1e-7)


def test_cp_gauge_group_rejects_bad_product():
    cp = _random_cp(dim=2, rank=2, seed=11)
    with pytest.raises(ValueError):
        cp.gauge_transform([(2.0, 2.0, 2.0, 2.0), (1.0, 1.0, 1.0, 1.0)])


def test_cp_gauge_negative_control_inconsistent_scaling_changes_tensor():
    """A per-component scale group is invariant; scaling only ONE factor
    matrix (not the whole component's 4-tuple) must NOT be invariant —
    otherwise the gauge-invariance test above would be vacuous."""
    cp = _random_cp(dim=3, rank=2, seed=12)
    K0 = cp.dense_tensor_explicit_loops()
    broken = CPTernaryLaw(A=cp.A * 3.0, B=cp.B, C=cp.C, O=cp.O)  # only A scaled, no compensation
    K1 = broken.dense_tensor_explicit_loops()
    assert not torch.allclose(K0, K1, atol=1e-6)


def test_cp_rank_mismatch_rejected():
    with pytest.raises(ValueError):
        CPTernaryLaw(
            A=torch.randn(3, 4, dtype=torch.float64),
            B=torch.randn(2, 4, dtype=torch.float64),  # rank mismatch vs A
            C=torch.randn(3, 4, dtype=torch.float64),
            O=torch.randn(4, 3, dtype=torch.float64),
        )


@settings(deadline=None, max_examples=15)
@given(seed=seed)
def test_cyclic_projector_idempotent(seed):
    g = torch.Generator().manual_seed(seed)
    dim = 3
    K = torch.randn(2, dim, dim, dim, generator=g, dtype=torch.float64)
    once = cyclic_projector(K)
    twice = cyclic_projector(once)
    assert torch.allclose(once, twice, atol=1e-9)


def test_cyclic_projector_rejects_unequal_input_dims():
    K = torch.randn(2, 3, 4, 3, dtype=torch.float64)
    with pytest.raises(ValueError):
        cyclic_projector(K)


def test_cyclic_projector_symmetric_under_manual_cyclic_shift():
    """Direct definition check: Pi_cyc(K)[d,i,j,k] must equal the average
    of K[d,i,j,k], K[d,j,k,i], K[d,k,i,j] (contract §IV)."""
    dim = 3
    K = torch.randn(1, dim, dim, dim, dtype=torch.float64)
    out = cyclic_projector(K)
    for d, i, j, k in [(0, 0, 1, 2), (0, 2, 1, 0), (0, 1, 1, 2)]:
        expected = (K[d, i, j, k] + K[d, j, k, i] + K[d, k, i, j]) / 3.0
        assert abs(float(out[d, i, j, k]) - float(expected)) < 1e-10


# ---------------------------------------------------- CLM_KGR_003 permutation half


@settings(deadline=None, max_examples=20)
@given(dim=small_dim, rank=small_rank, seed=seed)
def test_cp_permutation_gauge_leaves_tensor_invariant(dim, rank, seed):
    """Closes the gap explicitly flagged as TODO in CLM_KGR_003's
    limitation: only the scale half of the CP gauge group was tested
    before, not the permutation half."""
    cp = _random_cp(dim, rank, seed)
    g = torch.Generator().manual_seed(seed + 100)
    perm = torch.randperm(rank, generator=g).tolist()
    permuted = cp.permute_components(perm)
    K0 = cp.dense_tensor_explicit_loops()
    K1 = permuted.dense_tensor_explicit_loops()
    assert torch.allclose(K0, K1, atol=1e-9)


def test_cp_permutation_gauge_rejects_non_permutation():
    cp = _random_cp(dim=3, rank=3, seed=21)
    with pytest.raises(ValueError):
        cp.permute_components([0, 0, 1])  # not a permutation (repeats + missing)


def test_cp_permutation_negative_control_partial_swap_changes_tensor():
    """Negative control: permuting ONLY A's rows without correspondingly
    permuting B, C, O breaks the identity — otherwise the gauge test
    above would be vacuous."""
    cp = _random_cp(dim=3, rank=3, seed=22)
    K0 = cp.dense_tensor_explicit_loops()
    broken = CPTernaryLaw(A=cp.A[[1, 0, 2]], B=cp.B, C=cp.C, O=cp.O)  # only A permuted
    K1 = broken.dense_tensor_explicit_loops()
    assert not torch.allclose(K0, K1, atol=1e-6)
