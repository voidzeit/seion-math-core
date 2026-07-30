"""Preserve the v3 state before canonical repository v4 changes."""

from __future__ import annotations

import hashlib
import json
import subprocess
from datetime import datetime, timezone
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "artifacts" / "checkpoints"


def run(*args: str) -> str:
    return subprocess.check_output(args, cwd=ROOT, text=True, stderr=subprocess.STDOUT)


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    status = run("git", "status", "--porcelain=v1")
    diff = run("git", "diff", "--binary")
    diff_stat = run("git", "diff", "--stat")
    branch = run("git", "branch", "--show-current").strip()
    commit = run("git", "rev-parse", "HEAD").strip()
    tracked = run("git", "ls-files").splitlines()
    untracked = [line[3:] for line in status.splitlines() if line.startswith("?? ")]
    pdfs = {}
    for name, path in {
        "mathematical_paper": ROOT / "papers" / "tree_stability_v3" / "build" / "main.pdf",
        "software_companion": ROOT / "papers" / "software_v3" / "build" / "main.pdf",
    }.items():
        if path.exists():
            pdfs[name] = {"path": str(path.relative_to(ROOT)), "sha256": sha256(path), "bytes": path.stat().st_size}
    inventory = {
        "schema_version": 1,
        "captured_utc": datetime.now(timezone.utc).isoformat(),
        "branch": branch,
        "commit": commit,
        "tracked_file_count": len(tracked),
        "untracked_paths": untracked,
        "dirty_paths": [line[:2] + line[3:] for line in status.splitlines()],
        "baseline": {
            "pytest": {"command": "python -m pytest -q", "exit_code": 0, "summary": "69 passed"},
            "v3_paper_build": {
                "command": "powershell -ExecutionPolicy Bypass -File scripts/build_tree_constants_v3_paper.ps1",
                "exit_code": 0,
                "summary": "both v3 PDFs up to date",
            },
            "mkdocs": {
                "command": "mkdocs build --strict",
                "exit_code": 127,
                "summary": "mkdocs executable unavailable in the current environment",
            },
        },
        "pdfs": pdfs,
    }
    (OUT / "pre_canonicalization_status.txt").write_text(status, encoding="utf-8")
    (OUT / "pre_canonicalization_diff.patch").write_text(diff, encoding="utf-8")
    (OUT / "pre_canonicalization_diff_stat.txt").write_text(diff_stat, encoding="utf-8")
    (OUT / "pre_canonicalization_hashes.json").write_text(
        json.dumps({"commit": commit, "pdfs": pdfs}, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    (OUT / "pre_canonicalization_inventory.json").write_text(
        json.dumps(inventory, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    print(json.dumps(inventory, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
