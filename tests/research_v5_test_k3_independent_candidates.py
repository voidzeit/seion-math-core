import math

import pytest

from seion_core.research_v5.k3_independent_candidates import (
    construct_k3_independent_candidate,
)


@pytest.mark.parametrize("topology", ["chain", "branch"])
@pytest.mark.parametrize("eta", [0.1, 0.5, 1.0 / math.sqrt(2.0)])
def test_k3_independent_candidate_is_a_valid_lower_witness(topology, eta):
    result = construct_k3_independent_candidate(eta, topology=topology)
    expected = 2.0 * eta * math.sqrt(1.0 - eta * eta)
    assert result.realized_defect == pytest.approx(result.rho_budget)
    assert result.projected_error == pytest.approx(expected)
    assert result.normalized_constant_lower_bound == pytest.approx(2.0 * math.sqrt(1.0 - eta * eta))
    assert result.ratio_to_universal_bound == pytest.approx(math.sqrt(1.0 - eta * eta))
    assert result.projected_error <= result.universal_projected_bound + 1e-12


def test_k3_candidate_budget_optimization_never_exceeds_the_defect_budget():
    result = construct_k3_independent_candidate(0.9, topology="chain")
    assert result.realized_defect < result.rho_budget
    assert result.projected_error == pytest.approx(1.0)
    assert result.normalized_constant_lower_bound == pytest.approx(1.0 / 0.9)
    assert result.projected_error <= result.universal_projected_bound


def test_k3_candidate_rejects_invalid_inputs():
    with pytest.raises(ValueError):
        construct_k3_independent_candidate(0.5, topology="diamond")
    with pytest.raises(ValueError):
        construct_k3_independent_candidate(0.0, topology="chain")
    with pytest.raises(ValueError):
        construct_k3_independent_candidate(0.5, topology="branch", M=0.0)
