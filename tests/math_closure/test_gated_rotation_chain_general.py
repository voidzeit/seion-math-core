from __future__ import annotations

import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT / "research" / "math_closure" / "k3"))

from gated_rotation_chain_general import (  # noqa: E402
    symbolic_projected_error_squared,
    verify_closed_form,
)


def test_general_left_comb_gated_rotation_formula():
    assert verify_closed_form(max_k=5)
    assert symbolic_projected_error_squared(4, dimension=4, projector_rank=2) != 0
