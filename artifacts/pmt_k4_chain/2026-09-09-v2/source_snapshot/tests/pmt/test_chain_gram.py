"""Implementation and mutation controls, not substitutes for analytic proofs."""

import math
import numpy as np
import pytest

from seion_core.pmt import evaluate_pmt, projected_closure_bracket
from seion_core.pmt.chain import audit_chain, chain_as_pmt, evaluate_chain, planar_chain
from seion_core.pmt.phase import gated_phase_tree
from research.math_closure.k4_exploration.chain_analysis import chain4_formula, isometric_dilation


@pytest.mark.parametrize("eta", [1e-4, .2, .5, math.sqrt(3/7), .8, 1.])
def test_planar_witness_full_admissibility_typed_evaluation_and_correlations(eta):
    t = min(eta, math.sqrt(3/7))
    aa, pp, x = planar_chain([t]*3)
    audit = audit_chain(aa, pp, x, eta)
    assert audit["status"] == "NUMERICAL_CANDIDATE"
    tr = evaluate_chain(aa, pp, x)
    model, leaves = chain_as_pmt(aa, pp, x)
    ev = evaluate_pmt(model, leaves)
    assert tr.projected_error == pytest.approx(eta*chain4_formula(eta), abs=1e-13)
    assert ev.errors.projected == pytest.approx(tr.projected_error, abs=1e-13)
    assert tr.source_sum_residual < 1e-13
    assert tr.grams[2].sum().real == pytest.approx(tr.projected_error**2, abs=1e-13)
    assert abs(tr.grams[2].sum()-np.trace(tr.grams[2])) > t*t/10
    assert all(row["projected_closure_norm"] <= eta+1e-13 for row in audit["stages"])


def test_off_trajectory_reduced_direction_cannot_escape_closure_check():
    p = np.diag([1., 1., 0.])
    a1 = np.array([[1.], [0.], [0.]])
    a2 = np.array([[1., 0., 0.], [0., 0., 0.], [0., 1., 0.]])
    assert np.linalg.norm((np.eye(3)-p)@a2@a1) == 0
    result = audit_chain([a1, a2], [p, p], np.ones(1), .1)
    assert result["status"] == "REJECTED_INADMISSIBLE"
    assert result["stages"][1]["projected_closure_norm"] == 1


def test_oblique_projector_is_rejected_even_when_trajectory_looks_feasible():
    p = np.array([[1., 1.], [0., 0.]])
    a = np.array([[1.], [0.]])
    result = audit_chain([a], [p], np.ones(1), .1)
    assert result["status"] == "REJECTED_INADMISSIBLE"
    with pytest.raises(ValueError, match="orthogonal"):
        chain_as_pmt([a], [p], np.ones(1))


def test_complex_gauge_covariance_of_sources_and_dilation():
    aa, pp, x = planar_chain([.2, .17, .1])
    before = evaluate_chain(aa, pp, x)
    rng = np.random.default_rng(80)
    prev = np.eye(1, dtype=complex)
    out, projs = [], []
    for a, p in zip(aa, pp):
        u, _ = np.linalg.qr(rng.normal(size=(2,2))+1j*rng.normal(size=(2,2)))
        out.append(u@a@prev.conj().T)
        projs.append(u@p@u.conj().T)
        prev = u
    after = evaluate_chain(out, projs, x)
    np.testing.assert_allclose(after.grams[2], before.grams[2], atol=1e-13)
    model, leaves = chain_as_pmt(out, projs, x)
    assert evaluate_pmt(model, leaves).errors.projected == pytest.approx(before.projected_error)
    assert audit_chain(out, projs, x, .2)["globally_checked_in_floating_point"]


def test_dilation_preserves_original_values_global_closure_and_dominates_error():
    rng = np.random.default_rng(182)
    for rank in (1, 2):
        p = np.diag([1.]*rank+[0.]*(3-rank))
        aa = [rng.normal(size=(3,1)), rng.normal(size=(3,3)), rng.normal(size=(3,3))]
        prev = np.eye(1)
        for j, a in enumerate(aa):
            aa[j] = a/max(1., np.linalg.norm(a, 2), np.linalg.norm((np.eye(3)-p)@a@prev, 2)/.3)
            prev = p
        vs, ps = isometric_dilation(aa, [p]*3)
        old = evaluate_chain(aa, [p]*3, np.ones(1))
        new = evaluate_chain(vs, ps, np.ones(1))
        for j, v in enumerate(vs):
            np.testing.assert_allclose(v.T@v, np.eye(v.shape[1]), atol=2e-14)
            np.testing.assert_allclose(new.ambient[j][:3], old.ambient[j], atol=1e-13)
            np.testing.assert_allclose(new.reduced[j][:3], old.reduced[j], atol=1e-13)
        assert np.linalg.norm(old.ambient[-1]-old.reduced[-1]) <= np.linalg.norm(new.ambient[-1]-new.reduced[-1])+1e-13
        assert audit_chain(vs, ps, np.ones(1), .3)["globally_checked_in_floating_point"]


def test_leaf_phase_negative_control_and_canonical_gating():
    eta = .2
    c = math.sqrt(1-eta*eta)
    # Q exp(i theta) z w has scalar matrix [[eta,c],[c,-eta]].
    assert np.linalg.norm(np.array([[eta, c], [c, -eta]]), 2) == pytest.approx(1.)
    shape = (((None, None), None), None)
    model, leaves = gated_phase_tree(shape, eta)
    assert evaluate_pmt(model, leaves).errors.projected == pytest.approx(math.sin(2*math.asin(eta)))
    assert projected_closure_bracket(model, (0,0)).upper == pytest.approx(eta)
    assert projected_closure_bracket(model, (0,)).upper == pytest.approx(eta)


def test_symbolic_family_stationary_point_and_asymptotic():
    s = pytest.importorskip("sympy")
    z = s.Symbol("z")
    h = 9*z-15*z**2+7*z**3
    assert s.expand(s.diff(h,z)-3*(z-1)*(7*z-3)) == 0
    assert h.subs(z, s.Rational(3,7)) == s.Rational(81,49)
    assert s.series(s.sqrt(9-15*z+7*z**2), z, 0, 3).removeO() == 3-s.Rational(5,2)*z+s.Rational(1,8)*z*z


@pytest.mark.parametrize("eta", [.05, .5, math.sqrt(3/7), 1.])
@pytest.mark.parametrize("topology", ["mixed", "branch_below"])
def test_topology_lower_witnesses_through_canonical_evaluator(eta, topology):
    from research.math_closure.k4_exploration.topology_witnesses import k4_topology_witness
    model, leaves = k4_topology_witness(topology, eta)
    assert evaluate_pmt(model, leaves).errors.projected/eta == pytest.approx(chain4_formula(eta), abs=1e-13)


@pytest.mark.parametrize("n,eta", [(1,.2), (2,.2), (2,1.), (3,.2), (3,1.)])
def test_gram_sdp_calibrates_known_controls_and_records_precision(n, eta):
    pytest.importorskip("cvxpy")
    from seion_core.pmt import w3
    from research.math_closure.k4_exploration.chain_gram_sdp import solve_chain_sdp
    result = solve_chain_sdp(eta, n)
    expected = 1 if n == 1 else w3(eta) if n == 2 else chain4_formula(eta)
    assert result["normalized_error"] == pytest.approx(expected, abs=3e-5)
    assert result["certified_upper_bound"] is None
    assert result["status"] == "NUMERICAL_CANDIDATE"
    assert min(v for row in result["stages"] for v in row["minimum_eigenvalues"]) > -1e-7
