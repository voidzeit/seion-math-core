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
    """Audit the k=2 saturation equality conditions EQ1-EQ3 of
    ``research_v5.k2_characterization`` (there labelled generically; the
    condition IDs below are this module's own historical numbering).

    K2-EQ-05 was resolved by the V5-B repeated-law witness
    (``k2_sharpness.construct_k2_repeated_map_saturation``): a single
    bilinear law CAN satisfy both the closure-residual saturation
    requirement (evaluated at the leaf pair) and the operator-norm
    saturation requirement (evaluated at the propagated-error/sibling pair)
    simultaneously, because a generic bilinear map can have distinct
    norm-attaining input pairs for its two structurally different terms.
    This is no longer an open compatibility question for the explicitly
    declared same-map class; it remains open only for narrower restricted
    subclasses (e.g. the gated-planar-rotation family), which this function
    does not audit.
    """

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
            "COMPATIBLE" if not independent_laws else "NOT_REQUIRED",
            "construct_k2_repeated_map_saturation exhibits mu(x,y)=M*x1*y0*e0+rho*x0*y0*e1 "
            "satisfying both requirements at once for every 0<eta<=1",
        ),
    )
    conclusion = "SATURATED_BY_EXPLICIT_CONSTRUCTION"
    return K2EqualityAudit(eta, independent_laws, conditions, conclusion)
