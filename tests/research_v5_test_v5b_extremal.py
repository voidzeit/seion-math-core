import math

import pytest

from seion_core.research_v5.v5b_extremal import (
    asymptotic_k3_limit_witness,
    conditional_scalar_reduction_upper_bound,
    optimize_scalar_k3_family,
    repeated_law_k2_band,
    scalar_k3_objective,
    verify_scalar_closed_form,
    v5a_piecewise_lower_bound_closed_form,
)


@pytest.mark.parametrize("eta", [0.01, 0.25, 1.0 / math.sqrt(2.0), 0.8, 1.0])
def test_v5a_piecewise_curve_matches_exact_scalar_optimizer(eta):
    result = optimize_scalar_k3_family(eta)
    assert verify_scalar_closed_form(eta)
    assert result.normalized_by_rho_M2 == pytest.approx(
        v5a_piecewise_lower_bound_closed_form(eta)
    )
    assert result.objective_at_q_star <= result.universal_bound + 1e-12


def test_scalar_objective_is_maximized_at_the_declared_transition():
    eta = 1.0
    result = optimize_scalar_k3_family(eta)
    assert result.regime == "interior_extremum"
    assert result.q_star == pytest.approx(1.0 / math.sqrt(2.0))
    assert result.objective_at_q_star == pytest.approx(1.0)


def test_constraint_active_regime_uses_the_defect_budget():
    result = optimize_scalar_k3_family(0.25)
    assert result.regime == "constraint_active"
    assert result.q_star == pytest.approx(result.rho)
    assert result.normalized_by_rho_M2 == pytest.approx(
        2.0 * math.sqrt(1.0 - 0.25**2)
    )


def test_asymptotic_lower_curve_reaches_the_universal_limit():
    assert asymptotic_k3_limit_witness()


def test_conditional_upper_bound_is_not_mislabeled_as_global():
    result = conditional_scalar_reduction_upper_bound(0.4)
    assert result.status == "CONDITIONAL_ON_UNPROVED_SCALAR_REDUCTION"
    assert "E_proj <= 2*A*B" in result.assumptions


@pytest.mark.parametrize("eta", [0.1, 1.0 / math.sqrt(2.0), 1.0])
def test_repeated_law_band_is_explicitly_open(eta):
    result = repeated_law_k2_band(eta)
    assert result.known_lower_bound == pytest.approx(eta)
    assert result.universal_upper_bound == pytest.approx(1.0)
    assert result.gated_planar_exact_value == pytest.approx(eta * eta)
    assert result.status == "OPEN_FIXED_ETA_SHARPNESS"


def test_scalar_objective_rejects_invalid_domain():
    with pytest.raises(ValueError):
        scalar_k3_objective(-0.1)
    with pytest.raises(ValueError):
        scalar_k3_objective(1.1)
