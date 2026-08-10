from research.math_closure.k3.m19_finite_arity_asymptotic_sharpness import (
    rooted_shapes,
    verify_asymptotic,
    verify_formula,
)


def test_m19_formula_for_finite_arity_shapes() -> None:
    assert verify_formula(max_internal_nodes=3, max_arity=4)
    assert any(len(shape) == 4 for shape in rooted_shapes(1, max_arity=4) if shape)


def test_m19_asymptotic_k_minus_one_limit() -> None:
    assert verify_asymptotic(max_internal_nodes=7, max_arity=4)
