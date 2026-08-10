import pytest

from seion_core.research_v4.dag_certificate import DAGNode, ScalarEdge
from seion_core.research_v5.dag_asymptotic_sharpness import (
    complex_product_witness_ratio,
    exact_dag_asymptotic_path_constant,
)


def _chain_graph():
    nodes = {f"x{i}": DAGNode(f"x{i}", 0.0) for i in range(5)}
    nodes.update({f"n{i}": DAGNode(f"n{i}", 0.0) for i in range(4)})
    edges = (
        ScalarEdge("x0", "n0", 1.0), ScalarEdge("x1", "n0", 1.0),
        ScalarEdge("n0", "n1", 1.0), ScalarEdge("x2", "n1", 1.0),
        ScalarEdge("n1", "n2", 1.0), ScalarEdge("x3", "n2", 1.0),
        ScalarEdge("n2", "n3", 1.0), ScalarEdge("x4", "n3", 1.0),
    )
    return nodes, edges


def _diamond_graph():
    nodes = {name: DAGNode(name, 0.0) for name in ("x0", "x1", "x2", "u", "left", "right", "root")}
    edges = (
        ScalarEdge("x0", "u", 1.0), ScalarEdge("x1", "u", 1.0),
        ScalarEdge("u", "left", 1.0), ScalarEdge("x2", "left", 1.0),
        ScalarEdge("x0", "right", 1.0), ScalarEdge("u", "right", 1.0),
        ScalarEdge("left", "root", 1.0), ScalarEdge("right", "root", 1.0),
    )
    return nodes, edges


def test_fixed_chain_and_shared_diamond_have_exact_path_counts():
    chain_nodes, chain_edges = _chain_graph()
    chain = exact_dag_asymptotic_path_constant(
        chain_nodes, chain_edges, "n3", projected_nodes=("n0", "n1", "n2")
    )
    assert chain.asymptotic_constant == pytest.approx(3.0)
    diamond_nodes, diamond_edges = _diamond_graph()
    diamond = exact_dag_asymptotic_path_constant(
        diamond_nodes, diamond_edges, "root", projected_nodes=("u", "left", "right")
    )
    assert diamond.path_weights == {"u": 2.0, "left": 1.0, "right": 1.0}
    assert diamond.asymptotic_constant == pytest.approx(4.0)


def test_complex_witness_reaches_every_fixed_dag_path_constant_asymptotically():
    for count in (1, 3, 4, 7):
        assert complex_product_witness_ratio(count, 1.0e-5) == pytest.approx(count, abs=1.0e-4)

