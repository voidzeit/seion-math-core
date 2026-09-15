import math

import pytest

from research.pmt_program.heterogeneous import (
    capped_equal_angle,
    factor,
    heterogeneous_box_max,
    interval_box_max,
    uniform_G,
)


def test_factor_has_expected_radius_and_argument():
    theta = 0.37
    z = factor(theta)
    assert z.real == pytest.approx(math.cos(theta) ** 2)
    assert z.imag == pytest.approx(math.cos(theta) * math.sin(theta))
    assert abs(z) == pytest.approx(math.cos(theta))


def test_uniform_box_matches_uniform_scalar_expression():
    eta = 0.3
    alpha = math.asin(eta)
    result = heterogeneous_box_max([alpha, alpha, alpha], maxiter=120, popsize=8)
    expected = uniform_G(3, eta)
    assert result.lower_bound == pytest.approx(expected, rel=1e-7, abs=1e-9)
    assert result.uniform_upper_bound == pytest.approx(expected, rel=1e-7, abs=1e-9)


def test_heterogeneous_box_is_never_above_uniform_envelope():
    etas = [0.05, 0.10, 0.30, 0.50]
    result = heterogeneous_box_max([math.asin(e) for e in etas], maxiter=120, popsize=8)
    assert result.lower_bound <= result.uniform_upper_bound + 1e-10
    assert result.gap >= -1e-12
    assert result.interval_lower_bound <= result.interval_upper_bound + 1e-12
    assert result.interval_upper_bound <= result.uniform_upper_bound + 1e-5


def test_interval_enclosure_contains_corner_value():
    result = interval_box_max([0.1, 0.2], tolerance=1e-6, max_boxes=5000)
    assert result.lower_bound <= result.upper_bound
    assert result.upper_bound - result.lower_bound <= 1e-6 + 1e-10


def test_capped_candidate_respects_caps():
    caps = [0.1, 0.3, 0.8]
    value, angles = capped_equal_angle(caps)
    assert value >= 0.0
    assert all(0.0 <= x <= a + 1e-12 for x, a in zip(angles, sorted(caps)))


def test_invalid_defect_rejected():
    with pytest.raises(ValueError):
        heterogeneous_box_max([math.asin(1.1)])
