"""Fail-closed state machines for claims, experiments, development, papers, and releases."""

from __future__ import annotations

from dataclasses import dataclass


class TransitionError(ValueError):
    pass


TRANSITIONS: dict[str, dict[str, set[str]]] = {
    "claim": {
        "PROPOSED": {"FORMALIZED", "OPEN", "SUPERSEDED"},
        "FORMALIZED": {"PRIOR_ART_PENDING", "PROOF_IN_PROGRESS", "OPEN", "SUPERSEDED"},
        "PRIOR_ART_PENDING": {"PROOF_IN_PROGRESS", "OPEN", "SUPERSEDED"},
        "PROOF_IN_PROGRESS": {"PROVED", "PROVED_UNDER_ASSUMPTIONS", "REFUTED", "OPEN", "SUPERSEDED"},
        "PROVED": {"IMPLEMENTED", "HUMAN_REVIEWED", "PAPER_CANDIDATE", "SUPERSEDED"},
        "PROVED_UNDER_ASSUMPTIONS": {"IMPLEMENTED", "HUMAN_REVIEWED", "PAPER_CANDIDATE", "SUPERSEDED"},
        "REFUTED": {"SUPERSEDED", "OPEN"},
        "OPEN": {"FORMALIZED", "PROOF_IN_PROGRESS", "SUPERSEDED"},
        "IMPLEMENTED": {"VERIFIED", "SUPERSEDED"},
        "VERIFIED": {"HUMAN_REVIEWED", "PAPER_CANDIDATE", "SUPERSEDED"},
        "HUMAN_REVIEWED": {"PAPER_CANDIDATE", "PUBLISHED", "SUPERSEDED"},
        "PAPER_CANDIDATE": {"PUBLISHED", "SUPERSEDED"},
        "PUBLISHED": {"SUPERSEDED"},
        "SUPERSEDED": set(),
    },
    "experiment": {
        "PROPOSED": {"ACCEPTED", "ARCHIVED"},
        "ACCEPTED": {"BUDGETED", "ARCHIVED"},
        "BUDGETED": {"QUEUED", "ARCHIVED"},
        "QUEUED": {"RUNNING", "INTERRUPTED", "ARCHIVED"},
        "RUNNING": {"COMPLETE", "COMPLETE_WITH_WARNINGS", "INTERRUPTED", "FAILED_RUNTIME", "FAILED_NUMERICAL_GATE", "FAILED_MATHEMATICAL_GATE"},
        "INTERRUPTED": {"QUEUED", "ARCHIVED"},
        "FAILED_RUNTIME": {"QUEUED", "ARCHIVED"},
        "FAILED_NUMERICAL_GATE": {"QUEUED", "ARCHIVED"},
        "FAILED_MATHEMATICAL_GATE": {"QUEUED", "ARCHIVED"},
        "COMPLETE": {"AGGREGATED", "AUDITED", "ARCHIVED"},
        "COMPLETE_WITH_WARNINGS": {"AGGREGATED", "AUDITED", "ARCHIVED"},
        "AGGREGATED": {"AUDITED", "PAPER_ELIGIBLE", "ARCHIVED"},
        "AUDITED": {"PAPER_ELIGIBLE", "ARCHIVED"},
        "PAPER_ELIGIBLE": {"ARCHIVED"},
        "ARCHIVED": set(),
    },
    "development": {
        "INTAKE": {"CONTEXT"},
        "CONTEXT": {"PLANNED", "BLOCKED"},
        "PLANNED": {"IN_PROGRESS", "BLOCKED"},
        "IN_PROGRESS": {"VERIFYING", "BLOCKED", "SUPERSEDED"},
        "VERIFYING": {"EVIDENCE", "IN_PROGRESS", "BLOCKED"},
        "EVIDENCE": {"POSTFLIGHT", "IN_PROGRESS", "BLOCKED"},
        "POSTFLIGHT": {"RELEASE", "BLOCKED", "SUPERSEDED"},
        "RELEASE": {"COMPLETED", "BLOCKED"},
        "COMPLETED": set(),
        "BLOCKED": {"CONTEXT", "PLANNED", "SUPERSEDED"},
        "SUPERSEDED": set(),
    },
    "paper": {
        "DRAFT": {"INTERNAL_REVIEW", "BLOCKED"},
        "INTERNAL_REVIEW": {"REVISION", "HUMAN_REVIEW", "BLOCKED"},
        "REVISION": {"INTERNAL_REVIEW", "HUMAN_REVIEW", "BLOCKED"},
        "HUMAN_REVIEW": {"ACCEPTED", "REVISION", "BLOCKED"},
        "ACCEPTED": {"RELEASED", "SUPERSEDED"},
        "RELEASED": {"SUPERSEDED"},
        "BLOCKED": {"REVISION", "SUPERSEDED"},
        "SUPERSEDED": set(),
    },
    "software_release": {
        "DRAFT": {"CANDIDATE", "BLOCKED"},
        "CANDIDATE": {"VALIDATED", "BLOCKED"},
        "VALIDATED": {"APPROVED", "BLOCKED"},
        "APPROVED": {"RELEASED", "SUPERSEDED"},
        "RELEASED": {"SUPERSEDED"},
        "BLOCKED": {"CANDIDATE", "SUPERSEDED"},
        "SUPERSEDED": set(),
    },
}


@dataclass(frozen=True)
class Transition:
    machine: str
    previous: str
    next: str
    reason: str


def transition(machine: str, current: str, target: str, reason: str = "") -> Transition:
    allowed = TRANSITIONS.get(machine, {}).get(current, set())
    if target not in allowed:
        raise TransitionError(f"Invalid {machine} transition: {current} -> {target}")
    if machine == "claim" and target == "PROVED" and any(word in reason.lower() for word in ("numerical", "observational", "residual", "empirical")):
        raise TransitionError("Numerical or observational evidence cannot assign PROVED")
    return Transition(machine, current, target, reason)


def validate_state(machine: str, state: str) -> None:
    if state not in TRANSITIONS.get(machine, {}):
        raise TransitionError(f"Unknown state {state!r} for machine {machine!r}")
