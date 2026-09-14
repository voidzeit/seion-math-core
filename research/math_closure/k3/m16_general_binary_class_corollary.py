"""Deterministic scope corollary for the arbitrary-node-law binary k=3 class."""

from __future__ import annotations

import math

from research.math_closure.k3.m14_exact_chain_constant import exact_chain_constant
from research.math_closure.k3.m15_exact_branching_constant import exact_branching_constant


def exact_general_binary_constant(eta: float, topology: str) -> float:
    """Return the exact value for a binary topology with no sharing constraint."""
    if topology == "chain":
        return exact_chain_constant(eta)
    if topology == "branching":
        return exact_branching_constant(eta)
    raise ValueError("topology must be 'chain' or 'branching'")


def verify_corollary() -> bool:
    alpha = math.sqrt(2.0 / 3.0)
    for eta in (1.0e-8, 0.1, 0.5, alpha, 0.8, 1.0):
        chain = exact_general_binary_constant(eta, "chain")
        branch = exact_general_binary_constant(eta, "branching")
        if not math.isclose(chain, branch, rel_tol=0.0, abs_tol=1.0e-14):
            return False
        if eta <= alpha:
            expected = math.sqrt(4.0 - 3.0 * eta * eta)
        else:
            expected = 2.0 / (math.sqrt(3.0) * eta)
        if not math.isclose(chain, expected, rel_tol=1.0e-13, abs_tol=1.0e-13):
            return False
    try:
        exact_general_binary_constant(0.5, "ternary")
    except ValueError:
        pass
    else:
        return False
    return True


if __name__ == "__main__":
    assert verify_corollary()
    print("All checks passed: arbitrary-node-law binary k=3 class corollary.")
