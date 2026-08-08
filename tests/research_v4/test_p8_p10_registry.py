import numpy as np
import pytest

from seion_core.research_v4.approximate_law_error import homogeneous_approximate_law_budget, nodewise_approximate_law_budget
from seion_core.research_v4.certificate_selector import CertificateCandidate, select_best_sound_certificate
from seion_core.research_v4.operator_norm_enclosures import (
    cp_enclosure,
    exact_rank_one_enclosure,
    flattening_enclosure,
    frobenius_enclosure,
    validated_interval_enclosure,
)
from seion_core.research_v4.topology_registry import compute_topology_metrics, universal_topology_bound


def test_p8_certified_matrix_flattening_and_frobenius_enclosures():
    identity = np.eye(2)
    flattening = flattening_enclosure(identity)
    frobenius = frobenius_enclosure(identity)
    interval = validated_interval_enclosure(identity)
    assert flattening.certified and frobenius.certified and interval.certified
    assert flattening.lower <= 1.0 <= flattening.upper
    assert frobenius.upper >= np.sqrt(2.0)
    assert interval.upper >= np.sqrt(2.0)
    assert "power" not in flattening.method.lower()


def test_p8_cp_and_rank_one_exact_paths_are_explicit():
    factors = (np.array([1.0, 0.0]), np.array([2.0, 0.0]))
    exact = exact_rank_one_enclosure(3.0, factors)
    cp = cp_enclosure([3.0], [factors])
    assert exact.lower == exact.upper == 6.0
    assert cp.certified and cp.upper >= 6.0
    assert cp.method == "cp_structural"


def test_p8_selector_uses_only_certified_upper_bounds():
    selection = select_best_sound_certificate(
        (
            CertificateCandidate("frobenius", 4.0, True),
            CertificateCandidate("flattening", 2.0, True),
            CertificateCandidate("power_iteration", 0.5, False),
        )
    )
    assert selection.selected.name == "flattening"
    assert [item.name for item in selection.rejected_uncertified] == ["power_iteration"]
    with pytest.raises(ValueError, match="no sound"):
        select_best_sound_certificate((CertificateCandidate("heuristic", 0.1, False),))


def test_p10_separates_representation_closure_and_interaction():
    budget = homogeneous_approximate_law_budget(
        internal_nodes=3,
        exact_norm=2.0,
        representation_error=0.1,
        closure_residual=0.2,
        projected_root=True,
    )
    assert budget.certified
    assert budget.closure_contribution == 1.6
    assert budget.representation_contribution == 3 * 0.1 * 2.1**2
    assert budget.interaction_contribution == 2 * 0.2 * (2.1**2 - 2.0**2)
    assert budget.total == budget.closure_contribution + budget.representation_contribution + budget.interaction_contribution


def test_p10_nodewise_budget_is_conservative_maximum_reduction():
    budget = nodewise_approximate_law_budget([1.0, 2.0], [0.1, 0.2], [0.05, 0.1], projected_root=True)
    reference = homogeneous_approximate_law_budget(
        internal_nodes=2, exact_norm=2.0, representation_error=0.2, closure_residual=0.1, projected_root=True
    )
    assert budget.total == reference.total


def test_topology_registry_records_diamond_and_universal_bound_without_claiming_sharpness():
    topology = {
        "u": (),
        "a": ("u",),
        "b": ("u",),
        "root": ("a", "b"),
    }
    metrics = compute_topology_metrics(topology, "root")
    assert metrics.depth == 2
    assert metrics.max_fan_out == 2
    assert metrics.path_count_to_root == 2
    bound = universal_topology_bound(internal_nodes=3, closure_residual=0.5, operator_norm=1.0)
    assert bound == 1.0

