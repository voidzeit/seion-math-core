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
from .operator_norm_enclosures import (
    NormEnclosure,
    cp_enclosure,
    enclose_multilinear_norm,
    exact_rank_one_enclosure,
    flattening_enclosure,
    frobenius_enclosure,
    validated_interval_enclosure,
)
from .certificate_selector import CertificateCandidate, CertificateSelection, select_best_sound_certificate
from .approximate_law_error import ApproximateLawBudget, homogeneous_approximate_law_budget, nodewise_approximate_law_budget
from .topology_registry import TopologyMetrics, compute_topology_metrics, universal_topology_bound
from .extremal_registry import ExtremalRecord, merge_extremal_records

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
    "NormEnclosure",
    "frobenius_enclosure",
    "flattening_enclosure",
    "validated_interval_enclosure",
    "cp_enclosure",
    "exact_rank_one_enclosure",
    "enclose_multilinear_norm",
    "CertificateCandidate",
    "CertificateSelection",
    "select_best_sound_certificate",
    "ApproximateLawBudget",
    "homogeneous_approximate_law_budget",
    "nodewise_approximate_law_budget",
    "TopologyMetrics",
    "compute_topology_metrics",
    "universal_topology_bound",
    "ExtremalRecord",
    "merge_extremal_records",
]
