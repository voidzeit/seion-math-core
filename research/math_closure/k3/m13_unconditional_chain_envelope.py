"""Exact scalar checks for the unconditional M13 chain envelope."""

from __future__ import annotations

import math


ALPHA = math.sqrt(2.0 / 3.0)
ETA_STAR = math.sqrt((math.sqrt(5.0) - 1.0) / 2.0)


def m13_bound(eta: float) -> float:
    if not 0.0 < eta <= 1.0:
        raise ValueError("eta must lie in (0,1]")
    if eta <= ALPHA:
        return math.sqrt(4.0 - 3.0 * eta * eta)
    return 2.0 / (math.sqrt(3.0) * eta)


def m9_bound(eta: float) -> float:
    if not 0.0 < eta <= 1.0:
        raise ValueError("eta must lie in (0,1]")
    if eta <= ETA_STAR:
        return 1.0 + math.sqrt(1.0 - eta * eta)
    return math.sqrt(1.0 + eta * eta) / eta


def explicit_gap(eta: float) -> float:
    return m9_bound(eta) - m13_bound(eta)


def run_checks() -> None:
    assert math.isclose(m13_bound(ALPHA), math.sqrt(2.0), abs_tol=1.0e-14)
    assert math.isclose(m9_bound(ETA_STAR), (1.0 + math.sqrt(5.0)) / 2.0, abs_tol=1.0e-14)
    for eta in (1.0e-6, 0.1, ETA_STAR, 0.8, ALPHA, 0.9, 1.0):
        assert m13_bound(eta) < m9_bound(eta)
        assert explicit_gap(eta) > 0.0
    print("M13 unconditional chain-envelope checks passed.")


if __name__ == "__main__":
    run_checks()
