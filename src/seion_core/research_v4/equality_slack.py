"""P1 equality/slack audit for the projected-root ``(k-1)`` bound."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any


@dataclass(frozen=True, slots=True)
class EqualityAudit:
    """One proof step and its equality conditions."""

    step_id: str
    operation: str
    inequality_or_identity: str
    equality_condition: str
    unavoidable_slack: bool
    status: str = "AUDIT_ONLY"

    def as_dict(self) -> dict[str, Any]:
        return asdict(self)


def audit_projected_bound_equalities() -> tuple[EqualityAudit, ...]:
    """Return the equality/slack ledger for the homogeneous projected proof."""

    return (
        EqualityAudit("P1-01", "root projection", "P(I-P)=0", "exact identity for an orthogonal projection", False, "PROVED"),
        EqualityAudit("P1-02", "projection contractivity", "||Px|| <= ||x||", "x is in range(P), or x=0", True),
        EqualityAudit("P1-03", "multilinear telescoping", "||sum_j t_j|| <= sum_j ||t_j||", "all nonzero replacement terms are positively collinear (same phase over C)", True),
        EqualityAudit("P1-04", "operator norm application", "||mu(x_1,...,x_a)|| <= M product_i ||x_i||", "the input tuple attains the operator norm of mu", True),
        EqualityAudit("P1-05", "local closure bound", "||r_v(R)|| <= rho product_i ||R_i||", "the projected tuple attains the closure-map norm and all state bounds are tight", True),
        EqualityAudit("P1-06", "child magnitude induction", "||F_v||,||R_v|| <= M^(k_v)L_v", "every ancestor composition and projection is norm-preserving on the realized states", True),
        EqualityAudit("P1-07", "source accumulation", "sum of k-1 propagated source bounds", "every non-root source and every propagation step saturates with compatible directions/phases", True),
        EqualityAudit("P1-08", "fixed-eta compatibility", "simultaneous saturation of P1-03 through P1-07", "compatibility is not established in the general class", True, "OPEN_SHARPNESS_CONDITION"),
    )


def equality_audit_report() -> dict[str, Any]:
    return {
        "schema": "projected-tree-equality-slack-audit-v1",
        "theorem_target": "E_proj <= (k-1) rho M^(k-1) L_T",
        "root_residual_behavior": "exactly annihilated by P(I-P)=0",
        "rows": [row.as_dict() for row in audit_projected_bound_equalities()],
        "conclusion": "The coefficient k-1 is a certified upper bound; general fixed-eta equality compatibility remains open.",
    }
