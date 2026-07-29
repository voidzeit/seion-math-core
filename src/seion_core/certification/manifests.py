from __future__ import annotations

import json
import platform
import sys
from datetime import datetime, timezone
from pathlib import Path

from ..numerics.reproducibility import inventory


def run_manifest(repo_root: Path, config: dict, run_id: str, status: str) -> dict:
    env = inventory(repo_root)
    return {
        "run_id": run_id,
        "created_utc": datetime.now(timezone.utc).isoformat(),
        "status": status,
        "config": config,
        "code_version": "0.1.0",
        "git_commit": env.get("git_commit"),
        "dirty_worktree": env.get("dirty_worktree"),
        "python": sys.version,
        "os": platform.platform(),
        "hardware": env,
        "backend": "numpy",
    }


def write_json(path: Path, value: dict) -> None:
    path.write_text(json.dumps(value, indent=2, default=str) + "\n", encoding="utf-8")

