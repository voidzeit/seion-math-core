from __future__ import annotations

import sympy as sp


def symbolic_projector_identity() -> dict:
    q = sp.MatrixSymbol("Q", 3, 2)
    p = q * q.T
    return {"status": "simplification_under_assumption_QTQ_I", "identity": "P^2-P=Q(Q^TQ-I)Q^T", "expression": str(p * p - p)}

