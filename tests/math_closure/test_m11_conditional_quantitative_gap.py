from __future__ import annotations

import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT / "research" / "math_closure" / "k3"))

from m11_conditional_quantitative_gap import (  # noqa: E402
    ETA_M11,
    conditional_normalized_bound,
    verify_conditional_values,
)


def test_m11_conditional_piecewise_bound():
    assert verify_conditional_values()
    assert abs(conditional_normalized_bound(ETA_M11) - (2.0 / ETA_M11 / 3.0**0.5)) < 1e-12
