"""M2 exact example: E_T^proj = eta^2 for the k=2 homogeneous chain,
gated-planar-rotation construction (research/math_closure/k2/classification_theorem.tex).

Reproduces the exact symbolic proof directly against the real repo
evaluator (not a hand-reconstructed one) for several (dimension, rank)
pairs, confirming dimension/rank independence, then a floating-point
sweep over eta for a sanity cross-check.
"""

from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import sympy as sp

REPO_ROOT = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(REPO_ROOT / "src"))

from seion_core.research_v3.exact_evaluation import evaluate_ambient_numpy  # noqa: E402
from seion_core.research_v3.local_constants import TypedLaw  # noqa: E402
from seion_core.research_v3.projected_evaluation import evaluate_projected_numpy  # noqa: E402
from seion_core.research_v3.typed_tree import Leaf, Node  # noqa: E402
from seion_core.research_v3.types import TypeSystem, TypedSpace  # noqa: E402
from seion_core.research_v3.extremizers import rotation_extremizer  # noqa: E402


def symbolic_check(dimension: int, projector_rank: int) -> sp.Expr:
    eta = sp.Symbol("eta", real=True)
    tangent = sp.sqrt(1 - eta**2)
    rotation = sp.Matrix([[tangent, -eta], [eta, tangent]])
    tensor = np.zeros((dimension, dimension, dimension), dtype=object)
    for i in range(dimension):
        for j in range(dimension):
            tensor[(i, j, 0)] = sp.Integer(0)
    active = (0, projector_rank)
    for oi, oidx in enumerate(active):
        for fi, fidx in enumerate(active):
            tensor[(oidx, fidx, 0)] = rotation[oi, fi]
    law = TypedLaw("mu", ("tau", "tau"), "tau", tensor)
    types = TypeSystem([TypedSpace.coordinate("tau", dimension, projector_rank, field="real")])
    tree = Node("mu", "tau", (Node("mu", "tau", (Leaf(0, "tau"), Leaf(1, "tau"))), Leaf(2, "tau")))
    leaves = {
        i: np.array([sp.Integer(1)] + [sp.Integer(0)] * (projector_rank - 1), dtype=object)
        for i in range(3)
    }
    ambient = evaluate_ambient_numpy(tree, {"mu": law}, types, leaves).root
    projected = evaluate_projected_numpy(tree, {"mu": law}, types, leaves).root
    root_space = types["tau"]
    diff = root_space.project(np.array(ambient, dtype=object)) - np.array(projected, dtype=object)
    return sp.simplify(sum(sp.simplify(d) ** 2 for d in diff))


def numeric_check(eta: float) -> tuple[float, float]:
    tree = Node("mu", "tau", (Node("mu", "tau", (Leaf(0, "tau"), Leaf(1, "tau"))), Leaf(2, "tau")))
    ext = rotation_extremizer(tree, eta, dimension=2, projector_rank=1)
    ambient = evaluate_ambient_numpy(tree, ext.laws, ext.types, ext.reduced_inputs).root
    projected = evaluate_projected_numpy(tree, ext.laws, ext.types, ext.reduced_inputs).root
    root_space = ext.types["tau"]
    diff = root_space.project(ambient) - projected
    return float(np.linalg.norm(diff)), eta**2


def main() -> None:
    print("Symbolic (norm^2, should be eta**4 for every dimension/rank pair):")
    for dimension, rank in [(2, 1), (3, 1), (3, 2), (4, 2)]:
        result = symbolic_check(dimension, rank)
        print(f"  dimension={dimension} rank={rank}: norm^2 = {result}")
        (eta,) = result.free_symbols
        for test_val in (sp.Rational(1, 7), sp.Rational(1, 2), sp.Rational(9, 10)):
            lhs = complex(result.subs(eta, test_val))
            rhs = complex(test_val ** 4)
            assert abs(lhs - rhs) < 1e-12, f"closed form does not match at eta={test_val}"

    print("\nFloating-point cross-check (dimension=2, rank=1):")
    for eta in [1e-3, 1e-2, 1e-1, 0.5, 1.0]:
        measured, expected = numeric_check(eta)
        print(f"  eta={eta:6.3f}  measured={measured:.10f}  eta^2={expected:.10f}")
        assert abs(measured - expected) < 1e-9, "floating-point mismatch"

    print("\nAll checks passed: E_T^proj = eta^2 exactly for this construction.")


if __name__ == "__main__":
    main()
