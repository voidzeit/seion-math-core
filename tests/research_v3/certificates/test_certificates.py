import math

import numpy as np

from seion_core.research_v3.certificates import (
    LocalSummary,
    certify_tree,
    homogeneous_ambient_bound,
    homogeneous_projected_bound,
)
from seion_core.research_v3.extremizers import rotation_extremizer
from seion_core.research_v3.mixed_norms import compute_mixed_norms
from seion_core.research_v3.projected_evaluation import compute_tree_errors
from seion_core.research_v3.typed_tree import Leaf, Node


def _binary_chain():
    child = Node("inner", "tau", (Leaf(0, "tau"), Leaf(1, "tau")))
    return Node("root", "tau", (child, Leaf(2, "tau")))


def test_homogeneous_k_and_projected_k_minus_one_recurrence():
    tree = _binary_chain()
    summaries = {
        "inner": LocalSummary("inner", M=1.0, m=1.0, rho=0.1),
        "root": LocalSummary("root", M=1.0, m=1.0, rho=0.1),
    }
    certificate = certify_tree(
        tree, summaries, [1.0, 1.0, 1.0], homogeneous_M=1.0, homogeneous_rho=0.1
    )
    assert certificate.homogeneous_ambient == 0.2
    assert certificate.homogeneous_projected == 0.1
    assert certificate.root.B_A <= 0.2 + 1e-15
    assert certificate.root.B_P <= 0.1 + 1e-15
    assert math.isclose(sum(certificate.root.ambient_contributions.values()), certificate.root.path_sum_A)
    assert math.isclose(
        sum(certificate.root.projected_contributions.values()), certificate.root.path_sum_P
    )
    assert () not in certificate.root.projected_contributions


def test_mixed_mask_certificate_bounds_observed_rotation_errors():
    tree = _binary_chain()
    construction = rotation_extremizer(tree, eta=0.1)
    summaries = {}
    for law_id, law in construction.laws.items():
        mixed = compute_mixed_norms(law, construction.types, lower_restarts=2)
        summaries[law_id] = LocalSummary(law_id, M=1.0, m=1.0, rho=0.1, mixed=mixed)
    certificate = certify_tree(tree, summaries, [1.0, 1.0, 1.0])
    errors = compute_tree_errors(
        tree, construction.laws, construction.types, construction.reduced_inputs
    )
    assert errors.ambient <= certificate.root.B_A + 1e-12
    assert errors.projected_root <= certificate.root.B_P + 1e-12
    assert errors.normal_root <= certificate.root.B_N + 1e-12


def test_closed_form_bounds_have_named_zero_node_and_one_node_behavior():
    assert homogeneous_ambient_bound(0, 3.0, 0.2) == 0.0
    assert homogeneous_projected_bound(1, 3.0, 0.2) == 0.0
    assert math.isclose(homogeneous_projected_bound(4, 2.0, 0.1), 2.4)
