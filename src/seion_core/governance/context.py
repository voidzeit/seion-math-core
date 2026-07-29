"""Compile bounded, recoverable context packs from canonical SEION sources."""

from __future__ import annotations

import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterable

from .runs import collect_runs


def _read(path: Path, limit: int = 8000) -> str:
    try:
        value = path.read_text(encoding="utf-8")
    except OSError as exc:
        return f"[unavailable: {exc}]"
    if len(value) <= limit:
        return value
    return value[:limit] + "\n\n[truncated by context compiler]\n"


def _slug(value: str) -> str:
    result = re.sub(r"[^a-zA-Z0-9]+", "-", value.strip().lower()).strip("-")
    return result[:64] or "task"


def _candidate_files(root: Path) -> list[Path]:
    relative = [
        "AGENTS.md",
        ".ai/CURRENT_STATE.md",
        ".ai/TASKS.md",
        ".ai/KNOWN_BLOCKERS.md",
        ".ai/DECISIONS.md",
        ".ai/RISK_REGISTER.md",
        ".ai/WORKSTREAMS.md",
        "governance/PROJECT_MANIFEST.yaml",
        "governance/AUTHORITY_LADDER.yaml",
        "governance/DEVELOPMENT_LIFECYCLE.yaml",
        "governance/RESEARCH_SOFTWARE_SPLIT.yaml",
        "claims/claims_registry.yaml",
        "claims/theorem_registry.yaml",
        "experiments/matrices/canonical_run_matrix.yaml",
    ]
    return [root / path for path in relative if (root / path).exists()]


def build_context_pack(
    repo_root: str | Path,
    *,
    task: str,
    output: str | Path | None = None,
    extra_files: Iterable[str | Path] = (),
) -> Path:
    root = Path(repo_root).resolve()
    now = datetime.now(timezone.utc).isoformat()
    runs = collect_runs(root)
    latest = sorted(runs, key=lambda item: (item.created_utc or "", item.run_path), reverse=True)[:5]
    files = _candidate_files(root)
    for item in extra_files:
        path = Path(item)
        if not path.is_absolute():
            path = root / path
        if path.exists() and path not in files:
            files.append(path)
    sections = [
        "# SEION context pack",
        "",
        f"- Task: {task}",
        f"- Compiled UTC: {now}",
        "- Pack status: derived; rebuildable; not durable memory",
        "",
        "## Recent run snapshot",
        "",
    ]
    if latest:
        sections.extend(
            f"- `{item.experiment_id}` / `{item.run_id}`: {item.status}; seed={item.seed}; path=`{item.run_path}`"
            for item in latest
        )
    else:
        sections.append("- No run artifacts were found.")
    sections.append("")
    for path in files:
        sections.extend([f"## `{path.relative_to(root).as_posix()}`", "", "```text", _read(path), "```", ""])
    target = Path(output).resolve() if output else root / ".ai" / "packs" / f"context_{_slug(task)}.md"
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text("\n".join(sections), encoding="utf-8")
    return target
