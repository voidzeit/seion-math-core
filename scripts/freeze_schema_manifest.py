"""Compute/refresh schemas/SCHEMA_FREEZE_MANIFEST.json.

Run this deliberately, as part of a recorded migration (add an entry to
schemas/MIGRATIONS.md in the same commit), never as an incidental side
effect of unrelated work. tests/governance/test_evidence_contract.py
fails closed if the manifest and the actual file hashes disagree.
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCHEMA_DIR = ROOT / "schemas"
MANIFEST_PATH = SCHEMA_DIR / "SCHEMA_FREEZE_MANIFEST.json"


def compute_manifest() -> dict[str, str]:
    hashes = {}
    for path in sorted(SCHEMA_DIR.glob("*.json")):
        if path.name == MANIFEST_PATH.name:
            continue
        hashes[path.name] = hashlib.sha256(path.read_bytes()).hexdigest()
    return hashes


def main() -> int:
    manifest = {
        "version": 1,
        "note": "sha256 of each frozen schemas/*.json file. Regenerate only as part of a recorded migration in schemas/MIGRATIONS.md.",
        "hashes": compute_manifest(),
    }
    MANIFEST_PATH.write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(f"wrote {MANIFEST_PATH} ({len(manifest['hashes'])} schemas)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
