"""Append-only governance event ledger."""

from __future__ import annotations

import hashlib
import json
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable


def _git(root: Path, *args: str) -> str | None:
    try:
        result = subprocess.run(
            ["git", "-C", str(root), *args],
            check=False,
            capture_output=True,
            text=True,
            timeout=10,
        )
    except (OSError, subprocess.SubprocessError):
        return None
    return result.stdout.strip() if result.returncode == 0 else None


def append_event(
    repo_root: str | Path,
    *,
    kind: str,
    source: str,
    result: str,
    authority: str,
    limitations: Iterable[str],
    claim_ids: Iterable[str] = (),
    run_ids: Iterable[str] = (),
    artifacts: Iterable[str] = (),
    session_id: str | None = None,
) -> dict[str, Any]:
    root = Path(repo_root).resolve()
    created = datetime.now(timezone.utc).isoformat()
    payload = {
        "kind": kind,
        "created_utc": created,
        "authority": authority,
        "source": source,
        "result": result,
        "claim_ids": list(claim_ids),
        "run_ids": list(run_ids),
        "artifacts": list(artifacts),
        "limitations": list(limitations),
        "git_commit": _git(root, "rev-parse", "HEAD"),
        "branch": _git(root, "branch", "--show-current"),
    }
    if session_id is not None:
        payload["session_id"] = session_id
    event_id = hashlib.sha256(json.dumps(payload, sort_keys=True).encode("utf-8")).hexdigest()[:20]
    event = {"event_id": event_id, **payload}
    target = root / ".ai" / "evidence" / "ledger.jsonl"
    target.parent.mkdir(parents=True, exist_ok=True)
    with target.open("a", encoding="utf-8") as stream:
        stream.write(json.dumps(event, sort_keys=True) + "\n")
    return event
