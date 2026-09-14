"""Independent tests of the PMT-TN certificate arithmetic (closed forms, monotonicity, mp replay)."""
from __future__ import annotations

import math
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "research" / "pmt_program" / "tn_benchmark"))
import certificate as cert  # noqa: E402

ETAS = [1e-6, 1e-3, 0.05, 0.1, 0.3, 0.5, math.sqrt(3 / 7), 0.6, 0.7, math.sqrt(2 / 3), 0.9, 1.0]


@pytest.mark.parametrize("eta", ETAS)
def test_k2_is_eta(eta):
    assert cert.G_k(2, eta) == pytest.approx(eta, rel=1e-13, abs=1e-15)


@pytest.mark.parametrize("eta", ETAS)
def test_k3_closed_form(eta):
    expected = eta * math.sqrt(4 - 3 * eta ** 2) if eta ** 2 <= 2 / 3 else 2 / math.sqrt(3)
    assert cert.G_k(3, eta) == pytest.approx(expected, rel=1e-12)


@pytest.mark.parametrize("eta", ETAS)
def test_k4_closed_form(eta):
    s = eta ** 2
    expected = math.sqrt(s * (9 - 15 * s + 7 * s * s)) if s <= 3 / 7 else 9 / 7
    assert cert.G_k(4, eta) == pytest.approx(expected, rel=1e-12)


@pytest.mark.parametrize("eta", ETAS)
def test_k5_closed_form(eta):
    s_c = 3 / 5 - math.sqrt(21) / 15
    E5 = lambda s: s * (4 - 3 * s) * (4 - 8 * s + 5 * s * s)
    expected = math.sqrt(E5(min(eta ** 2, s_c)))
    assert cert.G_k(5, eta) == pytest.approx(expected, rel=1e-11)


@pytest.mark.parametrize("k", [2, 3, 5, 8, 17, 40])
def test_monotone_and_bounded(k):
    etas = [i / 200 for i in range(1, 201)]
    vals = [cert.G_k(k, e) for e in etas]
    assert all(b >= a - 1e-13 for a, b in zip(vals, vals[1:]))
    for e, v in zip(etas, vals):
        assert v <= (k - 1) * e + 1e-12
        assert v < 2.0


@pytest.mark.parametrize("k", [3, 6, 11, 30])
def test_saturation_lower_bound(k):
    n = k - 1
    if math.pi / n <= math.pi / 2:
        assert cert.G_k(k, 1.0) >= 1 + math.cos(math.pi / n) ** n - 1e-12


@pytest.mark.parametrize("k,eta", [(3, 0.4), (4, 0.2), (7, 0.35), (12, 0.9), (25, 0.08)])
def test_mp_replay_agrees(k, eta):
    assert float(cert.G_k_mp(k, eta, dps=40, grid=801)) == pytest.approx(cert.G_k(k, eta), rel=1e-11)


def test_certificate_scaling_uses_M_to_the_k():
    c = cert.certificate(k=4, eta_hat=0.2, M_hat=2.0, leaf_product=3.0, E_obs=0.0, F_norm=1.0,
                         M_provenance="test")
    assert c.B_R == pytest.approx(cert.G_k(4, 0.2) * 2.0 ** 4 * 3.0)
    assert c.B_naive == pytest.approx(3 * 0.2 * 2.0 ** 4 * 3.0)


def test_classify_trigger_semantics():
    c = cert.certificate(k=3, eta_hat=0.1, M_hat=1.0, leaf_product=1.0, E_obs=1.0, F_norm=1.0,
                         M_provenance="test")
    assert cert.classify(c, expected_violation=False) == "REPLAY_TRIGGERED"
    assert cert.classify(c, expected_violation=True) == "EXPECTED_VIOLATION_NEGATIVE_CONTROL"
