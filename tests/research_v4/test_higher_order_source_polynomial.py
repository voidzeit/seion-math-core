import numpy as np
import pytest

from seion_core.research_v4.higher_order_source_polynomial import (
    PolynomialDAGNode,
    certify_source_polynomial_dag,
    multiindex_degree,
)


def _multiply(*vectors):
    result = np.array([1.0])
    for vector in vectors:
        result = result * vector
    return result


def test_p6b_repeated_source_produces_multiindex_count_two():
    nodes = {
        "x": PolynomialDAGNode("x", 1, baseline=np.array([1.0]), local_sources={"s": np.array([1.0])}),
        "square": PolynomialDAGNode("square", 1, inputs=("x", "x"), law=_multiply),
    }
    certificate = certify_source_polynomial_dag(nodes, "square")
    coefficients = certificate.output_polynomial.coefficients
    assert certificate.reference_checked
    assert coefficients[(('s', 1),)][0] == 2.0
    assert coefficients[(('s', 2),)][0] == 1.0
    assert multiindex_degree((('s', 2),)) == 2
    assert np.allclose(certificate.output_polynomial.evaluate({"s": 0.5}), np.array([1.25]))


def test_p6b_two_sources_produce_linear_and_mixed_terms():
    nodes = {
        "x": PolynomialDAGNode("x", 1, baseline=np.array([1.0]), local_sources={"s": np.array([1.0])}),
        "y": PolynomialDAGNode("y", 1, baseline=np.array([1.0]), local_sources={"t": np.array([1.0])}),
        "product": PolynomialDAGNode("product", 1, inputs=("x", "y"), law=_multiply),
    }
    certificate = certify_source_polynomial_dag(nodes, "product")
    coefficients = certificate.output_polynomial.coefficients
    assert set(coefficients) == {(('s', 1),), (('t', 1),), (('s', 1), ('t', 1))}
    assert all(np.allclose(coefficients[index], np.array([1.0])) for index in coefficients)
    assert np.allclose(certificate.output_polynomial.evaluate({"s": 2.0, "t": 3.0}), np.array([11.0]))


def test_p6b_shared_subexpression_is_cached_but_matches_reference():
    nodes = {
        "x": PolynomialDAGNode("x", 1, baseline=np.array([1.0]), local_sources={"s": np.array([1.0])}),
        "double": PolynomialDAGNode("double", 1, inputs=("x",), law=lambda value: 2.0 * value),
        "combine": PolynomialDAGNode("combine", 1, inputs=("double", "double"), law=_multiply),
    }
    certificate = certify_source_polynomial_dag(nodes, "combine")
    assert certificate.reference_checked
    assert certificate.topological_order == ("x", "double", "combine")
    assert np.allclose(certificate.output_polynomial.evaluate({"s": 0.25}), np.array([2.25]))


def test_p6b_projected_root_removes_root_closure_source():
    projector = np.diag([1.0, 0.0])
    nodes = {
        "x": PolynomialDAGNode(
            "x", 2, baseline=np.array([1.0, 1.0]), local_sources={"s": np.array([1.0, 0.0])}
        ),
        "root": PolynomialDAGNode(
            "root", 2, inputs=("x",), law=lambda value: value, projector=projector
        ),
    }
    certificate = certify_source_polynomial_dag(nodes, "root", project_output=True)
    assert set(certificate.output_polynomial.coefficients) == {(('s', 1),)}
    assert np.allclose(certificate.output_polynomial.evaluate({"s": 2.0}), np.array([2.0, 0.0]))


def test_p6b_truncation_has_certified_remainder_for_orders_one_two_three():
    nodes = {
        "x": PolynomialDAGNode("x", 1, baseline=np.array([1.0]), local_sources={"s": np.array([1.0])}),
        "square": PolynomialDAGNode("square", 1, inputs=("x", "x"), law=_multiply),
    }
    polynomial = certify_source_polynomial_dag(nodes, "square").output_polynomial
    amplitudes = {"s": 0.5}
    exact = polynomial.evaluate(amplitudes)
    order_one = polynomial.truncate(1, amplitudes)
    order_two = polynomial.truncate(2, amplitudes)
    order_three = polynomial.truncate(3, amplitudes)
    assert order_one.omitted_terms == 1
    assert order_one.remainder_bound == 0.25
    assert np.linalg.norm(exact - order_one.evaluate(amplitudes)) <= order_one.remainder_bound
    assert order_two.omitted_terms == 0
    assert order_two.remainder_bound == 0.0
    assert order_three.omitted_terms == 0
    assert order_three.remainder_bound == 0.0


def test_p6b_supports_complex_sources():
    nodes = {
        "x": PolynomialDAGNode(
            "x", 1, baseline=np.array([1.0 + 0.0j]), local_sources={"s": np.array([1.0j])}
        ),
        "square": PolynomialDAGNode("square", 1, inputs=("x", "x"), law=_multiply),
    }
    certificate = certify_source_polynomial_dag(nodes, "square")
    assert np.allclose(certificate.output_polynomial.evaluate({"s": 1.0}), np.array([2.0j - 1.0]))


def test_p6b_rejects_cycles_and_dimension_mismatch():
    with pytest.raises(ValueError, match="cycle"):
        certify_source_polynomial_dag(
            {
                "a": PolynomialDAGNode("a", 1, inputs=("b",), law=lambda value: value),
                "b": PolynomialDAGNode("b", 1, inputs=("a",), law=lambda value: value),
            },
            "b",
        )
    with pytest.raises(ValueError, match="dimension"):
        certify_source_polynomial_dag(
            {
                "x": PolynomialDAGNode("x", 1, baseline=np.array([1.0])),
                "root": PolynomialDAGNode("root", 2, inputs=("x",), law=lambda value: value),
            },
            "root",
        )
