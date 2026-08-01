"""Resumable job queue (mission section 4/5): scientific_instance_id,
execution_id, seed, precision, hardware, config+script hash, checkpoint
lineage, status, retry count, output hashes — all in one JSONL-backed,
append-only, non-destructive ledger (same "never mutate history" pattern
as src/seion_core/governance/runs.py, adapted for this track's own schema
since the artifact sets don't match — see legacy_run_dedup_report.md).
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any


def sha256_of(obj: Any) -> str:
    payload = json.dumps(obj, sort_keys=True, default=str).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


@dataclass
class JobRecord:
    scientific_instance_id: str  # identifies the mathematical instance (config, independent of retries)
    execution_id: str  # identifies THIS attempt (unique per retry)
    seed: int
    precision: str
    hardware: str
    config_hash: str
    script_hash: str
    checkpoint_parent_execution_id: str | None
    status: str  # PENDING | RUNNING | COMPLETED | FAILED | RETRYING
    retry_count: int
    output_hashes: dict[str, str] = field(default_factory=dict)
    error: str | None = None


class JobQueue:
    def __init__(self, ledger_path: Path):
        self.ledger_path = ledger_path
        self.ledger_path.parent.mkdir(parents=True, exist_ok=True)

    def _read_all(self) -> list[JobRecord]:
        if not self.ledger_path.exists():
            return []
        records = []
        for line in self.ledger_path.read_text(encoding="utf-8").splitlines():
            if line.strip():
                records.append(JobRecord(**json.loads(line)))
        return records

    def _append(self, record: JobRecord) -> None:
        with self.ledger_path.open("a", encoding="utf-8") as f:
            f.write(json.dumps(asdict(record)) + "\n")

    def submit(self, *, scientific_instance_id: str, seed: int, precision: str, hardware: str, config: dict, script_hash: str, checkpoint_parent_execution_id: str | None = None) -> JobRecord:
        existing = self._read_all()
        prior_execution_ids = {r.execution_id for r in existing if r.scientific_instance_id == scientific_instance_id}
        retry_count = len(prior_execution_ids)
        execution_id = f"{scientific_instance_id}__exec{retry_count}"
        record = JobRecord(
            scientific_instance_id=scientific_instance_id,
            execution_id=execution_id,
            seed=seed,
            precision=precision,
            hardware=hardware,
            config_hash=sha256_of(config),
            script_hash=script_hash,
            checkpoint_parent_execution_id=checkpoint_parent_execution_id,
            status="PENDING",
            retry_count=retry_count,
        )
        self._append(record)
        return record

    def mark(self, execution_id: str, status: str, *, output_hashes: dict[str, str] | None = None, error: str | None = None) -> JobRecord:
        existing = self._read_all()
        matches = [r for r in existing if r.execution_id == execution_id]
        if not matches:
            raise KeyError(f"unknown execution_id {execution_id!r}")
        latest = matches[-1]
        latest.status = status
        if output_hashes is not None:
            latest.output_hashes = output_hashes
        if error is not None:
            latest.error = error
        self._append(latest)  # append-only: a new line records the status transition, history preserved
        return latest

    def resumable_jobs(self) -> list[JobRecord]:
        """The latest status per scientific_instance_id, for instances not
        yet COMPLETED — the actual list a scheduler should pick up."""
        existing = self._read_all()
        latest_by_instance: dict[str, JobRecord] = {}
        for r in existing:
            latest_by_instance[r.scientific_instance_id] = r  # append order preserved -> last write wins
        return [r for r in latest_by_instance.values() if r.status != "COMPLETED"]

    def lineage(self, execution_id: str) -> list[str]:
        existing = {r.execution_id: r for r in self._read_all()}
        chain = [execution_id]
        current = existing.get(execution_id)
        while current and current.checkpoint_parent_execution_id:
            chain.append(current.checkpoint_parent_execution_id)
            current = existing.get(current.checkpoint_parent_execution_id)
        return chain
