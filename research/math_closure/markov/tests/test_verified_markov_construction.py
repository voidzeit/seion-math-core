"""Regression test for the M6 verified Markov construction (symmetrized
quadratic weight W_kappa). Run with: pytest research/math_closure/markov/tests
"""

from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "examples"))
from finite_sinusoidal_kernel import build_W  # noqa: E402


@pytest.fixture
def n():
    return 6


@pytest.fixture
def W(n):
    return build_W(n)


def test_symmetry(W):
    assert np.allclose(W, W.T)


def test_nonnegativity(W):
    assert (W >= 0).all()


def test_degree_positive_and_finite(W):
    d = W.sum(axis=1)
    assert (d > 0).all()
    assert np.isfinite(d).all()


def test_stochastic(W):
    d = W.sum(axis=1)
    P = W / d[:, None]
    assert np.allclose(P.sum(axis=1), 1.0)


def test_self_adjoint_and_contraction(W):
    d = W.sum(axis=1)
    D = np.diag(d)
    P = W / d[:, None]
    DP = D @ P
    assert np.allclose(DP, DP.T)
    symmetrized = DP / np.sqrt(np.outer(d, d))
    eigenvalues = np.linalg.eigvalsh(symmetrized)
    assert np.isclose(max(eigenvalues), 1.0)
    assert all(ev < 1.0 + 1e-9 for ev in eigenvalues)


def test_dirichlet_form_identity(W):
    n_ = W.shape[0]
    d = W.sum(axis=1)
    D = np.diag(d)
    P = W / d[:, None]
    rng = np.random.default_rng(1)
    for _ in range(10):
        f = rng.standard_normal(n_)
        lhs = f @ D @ (f - P @ f)
        rhs = 0.5 * sum(W[p, s] * (f[p] - f[s]) ** 2 for p in range(n_) for s in range(n_))
        assert abs(lhs - rhs) < 1e-9
