"""M22: exact high-eta regime for the rank-one/common-leaf same-law chain."""

from __future__ import annotations

import math

import numpy as np

from research.math_closure.k3.m20_k3_arbitrary_arity_exact_constant import W3
from seion_core.research_v3.exact_evaluation import evaluate_ambient_numpy
from seion_core.research_v3.local_constants import TypedLaw
from seion_core.research_v3.projected_evaluation import evaluate_projected_numpy
from seion_core.research_v3.typed_tree import Leaf, Node
from seion_core.research_v3.types import TypeSystem, TypedSpace


ALPHA = math.sqrt(2.0 / 3.0)


def _chain() -> Node:
    bottom = Node("mu", "tau", (Leaf(0, "tau"), Leaf(1, "tau")))
    middle = Node("mu", "tau", (bottom, Leaf(2, "tau")))
    return Node("mu", "tau", (middle, Leaf(3, "tau")))


def evaluate_rank_one_rotation(eta: float) -> tuple[float, float, float]:
    """Evaluate the repeated gated rotation with defect t=alpha <= eta."""

    if not ALPHA <= eta <= 1.0:
        raise ValueError("this evaluator is for sqrt(2/3) <= eta <= 1")
    t = ALPHA
    a = math.sqrt(1.0 - t * t)
    rotation = np.array([[a, -t], [t, a]], dtype=float)
    tensor = np.zeros((2, 2, 2), dtype=float)
    for output in range(2):
        for first in range(2):
            tensor[output, first, 0] = rotation[output, first]
    laws = {"mu": TypedLaw("mu", ("tau", "tau"), "tau", tensor)}
    types = TypeSystem([TypedSpace.coordinate("tau", 2, 1, field="real")])
    leaves = {label: np.array([1.0]) for label in range(4)}
    ambient = evaluate_ambient_numpy(_chain(), laws, types, leaves).root
    projected = evaluate_projected_numpy(_chain(), laws, types, leaves).root
    error = float(np.linalg.norm(types["tau"].project(ambient) - projected))
    return error, 1.0, t


def exact_rank_one_same_law_chain_constant(eta: float) -> float:
    if not ALPHA <= eta <= 1.0:
        raise ValueError("this exact formula is for sqrt(2/3) <= eta <= 1")
    return 2.0 / (math.sqrt(3.0) * eta)


def verify_high_eta_regime() -> bool:
    for eta in (ALPHA, 0.85, 0.9, 1.0):
        error, norm, defect = evaluate_rank_one_rotation(eta)
        if not math.isclose(norm, 1.0, rel_tol=0.0, abs_tol=1.0e-12):
            return False
        if not math.isclose(defect, ALPHA, rel_tol=0.0, abs_tol=1.0e-12):
            return False
        if not math.isclose(error / eta, exact_rank_one_same_law_chain_constant(eta), rel_tol=0.0, abs_tol=2.0e-12):
            return False
        if not math.isclose(error / eta, W3(eta), rel_tol=0.0, abs_tol=2.0e-12):
            return False
    return True


if __name__ == "__main__":
    assert verify_high_eta_regime()
    print("All checks passed: M22 high-eta rank-one same-law chain is exact.")
