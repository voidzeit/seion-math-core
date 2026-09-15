"""Small deterministic scan for capped-equal-angle discrepancies.

This is a numerical stress test only. A zero discrepancy does not prove the
conjecture; a positive discrepancy is a useful counterexample candidate.
"""

from __future__ import annotations

import argparse
import json
import math

import numpy as np

from .scalar_extremization import capped_equal_angle, heterogeneous_box_max


def scan(seed: int, trials: int, max_n: int, maxiter: int) -> dict:
    rng = np.random.default_rng(seed)
    rows = []
    for n in range(2, max_n + 1):
        for trial in range(trials):
            caps = np.sort(rng.uniform(0.02, math.pi / 2, n)).tolist()
            capped, _ = capped_equal_angle(caps)
            box = heterogeneous_box_max(caps, seed=trial, maxiter=maxiter, popsize=6)
            rows.append({
                "n": n,
                "trial": trial,
                "caps": caps,
                "capped_candidate": capped,
                "box_lower_bound": box.lower_bound,
                "discrepancy": box.lower_bound - capped,
            })
    return {
        "status": "NUMERICAL_OBSERVATION",
        "seed": seed,
        "trials_per_n": trials,
        "max_n": max_n,
        "maxiter": maxiter,
        "positive_discrepancies": sum(row["discrepancy"] > 1e-7 for row in rows),
        "max_discrepancy": max((row["discrepancy"] for row in rows), default=0.0),
        "rows": rows,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--seed", type=int, default=20260914)
    parser.add_argument("--trials", type=int, default=12)
    parser.add_argument("--max-n", type=int, default=6)
    parser.add_argument("--maxiter", type=int, default=80)
    args = parser.parse_args()
    print(json.dumps(scan(args.seed, args.trials, args.max_n, args.maxiter), indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

