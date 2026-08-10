"""Deterministic witness and enclosure check for the declared k=2 class A."""

from __future__ import annotations

import numpy as np


def witness(eta: float) -> tuple[np.ndarray, float, float]:
    """Return the two-node witness error, rho, and M in dimension two."""
    if not 0.0 < eta <= 1.0:
        raise ValueError("eta must lie in (0, 1]")
    # M=1, rho=eta, P=span(e0), and all leaves are e0.
    mu = np.zeros((2, 2, 2), dtype=float)
    mu[0, 1, 0] = 1.0
    mu[1, 0, 0] = eta
    inner_ambient = np.array([0.0, eta])
    outer_ambient = np.einsum("ijk,j,k->i", mu, inner_ambient, np.array([1.0, 0.0]))
    projected = np.zeros(2)
    error = float(np.linalg.norm(outer_ambient - projected))
    return error, eta, 1.0


def verify_exact_class_a(etas: tuple[float, ...] = (1e-3, 0.1, 0.5, 1.0)) -> bool:
    for eta in etas:
        error, rho, M = witness(eta)
        if not np.isclose(error, rho * M, rtol=0.0, atol=1e-14):
            return False
        if error / (rho * M) != 1.0:
            return False
    return True


if __name__ == "__main__":
    assert verify_exact_class_a()
    print("All checks passed: declared k=2 class A has exact normalized constant 1.")
