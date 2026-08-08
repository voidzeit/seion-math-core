import numpy as np

from seion_core.research_v4.higher_order_source_polynomial import PolynomialDAGNode, SourcePolynomial, certify_source_polynomial_dag
from seion_core.research_v4.signed_compositional_expression import (
    CompositionalTerm,
    SignedCompositionalExpression,
    certify_signed_compositional_expression,
    make_associator_expression,
    make_filippov_defect_expression,
    make_jacobiator_expression,
)


def poly(*items):
    return SourcePolynomial(1, {index: np.array([value]) for index, value in items})


def test_p7c_associator_is_a_regression_case_of_generic_engine():
    expression = make_associator_expression(
        poly(((('s', 1),), 1.0), ((('s', 2),), 2.0)),
        poly(((('s', 1),), 1.0), ((('s', 2),), 1.0)),
    )
    certificate = certify_signed_compositional_expression(expression, {"s": 0.5})
    assert certificate.expression_kind == "ASSOCIATOR_CERTIFICATE"
    assert certificate.signed_bound == 0.25
    assert certificate.treewise_bound == 1.75
    assert certificate.actual_norm <= certificate.signed_bound


def test_p7c_jacobiator_exact_and_partial_defects_without_assuming_zero():
    exact = make_jacobiator_expression(poly(((('s', 1),), 1.0)), poly(((('s', 1),), 1.0)), poly(((('s', 1),), -2.0)))
    exact_certificate = exact.certify({"s": 1.0})
    assert exact_certificate.expression_kind == "JACOBIATOR_CERTIFICATE"
    assert exact_certificate.actual_norm == 0.0
    assert exact_certificate.signed_bound == 0.0

    false_identity = make_jacobiator_expression(poly(((('s', 1),), 1.0)), poly(((('s', 1),), 1.0)), poly(((('s', 1),), 1.0)))
    false_certificate = false_identity.certify({"s": 1.0})
    assert false_certificate.actual_norm == 3.0
    assert false_certificate.signed_bound == 3.0


def test_p7c_filippov_defect_preserves_repeated_and_mixed_orders():
    expression = make_filippov_defect_expression(
        poly(((('s', 2),), 2.0), ((('s', 1), ('t', 1)), 1.0)),
        [
            poly(((('s', 2),), 1.0), ((('s', 1), ('t', 1)), 0.5)),
            poly(((('s', 2),), 0.5), ((('s', 1), ('t', 1)), 0.25)),
        ],
    )
    certificate = expression.certify({"s": 1.0, "t": 2.0})
    assert certificate.expression_kind == "FILIPPOV_DEFECT_CERTIFICATE"
    assert set(certificate.certificate.aggregated_polynomial.coefficients) == {
        (('s', 2),),
        (('s', 1), ('t', 1)),
    }
    assert certificate.actual_norm <= certificate.signed_bound <= certificate.treewise_bound


def test_p7c_truncation_is_conservative_for_jacobiator():
    expression = make_jacobiator_expression(
        poly(((('s', 1),), 1.0), ((('s', 2),), 2.0)),
        poly(((('s', 2),), 1.0)),
        poly(((('s', 1), ('t', 1)), 3.0)),
    )
    certificate = expression.certify({"s": 0.5, "t": 0.5}, truncation_order=1)
    assert certificate.total_certified_bound >= certificate.actual_norm
    assert certificate.signed_bound <= certificate.treewise_bound
    assert certificate.remainder_bound > 0.0


def test_p7c_complex_projected_root_and_direct_reconstruction():
    projector = np.diag([1.0, 0.0])
    nodes = {
        "x": PolynomialDAGNode("x", 2, baseline=np.array([1.0, 1.0]), local_sources={"s": np.array([1.0j, 0.0j])}),
        "root": PolynomialDAGNode("root", 2, inputs=("x",), law=lambda value: value, projector=projector),
    }
    left = certify_source_polynomial_dag(nodes, "root", project_output=True).output_polynomial
    right = SourcePolynomial(2, {(("s", 1),): np.array([0.5j, 0.0j])})
    expression = make_associator_expression(left, right)
    certificate = expression.certify({"s": 1.0})
    direct = left.evaluate({"s": 1.0}) - right.evaluate({"s": 1.0})
    assert np.allclose(certificate.certificate.direct_value, direct)
    assert certificate.actual_norm <= certificate.signed_bound <= certificate.treewise_bound


def test_p7c_generic_expression_rejects_duplicate_term_ids():
    expression_terms = (
        CompositionalTerm("same", 1.0, poly(((('s', 1),), 1.0))),
        CompositionalTerm("same", -1.0, poly(((('s', 1),), 1.0))),
    )
    try:
        SignedCompositionalExpression("bad", "TEST", expression_terms)
    except ValueError as error:
        assert "unique" in str(error)
    else:
        raise AssertionError("duplicate term ids should be rejected")
