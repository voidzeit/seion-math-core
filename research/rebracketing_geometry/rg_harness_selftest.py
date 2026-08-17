"""Can the search harness even express the known extremizer?

The same-law arm of the sweep reaches only ~0.84 of J_2 = 2 at D=3, rank 2 --
the very cell where Theorem 3.1's witness attains 2 exactly, for every eta. A
shortfall like that has two very different causes, and they call for opposite
responses:

  OPTIMIZER FAILURE      the witness is inside the search space, Adam does not
                         find it       -> fix the optimizer/initialization
  REPRESENTABILITY BUG   the witness is NOT inside the search space, because
                         the feasibility pipeline distorts it -> fix the
                         parametrization; no amount of search will ever
                         calibrate the class

This file decides between them: it feeds the exact witness in as the raw
tensor, runs it through the harness's own feasibility projection and
evaluation, and reports the J it comes out with. If that is 2, the witness is
representable and the shortfall is optimizer failure. If it is below 2, the
pipeline is destroying the extremizer.

Coordinate note: `coordinate_projectors` puts Ran(P) on the FIRST `rank`
coordinates, so the witness of RG_CANONICAL.md Theorem 3.1 is relabelled
(e_0, e_1, e_2) -> (a, b, n) with P = diag(1,1,0):

    mu(x,y,z) = eta * x0 y0 z0 * e2  +  (x2 y0 - x0 y2) * z1 * e0
    leaves x1..x4 = e0,  x5 = e1
"""

from __future__ import annotations

import argparse
import math
import sys
from pathlib import Path

import torch

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

from rg_kernels import DTYPE, coordinate_projectors  # noqa: E402
from rg_fused_search import (  # noqa: E402
    audit_admissibility, build_laws, evaluate, feasibility_factors,
    share_laws,
)


def witness_raw(eta: float, device) -> torch.Tensor:
    """Theorem 3.1's witness in the harness's coordinate convention."""
    law = torch.zeros(1, 3, 3, 3, 3, dtype=DTYPE, device=device)
    law[0, 2, 0, 0, 0] = eta        # eta * x0 y0 z0 * e2   (the closure defect)
    law[0, 0, 2, 0, 1] = 1.0        # + x2 y0 z1 * e0
    law[0, 0, 0, 2, 1] = -1.0       # - x0 y2 z1 * e0
    return law


def witness_leaves(device) -> torch.Tensor:
    leaves = torch.zeros(1, 5, 3, dtype=DTYPE, device=device)
    leaves[0, :4, 0] = 1.0          # x1..x4 = e0
    leaves[0, 4, 1] = 1.0           # x5     = e1
    return leaves


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--etas", type=float, nargs="+",
                        default=[0.05, 0.3, 1 / math.sqrt(2), 1.0])
    parser.add_argument("--strength", type=int, nargs=2, default=[64, 200],
                        metavar=("RESTARTS", "ITERS"),
                        help="operator-norm estimator strength; must be "
                             "converged at this dimension (D=3 needs 18/120)")
    args = parser.parse_args()

    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    print(f"device={device}  witness: D=3, rank(P)=2, one law, one projector\n")
    print(f"{'eta':>8} {'J via harness':>15} {'exact':>8} {'gap':>11} "
          f"{'op norm':>9} {'closure/eta':>12} {'chi':>7}")

    worst = 0.0
    for eta in args.etas:
        eta_vec = torch.full((1,), eta, dtype=DTYPE, device=device)
        shared = torch.ones(1, dtype=torch.bool, device=device)
        rank = torch.full((1,), 2, dtype=torch.long, device=device)
        P = coordinate_projectors(rank, 3, device)
        projectors = (P, P, P)

        raw = witness_raw(eta, device)
        raws = {key: raw for key in ("inner_L", "inner_M", "root_L", "root_M")}
        leaves = witness_leaves(device)

        with torch.no_grad():
            laws = share_laws(raws, shared)
            strength = tuple(args.strength)
            factors = feasibility_factors(laws, projectors, *strength)
            A_hat, PA, D, geometry = evaluate(laws, projectors, leaves,
                                              eta_vec, factors, shared)
            built = build_laws(laws, projectors, eta_vec, factors, shared)
            op_norm, closure = audit_admissibility(built, projectors, eta_vec,
                                                   strength)
            e_L, e_M = geometry["e_L"][0], geometry["e_M"][0]
            chi = float(torch.dot(e_L, e_M)
                        / (e_L.norm() * e_M.norm()).clamp_min(1e-14))

        achieved = float(D[0].norm() / eta)
        gap = 2.0 - achieved
        worst = max(worst, abs(gap))
        print(f"{eta:8.4f} {achieved:15.9f} {2.0:8.1f} {gap:+11.2e} "
              f"{float(op_norm[0]):9.6f} {float(closure[0]):12.6f} "
              f"{chi:+7.3f}")

    print()
    if worst < 1e-9:
        print("REPRESENTABLE: the harness reproduces J_2 = 2 from the witness, "
              "so the same-law shortfall is OPTIMIZER FAILURE, not a\n"
              "               parametrization bug. Fix the search, not the "
              "class.")
    else:
        print(f"NOT REPRESENTABLE: worst gap {worst:.3e}. The feasibility "
              f"pipeline distorts the exact extremizer, so no amount of\n"
              f"                   searching can calibrate this class. Fix the "
              f"parametrization first.")


if __name__ == "__main__":
    main()
