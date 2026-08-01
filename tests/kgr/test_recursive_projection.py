"""Gate 5 (per the Fase-2 proposal this session received): conformance
check of the exact local subset-expansion identity
(``docs/theorems_v3/exact_subset_expansion.md``, already ``PROVED``
there for any bounded arity-``a`` multilinear law) against our concrete
``CPTernaryLaw``.

This does NOT re-prove the theorem — that would duplicate
``src/seion_core/research_v3/error_expansion.py`` for no reason. It
checks that ``CPTernaryLaw`` genuinely satisfies the theorem's
hypothesis (joint trilinearity in ``x,a,q``) by verifying the resulting
identity holds to machine precision, and that a law which does NOT
satisfy the hypothesis (has a non-multilinear term mixed in) correctly
fails the same check — otherwise the positive test could be passing for
the wrong reason.
"""
import itertools

import torch

from seion_kgr_reference_fp64 import CPTernaryLaw, Projector, closure_residual


def _exact_subset_expansion(mu_forward, R, D):
    """``r_v + sum_{S != empty} mu_v(Y^S)`` for a 3-argument law."""
    subset_sum = torch.zeros_like(R[0])
    for r in range(1, len(R) + 1):
        for S in itertools.combinations(range(len(R)), r):
            Y = [D[i] if i in S else R[i] for i in range(len(R))]
            subset_sum = subset_sum + mu_forward(*Y)
    return subset_sum


def test_exact_subset_expansion_holds_for_cp_ternary_law():
    dim, rank = 4, 3
    torch.manual_seed(5)
    cp = CPTernaryLaw(
        A=torch.randn(rank, dim, dtype=torch.float64),
        B=torch.randn(rank, dim, dtype=torch.float64),
        C=torch.randn(rank, dim, dtype=torch.float64),
        O=torch.randn(dim, rank, dtype=torch.float64),
    )
    proj = Projector.random_rank(dim=dim, rank=2, seed=5)

    R = [torch.randn(dim, dtype=torch.float64) for _ in range(3)]
    D = [torch.randn(dim, dtype=torch.float64) * 0.1 for _ in range(3)]
    F = [R[i] + D[i] for i in range(3)]

    F_v = cp.forward(F[0], F[1], F[2])
    ambient_at_R = cp.forward(R[0], R[1], R[2])
    R_v = proj.apply(ambient_at_R)
    delta_v = F_v - R_v

    r_v = closure_residual(proj, ambient_at_R)
    predicted = r_v + _exact_subset_expansion(cp.forward, R, D)

    assert torch.allclose(delta_v, predicted, atol=1e-9), (delta_v, predicted)


def test_exact_subset_expansion_fails_for_a_non_multilinear_law():
    """Negative control: a law with a non-multilinear term mixed in
    (here, an added ``||x||^2`` bias-like term breaking joint
    multilinearity in the first slot) must NOT satisfy the identity —
    otherwise the positive test above proves nothing about multilinearity
    specifically."""
    dim, rank = 4, 3
    torch.manual_seed(6)
    cp = CPTernaryLaw(
        A=torch.randn(rank, dim, dtype=torch.float64),
        B=torch.randn(rank, dim, dtype=torch.float64),
        C=torch.randn(rank, dim, dtype=torch.float64),
        O=torch.randn(dim, rank, dtype=torch.float64),
    )
    proj = Projector.random_rank(dim=dim, rank=2, seed=6)

    def broken_forward(x, a, q):
        return cp.forward(x, a, q) + (x * x).sum() * torch.ones(dim, dtype=torch.float64)  # not multilinear

    R = [torch.randn(dim, dtype=torch.float64) for _ in range(3)]
    D = [torch.randn(dim, dtype=torch.float64) * 0.1 for _ in range(3)]
    F = [R[i] + D[i] for i in range(3)]

    F_v = broken_forward(F[0], F[1], F[2])
    ambient_at_R = broken_forward(R[0], R[1], R[2])
    R_v = proj.apply(ambient_at_R)
    delta_v = F_v - R_v

    r_v = closure_residual(proj, ambient_at_R)
    predicted = r_v + _exact_subset_expansion(broken_forward, R, D)

    assert not torch.allclose(delta_v, predicted, atol=1e-6), "non-multilinear law should NOT satisfy the exact identity"


def test_k_equals_1_corollary_error_is_entirely_normal():
    """Corollary 15.2 (contract, elementary consequence of leaves having
    zero error by definition, `F_leaf = R_leaf` exactly): with a single
    internal node whose children ARE leaves (D_i = 0 for all i), the
    root error must equal the closure residual exactly and must be
    orthogonal to ran(P) — i.e. the projected-root error is zero."""
    dim, rank = 4, 3
    torch.manual_seed(7)
    cp = CPTernaryLaw(
        A=torch.randn(rank, dim, dtype=torch.float64),
        B=torch.randn(rank, dim, dtype=torch.float64),
        C=torch.randn(rank, dim, dtype=torch.float64),
        O=torch.randn(dim, rank, dtype=torch.float64),
    )
    proj = Projector.random_rank(dim=dim, rank=2, seed=7)

    R = [torch.randn(dim, dtype=torch.float64) for _ in range(3)]
    D = [torch.zeros(dim, dtype=torch.float64) for _ in range(3)]  # leaves: exact, D=0
    F = [R[i] + D[i] for i in range(3)]  # F == R

    F_v = cp.forward(F[0], F[1], F[2])
    ambient_at_R = cp.forward(R[0], R[1], R[2])
    R_v = proj.apply(ambient_at_R)
    delta_v = F_v - R_v
    r_v = closure_residual(proj, ambient_at_R)

    assert torch.allclose(delta_v, r_v, atol=1e-10)  # Delta_v = r_v exactly (all subset terms vanish)
    e_proj = torch.linalg.norm(proj.apply(delta_v)).item()
    assert e_proj < 1e-9  # error is entirely in (ran P)^perp -> projected-root error is 0
