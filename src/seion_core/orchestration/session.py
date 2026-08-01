"""Persistent lifecycle session state under .ai/runtime/sessions/.

Follows the same canonical/machine split used throughout .ai/: the
snapshot JSON (`<id>.json`) is the current-state view, always rebuildable
from the append-only history (`<id>.history.jsonl`), which is never
rewritten -- matching the pattern already established by
src/seion_core/governance/runs.py and .ai/evidence/ledger.jsonl.
"""

from __future__ import annotations

import json
import secrets
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

SESSIONS_DIRNAME = ("ai", "runtime", "sessions")


def _sessions_dir(repo_root: str | Path) -> Path:
    return Path(repo_root) / ".ai" / "runtime" / "sessions"


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def new_session_id(task: str) -> str:
    slug = "".join(c if c.isalnum() else "-" for c in task.lower())[:32].strip("-") or "task"
    return f"{slug}-{secrets.token_hex(4)}"


@dataclass
class LifecycleSession:
    session_id: str
    task: str
    workstream: str
    risk_level: str
    current_stage: str  # a STATE_MACHINES.yaml `development` state value
    retry_counts: dict[str, int] = field(default_factory=dict)
    lease_ids: list[str] = field(default_factory=list)
    blocked_reason: str | None = None
    created_utc: str = field(default_factory=_now)
    updated_utc: str = field(default_factory=_now)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "LifecycleSession":
        return cls(**data)


def snapshot_path(repo_root: str | Path, session_id: str) -> Path:
    return _sessions_dir(repo_root) / f"{session_id}.json"


def history_path(repo_root: str | Path, session_id: str) -> Path:
    return _sessions_dir(repo_root) / f"{session_id}.history.jsonl"


def save_session(repo_root: str | Path, session: LifecycleSession) -> Path:
    path = snapshot_path(repo_root, session.session_id)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(session.to_dict(), indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return path


def load_session(repo_root: str | Path, session_id: str) -> LifecycleSession:
    path = snapshot_path(repo_root, session_id)
    if not path.exists():
        raise FileNotFoundError(f"no lifecycle session {session_id!r} at {path}")
    return LifecycleSession.from_dict(json.loads(path.read_text(encoding="utf-8")))


def append_history(repo_root: str | Path, session_id: str, entry: dict[str, Any]) -> None:
    path = history_path(repo_root, session_id)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as stream:
        stream.write(json.dumps({"timestamp": _now(), **entry}, sort_keys=True) + "\n")


def list_sessions(repo_root: str | Path) -> list[LifecycleSession]:
    directory = _sessions_dir(repo_root)
    if not directory.exists():
        return []
    sessions = []
    for path in sorted(directory.glob("*.json")):
        sessions.append(LifecycleSession.from_dict(json.loads(path.read_text(encoding="utf-8"))))
    return sessions
