"""PMT-TN pipeline integrity: F6 positive control attains the certificate, F8 negative controls fail it."""
from __future__ import annotations

import math
import sys
from pathlib import Path

import numpy as np
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "research" / "pmt_program" / "tn_benchmark"))
import certificate as cert  # noqa: E402
import families_controls as fc  # noqa: E402
from pmt_eval import evaluate, check_projector_orthogonal, law_norm_lower_bound  # noqa: E402


def eta_c(k):
    ts = np.linspace(1e-4, math.pi / 2, 20000)
    best, arg = -1.0, None
    for t in ts:
        v = cert.g(t, k - 1)
        if v > best + 1e-15:
            best, arg = v, t
    return math.sin(arg)


def run_cert(out, expected_violation=False):
    c = cert.certificate(out["k"], out["eta_hat"], out["M_hat"], out["leaf_product"], out["E_obs"],
                         out["F_norm"], "test")
    return c, cert.classify(c, expected_violation)


@pytest.mark.parametrize("seed", range(12))
def test_F6_attains_certificate_on_random_trees(seed):
    rng = np.random.default_rng(seed)
    k = int(rng.integers(2, 11))
    kids, leaves = fc.random_tree(rng, k)
    eta = float(rng.uniform(0.01, 0.999)) * eta_c(k)
    th = math.asin(eta)
    nodes = fc.witness_nodes(kids, leaves, {v: th for v in kids if v != "n0"})
    out = evaluate(nodes, "n0")
    c, label = run_cert(out)
    assert out["k"] == k
    assert out["eta_hat"] == pytest.approx(eta, rel=1e-12)
    assert c.ratio_obs_to_BR == pytest.approx(1.0, abs=1e-11)
    assert label == "WITHIN_CERTIFICATE"


@pytest.mark.parametrize("seed", range(6))
def test_F6_unequal_angles_stay_below(seed):
    rng = np.random.default_rng(100 + seed)
    k = int(rng.integers(3, 9))
    kids, leaves = fc.random_tree(rng, k)
    eta = 0.7
    thetas = {v: float(rng.uniform(0, math.asin(eta))) for v in kids if v != "n0"}
    out = evaluate(fc.witness_nodes(kids, leaves, thetas), "n0")
    c, label = run_cert(out)
    assert c.ratio_obs_to_BR <= 1 + 1e-12


@pytest.mark.parametrize("k,theta,lam", [(2, 0.2, 1.5), (4, 0.1, 1.2), (6, 0.05, 2.0)])
def test_F8a_underestimated_M(k, theta, lam):
    out = evaluate(fc.f8a_nodes(k, theta, lam), "n0")
    c, label = run_cert(out, expected_violation=True)
    assert c.ratio_obs_to_BR == pytest.approx(lam, rel=1e-10)
    assert label == "EXPECTED_VIOLATION_NEGATIVE_CONTROL"
    # validator layer: sampled norm of the root law exceeds the claimed M_hat
    rng = np.random.default_rng(0)
    root = fc.f8a_nodes(k, theta, lam)["n0"]
    lb = law_norm_lower_bound(root.law, [(2,)] * len(root.children), [(2,)] * len(root.leaves), rng)
    assert lb > root.M_hat * (1 + 1e-6)


@pytest.mark.parametrize("theta,c", [(0.1, 1.0), (0.3, 3.0)])
def test_F8b_oblique_projector(theta, c):
    nodes = fc.f8b_nodes(theta, c)
    out = evaluate(nodes, "n0")
    cc, label = run_cert(out, expected_violation=True)
    assert cc.ratio_obs_to_BR == pytest.approx(math.sqrt(1 + c * c), rel=1e-10)
    assert label == "EXPECTED_VIOLATION_NEGATIVE_CONTROL"
    chk = check_projector_orthogonal(nodes["n1"].projector, (2,), np.random.default_rng(1))
    assert not chk["orthogonal"]


@pytest.mark.parametrize("theta,d", [(0.1, 4), (0.2, 9)])
def test_F8c_self_trace(theta, d):
    nodes = fc.f8c_nodes(theta, d)
    out = evaluate(nodes, "n0")
    c, label = run_cert(out, expected_violation=True)
    assert c.ratio_obs_to_BR == pytest.approx(math.sqrt(d), rel=1e-10)
    assert label == "EXPECTED_VIOLATION_NEGATIVE_CONTROL"
    lb = law_norm_lower_bound(nodes["n0"].law, [(d, d)], [], np.random.default_rng(2))
    assert lb > 1 + 1e-6


def test_F6_projectors_pass_orthogonality():
    assert check_projector_orthogonal(fc.re_projector, (2,), np.random.default_rng(3))["orthogonal"]
