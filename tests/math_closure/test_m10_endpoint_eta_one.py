import math

from research.math_closure.k3.m10_endpoint_eta_one import endpoint_values, run_checks


def test_m10_endpoint_algebra():
    run_checks()


def test_endpoint_scales_homogeneously_in_M():
    q_star, first, second = endpoint_values(3.5)
    assert math.isclose(q_star, 3.5 / math.sqrt(2.0), rel_tol=0.0, abs_tol=1.0e-14)
    assert math.isclose(first, 3.5**3 / math.sqrt(2.0), rel_tol=0.0, abs_tol=1.0e-13)
    assert math.isclose(second, 3.5**3 / math.sqrt(2.0), rel_tol=0.0, abs_tol=1.0e-13)
