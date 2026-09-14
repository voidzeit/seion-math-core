from research.math_closure.k3.m20_k3_arbitrary_arity_exact_constant import (
    rooted_shapes,
    topology_kind,
    verify_all_finite_arity_k3,
)


def test_m20_all_k3_arity_profiles_reduce_to_chain_or_branch() -> None:
    shapes = rooted_shapes(3, max_arity=4)
    assert shapes
    assert {topology_kind(shape) for shape in shapes} == {"chain", "branch"}
    assert verify_all_finite_arity_k3(max_arity=4)
