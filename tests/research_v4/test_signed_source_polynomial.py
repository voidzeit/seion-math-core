import numpy as np

from seion_core.research_v4.higher_order_source_polynomial import PolynomialDAGNode, certify_source_polynomial_dag
from seion_core.research_v4.signed_source_polynomial import (
    SignedPolynomialTerm,
    certify_signed_source_polynomial,
)


def polynomial(*items):
    from seion_core.research_v4.higher_order_source_polynomial import SourcePolynomial

    return SourcePolynomial(1, {index: np.array([value]) for index, value in items})


def test_p7b_first_order_cancellation_recovers_p7a():
    terms = (
        SignedPolynomialTerm("left", 1.0, polynomial(((('s', 1),), 1.0))),
        SignedPolynomialTerm("right", -1.0, polynomial(((('s', 1),), 1.0))),
    )
    certificate = certify_signed_source_polynomial(terms, {"s": 2.0})
    assert certificate.actual_norm == 0.0
    assert certificate.exact_polynomial_bound == 0.0
    assert certificate.treewise_bound == 4.0
    assert certificate.strict_improvement


def test_p7b_pure_second_order_partial_cancellation():
    terms = (
        SignedPolynomialTerm("left", 1.0, polynomial(((('s', 2),), 2.0))),
        SignedPolynomialTerm("right", -1.0, polynomial(((('s', 2),), 1.0))),
    )
    certificate = certify_signed_source_polynomial(terms, {"s": 1.0})
    assert np.allclose(certificate.aggregated_polynomial.coefficients[(('s', 2),)], np.array([1.0]))
    assert certificate.exact_polynomial_bound == 1.0
    assert certificate.treewise_bound == 3.0
    assert certificate.actual_norm <= certificate.exact_polynomial_bound


def test_p7b_mixed_second_order_exact_cancellation():
    terms = (
        SignedPolynomialTerm("left", 1.0, polynomial(((('s', 1), ('t', 1)), 3.0))),
        SignedPolynomialTerm("right", -1.0, polynomial(((('s', 1), ('t', 1)), 3.0))),
    )
    certificate = certify_signed_source_polynomial(terms, {"s": 2.0, "t": 0.5})
    assert set(certificate.aggregated_polynomial.coefficients) == {(('s', 1), ('t', 1))}
    assert certificate.exact_polynomial_bound == 0.0
    assert certificate.treewise_bound == 6.0


def test_p7b_independent_sources_do_not_fuse():
    terms = (
        SignedPolynomialTerm("left", 1.0, polynomial(((('s', 2),), 1.0))),
        SignedPolynomialTerm("right", -1.0, polynomial(((('t', 2),), 1.0))),
    )
    certificate = certify_signed_source_polynomial(terms, {"s": 1.0, "t": 1.0})
    assert set(certificate.aggregated_polynomial.coefficients) == {(('s', 2),), (('t', 2),)}
    assert certificate.exact_polynomial_bound == certificate.treewise_bound == 2.0


def test_p7b_truncated_bound_carries_signed_remainder():
    terms = (
        SignedPolynomialTerm(
            "left",
            1.0,
            polynomial(((('s', 1),), 1.0), ((('s', 2),), 2.0)),
        ),
        SignedPolynomialTerm("right", -1.0, polynomial(((('s', 2),), 1.0))),
    )
    certificate = certify_signed_source_polynomial(terms, {"s": 0.5}, truncation_order=1)
    assert certificate.truncated_signed_bound == 0.5
    assert certificate.remainder_bound == 0.25
    assert certificate.total_certified_bound == certificate.exact_polynomial_bound == 0.75
    assert certificate.treewise_bound == 1.25


def test_p7b_projected_root_polynomials_and_complex_data():
    projector = np.diag([1.0, 0.0])
    nodes = {
        "x": PolynomialDAGNode("x", 2, baseline=np.array([1.0, 1.0]), local_sources={"s": np.array([1.0j, 0.0j])}),
        "root": PolynomialDAGNode("root", 2, inputs=("x",), law=lambda value: value, projector=projector),
    }
    projected = certify_source_polynomial_dag(nodes, "root", project_output=True).output_polynomial
    term = SignedPolynomialTerm("left", 1.0 + 0.0j, projected)
    certificate = certify_signed_source_polynomial((term,), {"s": 1.0})
    assert set(certificate.aggregated_polynomial.coefficients) == {(('s', 1),)}
    assert np.allclose(certificate.direct_value, np.array([1.0j, 0.0j]))
    assert certificate.actual_norm <= certificate.exact_polynomial_bound
