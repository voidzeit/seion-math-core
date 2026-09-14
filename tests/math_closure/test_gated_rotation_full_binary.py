from __future__ import annotations

import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT / "research" / "math_closure" / "k3"))

from gated_rotation_full_binary import (  # noqa: E402
    closed_form_error_squared,
    full_binary_shapes,
    verify_closed_form,
)


def test_all_ordered_full_binary_gated_rotation_shapes_are_closed():
    assert verify_closed_form(max_internal_nodes=4)
    assert len(full_binary_shapes(4)) == 14
    assert closed_form_error_squared(((None, None), (None, None)), 0) == 0
