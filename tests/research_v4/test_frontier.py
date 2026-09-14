import math

import pytest

from seion_core.research_v4.dag_certificate import DAGNode, ScalarEdge, certify_dag_scalar
from seion_core.research_v4.equality_slack import audit_projected_bound_equalities


def test_equality_slack_audit_separates_exact_root_cancellation_from_inequalities():
    rows = audit_projected_bound_equalities()
    assert rows[0].step_id == "P1-01"
    assert rows[0].unavoidable_slack is False
    assert all(row.unavoidable_slack for row in rows[1:])
    assert rows[-1].status == "OPEN_SHARPNESS_CONDITION"


def test_dag_source_resolved_certificate_handles_shared_source_without_unrolling():
    nodes = {"u": DAGNode("u", 0.1), "v1": DAGNode("v1", 0.2), "v2": DAGNode("v2", 0.3), "root": DAGNode("root", 0.4)}
    edges = (ScalarEdge("u", "v1", 2.0), ScalarEdge("u", "v2", 3.0), ScalarEdge("v1", "root", 4.0), ScalarEdge("v2", "root", 5.0))
    certificate = certify_dag_scalar(nodes, edges, "root")
    assert certificate.topological_order == ("u", "v1", "v2", "root")
    assert math.isclose(certificate.forward_bounds["root"], 5.0)
    assert math.isclose(certificate.reverse_weights["u"], 23.0)
    assert math.isclose(sum(certificate.source_contributions.values()), 5.0)


def test_projected_root_omits_root_local_source_exactly():
    nodes = {"child": DAGNode("child", 0.25), "root": DAGNode("root", 0.9)}
    certificate = certify_dag_scalar(nodes, (ScalarEdge("child", "root", 2.0),), "root", include_root_source=False)
    assert math.isclose(certificate.root_bound, 0.5)
    assert "root" not in certificate.source_contributions
    assert math.isclose(certificate.source_contributions["child"], 0.5)


def test_dag_cycle_is_rejected():
    nodes = {"a": DAGNode("a", 0.1), "b": DAGNode("b", 0.2)}
    with pytest.raises(ValueError, match="cycle"):
        certify_dag_scalar(nodes, (ScalarEdge("a", "b", 1.0), ScalarEdge("b", "a", 1.0)), "b")
