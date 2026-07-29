from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path


def main() -> int:
    root = Path(__file__).resolve().parents[1]
    command = [sys.executable, "-m", "pytest", "-q"]
    result = subprocess.run(command, cwd=root)
    (root / "artifacts" / "index").mkdir(parents=True, exist_ok=True)
    (root / "artifacts" / "index" / "test_matrix_status.json").write_text(json.dumps({"command": command, "exit_code": result.returncode}, indent=2) + "\n", encoding="utf-8")
    return result.returncode


if __name__ == "__main__":
    raise SystemExit(main())

