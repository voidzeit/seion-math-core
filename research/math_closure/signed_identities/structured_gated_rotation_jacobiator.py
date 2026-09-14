"""Exact evaluator check for the restricted gated-rotation Jacobiator result."""

from __future__ import annotations

import numpy as np
import sympy as sp

from seion_core.research_v3.exact_evaluation import evaluate_ambient_numpy
from seion_core.research_v3.local_constants import TypedLaw
from seion_core.research_v3.polynomial_forests import binary_jacobiator
from seion_core.research_v3.projected_evaluation import evaluate_projected_numpy
from seion_core.research_v3.types import TypeSystem, TypedSpace


def symbolic_projected_jacobiator_squared(dimension: int, projector_rank: int) -> sp.Expr:
    """Return the squared projected Jacobiator error as a SymPy expression."""

    if not 1 <= projector_rank < dimension:
        raise ValueError("require 1 <= projector_rank < dimension")
    eta = sp.Symbol("eta", real=True)
    tangent = sp.sqrt(1 - eta**2)
    rotation = sp.Matrix([[tangent, -eta], [eta, tangent]])
    tensor = np.zeros((dimension, dimension, dimension), dtype=object)
    active = (0, projector_rank)
    for out_local, out_index in enumerate(active):
        for first_local, first_index in enumerate(active):
            tensor[(out_index, first_index, 0)] = rotation[out_local, first_local]

    law = TypedLaw("mu", ("tau", "tau"), "tau", tensor)
    types = TypeSystem(
        [TypedSpace.coordinate("tau", dimension, projector_rank, field="real")]
    )
    leaves = {
        i: np.array([sp.Integer(1)] + [sp.Integer(0)] * (projector_rank - 1), dtype=object)
        for i in range(3)
    }
    forest = binary_jacobiator()
    ambient_sum = None
    projected_sum = None
    for term in forest.terms:
        ambient = evaluate_ambient_numpy(term.tree, {"mu": law}, types, leaves).root
        projected = evaluate_projected_numpy(term.tree, {"mu": law}, types, leaves).root
        ambient_sum = ambient if ambient_sum is None else ambient_sum + ambient
        projected_sum = projected if projected_sum is None else projected_sum + projected

    difference = types["tau"].project(ambient_sum) - projected_sum
    return sp.simplify(sum(sp.simplify(value) ** 2 for value in difference))


def verify_symbolic_identity() -> bool:
    for dimension, rank in ((2, 1), (3, 1), (3, 2), (4, 2)):
        if sp.simplify(symbolic_projected_jacobiator_squared(dimension, rank)) != 0:
            return False
    return True


if __name__ == "__main__":
    assert verify_symbolic_identity()
    print("All checks passed: restricted gated-rotation projected Jacobiator error is zero.")
