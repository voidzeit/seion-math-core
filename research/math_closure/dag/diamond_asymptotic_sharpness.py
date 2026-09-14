"""Asymptotically sharp independent-law witness for the shared diamond DAG."""

from __future__ import annotations

import math


def diamond_witness_error(eta: float) -> float:
    """Exact error of the planar complex-multiplication diamond witness."""

    if not 0.0 < eta <= 1.0:
        raise ValueError("eta must lie in (0, 1]")
    theta = math.asin(eta)
    return abs(complex(math.cos(4.0 * theta), math.sin(4.0 * theta)) - math.cos(theta) ** 4)


def diamond_universal_path_constant() -> float:
    """The normalized first-order path constant for the shared diamond."""

    # u contributes along two paths; left and right contribute along one each.
    return 4.0


def diamond_witness_ratio(eta: float) -> float:
    return diamond_witness_error(eta) / eta


def run_checks() -> None:
    for eta in (1.0e-2, 1.0e-3, 1.0e-4):
        assert diamond_witness_ratio(eta) < diamond_universal_path_constant() + 1.0e-8
    assert abs(diamond_witness_ratio(1.0e-5) - 4.0) < 1.0e-4


if __name__ == "__main__":
    run_checks()
    print("Shared-diamond asymptotic sharpness checks passed.")

