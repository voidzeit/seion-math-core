import pytest

from research.math_closure.k3.m15_exact_branching_constant import (
    ALPHA,
    construct_branching_witness,
    exact_branching_constant,
)


@pytest.mark.parametrize("eta", [1.0e-6, 0.1, 0.5, ALPHA, 0.8, 0.9, 1.0])
def test_explicit_branching_witness_attains_exact_envelope(eta):
    witness = construct_branching_witness(eta)
    assert witness.normalized_constant == pytest.approx(
        exact_branching_constant(eta)
    )
    assert witness.child_one_residual <= eta + 1.0e-12
    assert witness.child_two_residual <= eta + 1.0e-12
    assert witness.root_residual <= eta + 1.0e-12
    assert witness.root_operator_norm <= 1.0 + 1.0e-12

