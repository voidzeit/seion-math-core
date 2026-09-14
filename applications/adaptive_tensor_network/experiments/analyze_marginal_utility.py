"""Analysis for M27, computed entirely from results/marginal_utility_raw.json.

Reuses Level 1's `metrics.spearman_corr` and `metrics.bootstrap_ci` so the
numbers are comparable to the rest of the campaign.

For each config and each candidate score, four quantities against the measured
marginal utility U_v:

  rho    Spearman rank correlation -- what an allocator actually needs, since
         it ranks nodes rather than calibrating magnitudes
  top1   did argmax(score) pick the node with the largest true utility
  top3   overlap of the two top-3 sets, as a fraction
  regret (U_max - U_at_argmax_score) / |U_max|, normalized so depths with very
         different error scales are comparable; reported only where U_max > 0
"""

from __future__ import annotations

import json
import statistics
import sys
from collections import defaultdict
from pathlib import Path

SRC = Path(__file__).resolve().parents[1] / "src"
sys.path.insert(0, str(SRC))

from metrics import bootstrap_ci, spearman_corr  # noqa: E402

RESULTS_DIR = Path(__file__).resolve().parents[1] / "results"
SCORES = ["score_local", "score_path", "score_m24", "score_m25"]
LABELS = {"score_local": "eps_v (local)", "score_path": "w_v*eps_v (path)",
          "score_m24": "M24 marginal", "score_m25": "M25 marginal"}


def evaluate(record: dict, score_key: str) -> dict:
    nodes = record["eligible"]
    utility = [record["utility"][n] for n in nodes]
    score = [record[score_key][n] for n in nodes]

    order_u = sorted(range(len(nodes)), key=lambda i: -utility[i])
    order_s = sorted(range(len(nodes)), key=lambda i: -score[i])
    best_u = order_u[0]
    picked = order_s[0]
    k = min(3, len(nodes))
    overlap = len(set(order_u[:k]) & set(order_s[:k])) / k

    u_max = utility[best_u]
    regret = None
    if u_max > 0:
        regret = (u_max - utility[picked]) / abs(u_max)

    return {
        "rho": spearman_corr(score, utility),
        "top1": 1.0 if picked == best_u else 0.0,
        "top3": overlap,
        "regret": regret,
    }


def main() -> None:
    records = json.loads((RESULTS_DIR / "marginal_utility_raw.json").read_text(encoding="utf-8"))
    print(f"Loaded {len(records)} raw records.\n")

    grouped: dict = defaultdict(lambda: defaultdict(lambda: defaultdict(list)))
    for record in records:
        key = (record["regime"], record["depth"])
        for score_key in SCORES:
            result = evaluate(record, score_key)
            for metric, value in result.items():
                if value is not None:
                    grouped[key][score_key][metric].append(value)

    report: dict = {}
    for (regime, depth), per_score in sorted(grouped.items()):
        entry = {}
        for score_key, metrics in per_score.items():
            rho_mean, rho_lo, rho_hi = bootstrap_ci(metrics["rho"])
            entry[score_key] = {
                "n_configs": len(metrics["rho"]),
                "spearman_mean": rho_mean,
                "spearman_ci_95": [rho_lo, rho_hi],
                "top1_accuracy": statistics.fmean(metrics["top1"]),
                "top3_overlap": statistics.fmean(metrics["top3"]),
                "normalized_regret_mean": (
                    statistics.fmean(metrics["regret"]) if metrics["regret"] else None
                ),
                "n_regret": len(metrics["regret"]),
            }
        report[f"{regime}_k{depth}"] = entry

    (RESULTS_DIR / "marginal_utility_analysis.json").write_text(
        json.dumps(report, indent=2), encoding="utf-8"
    )

    # Fraction of measured utilities that are negative: adding rank to a node
    # can increase root error, which bounds how well any nonnegative score can
    # rank them.
    all_u = [v for r in records for v in r["utility"].values()]
    negative = sum(1 for v in all_u if v < 0)
    print(f"measured marginal utilities: {len(all_u)}, "
          f"negative: {negative} ({100 * negative / len(all_u):.1f}%)\n")

    for regime in ("iid", "heterogeneous"):
        print(f"=== regime: {regime} ===")
        print(f"{'k':>4} {'score':>18} {'Spearman rho':>24} {'top1':>7} {'top3':>7} {'regret':>8}")
        for depth in sorted({d for (rg, d) in grouped if rg == regime}):
            for score_key in SCORES:
                e = report[f"{regime}_k{depth}"][score_key]
                lo, hi = e["spearman_ci_95"]
                reg = e["normalized_regret_mean"]
                print(f"{depth:4d} {LABELS[score_key]:>18} "
                      f"{e['spearman_mean']:+.3f} [{lo:+.3f},{hi:+.3f}]".ljust(56)
                      + f"{e['top1_accuracy']:7.2f} {e['top3_overlap']:7.2f} "
                      + (f"{reg:8.3f}" if reg is not None else "     n/a"))
            print()

    print("Wrote analysis to results/marginal_utility_analysis.json")


if __name__ == "__main__":
    main()
