from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from seion_core.examples.associative import coordinatewise_associative_law
from seion_core.algebra.associators import sample_associator_defect


def main() -> int:
    law = coordinatewise_associative_law(3)
    rows = []
    for dtype in ["float32", "float64", "complex64", "complex128"]:
        result = sample_associator_defect(law, samples=32, seed=11, dtype=dtype)
        rows.append(result.to_dict())
    target = ROOT / "artifacts" / "data" / "precision_sweep.json"
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(rows, indent=2) + "\n", encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

