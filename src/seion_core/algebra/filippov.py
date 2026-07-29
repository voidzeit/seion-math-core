"""Filippov fundamental identity evaluator for ternary laws."""

from __future__ import annotations


def fundamental_identity_residual(law, x1, x2, y1, y2, y3):
    lhs = law(x1, x2, law(y1, y2, y3))
    rhs = law(law(x1, x2, y1), y2, y3) + law(y1, law(x1, x2, y2), y3) + law(y1, y2, law(x1, x2, y3))
    return lhs - rhs

