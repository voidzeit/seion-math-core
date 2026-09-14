import pytest

from research.math_closure.dag.diamond_asymptotic_sharpness import (
    diamond_universal_path_constant,
    diamond_witness_error,
    diamond_witness_ratio,
    run_checks,
)


def test_shared_diamond_witness_checks_and_path_upper_bound():
    run_checks()
    assert diamond_universal_path_constant() == pytest.approx(4.0)
    assert diamond_witness_error(0.1) <= 4.0 * 0.1 + 1.0e-12


def test_shared_diamond_ratio_converges_to_exact_asymptotic_constant():
    assert diamond_witness_ratio(1.0e-5) == pytest.approx(4.0, abs=1.0e-4)

