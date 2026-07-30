"""Frozen evidence-contract invariants for SEION V5 (schemas/gates freeze, Phase 2).

These are pure, dependency-free predicate/validator functions — no I/O, no
registry parsing — so they can be reused by both the CANONICAL_FINITE_CORE
governance audit and, independently, by SPECTRAL_LEGACY_TRACK or Track T
tooling without creating a cross-track import dependency on either track's
own modules. Each function returns a list of violation messages (empty
list means the invariant held); callers decide how to surface that (as a
GovernanceIssue, an assertion, a CI failure, etc).

SCHEMA_VERSION is the frozen evidence-contract version. Bumping it without
recording the change in schemas/MIGRATIONS.md is itself a violation this
module's own test suite checks for (see tests/governance/test_evidence_contract.py).
"""

from __future__ import annotations

from typing import Any

SCHEMA_VERSION = 1

# Certificate-tier statuses that require a fully closed, zero-tolerance gap.
# Anything claiming one of these with a nonzero certified_gap is malformed —
# "exact status only when certified gap is zero".
EXACT_TIER_STATUSES = {"EXACT_CERTIFICATE", "exact_certificate", "PROVED", "proved", "REFUTED", "refuted"}

# Statuses that are evidence *for* a claim but must never, by themselves,
# promote a theorem-level claim to a proved/certified status.
EMPIRICAL_ONLY_STATUSES = {
    "empirical", "EMPIRICAL_ONLY", "EMPIRICAL_SCREENING_PASS",
    "STATISTICALLY_VALIDATED", "statistically_validated", "heuristic",
}

# Theorem-level statuses that require proof- or certificate-grade evidence,
# never empirical-only evidence, to reach.
PROOF_GRADE_THEOREM_STATUSES = {
    "PROVED", "proved", "PROVED_UNDER_ASSUMPTIONS", "proved_under_assumptions",
    "EXACT_CERTIFICATE", "exact_certificate", "symbolically_verified",
}

# Run/eval modes that may never emit a certificate-tier status.
SCREENING_MODES = {"screening", "SCREENING", "eval_mode=screening"}
CERTIFICATE_TIER_STATUSES = {
    "VALIDATED_NUMERICAL_CERTIFICATE", "EXACT_CERTIFICATE",
    "validated_numerical_certificate", "exact_certificate",
}


def check_bound_ordering(lower_bound: float, upper_bound: float, *, tolerance: float = 0.0) -> list[str]:
    """Invariant: lower_bound <= upper_bound + tolerance."""
    if lower_bound > upper_bound + tolerance:
        return [
            f"lower_bound ({lower_bound}) exceeds upper_bound + tolerance "
            f"({upper_bound} + {tolerance} = {upper_bound + tolerance})"
        ]
    return []


def check_exact_status_requires_zero_gap(status: str, certified_gap: float | None) -> list[str]:
    """Invariant: exact-tier status is only valid when the certified gap is exactly zero."""
    if status in EXACT_TIER_STATUSES:
        if certified_gap is None:
            return [f"status {status!r} claims an exact/certificate-tier result but certified_gap is absent"]
        if certified_gap != 0:
            return [f"status {status!r} claims an exact/certificate-tier result but certified_gap={certified_gap} != 0"]
    return []


def check_empirical_cannot_promote_theorem_status(
    theorem_status: str, supporting_evidence_statuses: list[str]
) -> list[str]:
    """Invariant: a theorem-level proof-grade status must be backed by at least one
    proof/certificate-grade evidence item, not empirical-only evidence alone."""
    if theorem_status not in PROOF_GRADE_THEOREM_STATUSES:
        return []
    if not supporting_evidence_statuses:
        return [f"theorem status {theorem_status!r} has no supporting evidence at all"]
    if all(item in EMPIRICAL_ONLY_STATUSES for item in supporting_evidence_statuses):
        return [
            f"theorem status {theorem_status!r} is only supported by empirical-only evidence "
            f"{supporting_evidence_statuses}; proof-grade theorem status requires proof/certificate-grade evidence"
        ]
    return []


def check_screening_cannot_emit_certificate(eval_mode: str, status: str) -> list[str]:
    """Invariant: a run executed in screening mode may never emit a certificate-tier status."""
    if eval_mode in SCREENING_MODES and status in CERTIFICATE_TIER_STATUSES:
        return [f"eval_mode={eval_mode!r} run emitted certificate-tier status {status!r}; screening runs cannot certify"]
    return []


def check_resumed_run_is_not_independent_seed(
    *, is_resumed: bool, restore_rng: bool, claimed_as_independent_seed: bool
) -> list[str]:
    """Invariant: a resumed run (checkpoint restart) is not a new independent seed/trial
    unless RNG state was NOT restored (i.e. it is a genuinely fresh trial, not a replay)."""
    if is_resumed and restore_rng and claimed_as_independent_seed:
        return [
            "run is resumed from a checkpoint with restore_rng=True and claimed as an "
            "independent seed/trial; a restored-RNG resume replays the same trial, it is "
            "not a fresh independent scientific instance"
        ]
    return []


def check_figure_values_exist_in_source(
    figure_values: dict[str, Any], source_artifact: dict[str, Any]
) -> list[str]:
    """Invariant: every value presented in a figure must be traceable to its declared
    source artifact by exact key+value match — a figure may not present a number that
    does not exist anywhere in its own cited provenance."""
    violations = []
    for key, value in figure_values.items():
        if key not in source_artifact:
            violations.append(f"figure value {key!r} has no corresponding key in its declared source artifact")
        elif source_artifact[key] != value:
            violations.append(
                f"figure value {key!r}={value!r} does not match source artifact value {source_artifact[key]!r}"
            )
    return violations


def check_table_count_reconciles(*, table_row_count: int, declared_total: int) -> list[str]:
    """Invariant: a table's declared summary count must equal its actual row count."""
    if table_row_count != declared_total:
        return [f"table declares total={declared_total} but has {table_row_count} actual rows"]
    return []


ALL_INVARIANTS = (
    check_bound_ordering,
    check_exact_status_requires_zero_gap,
    check_empirical_cannot_promote_theorem_status,
    check_screening_cannot_emit_certificate,
    check_resumed_run_is_not_independent_seed,
    check_figure_values_exist_in_source,
    check_table_count_reconciles,
)
