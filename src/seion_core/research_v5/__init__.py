"""Theorem-level projected-graph research beyond the frozen finite v4 core."""

from .k2_sharpness import K2SaturationResult, construct_k2_independent_map_saturation
from .equality_conditions import K2EqualityAudit, K2EqualityCondition, audit_k2_equality_conditions

__all__ = [
    "K2SaturationResult",
    "construct_k2_independent_map_saturation",
    "K2EqualityAudit",
    "K2EqualityCondition",
    "audit_k2_equality_conditions",
]
