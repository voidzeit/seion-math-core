"""Theorem-level projected-graph research beyond the frozen finite v4 core."""

from .k2_sharpness import K2SaturationResult, construct_k2_independent_map_saturation
from .equality_conditions import K2EqualityAudit, K2EqualityCondition, audit_k2_equality_conditions
from .k3_independent_candidates import K3IndependentCandidate, construct_k3_independent_candidate
from .dag_domain_certificate import (
    DAGDomainCertificate,
    DAGDomainNode,
    DAGRankAwareCertificate,
    certify_dag_domain,
    certify_dag_domain_rank_aware,
    optimal_dag_domain_ranks,
    optimal_rank_aware_dag_domain_ranks,
)
from .dag_path_constant import ExactDAGPathConstant, channel_root_value, exact_dag_path_constant

__all__ = [
    "K2SaturationResult",
    "construct_k2_independent_map_saturation",
    "K2EqualityAudit",
    "K2EqualityCondition",
    "audit_k2_equality_conditions",
    "K3IndependentCandidate",
    "construct_k3_independent_candidate",
    "DAGDomainNode",
    "DAGDomainCertificate",
    "DAGRankAwareCertificate",
    "certify_dag_domain",
    "certify_dag_domain_rank_aware",
    "optimal_dag_domain_ranks",
    "optimal_rank_aware_dag_domain_ranks",
    "ExactDAGPathConstant",
    "exact_dag_path_constant",
    "channel_root_value",
]
