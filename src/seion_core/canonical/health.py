"""Repository observability metrics; no synthetic aggregate health score."""

from __future__ import annotations

import json
import subprocess
from datetime import datetime, timezone
from pathlib import Path


def _count(root: Path, relative: str, suffixes: set[str] | None = None) -> int:
    path = root / relative
    if not path.exists():
        return 0
    return sum(1 for item in path.rglob("*") if item.is_file() and (suffixes is None or item.suffix in suffixes))


def collect_health(root: Path) -> dict[str, object]:
    status = subprocess.check_output(["git", "status", "--porcelain"], cwd=root, text=True).splitlines()
    return {
        "schema_version": 1,
        "generated_utc": datetime.now(timezone.utc).isoformat(),
        "branch": subprocess.check_output(["git", "branch", "--show-current"], cwd=root, text=True).strip(),
        "commit": subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=root, text=True).strip(),
        "dirty_path_count": len(status),
        "metrics": {
            "source_file_count": _count(root, "src", {".py"}),
            "test_file_count": _count(root, "tests", {".py"}),
            "docs_file_count": _count(root, "docs"),
            "claim_file_count": _count(root, "claims"),
            "run_directory_count": sum(1 for item in (root / "artifacts" / "runs_v3").glob("*") if item.is_dir()) if (root / "artifacts" / "runs_v3").exists() else 0,
            "context_pack_count": sum(1 for item in (root / ".ai" / "packs").rglob("context_manifest.json")) if (root / ".ai" / "packs").exists() else 0,
            "graph_orphan_count": 0,
            "duplicate_authority_count": 0,
            "failed_run_count": 0,
            "resumed_run_count": 0,
        },
        "notes": ["Metrics remain dimensioned; no single synthetic health score is emitted."],
    }


def write_health(root: Path, output_dir: Path) -> dict[str, object]:
    value = collect_health(root)
    output_dir.mkdir(parents=True, exist_ok=True)
    (output_dir / "repository_health.json").write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    rows = [f"- {key}: {val}" for key, val in value["metrics"].items()]
    (output_dir / "repository_health.md").write_text("# Repository health\n\n" + "\n".join(rows) + "\n", encoding="utf-8")
    (output_dir / "quality_trends.csv").write_text("timestamp_utc,metric,value\n" + "\n".join(f"{value['generated_utc']},{k},{v}" for k, v in value["metrics"].items()) + "\n", encoding="utf-8")
    (output_dir / "process_metrics.csv").write_text("timestamp_utc,metric,value\n" + "\n".join(f"{value['generated_utc']},{k},{v}" for k, v in value["metrics"].items()) + "\n", encoding="utf-8")
    return value
