"""M23: exact unary-operator reduction for the strict same-law chain class.

The reduction is deliberately weaker than an extremal theorem.  It identifies
the complete optimization problem forced by a common projected leaf and a
rank-one projector, while leaving its low-eta value open.
"""

from __future__ import annotations

import math

import numpy as np

from seion_core.research_v3.exact_evaluation import evaluate_ambient_numpy
from seion_core.research_v3.local_constants import TypedLaw
from seion_core.research_v3.projected_evaluation import evaluate_projected_numpy
from seion_core.research_v3.typed_tree import Leaf, Node
from seion_core.research_v3.types import TypeSystem, TypedSpace


def chain_tree() -> Node:
    """Return the strict binary three-internal-node left chain."""

    bottom = Node("mu", "tau", (Leaf(0, "tau"), Leaf(1, "tau")))
    middle = Node("mu", "tau", (bottom, Leaf(2, "tau")))
    return Node("mu", "tau", (middle, Leaf(3, "tau")))


def operator_error(A: np.ndarray, e0: np.ndarray | None = None) -> float:
    """Return ``|<e0,A^3 e0>-<e0,A e0>^3|`` for a real square matrix."""

    A = np.asarray(A, dtype=float)
    if A.ndim != 2 or A.shape[0] != A.shape[1]:
        raise ValueError("A must be a square matrix")
    if e0 is None:
        e0 = np.eye(A.shape[0], dtype=float)[0]
    e0 = np.asarray(e0, dtype=float)
    if e0.shape != (A.shape[0],) or not math.isclose(float(np.linalg.norm(e0)), 1.0, abs_tol=1.0e-12):
        raise ValueError("e0 must be a unit vector with the same dimension as A")
    a = float(e0 @ A @ e0)
    return abs(float(e0 @ np.linalg.matrix_power(A, 3) @ e0) - a**3)


def gated_tensor(A: np.ndarray, e0_index: int = 0) -> np.ndarray:
    """Realize a linear map as ``mu(x,y)=A x <e0,y>``."""

    A = np.asarray(A, dtype=float)
    if A.ndim != 2 or A.shape[0] != A.shape[1]:
        raise ValueError("A must be a square matrix")
    if not 0 <= e0_index < A.shape[0]:
        raise ValueError("e0_index is out of range")
    tensor = np.zeros((A.shape[0], A.shape[1], A.shape[1]), dtype=float)
    tensor[:, :, e0_index] = A
    return tensor


def evaluated_projected_error(A: np.ndarray, e0_index: int = 0) -> float:
    """Evaluate the realized gated law through the repository tree engine."""

    A = np.asarray(A, dtype=float)
    dimension = A.shape[0]
    if A.ndim != 2 or A.shape[1] != dimension:
        raise ValueError("A must be square")
    law = TypedLaw("mu", ("tau", "tau"), "tau", gated_tensor(A, e0_index))
    types = TypeSystem([TypedSpace.coordinate("tau", dimension, 1, field="real")])
    # The tree evaluator takes reduced coordinates at leaves; the coordinate
    # rank-one lift maps the scalar ``[1]`` to the ambient vector ``e0``.
    leaves = {label: np.array([1.0]) for label in range(4)}
    tree = chain_tree()
    ambient = evaluate_ambient_numpy(tree, {"mu": law}, types, leaves).root
    projected = evaluate_projected_numpy(tree, {"mu": law}, types, leaves).root
    return float(np.linalg.norm(types["tau"].project(ambient) - projected))


def verify_reduction(seed: int = 23, trials: int = 16) -> bool:
    """Check the exact identity on random finite-dimensional contractions."""

    rng = np.random.default_rng(seed)
    for _ in range(trials):
        dimension = int(rng.integers(2, 7))
        A = rng.normal(size=(dimension, dimension))
        A /= max(1.0, float(np.linalg.norm(A, 2)))
        matrix_value = operator_error(A)
        engine_value = evaluated_projected_error(A)
        if not math.isclose(matrix_value, engine_value, rel_tol=0.0, abs_tol=2.0e-11):
            return False
    return True


if __name__ == "__main__":
    assert verify_reduction()
    print("All checks passed: M23 unary-operator reduction is exact.")
