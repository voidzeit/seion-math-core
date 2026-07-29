"""Append durable postflight and handoff records after an executed session."""

from __future__ import annotations

import subprocess
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterable

from .events import append_event


def _git(root: Path, *args: str) -> str:
    try:
        result = subprocess.run(
            ["git", "-C", str(root), *args],
            capture_output=True,
            text=True,
            check=False,
            timeout=10,
        )
    except (OSError, subprocess.SubprocessError):
        return "unknown"
    return result.stdout.strip() if result.returncode == 0 else "unknown"


def record_postflight(
    repo_root: str | Path,
    *,
    task: str,
    summary: str,
    outcome: str,
    validation: str,
    command: str,
    changed_files: Iterable[str] = (),
    limitations: Iterable[str] = (),
) -> dict[str, str | list[str]]:
    root = Path(repo_root).resolve()
    now = datetime.now(timezone.utc).isoformat()
    files = list(changed_files)
    limits = list(limitations) or ["No additional limitations supplied; inspect the audit and test outputs."]
    branch = _git(root, "branch", "--show-current")
    commit = _git(root, "rev-parse", "HEAD")
    entry = [
        f"\n## {now} — {task}",
        "",
        f"- Command: `{command}`",
        f"- Branch/commit: `{branch}` / `{commit}`",
        f"- Outcome: **{outcome}**",
        f"- Summary: {summary}",
        f"- Validation: {validation}",
        "- Changed files:",
    ]
    entry.extend(f"  - `{path}`" for path in files or ["(not supplied)"])
    entry.append("- Limitations:")
    entry.extend(f"  - {item}" for item in limits)
    history = root / ".ai" / "RUN_HISTORY.md"
    with history.open("a", encoding="utf-8") as stream:
        stream.write("\n".join(entry) + "\n")
    handoff = root / ".ai" / "HANDOFF.md"
    with handoff.open("a", encoding="utf-8") as stream:
        stream.write(
            "\n".join(
                [
                    f"\n## Latest postflight: {task}",
                    "",
                    f"- Timestamp: {now}",
                    f"- Outcome: **{outcome}**",
                    f"- Validation: {validation}",
                    f"- Resume from commit: `{commit}` on `{branch}`",
                    f"- Limitation: {limits[0]}",
                    "",
                ]
            )
        )
    event = append_event(
        root,
        kind="postflight",
        source=command,
        result=outcome,
        authority="observed",
        artifacts=(".ai/RUN_HISTORY.md", ".ai/HANDOFF.md"),
        limitations=limits,
    )
    return {
        "timestamp": now,
        "task": task,
        "outcome": outcome,
        "branch": branch,
        "commit": commit,
        "event_id": event["event_id"],
        "changed_files": files,
        "limitations": limits,
    }
