from __future__ import annotations

import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT / "research" / "math_closure" / "k3"))

from gated_rotation_general_arity import (  # noqa: E402
    closed_form_error_squared,
    rooted_shapes,
    verify_closed_form,
)


def test_arity_compatible_gated_rotation_formula():
    assert verify_closed_form(max_internal_nodes=3, max_arity=3)
    assert any(len(shape) == 3 for shape in rooted_shapes(1, max_arity=3) if shape)
    assert closed_form_error_squared((None, None, None), 0) == 0
