import math

import numpy as np

from research.math_closure.k3.m23_rank_one_same_law_chain_operator_reduction import (
    evaluated_projected_error,
    operator_error,
    verify_reduction,
)


def test_m23_reduction_matches_repository_tree_evaluator() -> None:
    assert verify_reduction(seed=23, trials=24)


def test_m23_rotation_special_case() -> None:
    theta = 0.37
    c, s = math.cos(theta), math.sin(theta)
    rotation = np.array([[c, -s], [s, c]], dtype=float)
    expected = abs(math.cos(3.0 * theta) - c**3)
    assert math.isclose(operator_error(rotation), expected, rel_tol=0.0, abs_tol=2.0e-12)
    assert math.isclose(evaluated_projected_error(rotation), expected, rel_tol=0.0, abs_tol=2.0e-12)


def test_m23_zero_and_identity_maps_have_zero_error() -> None:
    zero = np.zeros((3, 3), dtype=float)
    identity = np.eye(3, dtype=float)
    assert operator_error(zero) == 0.0
    assert operator_error(identity) == 0.0
