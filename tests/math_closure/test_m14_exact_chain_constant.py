import pytest

from research.math_closure.k3.m14_exact_chain_constant import (
    ALPHA,
    construct_chain_witness,
    exact_chain_constant,
)


@pytest.mark.parametrize("eta", [1.0e-6, 0.1, 0.5, ALPHA, 0.8, 0.9, 1.0])
def test_explicit_witness_attains_m13_envelope(eta):
    witness = construct_chain_witness(eta)
    assert witness.normalized_constant == pytest.approx(exact_chain_constant(eta))
    assert witness.first_residual <= eta + 1.0e-12
    assert witness.second_residual <= eta + 1.0e-12
    assert witness.root_residual <= eta + 1.0e-12
    assert all(norm <= 1.0 + 1.0e-12 for norm in witness.operator_norms)


def test_exact_chain_constant_matches_m13_piecewise_formula():
    for eta in (0.05, 0.5, ALPHA, 0.9, 1.0):
        expected = (
            (4.0 - 3.0 * eta * eta) ** 0.5
            if eta <= ALPHA
            else 2.0 / (3.0**0.5 * eta)
        )
        assert exact_chain_constant(eta) == pytest.approx(expected)
