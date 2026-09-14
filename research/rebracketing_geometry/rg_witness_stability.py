"""Is the witness a fixed point of the search dynamics, or does the optimizer walk away from it?

DIAGNOSTIC, not calibration. The same-law arm plateaus near `gamma_J = 0.84`
whatever the initialization, the schedule or the step count, which is too flat a
ceiling to read as "not enough search". Two very different causes produce it:

  BASIN NOT FOUND   the witness is a stable maximum of the search dynamics, and
                    generic starts simply never reach its basin
                    -> an initialization / basin-hopping problem

  NOT A FIXED POINT the optimizer, started AT the witness, walks away from it
                    -> the plateau is a property of the optimization setup, not
                       of the landscape, and no amount of restarting fixes it

This file decides between them by starting at the exact witness plus noise of
several scales and running the sweep's own optimizer. `noise = 0` is the sharp
test: if J falls from 2 under a loop that begins exactly at the extremizer, the
dynamics are the problem.

Starting from the witness makes `gamma_J` useless AS A CONTROL -- the search is
being told the answer. Nothing here may be quoted as calibration; it exists
only to say which repair to attempt.
"""

from __future__ import annotations

import argparse
import math
import sys
from pathlib import Path

import torch

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

from rg_fused_search import (  # noqa: E402
    build_laws, evaluate, feasibility_factors, score, share_laws,
)
from rg_harness_selftest import witness_leaves, witness_raw  # noqa: E402
from rg_kernels import DTYPE, coordinate_projectors  # noqa: E402


def run(eta, noise, steps, restarts, refresh, lr, device, seed,
        grade=(64, 40), loop=(3, 20), differentiable=False,
        warm_loop=None):
    """Optimize starting from the witness perturbed by `noise`.

    `loop` is the estimator strength for the first, cold feasibility call;
    `warm_loop` is used for every later step, where the extremizers are warm
    started from the previous one and a handful of iterations suffices.
    """
    warm_loop = warm_loop or (loop[0], 3)
    generator = torch.Generator(device=device).manual_seed(seed)
    base_law = witness_raw(eta, device).expand(restarts, 3, 3, 3, 3)
    base_leaves = witness_leaves(device).expand(restarts, 5, 3)

    law = (base_law + noise * torch.randn(base_law.shape, dtype=DTYPE,
                                          device=device, generator=generator)
           ).clone().requires_grad_(True)
    leaves = (base_leaves + noise * torch.randn(base_leaves.shape, dtype=DTYPE,
                                                device=device,
                                                generator=generator)
              ).clone().requires_grad_(True)

    eta_vec = torch.full((restarts,), eta, dtype=DTYPE, device=device)
    shared = torch.ones(restarts, dtype=torch.bool, device=device)
    rank = torch.full((restarts,), 2, dtype=torch.long, device=device)
    projector = coordinate_projectors(rank, 3, device)
    projectors = (projector, projector, projector)
    coefficients = torch.tensor([[1.0, 0.0, 0.0]], dtype=DTYPE,
                                device=device).expand(restarts, 3)
    raws = dict.fromkeys(("inner_L", "inner_M", "root_L", "root_M"), law)

    def graded():
        with torch.no_grad():
            laws = share_laws(raws, shared)
            factors = feasibility_factors(laws, projectors, *grade)
            A_hat, PA, D, _ = evaluate(laws, projectors, leaves, eta_vec,
                                       factors, shared)
            return float(score(coefficients, A_hat, PA, D, eta_vec).max())

    start = graded()
    optimizer = torch.optim.Adam([law, leaves], lr=lr)
    factors, warm = None, None
    for step in range(steps):
        laws = share_laws(raws, shared)
        # A differentiable factor carries a graph, and a graph cannot be
        # cached across steps: reusing it makes autograd walk a freed graph.
        # Caching is only sound when the factor is a detached constant -- which
        # is precisely the frozen mode that breaks the gradient. So the two
        # design choices are mutually exclusive, and the correct one pays the
        # feasibility cost on every step.
        if differentiable or step % refresh == 0:
            # The factors must be rebuilt every step in differentiable mode --
            # a graph cannot be cached -- but the EXTREMIZERS can be carried
            # over, and under a slowly moving law a warm start converges in a
            # few iterations instead of forty.
            factors, warm = feasibility_factors(
                laws, projectors, *(loop if warm is None else warm_loop),
                differentiable=differentiable, warm=warm, return_warm=True)
        optimizer.zero_grad(set_to_none=True)
        A_hat, PA, D, _ = evaluate(laws, projectors, leaves, eta_vec, factors,
                                   shared)
        values = score(coefficients, A_hat, PA, D, eta_vec)
        (-values.sum()).backward()
        torch.nn.utils.clip_grad_norm_([law, leaves], 10.0)
        optimizer.step()
    return start, graded()


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--etas", type=float, nargs="+", default=[0.3, 1.0])
    parser.add_argument("--noises", type=float, nargs="+",
                        default=[0.0, 1e-3, 1e-2, 0.1, 0.3])
    parser.add_argument("--steps", type=int, default=150)
    parser.add_argument("--restarts", type=int, default=256)
    parser.add_argument("--refresh", type=int, default=6)
    parser.add_argument("--lr", type=float, default=0.05)
    parser.add_argument("--differentiable", action="store_true",
                        help="let the gradient flow through the admissibility "
                             "normalization (envelope theorem) instead of "
                             "treating the scale factors as constants")
    parser.add_argument("--loop-strength", type=int, nargs=2, default=[3, 20],
                        metavar=("RESTARTS", "ITERS"),
                        help="estimator INSIDE the loop. The default is cheap, "
                             "which means the loop ascends an INFLATED "
                             "objective whose maximum is not the true one")
    args = parser.parse_args()

    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    print(f"device={device}  witness D=3 rank(P)=2, J_2 = 2 exactly\n")
    print(f"{'eta':>6} {'noise':>8} {'J at start':>12} {'J after opt':>13} "
          f"{'drift':>10}   verdict")

    walked_away = False
    for eta in args.etas:
        for noise in args.noises:
            start, end = run(eta, noise, args.steps, args.restarts,
                             args.refresh, args.lr, device,
                             seed=int(1000 * eta) + int(1e5 * noise) + 7,
                             loop=tuple(args.loop_strength),
                             differentiable=args.differentiable)
            drift = end - start
            verdict = ("stays" if drift > -1e-6
                       else "WALKS AWAY" if drift < -0.01 else "drifts")
            walked_away |= drift < -0.01
            print(f"{eta:6.2f} {noise:8.4f} {start:12.6f} {end:13.6f} "
                  f"{drift:+10.4f}   {verdict}", flush=True)

    print()
    if walked_away:
        print("NOT A FIXED POINT: the optimizer moves DOWNHILL from the exact")
        print("extremizer. The 0.84 plateau is a property of the optimization")
        print("setup, not of the landscape -- more restarts cannot fix it.")
    else:
        print("BASIN NOT FOUND: the witness is stable under the search, so the")
        print("plateau is a basin-reaching problem -- initialization or")
        print("basin-hopping is the lever, not more steps.")


if __name__ == "__main__":
    main()
