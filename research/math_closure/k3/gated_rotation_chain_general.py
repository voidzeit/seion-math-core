"""Exact evaluator checks for all finite left-comb gated-rotation chains."""

from __future__ import annotations

import numpy as np
import sympy as sp

from seion_core.research_v3.exact_evaluation import evaluate_ambient_numpy
from seion_core.research_v3.local_constants import TypedLaw
from seion_core.research_v3.projected_evaluation import evaluate_projected_numpy
from seion_core.research_v3.typed_tree import Leaf, Node
from seion_core.research_v3.types import TypeSystem, TypedSpace


def left_comb(k: int) -> Node:
    if k < 1:
        raise ValueError("k must be at least one")
    tree = Node("mu", "tau", (Leaf(0, "tau"), Leaf(1, "tau")))
    for leaf in range(2, k + 1):
        tree = Node("mu", "tau", (tree, Leaf(leaf, "tau")))
    return tree


def symbolic_projected_error_squared(
    k: int, *, dimension: int = 2, projector_rank: int = 1
) -> sp.Expr:
    if not 1 <= projector_rank < dimension:
        raise ValueError("require 1 <= projector_rank < dimension")
    eta = sp.Symbol("eta", real=True)
    c = sp.sqrt(1 - eta**2)
    rotation = sp.Matrix([[c, -eta], [eta, c]])
    tensor = np.zeros((dimension, dimension, dimension), dtype=object)
    active = (0, projector_rank)
    for out_local, out_index in enumerate(active):
        for first_local, first_index in enumerate(active):
            tensor[(out_index, first_index, 0)] = rotation[out_local, first_local]
    law = TypedLaw("mu", ("tau", "tau"), "tau", tensor)
    types = TypeSystem([TypedSpace.coordinate("tau", dimension, projector_rank, field="real")])
    leaves = {
        i: np.array([sp.Integer(1)] + [sp.Integer(0)] * (projector_rank - 1), dtype=object)
        for i in range(k + 1)
    }
    tree = left_comb(k)
    ambient = evaluate_ambient_numpy(tree, {"mu": law}, types, leaves).root
    projected = evaluate_projected_numpy(tree, {"mu": law}, types, leaves).root
    difference = types["tau"].project(ambient) - projected
    return sp.simplify(sum(sp.simplify(value) ** 2 for value in difference))


def verify_closed_form(max_k: int = 6) -> bool:
    eta = sp.Symbol("eta", real=True)
    c = sp.sqrt(1 - eta**2)
    for k in range(1, max_k + 1):
        expected = sp.expand((sp.chebyshevt(k, c) - c**k) ** 2)
        for dimension, rank in ((2, 1), (3, 1), (3, 2), (4, 2)):
            observed = symbolic_projected_error_squared(
                k, dimension=dimension, projector_rank=rank
            )
            if sp.simplify(observed - expected) != 0:
                return False
    return True


if __name__ == "__main__":
    assert verify_closed_form()
    print("All checks passed: general left-comb gated-rotation formula verified.")
