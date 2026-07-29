"""Run every row in experiments/matrices/canonical_run_matrix.yaml."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from seion_core.certification.matrix import run_canonical_matrix


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--device", default="auto")
    parser.add_argument("--profile", default="manual")
    args = parser.parse_args()
    result = run_canonical_matrix(ROOT, device=args.device, profile=args.profile)
    print(json.dumps(result, indent=2))
    return 0 if result["all_mandatory_rows_passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
