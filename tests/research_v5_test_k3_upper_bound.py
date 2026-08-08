import math

import pytest

from seion_core.research_v5.k3_upper_bound import (
    eta_transition_point,
    h_chain_or_branch,
    k3_upper_envelope,
    verify_asymptotic_limit,
    verify_continuity_at_transition,
)
from seion_core.research_v5.v5b_extremal import v5a_piecewise_lower_bound_closed_form


def test_transition_point_is_the_golden_ratio_conjugate_root():
    eta_c = eta_transition_point()
    assert eta_c == pytest.approx(math.sqrt((math.sqrt(5.0) - 1.0) / 2.0))
    assert 0.0 < eta_c < 1.0


def test_regimes_agree_exactly_at_the_transition_and_equal_the_golden_ratio():
    assert verify_continuity_at_transition()


def test_bound_recovers_the_universal_constant_in_the_eta_to_zero_limit():
    assert verify_asymptotic_limit()


@pytest.mark.parametrize("eta", [0.05, 0.3, 0.6, 0.7861513777574233, 0.9, 1.0])
def test_new_bound_is_strictly_tighter_than_the_universal_bound_for_eta_greater_than_zero(eta):
    result = k3_upper_envelope(eta)
    assert result.normalized_bound < result.universal_bound / (result.rho * result.M * result.M) + 1e-12
    assert result.normalized_bound <= 2.0 + 1e-9
    assert result.improvement_over_universal > 0.0


@pytest.mark.parametrize("eta", [0.01, 0.1, 0.3, 0.6, 0.7861513777574233, 0.9, 1.0])
def test_new_bound_dominates_the_certified_lower_witness_everywhere(eta):
    # Sharpness would require these to coincide; the point of this test is
    # only the ORDERING L_3(eta) <= U_3(eta) <= 2, i.e. the certified gap
    # narrowed but did not close.
    lower = v5a_piecewise_lower_bound_closed_form(eta)
    upper = k3_upper_envelope(eta).normalized_bound
    assert lower <= upper + 1e-9
    assert upper <= 2.0 + 1e-9


def test_at_eta_one_the_new_bound_is_a_real_numeric_improvement():
    result = k3_upper_envelope(1.0)
    # sqrt(2) ~= 1.4142, versus the trivial universal bound of 2.
    assert result.normalized_bound == pytest.approx(math.sqrt(2.0), rel=1e-9)
    assert result.normalized_bound < 1.5


def test_h_function_matches_the_envelope_optimizer_by_construction():
    for eta in (0.2, 0.5, 0.8, 1.0):
        result = k3_upper_envelope(eta)
        recomputed = h_chain_or_branch(result.q_star, M=result.M, rho=result.rho)
        assert recomputed == pytest.approx(result.h_at_q_star, rel=1e-12)


def test_h_rejects_out_of_domain_q():
    with pytest.raises(ValueError):
        h_chain_or_branch(2.0, M=1.0, rho=0.5)


def test_k3_upper_envelope_rejects_out_of_domain_eta():
    with pytest.raises(ValueError):
        k3_upper_envelope(0.0)
    with pytest.raises(ValueError):
        k3_upper_envelope(1.5)
