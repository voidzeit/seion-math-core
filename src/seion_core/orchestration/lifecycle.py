"""Formalizes governance/DEVELOPMENT_LIFECYCLE.yaml + STATE_MACHINES.yaml
into an executable stage graph.

Honesty note: DEVELOPMENT_LIFECYCLE.yaml's own `state_transitions` block
lists a flat `allowed` vocabulary (`declared, in_progress, verified,
blocked, superseded, released`) and named anti-patterns under
`forbidden` (e.g. `historical_pass_to_current_pass_without_execution`) --
it does NOT specify an exact transition graph between the 11
`development` states in STATE_MACHINES.yaml. This module formalizes one
concrete, conservative transition table from the 8 stages' declared
ORDER plus the state enum, rather than claiming to parse a graph that
the source YAML does not actually contain. The table is:

    INTAKE -> CONTEXT -> PLANNED -> IN_PROGRESS -> VERIFYING -> EVIDENCE
    -> POSTFLIGHT -> RELEASE -> COMPLETED

    VERIFYING -> IN_PROGRESS   (the one legal backward edge: a failed
                                verification sends work back to `change`,
                                matching the mission-level rule that
                                "stale historical output cannot stand in
                                for current execution")

    <any non-terminal state> -> BLOCKED
    <any non-terminal state> -> SUPERSEDED

COMPLETED, BLOCKED, and SUPERSEDED are terminal: no transitions out.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import yaml

STAGE_ORDER: tuple[str, ...] = (
    "intake",
    "context",
    "plan",
    "change",
    "verify",
    "evidence",
    "postflight",
    "release",
)

# Lifecycle stage key -> STATE_MACHINES.yaml `development` state value.
STAGE_TO_STATE: dict[str, str] = {
    "intake": "INTAKE",
    "context": "CONTEXT",
    "plan": "PLANNED",
    "change": "IN_PROGRESS",
    "verify": "VERIFYING",
    "evidence": "EVIDENCE",
    "postflight": "POSTFLIGHT",
    "release": "RELEASE",
}
STATE_TO_STAGE: dict[str, str] = {v: k for k, v in STAGE_TO_STATE.items()}

TERMINAL_STATES: frozenset[str] = frozenset({"COMPLETED", "BLOCKED", "SUPERSEDED"})

# The one legal backward edge.
BACKWARD_EDGES: dict[str, str] = {"VERIFYING": "IN_PROGRESS"}


class LifecycleError(ValueError):
    pass


@dataclass(frozen=True)
class StageSpec:
    key: str
    state: str
    purpose: str
    required: tuple[str, ...]
    gate: str | None
    command: str | None


@dataclass(frozen=True)
class Lifecycle:
    stages: dict[str, StageSpec]  # keyed by stage key (e.g. "verify")
    development_states: tuple[str, ...]

    def stage_for_state(self, state: str) -> StageSpec | None:
        key = STATE_TO_STAGE.get(state)
        return self.stages.get(key) if key else None

    def stage_requirements(self, state: str) -> tuple[str, ...]:
        spec = self.stage_for_state(state)
        return spec.required if spec else ()

    def ordered_forward_states(self) -> tuple[str, ...]:
        return tuple(STAGE_TO_STATE[s] for s in STAGE_ORDER) + ("COMPLETED",)

    def validate_transition(self, current: str, target: str) -> list[str]:
        """Returns a list of problems; empty list means the transition is legal."""
        problems: list[str] = []
        valid_states = set(self.ordered_forward_states()) | TERMINAL_STATES
        if current not in valid_states:
            problems.append(f"unknown current state {current!r}")
        if target not in valid_states:
            problems.append(f"unknown target state {target!r}")
        if problems:
            return problems

        if current in TERMINAL_STATES:
            problems.append(f"{current} is terminal; no transition is legal from it")
            return problems

        if target in ("BLOCKED", "SUPERSEDED"):
            return []  # always legal from any non-terminal state

        forward = self.ordered_forward_states()
        if current in forward and target in forward:
            current_idx = forward.index(current)
            target_idx = forward.index(target)
            if target_idx == current_idx + 1:
                return []
            if BACKWARD_EDGES.get(current) == target:
                return []
            problems.append(
                f"{current} -> {target} is not a legal edge: the only forward step is "
                f"{current} -> {forward[current_idx + 1] if current_idx + 1 < len(forward) else '(none, already at COMPLETED)'}"
                + (f", or the backward edge {current} -> {BACKWARD_EDGES[current]}" if current in BACKWARD_EDGES else "")
            )
            return problems

        problems.append(f"{current} -> {target} is not a recognized transition")
        return problems


def load_lifecycle(repo_root: str | Path) -> Lifecycle:
    root = Path(repo_root)
    lifecycle_doc = yaml.safe_load((root / "governance" / "DEVELOPMENT_LIFECYCLE.yaml").read_text(encoding="utf-8"))
    state_doc = yaml.safe_load((root / "governance" / "STATE_MACHINES.yaml").read_text(encoding="utf-8"))

    stages: dict[str, StageSpec] = {}
    for key, body in lifecycle_doc.get("stages", {}).items():
        if key not in STAGE_TO_STATE:
            raise LifecycleError(f"DEVELOPMENT_LIFECYCLE.yaml declares unknown stage {key!r}")
        stages[key] = StageSpec(
            key=key,
            state=STAGE_TO_STATE[key],
            purpose=body.get("purpose", ""),
            required=tuple(body.get("required", ())),
            gate=body.get("gate"),
            command=body.get("command"),
        )
    missing = set(STAGE_ORDER) - set(stages)
    if missing:
        raise LifecycleError(f"DEVELOPMENT_LIFECYCLE.yaml is missing stage(s): {sorted(missing)}")

    development_states = tuple(state_doc.get("development", ()))
    return Lifecycle(stages=stages, development_states=development_states)
