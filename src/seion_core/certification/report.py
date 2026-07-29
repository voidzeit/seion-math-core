from __future__ import annotations

import json
from pathlib import Path


def summarize_runs(repo_root: str | Path) -> list[dict]:
    root = Path(repo_root) / "artifacts" / "runs"
    records = []
    if not root.exists():
        return records
    for path in root.rglob("final_metrics.json"):
        try:
            record = json.loads(path.read_text(encoding="utf-8"))
            record["run_path"] = str(path.parent).replace("\\", "/")
            records.append(record)
        except Exception as exc:
            records.append({"status": "FAILED_RUNTIME", "run_path": str(path), "error": str(exc)})
    return records


def write_claims_report(repo_root: str | Path) -> Path:
    root = Path(repo_root)
    records = summarize_runs(root)
    target = root / "artifacts" / "index" / "claims_report.json"
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps({"runs": records, "count": len(records)}, indent=2) + "\n", encoding="utf-8")
    return target

