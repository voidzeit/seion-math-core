from seion_core.examples.registry import available_examples


def test_required_example_registry_is_present():
    required = {"zero_law", "rank_one_cp", "associative_algebra", "matrix_algebra", "lie_derived", "filippov_4d", "octonion", "random_dense", "random_scale_matched", "cyclic_random", "ill_conditioned", "known_invariant_subspace", "no_closed_subspace_control", "kernel_integrated_discrete", "torus_fourier"}
    assert required.issubset(set(available_examples()))

