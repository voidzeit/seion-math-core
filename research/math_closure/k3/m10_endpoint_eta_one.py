"""Executable algebraic check for the M10 endpoint eta=1 addendum."""

from __future__ import annotations

import math


def endpoint_values(M: float = 1.0) -> tuple[float, float, float]:
    if M <= 0.0:
        raise ValueError("M must be positive")
    rho = M
    q_star = M / math.sqrt(2.0)
    first = M * M * q_star
    second = M * rho * math.sqrt(M * M - q_star * q_star)
    envelope = (first + second) / (rho * M * M)
    return q_star, first, second if math.isfinite(envelope) else float("nan")


def run_checks() -> None:
    q_star, first, second = endpoint_values()
    assert math.isclose(q_star, 1.0 / math.sqrt(2.0), rel_tol=0.0, abs_tol=1.0e-15)
    assert math.isclose(first, 1.0 / math.sqrt(2.0), rel_tol=0.0, abs_tol=1.0e-15)
    assert math.isclose(second, 1.0 / math.sqrt(2.0), rel_tol=0.0, abs_tol=1.0e-15)
    assert math.isclose(first + second, math.sqrt(2.0), rel_tol=0.0, abs_tol=1.0e-15)
    print("M10 eta=1 endpoint algebra checks passed: U3(1)=sqrt(2), both terms nonzero.")


if __name__ == "__main__":
    run_checks()
