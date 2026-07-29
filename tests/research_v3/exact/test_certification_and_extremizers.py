from fractions import Fraction

import numpy as np

from seion_core.research_v3.extremizers import normalized_ratios, rotation_extremizer, rotation_tensor
from seion_core.research_v3.interval_certification import rotation_comb_ratio_interval
from seion_core.research_v3.operator_norms import multilinear_power_lower_bound
from seion_core.research_v3.sos_certification import certify_quadratic_on_unit_interval
from seion_core.research_v3.typed_tree import Leaf, Node


def _chain(k: int):
    tree = Node("mu", "tau", (Leaf(0, "tau"), Leaf(1, "tau")))
    next_leaf = 2
    for _ in range(1, k):
        tree = Node("mu", "tau", (tree, Leaf(next_leaf, "tau")))
        next_leaf += 1
    return tree


def test_rotation_tensor_has_exact_declared_frobenius_and_attained_norm_one():
    tensor = rotation_tensor(3, 0.2)
    bracket = multilinear_power_lower_bound(tensor, restarts=4, seed=2)
    assert np.isclose(np.linalg.norm(tensor), np.sqrt(2.0))  # rotation has two orthogonal columns
    assert bracket.lower > 0.999999
    assert bracket.upper >= bracket.lower


def test_one_node_interval_lower_construction_is_exact():
    ambient = rotation_comb_ratio_interval(1, 0.1, "ambient")
    projected = rotation_comb_ratio_interval(1, 0.1, "projected")
    normal = rotation_comb_ratio_interval(1, 0.1, "normal")
    assert ambient.lower <= 1.0 <= ambient.upper
    assert projected.lower <= 0.0 <= projected.upper
    assert normal.lower <= 1.0 <= normal.upper


def test_rotation_construction_respects_universal_bounds():
    tree = _chain(4)
    construction = rotation_extremizer(tree, 0.05)
    ratios = normalized_ratios(tree, construction)
    assert ratios["ambient"] <= 4.0 + 1e-12
    assert ratios["projected"] <= 3.0 + 1e-12
    assert ratios["normal"] <= 4.0 + 1e-12


def test_exact_quadratic_global_certificate():
    certificate = certify_quadratic_on_unit_interval(-1, 2, 0)
    assert certificate.lower == Fraction(1, 1)
    assert certificate.upper == Fraction(1, 1)
    assert certificate.status == "VERIFIED_GLOBAL_OPTIMUM_SMALL_CASE"
