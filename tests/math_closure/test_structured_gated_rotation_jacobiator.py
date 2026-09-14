from __future__ import annotations

import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT / "research" / "math_closure" / "signed_identities"))

from structured_gated_rotation_jacobiator import (  # noqa: E402
    symbolic_projected_jacobiator_squared,
    verify_symbolic_identity,
)


def test_restricted_gated_rotation_jacobiator_is_exactly_zero():
    assert verify_symbolic_identity()
    assert symbolic_projected_jacobiator_squared(4, 2) == 0
