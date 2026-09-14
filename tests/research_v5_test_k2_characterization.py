import math

import numpy as np
import pytest

from seion_core.research_v5.k2_characterization import certify_k2_saturation


def _proj(dim, indices):
    P = np.zeros((dim, dim))
    for i in indices:
        P[i, i] = 1.0
    return P


@pytest.mark.parametrize("eta", [0.1, 0.5, math.sqrt(0.5), 1.0])
def test_independent_law_witness_satisfies_all_three_conditions(eta):
    M = 1.0
    rho = eta * M
    P = _proj(2, [0])
    P_out = _proj(2, [0])

    def mu_in(x, y):
        return np.array([M * x[1] * y[1], rho * x[0] * y[0]])

    def mu_out(x, y):
        return np.array([M * x[1] * y[0], 0.0])

    e0 = np.array([1.0, 0.0])
    cert = certify_k2_saturation(mu_in, mu_out, P, P_out, e0, e0, e0, M=M, rho=rho)
    assert cert.all_conditions_hold
    assert cert.saturates
    assert cert.E_P == pytest.approx(cert.universal_bound, rel=1e-9)


@pytest.mark.parametrize("eta", [0.05, 0.3, 0.7, 1.0])
def test_repeated_law_witness_also_satisfies_all_three_conditions(eta):
    M = 1.0
    rho = eta * M
    P = _proj(2, [0])
    P_out = _proj(2, [0])

    def mu(x, y):
        return np.array([M * x[1] * y[0], rho * x[0] * y[0]])

    e0 = np.array([1.0, 0.0])
    cert = certify_k2_saturation(mu, mu, P, P_out, e0, e0, e0, M=M, rho=rho)
    assert cert.all_conditions_hold
    assert cert.saturates
    assert cert.E_P == pytest.approx(cert.universal_bound, rel=1e-9)


def test_non_extremal_configuration_fails_at_least_one_condition_and_does_not_saturate():
    # A generic, non-adversarial random configuration should (a) obey the
    # universal upper bound (sanity: never exceed it) and (b) generically
    # fail to saturate it, with at least one of EQ1-EQ3 strictly slack --
    # this is the necessity direction of the iff theorem exercised on a
    # concrete instance, not a full proof (the proof is the docstring
    # argument in k2_characterization.py).
    rng = np.random.default_rng(7)
    M, rho = 1.0, 0.4
    dim = 3
    A = rng.normal(size=(dim, dim, dim)) * 0.3  # deliberately not norm-M
    B = rng.normal(size=(dim, dim, dim)) * 0.3
    P = _proj(dim, [0, 1])
    P_out = _proj(dim, [0])

    def mu_in(x, y):
        return np.einsum("rpq,p,q->r", A, x, y)

    def mu_out(x, y):
        return np.einsum("rpq,p,q->r", B, x, y)

    a = rng.normal(size=dim); a /= np.linalg.norm(a)
    b = rng.normal(size=dim); b /= np.linalg.norm(b)
    d = rng.normal(size=dim); d /= np.linalg.norm(d)

    cert = certify_k2_saturation(mu_in, mu_out, P, P_out, a, b, d, M=M, rho=rho)
    assert cert.E_P <= cert.universal_bound + 1e-9
    assert not cert.saturates
    assert not cert.all_conditions_hold


def test_theorem_predicts_a_novel_saturating_configuration_not_in_prior_registries():
    # Construct a THIRD instance, distinct from both k2_sharpness.py
    # witnesses (different operator direction convention, dimension-3
    # ambient space, projector of rank 2), built purely by satisfying
    # EQ1-EQ3 directly, and check it saturates -- exercising the theorem's
    # SUFFICIENCY direction predictively rather than re-verifying a known
    # construction.
    M, rho = 2.0, 0.6
    dim = 3
    P = _proj(dim, [0, 1])  # rank 2
    P_out = _proj(dim, [2])  # rank 1, different axis

    e0, e1, e2 = np.eye(dim)

    def mu_in(x, y):
        # (I-P) mu_in(e0,e0) must have norm rho: put all of it on e2 (outside P).
        return M * x[1] * y[1] * e0 + rho * x[0] * y[0] * e2

    def mu_out(x, y):
        # Must attain M on (D_in, d) = (e2, e0) and land the output inside
        # Range(P_out) = span(e2).
        return M * x[2] * y[0] * e2

    a, b, d = e0, e0, e0
    cert = certify_k2_saturation(mu_in, mu_out, P, P_out, a, b, d, M=M, rho=rho)
    assert cert.all_conditions_hold
    assert cert.saturates
    assert cert.E_P == pytest.approx(rho * M, rel=1e-9)
