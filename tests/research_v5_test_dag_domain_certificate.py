import itertools

import pytest

from seion_core.research_v5.dag_domain_certificate import (
    DAGDomainNode,
    certify_dag_domain,
    certify_dag_domain_rank_aware,
    optimal_dag_domain_ranks,
    optimal_rank_aware_dag_domain_ranks,
)


def _diamond_nodes():
    return {
        "a": DAGDomainNode("a"),
        "b": DAGDomainNode("b"),
        "u": DAGDomainNode("u", ("a", "b"), operator_bound=2.0, normal_bounds=(0.0, 0.5, 0.25, 0.1)),
        "left": DAGDomainNode(
            "left", ("u", "b"), operator_bound=3.0, normal_bounds=(0.0, 0.4, 0.2, 0.1)
        ),
        "right": DAGDomainNode(
            "right", ("a", "u"), operator_bound=5.0, normal_bounds=(0.0, 0.3, 0.15, 0.05)
        ),
        "root": DAGDomainNode("root", ("left", "right"), operator_bound=7.0, normal_bounds=(0.0, 0.0, 0.0, 0.0)),
    }


def test_dag_certificate_preserves_shared_subexpression_and_fanout_weights():
    certificate = certify_dag_domain(
        _diamond_nodes(), "root", leaf_norm_bounds={"a": 1.0, "b": 1.0}
    )

    assert certificate.topological_order == ("a", "b", "u", "left", "right", "root")
    assert certificate.value_bounds["u"] == 2.0
    assert certificate.error_bounds["left"] == pytest.approx(2.3)
    assert certificate.error_bounds["right"] == pytest.approx(3.1)
    assert certificate.root_bound == pytest.approx(291.2)
    assert certificate.downstream_gains["u"] == pytest.approx(420.0)
    assert certificate.rank_costs["u"][1] == pytest.approx(210.0)
    assert certificate.rank_costs["left"][1] == pytest.approx(56.0)
    assert certificate.rank_costs["right"][1] == pytest.approx(25.2)
    assert sum(certificate.rank_costs[node][1] for node in ("u", "left", "right")) == pytest.approx(
        certificate.root_bound
    )


def test_repeated_input_slot_is_charged_twice():
    nodes = {
        "x": DAGDomainNode("x"),
        "u": DAGDomainNode("u", ("x",), operator_bound=1.0, normal_bounds=(0.0, 0.5, 0.1)),
        "root": DAGDomainNode("root", ("u", "u"), operator_bound=1.0, normal_bounds=(0.0, 0.0)),
    }
    certificate = certify_dag_domain(nodes, "root", leaf_norm_bounds={"x": 1.0})
    assert certificate.error_bounds["u"] == pytest.approx(0.5)
    assert certificate.root_bound == pytest.approx(1.0)
    assert certificate.downstream_gains["u"] == pytest.approx(2.0)


def test_rank_dynamic_program_matches_exhaustive_diamond_search():
    nodes = _diamond_nodes()
    budget = 6
    allocation, objective = optimal_dag_domain_ranks(
        nodes, "root", leaf_norm_bounds={"a": 1.0, "b": 1.0}, budget=budget
    )
    assert set(allocation) == {"u", "left", "right"}
    actual = certify_dag_domain(nodes, "root", leaf_norm_bounds={"a": 1.0, "b": 1.0}, ranks=allocation)
    assert objective == pytest.approx(actual.root_bound)

    best = float("inf")
    for ranks in itertools.product((1, 2, 3), repeat=3):
        if sum(ranks) > budget:
            continue
        candidate = certify_dag_domain(
            nodes,
            "root",
            leaf_norm_bounds={"a": 1.0, "b": 1.0},
            ranks=dict(zip(("u", "left", "right"), ranks)),
        )
        best = min(best, candidate.root_bound)
    assert actual.root_bound == pytest.approx(best)


def test_dag_certificate_rejects_cycles_and_invalid_leaf_domains():
    with pytest.raises(ValueError, match="cycle"):
        certify_dag_domain(
            {
                "a": DAGDomainNode("a", ("b",), operator_bound=1.0, normal_bounds=(0.0, 1.0)),
                "b": DAGDomainNode("b", ("a",), operator_bound=1.0, normal_bounds=(0.0, 1.0)),
            },
            "a",
            leaf_norm_bounds={},
        )


def test_rank_aware_certificate_uses_projected_values_and_small_case_oracle():
    nodes = {
        "a": DAGDomainNode("a"),
        "b": DAGDomainNode("b"),
        "u": DAGDomainNode(
            "u", ("a", "b"), operator_bound=1.0,
            normal_bounds=(0.0, 0.4, 0.1), projected_operator_bounds=(0.0, 0.6, 0.2),
        ),
        "left": DAGDomainNode(
            "left", ("u", "b"), operator_bound=1.0,
            normal_bounds=(0.0, 0.3, 0.05), projected_operator_bounds=(0.0, 0.7, 0.2),
        ),
        "right": DAGDomainNode(
            "right", ("a", "u"), operator_bound=1.0,
            normal_bounds=(0.0, 0.25, 0.05), projected_operator_bounds=(0.0, 0.65, 0.2),
        ),
        "root": DAGDomainNode("root", ("left", "right"), operator_bound=1.0, normal_bounds=(0.0, 0.0)),
    }
    certificate = certify_dag_domain_rank_aware(
        nodes,
        "root",
        leaf_norm_bounds={"a": 1.0, "b": 1.0},
        ranks={"u": 1, "left": 2, "right": 1},
    )
    assert certificate.approximate_value_bounds["u"] == pytest.approx(0.6)
    assert certificate.exact_value_bounds["u"] == pytest.approx(1.0)
    assert certificate.root_bound > 0.0
    allocation, objective = optimal_rank_aware_dag_domain_ranks(
        nodes, "root", leaf_norm_bounds={"a": 1.0, "b": 1.0}, budget=4
    )
    assert sum(allocation.values()) <= 4
    assert objective == pytest.approx(
        certify_dag_domain_rank_aware(
            nodes, "root", leaf_norm_bounds={"a": 1.0, "b": 1.0}, ranks=allocation
        ).root_bound
    )
    with pytest.raises(ValueError, match="missing leaf"):
        certify_dag_domain(
            {"x": DAGDomainNode("x"), "root": DAGDomainNode("root", ("x",), 1.0, (0.0, 1.0))},
            "root",
            leaf_norm_bounds={},
        )
