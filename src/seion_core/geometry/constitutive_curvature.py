from __future__ import annotations

from ..algebra.ternary_law import TernaryLaw


def constitutive_curvature(law: TernaryLaw, *vectors):
    """Definition: the selected algebraic curvature is the selected associator."""
    return law.five_input_associator(*vectors)

