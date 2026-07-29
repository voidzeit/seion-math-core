from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from seion_core.certification.report import write_claims_report


if __name__ == "__main__":
    print(write_claims_report(ROOT))

