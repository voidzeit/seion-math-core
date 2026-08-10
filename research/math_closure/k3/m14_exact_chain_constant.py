"""Explicit two-dimensional witnesses attaining the M13 chain envelope."""

from __future__ import annotations

from dataclasses import dataclass
import math

import numpy as np


ALPHA = math.sqrt(2.0 / 3.0)


def exact_chain_constant(eta: float) -> float:
    if not 0.0 < eta <= 1.0:
        raise ValueError("eta must lie in (0,1]")
    if eta <= ALPHA:
        return math.sqrt(4.0 - 3.0 * eta * eta)
    return 2.0 / (math.sqrt(3.0) * eta)


@dataclass(frozen=True, slots=True)
class ChainWitness:
    eta: float
    realized_defect: float
    projected_error: float
    normalized_constant: float
    first_residual: float
    second_residual: float
    root_residual: float
    operator_norms: tuple[float, float, float]


def construct_chain_witness(eta: float) -> ChainWitness:
    """Build and evaluate the dimension-two M14 witness at ``M=L=1``."""

    if not 0.0 < eta <= 1.0:
        raise ValueError("eta must lie in (0,1]")
    t = min(eta, ALPHA)
    p = math.sqrt(1.0 - t * t)
    c = p
    e0 = np.array([1.0, 0.0])
    e1 = np.array([0.0, 1.0])
    P = np.outer(e0, e0)
    Q = np.eye(2) - P

    # N e0 = t e1 - c e0 and N e1 = c e1 + t e0.
    N = np.array([[-c, t], [t, c]], dtype=float)
    f1 = t * e1 + p * e0
    r1 = P @ f1
    f2 = N @ f1
    r2 = P @ (N @ r1)
    d2 = f2 - r2
    v = d2
    vnorm = float(np.linalg.norm(v))
    A = np.outer(e0, v) / vnorm
    ambient_root = A @ f2
    reduced_root = P @ (A @ r2)
    projected_error = float(np.linalg.norm(P @ ambient_root - reduced_root))

    first_residual = float(np.linalg.norm(Q @ f1))
    second_residual = float(np.linalg.norm(Q @ (N @ e0)))
    root_residual = float(np.linalg.norm(Q @ (A @ e0)))
    return ChainWitness(
        eta=eta,
        realized_defect=t,
        projected_error=projected_error,
        normalized_constant=projected_error / eta,
        first_residual=first_residual,
        second_residual=second_residual,
        root_residual=root_residual,
        operator_norms=(float(np.linalg.norm(N, 2)), float(np.linalg.norm(A, 2)), 1.0),
    )


def run_checks() -> None:
    for eta in (1.0e-6, 0.1, 0.5, ALPHA, 0.8, 0.9, 1.0):
        witness = construct_chain_witness(eta)
        assert witness.normalized_constant == pytest_approx(exact_chain_constant(eta))
        assert witness.first_residual <= eta + 1.0e-12
        assert witness.second_residual <= eta + 1.0e-12
        assert witness.root_residual <= eta + 1.0e-12
        assert all(norm <= 1.0 + 1.0e-12 for norm in witness.operator_norms)
    print("M14 exact chain-constant witness checks passed.")


def pytest_approx(value: float):
    """Small local comparison helper so the executable has no test dependency."""

    class _Approx:
        def __eq__(self, other: object) -> bool:
            return isinstance(other, (int, float)) and math.isclose(
                float(other), value, rel_tol=1.0e-12, abs_tol=1.0e-12
            )

    return _Approx()


if __name__ == "__main__":
    run_checks()
