"""Run identity, artifact-contract checks, and non-destructive deduplication."""

from __future__ import annotations

import csv
import hashlib
import json
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable

import yaml

from .models import RUN_STATUS_RANK, RunRecord


REQUIRED_RUN_ARTIFACTS = (
    "config.yaml",
    "resolved_config.yaml",
    "command.txt",
    "stdout.log",
    "stderr.log",
    "environment.json",
    "hardware.json",
    "run_manifest.json",
    "metrics.jsonl",
    "final_metrics.json",
    "certificate.json",
    "summary.md",
    "artifact_hashes.json",
)


def _read_json(path: Path) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}
    return value if isinstance(value, dict) else {}


def _config_fingerprint(run_dir: Path, manifest: dict[str, Any]) -> str:
    for name in ("resolved_config.yaml", "config.yaml"):
        path = run_dir / name
        if path.exists():
            return hashlib.sha256(path.read_bytes()).hexdigest()
    config = manifest.get("config", {})
    payload = json.dumps(config, sort_keys=True, default=str).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


def _as_int(value: Any) -> int | None:
    try:
        return None if value is None or value == "" else int(value)
    except (TypeError, ValueError):
        return None


def _relative(root: Path, path: Path) -> str:
    try:
        return path.resolve().relative_to(root.resolve()).as_posix()
    except ValueError:
        return path.as_posix()


def _record_from_directory(root: Path, run_dir: Path) -> RunRecord | None:
    metrics_path = run_dir / "final_metrics.json"
    metrics = _read_json(metrics_path)
    if not metrics and metrics_path.exists():
        metrics = {"status": "FAILED_RUNTIME", "error": "invalid final_metrics.json"}
    manifest = _read_json(run_dir / "run_manifest.json")
    config = manifest.get("config", {}) if isinstance(manifest.get("config"), dict) else {}
    experiment_id = str(
        metrics.get("experiment_id")
        or config.get("experiment_id")
        or config.get("id")
        or run_dir.parent.name
    )
    status = str(metrics.get("status") or manifest.get("status") or "UNKNOWN")
    precision = metrics.get("precision") or config.get("precision")
    seed = _as_int(metrics.get("seed", config.get("seed")))
    backend = metrics.get("backend") or config.get("backend") or manifest.get("backend")
    device = (
        metrics.get("device")
        or metrics.get("device_requested")
        or config.get("device")
        or manifest.get("device")
    )
    created = manifest.get("created_utc")
    if not created:
        created = datetime.fromtimestamp(run_dir.stat().st_mtime, timezone.utc).isoformat()
    missing = tuple(name for name in REQUIRED_RUN_ARTIFACTS if not (run_dir / name).exists())
    return RunRecord(
        run_id=str(manifest.get("run_id") or run_dir.name),
        experiment_id=experiment_id,
        status=status,
        epistemic_status=(
            metrics.get("epistemic_status") or manifest.get("epistemic_status")
        ),
        precision=None if precision is None else str(precision),
        seed=seed,
        backend=None if backend is None else str(backend),
        device=None if device is None else str(device),
        created_utc=str(created),
        run_path=_relative(root, run_dir),
        config_fingerprint=_config_fingerprint(run_dir, manifest),
        metrics=metrics,
        manifest=manifest,
        missing_artifacts=missing,
    )


def collect_runs(repo_root: str | Path) -> list[RunRecord]:
    root = Path(repo_root).resolve()
    runs_root = root / "artifacts" / "runs"
    if not runs_root.exists():
        return []
    records: list[RunRecord] = []
    for metrics_path in sorted(runs_root.rglob("final_metrics.json")):
        record = _record_from_directory(root, metrics_path.parent)
        if record is not None:
            records.append(record)
    return records


def _sort_key(record: RunRecord) -> tuple[int, str, str]:
    return (
        RUN_STATUS_RANK.get(record.status, -1),
        record.created_utc or "",
        record.run_path,
    )


def _csv_record(record: RunRecord, group: list[RunRecord]) -> dict[str, Any]:
    representative = sorted(group, key=_sort_key, reverse=True)[0]
    return {
        "run_id": representative.run_id,
        "experiment_id": representative.experiment_id,
        "status": representative.status,
        "epistemic_status": representative.epistemic_status or "",
        "precision": representative.precision or "",
        "seed": "" if representative.seed is None else representative.seed,
        "backend": representative.backend or "",
        "device": representative.device or "",
        "created_utc": representative.created_utc or "",
        "run_path": representative.run_path,
        "config_fingerprint": representative.config_fingerprint,
        "duplicate_count": len(group),
        "duplicate_run_ids": ";".join(item.run_id for item in sorted(group, key=lambda x: x.run_path)),
        "duplicate_paths": ";".join(item.run_path for item in sorted(group, key=lambda x: x.run_path)),
        "missing_artifacts": ";".join(representative.missing_artifacts),
        "limitation": "one representative per experiment/config/seed/precision/backend/device; history preserved",
    }


def _write_csv(path: Path, rows: Iterable[dict[str, Any]]) -> None:
    rows = list(rows)
    path.parent.mkdir(parents=True, exist_ok=True)
    fieldnames = list(rows[0].keys()) if rows else ["run_id", "experiment_id", "status"]
    with path.open("w", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(stream, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def deduplicate_runs(
    repo_root: str | Path,
    output: str | Path | None = None,
) -> dict[str, Any]:
    """Build a deterministic unique-instance view without modifying historical runs."""
    root = Path(repo_root).resolve()
    records = collect_runs(root)
    groups: dict[tuple[str, str, str, str, str, str], list[RunRecord]] = defaultdict(list)
    for record in records:
        groups[record.key].append(record)
    rows = [_csv_record(record, group) for key, group in sorted(groups.items(), key=lambda item: item[0]) for record in [group[0]]]
    target = Path(output).resolve() if output else root / "artifacts" / "index" / "run_index_deduplicated.csv"
    _write_csv(target, rows)
    duplicate_groups = [group for group in groups.values() if len(group) > 1]
    report = {
        "version": 1,
        "generated_utc": datetime.now(timezone.utc).isoformat(),
        "historical_run_count": len(records),
        "unique_scientific_instance_count": len(groups),
        "duplicate_group_count": len(duplicate_groups),
        "duplicate_record_count": sum(len(group) - 1 for group in duplicate_groups),
        "status_counts_historical": dict(Counter(record.status for record in records)),
        "status_counts_unique": dict(Counter(row["status"] for row in rows)),
        "incomplete_artifact_contract_runs": [
            record.run_path for record in records if record.missing_artifacts
        ],
        "historical_index_preserved": True,
        "output": _relative(root, target),
        "limitations": [
            "Scientific identity is inferred from experiment, resolved-config hash, seed, precision, backend, and device.",
            "Different seeds are separate instances; repeated attempts with the same identity are not.",
            "This is a derived view and does not establish independence of the underlying data-generating process.",
        ],
    }
    report_path = root / "artifacts" / "index" / "run_deduplication_report.json"
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    return report


def audit_run_artifacts(repo_root: str | Path) -> dict[str, Any]:
    records = collect_runs(repo_root)
    missing = {
        record.run_path: list(record.missing_artifacts)
        for record in records
        if record.missing_artifacts
    }
    return {
        "run_count": len(records),
        "contract_complete_count": len(records) - len(missing),
        "contract_incomplete_count": len(missing),
        "missing_artifacts": missing,
        "statuses": dict(Counter(record.status for record in records)),
    }
