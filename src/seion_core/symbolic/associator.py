from __future__ import annotations

import sympy as sp


def symbolic_associator_expansion() -> dict:
    a, b, c, d, e = sp.symbols("a b c d e")
    mu = sp.Function("mu")
    expression = mu(mu(a, b, c), d, e) - mu(a, b, mu(c, d, e))
    return {"status": "general_symbolic_derivation", "expression": str(expression), "simplified": str(sp.expand(expression))}

