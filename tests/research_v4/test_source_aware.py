import numpy as np
import pytest

from seion_core.research_v4.signed_certificate import SignedSourceTerm, certify_signed_source_forest
from seion_core.research_v4.source_aware_dag import VectorDAGEdge, VectorDAGNode, certify_source_aware_dag


def test_p6a_aggregates_shared_source_before_taking_norm_at_fanin():
    nodes = {
        "u": VectorDAGNode("u", 1, {"s": np.array([[1.0]])}),
        "a": VectorDAGNode("a", 1),
        "b": VectorDAGNode("b", 1),
        "root": VectorDAGNode("root", 1),
    }
    edges = (
        VectorDAGEdge("u", "a", np.array([[1.0]])),
        VectorDAGEdge("u", "b", np.array([[-1.0]])),
        VectorDAGEdge("a", "root", np.array([[1.0]])),
        VectorDAGEdge("b", "root", np.array([[1.0]])),
    )
    certificate = certify_source_aware_dag(nodes, edges, "root", {"s": np.array([2.0])})
    assert np.allclose(certificate.coefficient_maps["root"]["s"], np.zeros((1, 1)))
    assert np.allclose(certificate.forward_error, np.zeros(1))
    assert certificate.source_aware_bound == 0.0
    assert certificate.pathwise_triangle_bound == 4.0
    assert certificate.no_worse_than_pathwise


def test_p6a_preserves_multiple_sources_and_runs_in_linear_graph_mode():
    nodes = {
        "u": VectorDAGNode("u", 2, {"s": np.eye(2)}),
        "root": VectorDAGNode("root", 2, {"t": np.eye(2)}),
    }
    edges = (VectorDAGEdge("u", "root", 2.0 * np.eye(2)),)
    certificate = certify_source_aware_dag(
        nodes,
        edges,
        "root",
        {"s": np.array([1.0, 0.0]), "t": np.array([0.0, 3.0])},
    )
    assert certificate.complexity == "O(|V|+|E|)"
    assert np.allclose(certificate.forward_error, np.array([2.0, 3.0]))
    assert certificate.source_aware_bound == certificate.pathwise_triangle_bound


def test_p6a_projected_root_omits_root_local_source():
    nodes = {
        "u": VectorDAGNode("u", 1, {"s": np.array([[1.0]])}),
        "root": VectorDAGNode("root", 1, {"root_source": np.array([[5.0]])}),
    }
    certificate = certify_source_aware_dag(
        nodes,
        (VectorDAGEdge("u", "root", np.array([[2.0]])),),
        "root",
        {"s": np.array([3.0]), "root_source": np.array([7.0])},
        include_root_sources=False,
    )
    assert set(certificate.coefficient_maps["root"]) == {"s"}
    assert np.allclose(certificate.forward_error, np.array([6.0]))


def test_p6a_rejects_edge_shape_and_cycles():
    nodes = {"a": VectorDAGNode("a", 1), "b": VectorDAGNode("b", 2)}
    with pytest.raises(ValueError, match="shape"):
        certify_source_aware_dag(
            nodes,
            (VectorDAGEdge("a", "b", np.ones((1, 1))),),
            "b",
            {},
        )
    with pytest.raises(ValueError, match="cycle"):
        certify_source_aware_dag(
            {"a": VectorDAGNode("a", 1), "b": VectorDAGNode("b", 1)},
            (VectorDAGEdge("a", "b", np.ones((1, 1))), VectorDAGEdge("b", "a", np.ones((1, 1)))),
            "b",
            {},
        )


def test_p7a_signed_source_aggregation_preserves_associator_cancellation():
    terms = (
        SignedSourceTerm("left", 1.0, {"s": np.array([[1.0]])}),
        SignedSourceTerm("right", -1.0, {"s": np.array([[1.0]])}),
    )
    certificate = certify_signed_source_forest(terms, {"s": np.array([2.0])})
    assert np.allclose(certificate.aggregated_operators["s"], np.zeros((1, 1)))
    assert certificate.signed_bound == 0.0
    assert certificate.naive_treewise_bound == 4.0
    assert certificate.strict_improvement


def test_p7a_signed_bound_is_never_larger_than_treewise_triangle_bound():
    terms = (
        SignedSourceTerm("left", 2.0, {"s": np.array([[1.0], [0.0]])}),
        SignedSourceTerm("right", -1.0, {"s": np.array([[0.0], [1.0]])}),
    )
    certificate = certify_signed_source_forest(terms, {"s": np.array([3.0])})
    assert certificate.signed_bound <= certificate.naive_treewise_bound

