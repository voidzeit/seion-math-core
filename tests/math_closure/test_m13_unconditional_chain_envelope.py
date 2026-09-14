import math

from research.math_closure.k3.m13_unconditional_chain_envelope import (
    ALPHA,
    ETA_STAR,
    explicit_gap,
    m13_bound,
    m9_bound,
    run_checks,
)


def test_m13_scalar_envelope_and_strict_gap():
    run_checks()


def test_m13_transition_values():
    assert math.isclose(m13_bound(ALPHA), math.sqrt(2.0), abs_tol=1.0e-14)
    assert math.isclose(m9_bound(1.0), math.sqrt(2.0), abs_tol=1.0e-14)
    assert explicit_gap(1.0) > 0.25
    assert ETA_STAR < ALPHA
