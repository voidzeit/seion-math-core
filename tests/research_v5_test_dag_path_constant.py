import itertools

import pytest

from seion_core.research_v4.dag_certificate import DAGNode, ScalarEdge
from seion_core.research_v5.dag_path_constant import channel_root_value, exact_dag_path_constant


def _diamond(rho: float = 0.25):
    nodes = {
        "u": DAGNode("u", rho),
        "left": DAGNode("left", rho),
        "right": DAGNode("right", rho),
        "root": DAGNode("root", 0.0),
    }
    edges = (
        ScalarEdge("u", "left", 1.0),
        ScalarEdge("u", "right", 1.0),
        ScalarEdge("left", "root", 1.0),
        ScalarEdge("right", "root", 1.0),
    )
    return nodes, edges


def test_shared_dag_path_constant_counts_all_fanout_paths():
    nodes, edges = _diamond()
    certificate = exact_dag_path_constant(nodes, edges, "root")
    assert certificate.downstream_path_weights["u"] == pytest.approx(2.0)
    assert certificate.constant == pytest.approx(4.0 * 0.25)
    assert certificate.source_contributions == {
        "u": pytest.approx(0.5),
        "left": pytest.approx(0.25),
        "right": pytest.approx(0.25),
    }


def test_nonnegative_channel_box_attains_the_constant_and_never_exceeds_it():
    nodes, edges = _diamond(rho=0.4)
    certificate = exact_dag_path_constant(nodes, edges, "root")
    for values in itertools.product((0.0, 0.2, 0.4), repeat=3):
        source_values = dict(zip(("u", "left", "right"), values))
        assert channel_root_value(source_values, nodes, edges, "root") <= certificate.constant + 1.0e-12
    attained = channel_root_value(
        {"u": 0.4, "left": 0.4, "right": 0.4}, nodes, edges, "root"
    )
    assert attained == pytest.approx(certificate.constant)


def test_parallel_edges_are_repeated_input_slots():
    nodes = {"u": DAGNode("u", 0.3), "root": DAGNode("root", 0.0)}
    edges = (ScalarEdge("u", "root", 0.8), ScalarEdge("u", "root", 0.8))
    certificate = exact_dag_path_constant(nodes, edges, "root")
    assert certificate.downstream_path_weights["u"] == pytest.approx(1.6)
    assert certificate.constant == pytest.approx(0.48)

