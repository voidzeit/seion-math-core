from research.math_closure.k3.m18_binary_tree_asymptotic_sharpness import (
    verify_asymptotic,
    verify_formula,
)


def test_m18_formula_for_all_small_binary_shapes() -> None:
    assert verify_formula(max_internal_nodes=5)


def test_m18_asymptotic_k_minus_one_limit() -> None:
    assert verify_asymptotic(max_internal_nodes=8)
