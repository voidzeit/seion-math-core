"""Research-v4 projected-tree frontier utilities."""

from .dag_certificate import DAGCertificate, DAGNode, ScalarEdge, certify_dag_scalar
from .equality_slack import EqualityAudit, audit_projected_bound_equalities
from .signed_certificate import SignedSourceCertificate, SignedSourceTerm, certify_signed_source_forest
from .source_aware_dag import (
    SourceAwareDAGCertificate,
    VectorDAGEdge,
    VectorDAGNode,
    certify_source_aware_dag,
)
from .higher_order_source_polynomial import (
    MultiIndex,
    PolynomialDAGNode,
    SourcePolynomial,
    SourcePolynomialCertificate,
    TruncationResult,
    certify_source_polynomial_dag,
    multiindex_degree,
)
from .signed_source_polynomial import (
    SignedPolynomialTerm,
    SignedSourcePolynomialCertificate,
    certify_signed_source_polynomial,
)
from .signed_compositional_expression import (
    CompositionalTerm,
    SignedCompositionalExpression,
    SignedCompositionalExpressionCertificate,
    certify_signed_compositional_expression,
    make_associator_expression,
    make_filippov_defect_expression,
    make_jacobiator_expression,
)

__all__ = [
    "DAGCertificate",
    "DAGNode",
    "ScalarEdge",
    "EqualityAudit",
    "audit_projected_bound_equalities",
    "certify_dag_scalar",
    "SourceAwareDAGCertificate",
    "VectorDAGEdge",
    "VectorDAGNode",
    "certify_source_aware_dag",
    "SignedSourceCertificate",
    "SignedSourceTerm",
    "certify_signed_source_forest",
    "MultiIndex",
    "PolynomialDAGNode",
    "SourcePolynomial",
    "SourcePolynomialCertificate",
    "TruncationResult",
    "certify_source_polynomial_dag",
    "multiindex_degree",
    "SignedPolynomialTerm",
    "SignedSourcePolynomialCertificate",
    "certify_signed_source_polynomial",
    "CompositionalTerm",
    "SignedCompositionalExpression",
    "SignedCompositionalExpressionCertificate",
    "certify_signed_compositional_expression",
    "make_associator_expression",
    "make_jacobiator_expression",
    "make_filippov_defect_expression",
]
