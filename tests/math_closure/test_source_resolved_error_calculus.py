import numpy as np

from research.math_closure.dag.source_resolved_error_calculus import run_checks
from seion_core.research_v4.higher_order_source_polynomial import (
    PolynomialDAGNode,
    certify_source_polynomial_dag,
)


def test_canonical_source_calculus_witness():
    run_checks()


def test_projected_root_removes_closure_source_in_canonical_package():
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
    assert np.allclose(certificate.output_polynomial.evaluate({"s": 2.0}), [2.0, 0.0])
