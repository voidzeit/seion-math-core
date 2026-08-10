"""Explicit two-dimensional witness for the exact k=3 branching constant."""

from __future__ import annotations

from dataclasses import dataclass
import math

import numpy as np


ALPHA = math.sqrt(2.0 / 3.0)


def exact_branching_constant(eta: float) -> float:
    if not 0.0 < eta <= 1.0:
        raise ValueError("eta must lie in (0,1]")
    if eta <= ALPHA:
        return math.sqrt(4.0 - 3.0 * eta * eta)
    return 2.0 / (math.sqrt(3.0) * eta)


@dataclass(frozen=True, slots=True)
class BranchingWitness:
    eta: float
    realized_defect: float
    projected_error: float
    normalized_constant: float
    child_one_residual: float
    child_two_residual: float
    root_residual: float
    root_operator_norm: float


def construct_branching_witness(eta: float) -> BranchingWitness:
    """Build the M15 rank-one-projector witness at ``M=L=1``."""

    if not 0.0 < eta <= 1.0:
        raise ValueError("eta must lie in (0,1]")
    t = min(eta, ALPHA)
    p = math.sqrt(1.0 - t * t)
    e0 = np.array([1.0, 0.0])
    e1 = np.array([0.0, 1.0])
    P = np.outer(e0, e0)
    Q = np.eye(2) - P
    f = t * e1 + p * e0
    d = e1
    K = t * np.outer(e1, f) + p * t * np.outer(e0, d)
    U, _, Vt = np.linalg.svd(K)
    A = U @ Vt
    f1 = f.copy()
    f2 = f.copy()
    r1 = P @ f1
    r2 = P @ f2
    ambient_root = float(f1 @ A @ f2) * e0
    reduced_root = float(r1 @ A @ r2) * e0
    projected_error = float(np.linalg.norm(P @ ambient_root - reduced_root))
    return BranchingWitness(
        eta=eta,
        realized_defect=t,
        projected_error=projected_error,
        normalized_constant=projected_error / eta,
        child_one_residual=float(np.linalg.norm(Q @ f1)),
        child_two_residual=float(np.linalg.norm(Q @ f2)),
        root_residual=0.0,
        root_operator_norm=float(np.linalg.norm(A, 2)),
    )


def run_checks() -> None:
    for eta in (1.0e-6, 0.1, 0.5, ALPHA, 0.8, 0.9, 1.0):
        witness = construct_branching_witness(eta)
        assert math.isclose(
            witness.normalized_constant,
            exact_branching_constant(eta),
            rel_tol=1.0e-12,
            abs_tol=1.0e-12,
        )
        assert witness.child_one_residual <= eta + 1.0e-12
        assert witness.child_two_residual <= eta + 1.0e-12
        assert witness.root_residual <= eta + 1.0e-12
        assert witness.root_operator_norm <= 1.0 + 1.0e-12
    print("M15 exact branching-constant witness checks passed.")


if __name__ == "__main__":
    run_checks()
