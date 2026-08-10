"""M11: quantitative k=3 gap under first-propagator saturation."""

from __future__ import annotations

from math import sqrt

ETA_M11 = sqrt(2.0 / 3.0)


def conditional_absolute_bound(eta: float, *, M: float = 1.0) -> float:
    """Return the normalized conditional bound G(eta)*M^3.

    The theorem applies to the k=3 chain when the first propagated-error
    direction attains the norm-M bound at the next node. Leaf norm product is
    normalized to one here.
    """

    if not 0.0 < eta <= 1.0 or M <= 0.0:
        raise ValueError("require 0 < eta <= 1 and M > 0")
    if eta <= ETA_M11:
        return M**3 * eta * sqrt(4.0 - 3.0 * eta * eta)
    return M**3 * (2.0 / sqrt(3.0))


def conditional_normalized_bound(eta: float) -> float:
    """Return G(eta)/eta relative to rho*M^2 (with rho=eta*M)."""

    return conditional_absolute_bound(eta) / eta


def verify_transition(tol: float = 1e-12) -> bool:
    left = ETA_M11 * sqrt(4.0 - 3.0 * ETA_M11 * ETA_M11)
    right = 2.0 / sqrt(3.0)
    return abs(left - right) <= tol


def verify_conditional_values() -> bool:
    if abs(conditional_normalized_bound(1.0) - 2.0 / sqrt(3.0)) > 1e-12:
        return False
    if conditional_normalized_bound(0.5) >= 2.0:
        return False
    if conditional_normalized_bound(0.9) >= 2.0:
        return False
    return verify_transition()


if __name__ == "__main__":
    assert verify_conditional_values()
    print(
        "M11 checks passed: conditional bound is eta*sqrt(4-3 eta^2) "
        "below sqrt(2/3), and 2/sqrt(3) above."
    )
