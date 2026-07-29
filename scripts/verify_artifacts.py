from __future__ import annotations

import json
import sys
from pathlib import Path


def main() -> int:
    root = Path(__file__).resolve().parents[1]
    errors = []
    for path in (root / "artifacts" / "runs").rglob("artifact_hashes.json") if (root / "artifacts" / "runs").exists() else []:
        hashes = json.loads(path.read_text(encoding="utf-8"))
        for relative, expected in hashes.items():
            target = path.parent / relative
            if not target.exists():
                errors.append(f"missing {target}")
    print(json.dumps({"checked": True, "errors": errors}, indent=2))
    return 1 if errors else 0


if __name__ == "__main__":
    raise SystemExit(main())

