import pytest

from research.pmt_program.heterogeneous import NodeChoice, make_certificate, optimize_allocation


def test_certificate_uses_root_plus_active_node_convention():
    report = make_certificate([2.0, 1.0, 1.5], [0.1, 0.3], 4.0, maxiter=80, seed=2)
    assert report.normalized_defects == pytest.approx((0.1, 0.2))
    assert report.scale == pytest.approx(12.0)
    assert report.uniform_safe_bound >= report.exploratory_bound - 1e-10


def test_allocation_uses_safe_certificate_for_feasibility():
    choices = [
        [NodeChoice("high", 1.0, 0.05, 3.0), NodeChoice("low", 1.0, 0.5, 1.0)],
        [NodeChoice("high", 1.0, 0.05, 3.0), NodeChoice("low", 1.0, 0.5, 1.0)],
    ]
    result = optimize_allocation(1.0, choices, 1.0, target_error=0.25, max_combinations=10)
    assert result.feasible_under_safe_bound
    assert all(choice.label == "high" for choice in result.choices)

