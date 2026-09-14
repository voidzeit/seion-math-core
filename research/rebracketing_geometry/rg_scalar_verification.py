"""Independent check of Theorem 5.1's optimization, with no tensors involved.

The GPU search tests the bound on actual multilinear laws, which means it also
depends on the operator-norm estimator used to enforce admissibility -- and
that estimator turned out not to be converged. This file checks a different
thing, and is immune to that: it verifies the *scalar* optimization the proof
reduces to.

By Lemma 2.1 a k=2 rebracketing pair is described by (d, r, u, v; d', r', u',
v'). Scalarizing along psi := Ahat/||Ahat|| with a := <psi,u>, b := <psi,v>,
and PA = 0, everything collapses to:

    maximize    t = r b - r' b'
    subject to  d a + r b = d' a' + r' b'          (PA = 0, scalarized)
                a^2 + b^2 <= 1,  a'^2 + b'^2 <= 1  (Lemma 2.1)
                0 <= d, d' <= eta                   (closure budget)
                r <= sqrt(1 - d^2), r' <= sqrt(1 - d'^2)   (||F_i|| <= M L)

The proof claims this maximum is exactly

    sin(min(2 arcsin eta, pi/2))  =  eta * Sigma_2(eta).

The two expressions for t used in the proof, t = r b - r' b' and
t = d' a' - d a, are *equivalent* given the constraint, so only one appears
here; the proof's interpolation between them with weight
lambda = cos(alpha)cos(alpha')/cos(alpha - alpha') is a proof device, and this
file deliberately does NOT use it. It searches the raw feasible set instead, so
agreement is a genuine check of the analytic optimum rather than a restatement.

Cheap, deterministic in its seeding, and spread over all cores.
"""

from __future__ import annotations

import argparse
import json
import math
import os
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent


def sigma2(eta: float) -> float:
    return math.sin(min(2.0 * math.asin(min(eta, 1.0)), 0.5 * math.pi)) / eta


def best_for_cell(job) -> dict:
    """Maximize t over the feasible set at one eta, by sampling + refinement.

    For fixed (d, d') the feasible (a,b,a',b') set is two unit discs cut by one
    linear equation, so sampling the discs and keeping only near-feasible
    points would waste almost every sample. Instead b' is SOLVED from the
    constraint once (a, b, a') are drawn, and the sample is kept when the
    resulting (a', b') lands inside its disc.
    """
    seed, eta, samples, grid = job
    rng = np.random.default_rng(seed)

    best = 0.0
    best_state = None
    for d in np.linspace(0.0, eta, grid):
        for d_prime in np.linspace(0.0, eta, grid):
            r = math.sqrt(max(0.0, 1.0 - d * d))
            r_prime = math.sqrt(max(0.0, 1.0 - d_prime * d_prime))
            if r_prime < 1e-12:
                continue
            angle = rng.uniform(0.0, 2.0 * math.pi, samples)
            radius = np.sqrt(rng.uniform(0.0, 1.0, samples))
            a, b = radius * np.cos(angle), radius * np.sin(angle)
            a_prime = rng.uniform(-1.0, 1.0, samples)
            # b' from the constraint  d a + r b = d' a' + r' b'
            b_prime = (d * a + r * b - d_prime * a_prime) / r_prime
            inside = a_prime**2 + b_prime**2 <= 1.0 + 1e-15
            if not inside.any():
                continue
            t = r * b[inside] - r_prime * b_prime[inside]
            index = int(np.argmax(t))
            if t[index] > best:
                best = float(t[index])
                best_state = {"d": float(d), "d_prime": float(d_prime),
                              "r": r, "r_prime": r_prime,
                              "a": float(a[inside][index]),
                              "b": float(b[inside][index]),
                              "a_prime": float(a_prime[inside][index]),
                              "b_prime": float(b_prime[inside][index])}
    predicted = math.sin(min(2.0 * math.asin(min(eta, 1.0)), 0.5 * math.pi))
    return {"eta": eta, "found": best, "predicted": predicted,
            "ratio": best / predicted if predicted > 0 else float("nan"),
            "state": best_state}


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--etas", type=float, nargs="+",
                        default=[0.05, 0.1, 0.2, 0.3, 0.45, 0.6,
                                 1 / math.sqrt(2), 0.8, 0.9, 0.95, 1.0])
    parser.add_argument("--samples", type=int, default=200_000)
    parser.add_argument("--grid", type=int, default=61)
    parser.add_argument("--workers", type=int, default=0)
    parser.add_argument("--json", type=str,
                        default="rg_scalar_verification.json")
    args = parser.parse_args()

    workers = args.workers or os.cpu_count() or 1
    jobs = [(4242 + index, eta, args.samples, args.grid)
            for index, eta in enumerate(args.etas)]
    print(f"scalar optimum vs Theorem 5.1, {len(jobs)} etas, "
          f"{args.grid}x{args.grid} (d,d') grid x {args.samples:,} samples, "
          f"{workers} cores\n")

    with ProcessPoolExecutor(max_workers=workers) as pool:
        results = list(pool.map(best_for_cell, jobs, chunksize=1))

    print(f"{'eta':>7} {'found':>12} {'sin(min(2asin,pi/2))':>22} "
          f"{'found/predicted':>17} {'d*':>7} {'dp*':>7}")
    worst_over = 0.0
    for row in sorted(results, key=lambda r: r["eta"]):
        state = row["state"] or {}
        worst_over = max(worst_over, row["found"] - row["predicted"])
        print(f"{row['eta']:7.4f} {row['found']:12.8f} "
              f"{row['predicted']:22.8f} {row['ratio']:17.6f} "
              f"{state.get('d', float('nan')):7.4f} "
              f"{state.get('d_prime', float('nan')):7.4f}")

    (HERE / args.json).write_text(json.dumps(results, indent=2),
                                  encoding="utf-8")
    print(f"\n  largest amount by which sampling EXCEEDED the proved optimum: "
          f"{worst_over:+.3e}")
    print("  (a positive value beyond sampling tolerance would refute the "
          "optimization step of Theorem 5.1;\n   a value slightly below is "
          "expected -- random sampling approaches an optimum from within.)")


if __name__ == "__main__":
    main()
