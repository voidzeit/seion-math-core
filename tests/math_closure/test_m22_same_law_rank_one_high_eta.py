from research.math_closure.k3.m22_same_law_rank_one_high_eta import (
    evaluate_rank_one_rotation,
    exact_rank_one_same_law_chain_constant,
    verify_high_eta_regime,
)


def test_m22_rank_one_common_leaf_same_law_high_eta_is_exact() -> None:
    assert verify_high_eta_regime()
    error, norm, defect = evaluate_rank_one_rotation(1.0)
    assert norm == 1.0
    assert abs(defect - (2.0 / 3.0) ** 0.5) < 1.0e-12
    assert abs(error - 2.0 / (3.0**0.5)) < 2.0e-12
    assert abs(error - exact_rank_one_same_law_chain_constant(1.0)) < 2.0e-12
