"""Typed, serializable domain records used by the canonical services."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from enum import IntEnum
from typing import Any, Mapping


class AuthorityLevel(IntEnum):
    HUMAN_FORMAL = 0
    EXACT_VALIDATED = 1
    DETERMINISTIC_OBSERVED = 2
    DERIVED = 3
    COMPILED_CONTEXT = 4
    DECLARED_PROPOSED = 5


class EvidenceKind(str):
    PROOF = "proof"
    EXACT_CERTIFICATE = "exact_certificate"
    VALIDATED_INTERVAL = "validated_interval"
    NUMERICAL_RUN = "numerical_run"
    TEST = "test"
    REVIEW = "review"
    DERIVED_TABLE = "derived_table"
    DERIVED_FIGURE = "derived_figure"
    CONTEXT = "context"


@dataclass(frozen=True)
class EvidenceEvent:
    """Append-only event linking a repository action to its authority."""

    event_id: str
    event_type: str
    subject_id: str
    authority_level: int
    actor: str
    status: str
    source_paths: tuple[str, ...] = ()
    artifact_hashes: Mapping[str, str] = field(default_factory=dict)
    timestamp_utc: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    notes: str = ""

    def to_dict(self) -> dict[str, Any]:
        value = asdict(self)
        value["source_paths"] = list(self.source_paths)
        value["authority_level"] = int(self.authority_level)
        return value


@dataclass(frozen=True)
class RepositoryState:
    branch: str
    commit: str
    dirty: bool
    memory_status: str
    graph_status: str
    tests_passed: int
    blockers: tuple[str, ...] = ()

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class ClaimRecord:
    claim_id: str
    statement: str
    state: str
    authority_level: int
    proof_path: str | None = None
    evidence_paths: tuple[str, ...] = ()
    blocker_ids: tuple[str, ...] = ()

    def to_dict(self) -> dict[str, Any]:
        value = asdict(self)
        value["evidence_paths"] = list(self.evidence_paths)
        value["blocker_ids"] = list(self.blocker_ids)
        return value


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def normalize_record(record: Mapping[str, Any]) -> dict[str, Any]:
    """Make registry values JSON-safe without changing their semantics."""

    result: dict[str, Any] = {}
    for key, value in record.items():
        if isinstance(value, Mapping):
            result[key] = normalize_record(value)
        elif isinstance(value, (list, tuple)):
            result[key] = [normalize_record(item) if isinstance(item, Mapping) else item for item in value]
        elif isinstance(value, IntEnum):
            result[key] = int(value)
        else:
            result[key] = value
    return result
