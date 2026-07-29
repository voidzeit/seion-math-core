"""Gauge utilities for CP representations."""

from .cp_law import CPLaw


def gauge_equivalent(left: CPLaw, right: CPLaw, tolerance: float = 1e-10) -> bool:
    if left.arity != right.arity or left.rank != right.rank:
        return False
    return left.gauge_aligned_distance(right) <= tolerance

