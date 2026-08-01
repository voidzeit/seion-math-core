"""M3 certificates: exact closed forms for the k=3 chain and branching
gated-rotation constructions (research/math_closure/k3/topology_{chain,branching}.tex).

Reproduces both results directly against the real repo evaluator with
symbolic eta (not a hand-reconstructed evaluator), then locates the exact
optimal eta and the exact best-achievable ratio to the universal
(k-1)=2 bound for each topology.
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


def _symbolic_rotation_tensor(dimension: int, projector_rank: int, eta: sp.Symbol) -> np.ndarray:
    tangent = sp.sqrt(1 - eta**2)
    rotation = sp.Matrix([[tangent, -eta], [eta, tangent]])
    tensor = np.zeros((dimension, dimension, dimension), dtype=object)
    for idx in np.ndindex(tensor.shape):
        tensor[idx] = sp.Integer(0)
    active = (0, projector_rank)
    for oi, oidx in enumerate(active):
        for fi, fidx in enumerate(active):
            tensor[(oidx, fidx, 0)] = rotation[oi, fi]
    return tensor


def projected_error_squared(tree: Node, n_leaves: int, *, dimension: int = 2, projector_rank: int = 1) -> sp.Expr:
    eta = sp.Symbol("eta", real=True)
    tensor = _symbolic_rotation_tensor(dimension, projector_rank, eta)
    law = TypedLaw("mu", ("tau", "tau"), "tau", tensor)
    types = TypeSystem([TypedSpace.coordinate("tau", dimension, projector_rank, field="real")])
    leaves = {i: np.array([sp.Integer(1)] + [sp.Integer(0)] * (projector_rank - 1), dtype=object) for i in range(n_leaves)}
    ambient = evaluate_ambient_numpy(tree, {"mu": law}, types, leaves).root
    projected = evaluate_projected_numpy(tree, {"mu": law}, types, leaves).root
    root_space = types["tau"]
    diff = root_space.project(np.array(ambient, dtype=object)) - np.array(projected, dtype=object)
    return sp.simplify(sum(sp.simplify(d) ** 2 for d in diff))


def main() -> None:
    chain = Node("mu", "tau", (Node("mu", "tau", (Node("mu", "tau", (Leaf(0, "tau"), Leaf(1, "tau"))), Leaf(2, "tau"))), Leaf(3, "tau")))
    branch = Node("mu", "tau", (Node("mu", "tau", (Leaf(0, "tau"), Leaf(1, "tau"))), Node("mu", "tau", (Leaf(2, "tau"), Leaf(3, "tau")))))

    chain_sq = projected_error_squared(chain, 4)
    branch_sq = projected_error_squared(branch, 4)
    print("chain:  E_T^proj(eta)^2 =", chain_sq, " -> E_T^proj =", sp.sqrt(chain_sq))
    print("branch: E_T^proj(eta)^2 =", branch_sq, " -> E_T^proj =", sp.sqrt(branch_sq))

    (eta,) = chain_sq.free_symbols
    universal_bound = 2 * eta  # (k-1)*rho*M^(k-1)*L, k=3, rho=eta, M=1, L=1
    chain_ratio = sp.sqrt(chain_sq) / universal_bound
    branch_ratio = sp.sqrt(branch_sq) / universal_bound

    for name, ratio in [("chain", chain_ratio), ("branch", branch_ratio)]:
        f = sp.simplify(ratio)
        crit = sp.solve(sp.diff(f, eta), eta)
        real_valid = []
        for c in crit:
            try:
                value = complex(c)
            except TypeError:
                continue
            if abs(value.imag) < 1e-9 and 0 < value.real < 1:
                real_valid.append(sp.nsimplify(value.real, [sp.sqrt(2)]))
        best_eta = real_valid[0]
        best_ratio = sp.simplify(f.subs(eta, best_eta))
        print(f"{name}: optimal eta = {best_eta} = {float(best_eta):.6f}, "
              f"best ratio = {best_ratio} = {float(best_ratio):.6f}, "
              f"min relative gap = {float(1 - best_ratio):.6f}")


if __name__ == "__main__":
    main()
