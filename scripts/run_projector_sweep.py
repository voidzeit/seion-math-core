from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from seion_core.certification.runner import certify_config


def main() -> int:
    run = certify_config(ROOT / "experiments" / "configs" / "finite_ternary_v1.yaml", ROOT)
    out = ROOT / "artifacts" / "data" / "projector_sweep.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps({"vertical_slice": str(run)}, indent=2) + "\n", encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

