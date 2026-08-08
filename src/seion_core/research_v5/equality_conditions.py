"""Equality-condition audit for the projected k=2 proof."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class K2EqualityCondition:
    condition_id: str
    statement: str
    status: str
    witness: str


@dataclass(frozen=True, slots=True)
class K2EqualityAudit:
    eta: float
    independent_laws: bool
    conditions: tuple[K2EqualityCondition, ...]
    conclusion: str


def audit_k2_equality_conditions(eta: float, *, independent_laws: bool = True) -> K2EqualityAudit:
    if not 0.0 < eta <= 1.0:
        raise ValueError("require 0 < eta <= 1")
    conditions = (
        K2EqualityCondition(
            "K2-EQ-01",
            "inner closure residual attains rho on projected leaf inputs",
            "COMPATIBLE",
            "rho*x0*y0*e1",
        ),
        K2EqualityCondition(
            "K2-EQ-02",
            "outer law attains M on the normal inner error and projected sibling",
            "COMPATIBLE",
            "M*x1*y0*e0",
        ),
        K2EqualityCondition(
            "K2-EQ-03",
            "root projection preserves the propagated output",
            "COMPATIBLE",
            "output is e0 in im(P)",
        ),
        K2EqualityCondition(
            "K2-EQ-04",
            "unit-leaf/state induction equalities are attained",
            "COMPATIBLE",
            "leaves are e0 and operator norms are attained on e1/e0",
        ),
        K2EqualityCondition(
            "K2-EQ-05",
            "same law must satisfy all inner and outer witness requirements",
            "OPEN_IF_REPEATED" if not independent_laws else "NOT_REQUIRED",
            "independent maps permit separate inner/outer witnesses",
        ),
    )
    conclusion = "SATURATED_BY_EXPLICIT_CONSTRUCTION" if independent_laws else "OPEN_REPEATED_LAW_COMPATIBILITY"
    return K2EqualityAudit(eta, independent_laws, conditions, conclusion)
