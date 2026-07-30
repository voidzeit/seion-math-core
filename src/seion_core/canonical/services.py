"""Application services for canonical SEION mutations."""

from __future__ import annotations

import hashlib
import json
import uuid
from pathlib import Path
from typing import Any, Mapping

from .atomic import append_jsonl, atomic_write_json, sha256_bytes
from .models import EvidenceEvent, utc_now


class CanonicalServiceError(RuntimeError):
    pass


class CanonicalRepositoryService:
    """The only supported boundary for canonical memory/evidence writes."""

    def __init__(self, root: Path) -> None:
        self.root = root.resolve()
        self.memory = self.root / ".ai"
        self.backups = self.memory / "runtime" / "backups"
        self.ledger = self.root / "claims" / "evidence_ledger.jsonl"
        self.events = self.memory / "evidence" / "ledger.jsonl"

    def _path(self, relative: str | Path) -> Path:
        path = (self.root / relative).resolve()
        if self.root not in path.parents and path != self.root:
            raise CanonicalServiceError(f"Path escapes repository: {relative}")
        return path

    def write_derived_json(self, relative: str | Path, value: Any) -> str:
        path = self._path(relative)
        return atomic_write_json(path, value, backup_dir=self.backups)

    def append_event(self, event: EvidenceEvent) -> str:
        payload = event.to_dict()
        for key in ("event_id", "event_type", "subject_id", "actor", "status"):
            if not payload.get(key):
                raise CanonicalServiceError(f"Missing event field: {key}")
        line_hash = append_jsonl(self.events, payload)
        append_jsonl(self.ledger, {**payload, "ledger_line_hash": line_hash})
        return line_hash

    def record_transition(self, event_type: str, subject_id: str, previous: str, next_state: str, actor: str, source_paths: tuple[str, ...] = ()) -> str:
        event = EvidenceEvent(
            event_id=f"evt_{uuid.uuid4().hex[:16]}",
            event_type=event_type,
            subject_id=subject_id,
            authority_level=4,
            actor=actor,
            status=next_state,
            source_paths=source_paths,
            notes=f"transition {previous} -> {next_state}",
        )
        return self.append_event(event)

    def hash_file(self, relative: str | Path) -> str:
        return sha256_bytes(self._path(relative).read_bytes())

    def manifest(self, paths: list[str]) -> dict[str, Any]:
        outputs = {path: self.hash_file(path) for path in sorted(paths) if self._path(path).exists()}
        return {"schema_version": 1, "generated_utc": utc_now(), "outputs": outputs}
