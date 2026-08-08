"""Theorem-level projected-graph research beyond the frozen finite v4 core."""

from .k2_sharpness import K2SaturationResult, construct_k2_independent_map_saturation
from .equality_conditions import K2EqualityAudit, K2EqualityCondition, audit_k2_equality_conditions
from .k3_independent_candidates import K3IndependentCandidate, construct_k3_independent_candidate

__all__ = [
    "K2SaturationResult",
    "construct_k2_independent_map_saturation",
    "K2EqualityAudit",
    "K2EqualityCondition",
    "audit_k2_equality_conditions",
    "K3IndependentCandidate",
    "construct_k3_independent_candidate",
]
