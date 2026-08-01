"""Typed-gate status vocabulary and fail-closed combination logic.

Replaces v17's `compute_master_score` (WARN -> 0.5, N/A -> 1.0, averaged
across 14 blocks). See GATE_TAXONOMY.md for the full definition of every
state and gate. This module is the enforcement point: it is a hard error,
not a silent downgrade, to assign a certification-tier status to a
screening-mode run.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


class TypedStatus(str, Enum):
    STRUCTURAL_IDENTITY_PASS = "STRUCTURAL_IDENTITY_PASS"
    NUMERICAL_SANITY_PASS = "NUMERICAL_SANITY_PASS"
    EMPIRICAL_SCREENING_PASS = "EMPIRICAL_SCREENING_PASS"
    STATISTICALLY_VALIDATED_PASS = "STATISTICALLY_VALIDATED_PASS"
    VALIDATED_NUMERICAL_CERTIFICATE = "VALIDATED_NUMERICAL_CERTIFICATE"
    EXACT_CERTIFICATE = "EXACT_CERTIFICATE"
    WARN = "WARN"
    FAIL = "FAIL"
    NOT_APPLICABLE = "NOT_APPLICABLE"
    NOT_CERTIFIABLE_AS_DEFINED = "NOT_CERTIFIABLE_AS_DEFINED"


# Ordering used ONLY to pick a minimum over a gate's contributing blocks.
# This is not a numeric score and must never be averaged, summed, or
# divided. NOT_APPLICABLE is deliberately absent: it is excluded from the
# ordering and handled separately (see combine_gate_status).
_STRENGTH_ORDER: tuple[TypedStatus, ...] = (
    TypedStatus.NOT_CERTIFIABLE_AS_DEFINED,
    TypedStatus.FAIL,
    TypedStatus.WARN,
    TypedStatus.STRUCTURAL_IDENTITY_PASS,
    TypedStatus.NUMERICAL_SANITY_PASS,
    TypedStatus.EMPIRICAL_SCREENING_PASS,
    TypedStatus.STATISTICALLY_VALIDATED_PASS,
    TypedStatus.VALIDATED_NUMERICAL_CERTIFICATE,
    TypedStatus.EXACT_CERTIFICATE,
)
_RANK = {status: i for i, status in enumerate(_STRENGTH_ORDER)}

# Statuses that may only ever be assigned to a certification-mode run.
_CERTIFICATION_TIER = {
    TypedStatus.VALIDATED_NUMERICAL_CERTIFICATE,
    TypedStatus.EXACT_CERTIFICATE,
}

CRITICAL_GATES: dict[str, tuple[str, ...]] = {
    "projector_gate": ("A_projector", "D_snapping"),
    "algebra_gate": ("G_nary_closure", "H_nary_associator", "N_cyclic_law"),
    "dynamic_explanation_gate": ("B_commutator", "C_beals"),
    "interscale_gate": ("E_interscale", "J_tensor_interscale"),
    "gauge_gate": ("L_gauge_canonicalization",),
    "persistence_gate": ("K_hosvd", "M_persistent_factorization"),
    "reproducibility_gate": (),  # derived cross-cuttingly, not from a block letter
    "mathematical_proof_gate": ("F_rigidity", "I_reduced_tensor"),
}


class ScreeningCertificateViolation(RuntimeError):
    """Raised when code attempts to assign a certification-tier status to a
    screening-mode run. This must fail loudly, not silently downgrade —
    mission section 3: "A run with eval_mode = screening may never produce
    a certificate, regardless of score."
    """


def assign_block_status(*, eval_mode: str, status: TypedStatus, block_name: str) -> TypedStatus:
    """Single enforcement point for every block result in the v18 suite."""
    if eval_mode != "certification" and status in _CERTIFICATION_TIER:
        raise ScreeningCertificateViolation(
            f"block {block_name!r}: attempted to assign {status.value} under "
            f"eval_mode={eval_mode!r}; certification-tier statuses require "
            "eval_mode='certification'."
        )
    return status


def combine_gate_status(block_statuses: dict[str, TypedStatus]) -> TypedStatus:
    """A gate's status is the minimum (weakest) over its contributing
    blocks' statuses, excluding NOT_APPLICABLE. If every contributing block
    is NOT_APPLICABLE, the gate itself is NOT_APPLICABLE."""
    applicable = {k: v for k, v in block_statuses.items() if v != TypedStatus.NOT_APPLICABLE}
    if not applicable:
        return TypedStatus.NOT_APPLICABLE
    return min(applicable.values(), key=lambda s: _RANK[s])


# Gates required to pass for a global certificate; NOT_APPLICABLE gates are
# excluded from this requirement (never counted as passing OR failing) but
# must still be listed in any certificate artifact with their exclusion
# reason.
_PASSING_MINIMUM_SCREENING = TypedStatus.EMPIRICAL_SCREENING_PASS
_PASSING_MINIMUM_CERTIFICATION = TypedStatus.VALIDATED_NUMERICAL_CERTIFICATE


@dataclass(frozen=True)
class GlobalCertificateResult:
    final_state: str
    passed_gates: tuple[str, ...]
    excluded_gates: tuple[str, ...]
    failing_gates: tuple[str, ...]
    gate_statuses: dict[str, TypedStatus]


def evaluate_global_certificate(
    gate_statuses: dict[str, TypedStatus],
    *,
    eval_mode: str,
    required_gates: tuple[str, ...] = tuple(CRITICAL_GATES),
) -> GlobalCertificateResult:
    """Fail-closed combination: every required, applicable gate must reach
    at least the screening or certification passing minimum. No averaging.
    """
    minimum = _PASSING_MINIMUM_CERTIFICATION if eval_mode == "certification" else _PASSING_MINIMUM_SCREENING
    passed: list[str] = []
    excluded: list[str] = []
    failing: list[str] = []
    for gate in required_gates:
        status = gate_statuses.get(gate)
        if status is None:
            failing.append(gate)
            continue
        if status == TypedStatus.NOT_APPLICABLE:
            excluded.append(gate)
            continue
        if _RANK[status] >= _RANK[minimum]:
            passed.append(gate)
        else:
            failing.append(gate)

    if failing:
        # Name the state after the first failing gate for traceability; a
        # real certificate artifact lists all of them, this is the summary
        # label only.
        final_state = f"FAIL_CLOSED_{failing[0].upper()}_NOT_ESTABLISHED"
    elif eval_mode != "certification":
        final_state = "PASS_A_TO_N_SCREENING_ONLY_NOT_A_CERTIFICATE"
    else:
        final_state = "PASS_A_TO_N_PARTIAL_CERTIFICATION"

    return GlobalCertificateResult(
        final_state=final_state,
        passed_gates=tuple(passed),
        excluded_gates=tuple(excluded),
        failing_gates=tuple(failing),
        gate_statuses=dict(gate_statuses),
    )
