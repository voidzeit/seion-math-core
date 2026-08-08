import numpy as np
import pytest

from seion_core.research_v5.k3_non_sharpness import (
    forced_orthogonality_holds,
    pareto_frontier_two_direction_norm_budget,
)


def _svd_aligned_map(dim_out, u_hat, v_hat, M, sigma2, rng):
    # Build N restricted to span(u_hat, v_hat) via explicit SVD: top
    # singular value M at u_hat, second singular value sigma2 at v_hat,
    # with random orthonormal left singular vectors -- by construction
    # this attains ||N||_op=M exactly at u_hat.
    u1 = rng.normal(size=dim_out); u1 /= np.linalg.norm(u1)
    u2 = rng.normal(size=dim_out)
    u2 -= np.dot(u2, u1) * u1
    u2 /= np.linalg.norm(u2)
    dim_in = u_hat.shape[0]
    N = M * np.outer(u1, u_hat) + sigma2 * np.outer(u2, v_hat)
    return N


@pytest.mark.parametrize("sigma2", [0.0, 0.3, 0.7, 1.0])
def test_svd_aligned_construction_satisfies_forced_orthogonality(sigma2):
    rng = np.random.default_rng(3)
    dim_in, dim_out = 4, 5
    u_hat = rng.normal(size=dim_in); u_hat /= np.linalg.norm(u_hat)
    w = rng.normal(size=dim_in)
    w -= np.dot(w, u_hat) * u_hat
    v_hat = w / np.linalg.norm(w)
    M = 1.0
    N = _svd_aligned_map(dim_out, u_hat, v_hat, M, sigma2, rng)
    assert forced_orthogonality_holds(N, u_hat, v_hat)


def test_a_map_not_attaining_its_norm_at_u_hat_raises():
    # N(u_hat) has norm 1 but the true operator-norm max is larger
    # (attained off the (u_hat,v_hat) plane's u_hat point) -- the lemma's
    # PRECONDITION fails, so the checker must refuse to certify anything.
    N = np.array([[1.0, 0.5], [0.0, 0.0]])
    u_hat = np.array([1.0, 0.0])
    v_hat = np.array([0.0, 1.0])
    with pytest.raises(ValueError):
        forced_orthogonality_holds(N, u_hat, v_hat)


def test_pareto_frontier_orthogonal_case_recovers_independent_budgets():
    # At angle=pi/2 (orthogonal), the joint cap should just be M itself
    # (both directions independently capped at M, ratio irrelevant to the
    # ceiling on the smaller-normalized one) -- sanity check against the
    # closed-form diag-Gram-matrix eigenvalues used in the k3 upper-bound
    # derivation (M9): lambda_max = max(1, ratio^2) per unit k^2.
    k = pareto_frontier_two_direction_norm_budget(np.pi / 2, ratio=0.6, M=1.0)
    assert k == pytest.approx(1.0 / max(1.0, 0.6), rel=1e-9)


def test_pareto_frontier_shrinks_as_directions_align():
    # As angle -> 0 (parallel), the joint budget for supporting the SAME
    # magnitude ratio must shrink relative to the orthogonal case --
    # this is the numeric shadow of the trade-off the k=3 non-sharpness
    # proof identifies (full triangle-inequality alignment costs budget).
    ratio = 0.6
    k_orth = pareto_frontier_two_direction_norm_budget(np.pi / 2, ratio, M=1.0)
    k_parallel = pareto_frontier_two_direction_norm_budget(0.0, ratio, M=1.0)
    assert k_parallel < k_orth


def test_pareto_frontier_rejects_invalid_inputs():
    with pytest.raises(ValueError):
        pareto_frontier_two_direction_norm_budget(-0.1, 0.5)
    with pytest.raises(ValueError):
        pareto_frontier_two_direction_norm_budget(0.5, -1.0)
