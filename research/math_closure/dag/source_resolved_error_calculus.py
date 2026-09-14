"""Deterministic executable witness for the finite source-calculus theorem."""

from __future__ import annotations

import numpy as np

from seion_core.research_v4.higher_order_source_polynomial import (
    PolynomialDAGNode,
    certify_source_polynomial_dag,
)
from seion_core.research_v4.signed_source_polynomial import (
    SignedPolynomialTerm,
    certify_signed_source_polynomial,
)


def _multiply(*vectors: np.ndarray) -> np.ndarray:
    result = np.array([1.0])
    for vector in vectors:
        result = result * vector
    return result


def run_checks() -> None:
    # A shared finite DAG: (1+s)(2+t)=2+2s+t+st.
    nodes = {
        "x": PolynomialDAGNode("x", 1, baseline=np.array([1.0]), local_sources={"s": np.array([1.0])}),
        "y": PolynomialDAGNode("y", 1, baseline=np.array([2.0]), local_sources={"t": np.array([1.0])}),
        "root": PolynomialDAGNode("root", 1, inputs=("x", "y"), law=_multiply),
    }
    certificate = certify_source_polynomial_dag(nodes, "root")
    expected = {(('s', 1),): 2.0, (('t', 1),): 1.0, (('s', 1), ('t', 1)): 1.0}
    assert set(certificate.output_polynomial.coefficients) == set(expected)
    for index, value in expected.items():
        assert np.allclose(certificate.output_polynomial.coefficients[index], [value])
    assert np.allclose(certificate.output_polynomial.evaluate({"s": 0.5, "t": 0.25}), [1.375])
    # The constant baseline is 2 and is intentionally not an error term.

    # Signed aggregation cancels the linear source while retaining a mixed order.
    from seion_core.research_v4.higher_order_source_polynomial import SourcePolynomial

    left = SourcePolynomial(1, {
        (('s', 1),): np.array([2.0]),
        (('s', 1), ('t', 1)): np.array([3.0]),
    })
    right = SourcePolynomial(1, {
        (('s', 1),): np.array([2.0]),
        (('s', 1), ('t', 1)): np.array([1.0]),
    })
    signed = certify_signed_source_polynomial(
        (SignedPolynomialTerm("left", 1.0, left), SignedPolynomialTerm("right", -1.0, right)),
        {"s": 0.5, "t": 0.25},
        truncation_order=1,
    )
    assert set(signed.aggregated_polynomial.coefficients) == {
        (('s', 1),), (('s', 1), ('t', 1))
    }
    assert np.allclose(signed.aggregated_polynomial.coefficients[(('s', 1),)], [0.0])
    assert np.allclose(signed.aggregated_polynomial.coefficients[(('s', 1), ('t', 1))], [2.0])
    assert signed.truncated_signed_bound == 0.0
    assert np.isclose(signed.remainder_bound, 0.25)
    assert signed.exact_polynomial_bound <= signed.treewise_bound
    print("Finite source-resolved error-calculus checks passed.")


if __name__ == "__main__":
    run_checks()
