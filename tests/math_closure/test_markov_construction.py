"""Pytest wrapper (self-contained, no cross-module fixture import - that
approach was tried and correctly rejected by pytest, since fixtures
don't travel with a bare imported function) for the M6 verified Markov
construction, so it's picked up by the default `pytest` invocation
(testpaths=["tests"]) alongside the rest of the mission's math-closure
test coverage. Delegates all computation to
research/math_closure/markov/examples/finite_sinusoidal_kernel.py -
logic is not duplicated, only the pytest fixture wiring is redone here.
"""

from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT / "research" / "math_closure" / "markov" / "examples"))

from finite_sinusoidal_kernel import build_W  # noqa: E402


@pytest.fixture
def W():
    return build_W(6)


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
    n = W.shape[0]
    d = W.sum(axis=1)
    D = np.diag(d)
    P = W / d[:, None]
    rng = np.random.default_rng(1)
    for _ in range(10):
        f = rng.standard_normal(n)
        lhs = f @ D @ (f - P @ f)
        rhs = 0.5 * sum(W[p, s] * (f[p] - f[s]) ** 2 for p in range(n) for s in range(n))
        assert abs(lhs - rhs) < 1e-9
