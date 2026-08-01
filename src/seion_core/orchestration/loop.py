"""The lifecycle executor: validates transitions, checks required
evidence, logs to .ai/evidence/ledger.jsonl, and implements the one
capped loop-back (verify failure -> change) this project's fail-closed
philosophy requires -- retries are counted and hard-capped, never
silent, never infinite.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from ..governance.events import append_event
from .lifecycle import TERMINAL_STATES, load_lifecycle
from .session import (
    LifecycleSession,
    append_history,
    load_session,
    new_session_id,
    save_session,
)

DEFAULT_MAX_VERIFY_RETRIES = 5


class LifecycleGateError(RuntimeError):
    pass


def _required_satisfied(required: tuple[str, ...], evidence: dict[str, Any]) -> list[str]:
    """An item is satisfied if it's a key in `evidence`, or (for file/path-
    looking required entries) it appears in evidence.get('files_consulted', [])."""
    files_consulted = set(evidence.get("files_consulted", ()))
    missing = []
    for item in required:
        looks_like_path = "/" in item or item.endswith((".md", ".yaml", ".yml"))
        if item in evidence:
            continue
        if looks_like_path and item in files_consulted:
            continue
        missing.append(item)
    return missing


@dataclass(frozen=True)
class AdvanceResult:
    ok: bool
    session: LifecycleSession
    problems: tuple[str, ...] = ()
    event_id: str | None = None


def start_session(
    repo_root: str | Path,
    *,
    task: str,
    workstream: str,
    risk_level: str,
    evidence: dict[str, Any],
) -> AdvanceResult:
    root = Path(repo_root)
    lifecycle = load_lifecycle(root)
    intake_spec = lifecycle.stages["intake"]
    missing = _required_satisfied(intake_spec.required, evidence)
    session_id = new_session_id(task)
    session = LifecycleSession(
        session_id=session_id,
        task=task,
        workstream=workstream,
        risk_level=risk_level,
        current_stage="INTAKE",
    )
    if missing:
        session.blocked_reason = f"intake missing required evidence: {missing}"
        session.current_stage = "BLOCKED"
    save_session(root, session)
    append_history(root, session_id, {"stage": "INTAKE", "event": "start", "evidence": evidence, "missing": missing})
    event = append_event(
        root,
        kind="lifecycle_start",
        source="seion-core governance lifecycle start",
        result=session.current_stage,
        authority="declared",
        limitations=[f"missing required: {missing}"] if missing else ["none supplied"],
        session_id=session_id,
    )
    return AdvanceResult(ok=not missing, session=session, problems=tuple(missing), event_id=event["event_id"])


def advance(
    repo_root: str | Path,
    *,
    session_id: str,
    target: str,
    evidence: dict[str, Any] | None = None,
    gate_confirmations: dict[str, bool] | None = None,
) -> AdvanceResult:
    root = Path(repo_root)
    lifecycle = load_lifecycle(root)
    session = load_session(root, session_id)
    evidence = evidence or {}
    gate_confirmations = gate_confirmations or {}

    target_state = _normalize_target(target)
    problems = list(lifecycle.validate_transition(session.current_stage, target_state))

    current_spec = lifecycle.stage_for_state(session.current_stage)
    if current_spec and current_spec.gate and target_state not in ("BLOCKED", "SUPERSEDED"):
        if not gate_confirmations.get(current_spec.key, False):
            problems.append(
                f"stage {current_spec.key!r}'s gate ({current_spec.gate!r}) requires an explicit "
                f"gate_confirmations[{current_spec.key!r}]=True (with justification in evidence), "
                "never assumed"
            )

    target_spec = lifecycle.stage_for_state(target_state)
    missing_required: list[str] = []
    if target_spec and target_state not in ("BLOCKED", "SUPERSEDED"):
        missing_required = _required_satisfied(target_spec.required, evidence)
        if missing_required:
            problems.append(f"target stage {target_spec.key!r} missing required evidence: {missing_required}")

    if problems:
        event = append_event(
            root,
            kind="lifecycle_advance",
            source="seion-core governance lifecycle advance",
            result="REJECTED",
            authority="declared",
            limitations=problems,
            session_id=session_id,
        )
        return AdvanceResult(ok=False, session=session, problems=tuple(problems), event_id=event["event_id"])

    session.current_stage = target_state
    session.updated_utc = datetime.now(timezone.utc).isoformat()
    save_session(root, session)
    append_history(root, session_id, {"stage": target_state, "event": "advance", "evidence": evidence, "gate_confirmations": gate_confirmations})
    event = append_event(
        root,
        kind="lifecycle_advance",
        source="seion-core governance lifecycle advance",
        result=target_state,
        authority="observed",
        limitations=evidence.get("limitations", []) or ["none supplied"],
        session_id=session_id,
    )
    return AdvanceResult(ok=True, session=session, event_id=event["event_id"])


def record_verify_result(
    repo_root: str | Path,
    *,
    session_id: str,
    passed: bool,
    evidence: dict[str, Any],
    gate_confirmations: dict[str, bool] | None = None,
    max_retries: int = DEFAULT_MAX_VERIFY_RETRIES,
) -> AdvanceResult:
    """The one specialized loop-back: a failed verify stage routes back to
    change (IN_PROGRESS) with a counted, capped retry -- never a silent or
    unbounded loop. Must be called while the session is at VERIFYING."""
    root = Path(repo_root)
    session = load_session(root, session_id)
    if session.current_stage != "VERIFYING":
        raise LifecycleGateError(
            f"record_verify_result requires the session to be at VERIFYING, currently {session.current_stage!r}"
        )

    if passed:
        return advance(root, session_id=session_id, target="evidence", evidence=evidence, gate_confirmations=gate_confirmations)

    retries = session.retry_counts.get("verify", 0) + 1
    session.retry_counts["verify"] = retries
    save_session(root, session)

    if retries > max_retries:
        session.current_stage = "BLOCKED"
        session.blocked_reason = f"verify failed {retries} times, exceeding max_retries={max_retries}"
        save_session(root, session)
        append_history(root, session_id, {"stage": "BLOCKED", "event": "verify_retry_cap_exceeded", "retries": retries, "max_retries": max_retries})
        event = append_event(
            root,
            kind="lifecycle_blocked",
            source="seion-core governance lifecycle verify-result",
            result="BLOCKED",
            authority="observed",
            limitations=[f"verify failed {retries} times (max_retries={max_retries}); logged, not hidden"],
            session_id=session_id,
        )
        return AdvanceResult(ok=False, session=session, problems=(f"verify retry cap exceeded ({retries} > {max_retries})",), event_id=event["event_id"])

    append_history(root, session_id, {"stage": "VERIFYING", "event": "verify_failed_routing_to_change", "retries": retries, "evidence": evidence})
    return advance(root, session_id=session_id, target="change", evidence=evidence, gate_confirmations=gate_confirmations)


def _normalize_target(target: str) -> str:
    from .lifecycle import STAGE_TO_STATE

    lowered = target.lower()
    if lowered in STAGE_TO_STATE:
        return STAGE_TO_STATE[lowered]
    upper = target.upper()
    if upper in TERMINAL_STATES:
        return upper
    return upper  # let validate_transition report "unknown state" uniformly
