"""Analysis for M33, computed entirely from results/coupled_allocator_raw.json.

Reports the true root error after every round for each method, plus the
acquisition cost in forward evaluations, since the coupled methods pay O(m^2)
per round to build I and that is the obstacle to scaling.

The target pattern from M32A would be

    E_lowrank ~= E_full_pairwise < E_first_order < E_heuristics

with the oracle below all of them. Errors are normalized per configuration by
the starting error so trajectories from different instances can be averaged.
"""

from __future__ import annotations

import json
import statistics
import sys
from collections import defaultdict
from pathlib import Path

SRC = Path(__file__).resolve().parents[1] / "src"
sys.path.insert(0, str(SRC))

from metrics import bootstrap_ci  # noqa: E402

RESULTS_DIR = Path(__file__).resolve().parents[1] / "results"
METHODS = ("uniform", "local_greedy", "pathwise", "first_order",
           "full_pairwise", "lowrank_pairwise", "oracle")


def main() -> None:
    records = json.loads((RESULTS_DIR / "coupled_allocator_raw.json").read_text(encoding="utf-8"))
    print(f"Loaded {len(records)} configurations.\n")

    for regime in ("iid", "heterogeneous"):
        rows = [r for r in records if r["regime"] == regime]
        if not rows:
            continue
        rounds = min(len(r["methods"]["uniform"]["trajectory"]) for r in rows)
        print(f"=== regime: {regime} — true root error by round "
              f"(normalized to each instance's round-0 uniform value) ===")
        print(f"{'method':>18} " + " ".join(f"{'r' + str(t + 1):>8}" for t in range(rounds))
              + f" {'evals':>8}")
        finals = {}
        for method in METHODS:
            normalized = []
            for record in rows:
                reference = record["methods"]["uniform"]["trajectory"][0]
                if reference <= 0:
                    continue
                normalized.append([v / reference
                                   for v in record["methods"][method]["trajectory"][:rounds]])
            column = [statistics.fmean([n[t] for n in normalized]) for t in range(rounds)]
            evaluations = statistics.fmean(
                [record["methods"][method]["evaluations"][rounds - 1] for record in rows])
            finals[method] = [n[rounds - 1] for n in normalized]
            print(f"{method:>18} " + " ".join(f"{v:8.4f}" for v in column)
                  + f" {evaluations:8.0f}")

        print(f"\n  paired comparisons on the final round (positive = row is better):")
        base = finals["local_greedy"]
        for method in ("first_order", "full_pairwise", "lowrank_pairwise", "oracle"):
            diffs = [b - a for a, b in zip(finals[method], base)]
            mean, lo, hi = bootstrap_ci(diffs)
            mark = "+" if lo > 0 else ("-" if hi < 0 else "0")
            print(f"    {method:>18} vs local_greedy: {mean:+.4f} "
                  f"[{lo:+.4f}, {hi:+.4f}] {mark}")
        diffs = [b - a for a, b in zip(finals["lowrank_pairwise"], finals["full_pairwise"])]
        mean, lo, hi = bootstrap_ci(diffs)
        print(f"    {'lowrank vs full':>18}: {mean:+.4f} [{lo:+.4f}, {hi:+.4f}]")
        print()


if __name__ == "__main__":
    main()
