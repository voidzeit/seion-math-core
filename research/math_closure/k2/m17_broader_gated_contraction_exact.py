"""Exact evaluator for the contractive gated-planar repeated-law subclass."""

from __future__ import annotations

import math

import numpy as np


def contractive_gated_error(eta: float, M: float = 1.0) -> tuple[float, float, float]:
    """Return projected error, operator norm, and closure norm of the witness."""
    if not 0.0 < eta <= 1.0 or M <= 0.0:
        raise ValueError("require 0 < eta <= 1 and M > 0")
    rho = eta * M
    A = np.array([[0.0, M], [rho, 0.0]])
    P = np.diag([1.0, 0.0])
    Q = np.eye(2) - P
    e0 = np.array([1.0, 0.0])
    error_vector = P @ A @ Q @ A @ e0
    return float(np.linalg.norm(error_vector)), float(np.linalg.norm(A, 2)), float(np.linalg.norm(Q @ A @ P, 2))


def exact_constant(eta: float) -> float:
    if not 0.0 < eta <= 1.0:
        raise ValueError("eta must lie in (0,1]")
    return 1.0


def verify_theorem() -> bool:
    for eta in (1.0e-8, 0.1, 0.5, 1.0):
        error, operator_norm, closure_norm = contractive_gated_error(eta, M=3.0)
        rho = 3.0 * eta
        if not math.isclose(operator_norm, 3.0, rel_tol=0.0, abs_tol=1.0e-14):
            return False
        if not math.isclose(closure_norm, rho, rel_tol=0.0, abs_tol=1.0e-14):
            return False
        if not math.isclose(error, 3.0 * rho, rel_tol=0.0, abs_tol=1.0e-12):
            return False
        if not math.isclose(error / (rho * 3.0), exact_constant(eta), rel_tol=0.0, abs_tol=1.0e-14):
            return False
    return True


if __name__ == "__main__":
    assert verify_theorem()
    print("All checks passed: contractive gated-planar repeated-law constant is 1.")
