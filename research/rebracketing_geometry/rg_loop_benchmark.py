"""What does a mathematically correct search loop actually cost?

The first loop cached the feasibility factors across `refresh` steps. That is
only sound when the factor is a detached constant -- which is exactly the frozen
mode whose backward differentiates the wrong function. A differentiable factor
carries a graph, and a graph cannot be cached, so the correct loop must rebuild
it every step. The question this file answers is what that costs, and how much
of it warm-starting the extremizers gives back.

The reusable object is NOT the norm, the scale factor, or its graph. It is the
maximizing direction `v*`, a detached numerical state. So the architecture is

    cache numerical optimizer state;  rebuild differentiable quantities.

with one guard: local refinement only tracks the maximizer it started on, so a
fraction of the restarts is always re-drawn cold. Measured on this repository, a
warm start with no cold fraction underestimates by 24% after an abrupt change of
the dominant maximizer -- which is the same underestimate-the-norm failure that
made a law inadmissible and inflated its value in the first place.

Four configurations, same work otherwise:

    frozen/cached        what the committed sweep did: wrong backward, cheap
    frozen/every-step    isolates the cost of dropping the cache alone
    diff/every-step      correct backward, full feasibility every step
    diff/warm            correct backward, warm-started extremizers
"""

from __future__ import annotations

import argparse
import sys
import time
from pathlib import Path

import torch

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

from rg_fused_search import (  # noqa: E402
    evaluate, feasibility_factors, score, share_laws,
)
from rg_kernels import DTYPE, coordinate_projectors  # noqa: E402


def timed_loop(dim, rank, eta, batch, steps, strength, device, seed,
               differentiable, cache_every, warm_iters, global_refresh=25):
    generator = torch.Generator(device=device).manual_seed(seed)
    law = torch.randn(batch, dim, dim, dim, dim, dtype=DTYPE, device=device,
                      generator=generator).requires_grad_(True)
    leaves = torch.randn(batch, 5, dim, dtype=DTYPE, device=device,
                         generator=generator).requires_grad_(True)
    ranks = torch.full((batch,), rank, dtype=torch.long, device=device)
    projector = coordinate_projectors(ranks, dim, device)
    projectors = (projector, projector, projector)
    eta_vec = torch.full((batch,), eta, dtype=DTYPE, device=device)
    shared = torch.ones(batch, dtype=torch.bool, device=device)
    coefficients = torch.tensor([[1.0, 0.0, 0.0]], dtype=DTYPE,
                                device=device).expand(batch, 3)
    raws = dict.fromkeys(("inner_L", "inner_M", "root_L", "root_M"), law)
    optimizer = torch.optim.Adam([law, leaves], lr=0.05)

    if device.type == "cuda":
        torch.cuda.empty_cache()
        torch.cuda.reset_peak_memory_stats()
        torch.cuda.synchronize()
    started = time.time()

    factors, warm = None, None
    for step in range(steps):
        laws = share_laws(raws, shared)
        rebuild = differentiable or step % cache_every == 0
        if rebuild:
            # periodic global refresh: a long run of purely local refinements
            # accumulates drift that neither warm nor the cold fraction sees
            full = warm is None or (global_refresh and
                                    step % global_refresh == 0)
            current = strength if (full or not warm_iters) else (strength[0],
                                                                 warm_iters)
            result = feasibility_factors(
                laws, projectors, *current, differentiable=differentiable,
                warm=(warm if warm_iters and not full else None),
                return_warm=bool(warm_iters))
            factors, warm = result if warm_iters else (result, None)
        optimizer.zero_grad(set_to_none=True)
        A_hat, PA, D, _ = evaluate(laws, projectors, leaves, eta_vec, factors,
                                   shared)
        (-score(coefficients, A_hat, PA, D, eta_vec).sum()).backward()
        torch.nn.utils.clip_grad_norm_([law, leaves], 10.0)
        optimizer.step()

    if device.type == "cuda":
        torch.cuda.synchronize()
    elapsed = time.time() - started
    peak = (torch.cuda.max_memory_allocated() / 1e9
            if device.type == "cuda" else 0.0)

    # grade the endpoint honestly, so cost is compared at equal meaning
    with torch.no_grad():
        laws = share_laws(raws, shared)
        graded = feasibility_factors(laws, projectors, 64, 40)
        A_hat, PA, D, _ = evaluate(laws, projectors, leaves, eta_vec, graded,
                                   shared)
        value = float(score(coefficients, A_hat, PA, D, eta_vec).max())
    return elapsed, peak, value


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dim", type=int, default=3)
    parser.add_argument("--rank", type=int, default=2)
    parser.add_argument("--eta", type=float, default=0.3)
    parser.add_argument("--batch", type=int, default=1024)
    parser.add_argument("--steps", type=int, default=100)
    parser.add_argument("--strength", type=int, nargs=2, default=[32, 40])
    parser.add_argument("--warm-iters", type=int, default=3)
    parser.add_argument("--cache-every", type=int, default=6)
    args = parser.parse_args()

    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    print(f"device={device} D={args.dim} batch={args.batch} "
          f"steps={args.steps} strength={tuple(args.strength)}\n")
    print(f"{'configuration':>22} {'backward':>14} {'s/step':>9} "
          f"{'peak GB':>9} {'J graded':>10} {'vs cached':>10}")

    configurations = [
        ("frozen / cached", False, args.cache_every, 0),
        ("frozen / every step", False, 1, 0),
        ("diff / every step", True, 1, 0),
        ("diff / warm", True, 1, args.warm_iters),
    ]
    baseline = None
    for label, differentiable, cache_every, warm_iters in configurations:
        elapsed, peak, value = timed_loop(
            args.dim, args.rank, args.eta, args.batch, args.steps,
            tuple(args.strength), device, 4242, differentiable, cache_every,
            warm_iters)
        per_step = elapsed / args.steps
        baseline = baseline or per_step
        print(f"{label:>22} {'WRONG' if not differentiable else 'correct':>14} "
              f"{per_step:9.4f} {peak:9.2f} {value:10.6f} "
              f"{per_step / baseline:9.2f}x")

    print("\nThe first row is what the committed sweep ran: cheap, and")
    print("differentiating a function the forward does not evaluate. The last")
    print("row is the correct loop with the extremizers warm started.")


if __name__ == "__main__":
    main()
