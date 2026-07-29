import numpy as np

from seion_core.research_v3.certificates import homogeneous_projected_bound
from seion_core.research_v3.extremizers import rotation_extremizer
from seion_core.research_v3.projected_evaluation import compute_tree_errors
from seion_core.research_v3.tree_enumeration import full_ordered_shapes, label_shape
from seion_core.research_v3.typed_tree import iter_internal


def test_projected_k_minus_one_on_every_binary_shape_through_six_for_rotation_family():
    eta = 0.07
    maximum_ratio = 0.0
    checked = 0
    for k in range(1, 7):
        bound = homogeneous_projected_bound(k, 1.0, eta)
        for shape in full_ordered_shapes(k, 2):
            tree = label_shape(shape)
            construction = rotation_extremizer(tree, eta)
            errors = compute_tree_errors(
                tree, construction.laws, construction.types, construction.reduced_inputs
            )
            assert errors.projected_root <= bound + 2e-12
            if bound:
                maximum_ratio = max(maximum_ratio, errors.projected_root / bound)
            checked += 1
    assert checked == 196
    assert maximum_ratio <= 1.0
