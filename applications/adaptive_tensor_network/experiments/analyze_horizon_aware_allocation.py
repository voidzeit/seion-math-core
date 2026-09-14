"""M35b analysis: policy benchmark against a true terminal reference at m = 8,
and within-m comparisons at larger m.

Terminology is enforced here:
  E_terminal_star   the exact finite-horizon optimum over all admissible
                    terminal profiles. Exists only at m = 8 in this campaign.
  step_greedy       the one-step greedy policy. NOT an oracle. M35 showed it is
                    not a terminal lower bound.
  pool optimum      the best candidate in a sampled pool at a single state.

Cross-m comparisons of raw error are not produced: deeper chains carry larger
absolute truncation error, so only within-m differences are meaningful.
"""

from __future__ import annotations

import csv
import json
import statistics
import sys
from collections import defaultdict
from pathlib import Path

import numpy as np

SRC = Path(__file__).resolve().parents[1] / "src"
sys.path.insert(0, str(SRC))

from metrics import bootstrap_ci  # noqa: E402

RESULTS_DIR = Path(__file__).resolve().parents[1] / "results"
POLICIES = ("uniform", "local_greedy", "measured_first_order",
            "full_pairwise", "lowrank_pairwise_q4", "step_greedy")


def load(name: str):
    path = RESULTS_DIR / name
    return json.loads(path.read_text(encoding="utf-8")) if path.exists() else None


def main() -> None:
    report = {}
    oracle = load("terminal_oracle_m8_raw.json")
    rows_csv = []

    for source in ("policy_scaling_m8.json", "policy_scaling_raw.json"):
        payload = load(source)
        if not payload:
            continue
        by_m = defaultdict(list)
        for run in payload["runs"]:
            by_m[run["m"]].append(run)

        for m, runs in sorted(by_m.items()):
            seeds = sorted({r["seed"] for r in runs})
            has_oracle = (m == 8 and oracle is not None)
            print(f"\n=== m = {m}  ({len(seeds)} seeds)"
                  + ("  — TRUE terminal optimum available" if has_oracle else
                     "  — no terminal oracle; within-m comparisons only") + " ===")

            header = (f"{'policy':>22} {'terminal/E0':>12} {'CI95':>20} "
                      f"{'evals':>8}")
            if has_oracle:
                header += f" {'true regret':>12} {'profile rank':>13} {'pctile':>8}"
            print(header)

            per_policy = {}
            for policy in POLICIES:
                selected = [r for r in runs if r["policy"] == policy]
                if not selected:
                    continue
                normalized = [r["terminal_error"] / r["base_error"] for r in selected]
                mean, lo, hi = bootstrap_ci(normalized)
                entry = {
                    "n": len(selected),
                    "terminal_over_E0_mean": mean,
                    "ci95": [lo, hi],
                    "median": statistics.median(normalized),
                    "evaluations": statistics.fmean([r["evaluations"] for r in selected]),
                    "wall_seconds": statistics.fmean([r["wall_seconds"] for r in selected]),
                }
                line = (f"{policy:>22} {mean:12.5f} [{lo:7.5f},{hi:7.5f}] "
                        f"{entry['evaluations']:8.0f}")

                if has_oracle:
                    regrets, ranks, pcts = [], [], []
                    for run in selected:
                        info = oracle["seeds"].get(str(run["seed"]))
                        if not info or not info.get("path_independent"):
                            continue
                        values_path = (RESULTS_DIR /
                                       f"terminal_oracle_m8_values_seed{run['seed']}.npy")
                        if not values_path.exists():
                            continue
                        values = np.load(values_path)
                        star = info["E_terminal_star"]
                        regrets.append(run["terminal_error"] - star)
                        rank = int(np.sum(values < run["terminal_error"] - 1e-12))
                        ranks.append(rank)
                        pcts.append(100.0 * rank / len(values))
                    if regrets:
                        entry.update({
                            "true_terminal_regret_mean": statistics.fmean(regrets),
                            "profile_rank_mean": statistics.fmean(ranks),
                            "profile_percentile_mean": statistics.fmean(pcts),
                            "n_oracle_matched": len(regrets),
                        })
                        # n is printed because the oracle covers fewer seeds
                        # than the policy runs while enumeration is in progress;
                        # averaging silently over a different n than the
                        # terminal/E0 column would misrepresent both.
                        line += (f" {statistics.fmean(regrets):12.6f} "
                                 f"{statistics.fmean(ranks):13.0f} "
                                 f"{statistics.fmean(pcts):7.3f}% "
                                 f"n={len(regrets)}")
                print(line)
                per_policy[policy] = entry
                rows_csv.append({
                    "m": m, "policy": policy,
                    "terminal_over_E0": mean, "ci_lo": lo, "ci_hi": hi,
                    "evaluations": entry["evaluations"],
                    "true_terminal_regret": entry.get("true_terminal_regret_mean", ""),
                    "profile_rank": entry.get("profile_rank_mean", ""),
                    "profile_percentile": entry.get("profile_percentile_mean", ""),
                })

            print(f"\n  seed-matched differences (positive = row better than "
                  f"measured_first_order):")
            reference = {r["seed"]: r["terminal_error"] / r["base_error"]
                         for r in runs if r["policy"] == "measured_first_order"}
            for policy in POLICIES:
                if policy == "measured_first_order":
                    continue
                paired = [(reference[r["seed"]] - r["terminal_error"] / r["base_error"])
                          for r in runs if r["policy"] == policy and r["seed"] in reference]
                if not paired:
                    continue
                mean, lo, hi = bootstrap_ci(paired)
                wins = sum(1 for d in paired if d > 1e-12)
                losses = sum(1 for d in paired if d < -1e-12)
                mark = "+" if lo > 0 else ("-" if hi < 0 else "0")
                print(f"    {policy:>22}: {mean:+.5f} [{lo:+.5f},{hi:+.5f}] {mark}  "
                      f"W/T/L = {wins}/{len(paired)-wins-losses}/{losses}")
                per_policy.setdefault(policy, {})["vs_first_order"] = {
                    "mean": mean, "ci95": [lo, hi],
                    "wins": wins, "losses": losses, "n": len(paired),
                }

            report[f"m{m}"] = per_policy

    if oracle:
        print("\n=== terminal optimum landscape at m = 8 ===")
        for seed, info in sorted(oracle["seeds"].items()):
            if not info.get("path_independent"):
                print(f"  seed {seed}: PATH DEPENDENCE FAILED — enumeration invalid")
                continue
            q = info["value_quantiles"]
            print(f"  seed {seed}: E* = {info['E_terminal_star']:.6f}, ties = "
                  f"{info['n_tied_optima']}, base = {info['base_error']:.6f}, "
                  f"median = {q['50']:.6f}, worst = {q['100']:.6f}, "
                  f"path spread = {info['path_spread']:.1e}")

    (RESULTS_DIR / "m35b_analysis.json").write_text(
        json.dumps(report, indent=2), encoding="utf-8")
    if rows_csv:
        with (RESULTS_DIR / "m35b_policy_table.csv").open("w", newline="",
                                                          encoding="utf-8") as handle:
            writer = csv.DictWriter(handle, fieldnames=list(rows_csv[0]))
            writer.writeheader()
            writer.writerows(rows_csv)
    print("\nWrote results/m35b_analysis.json and results/m35b_policy_table.csv")


if __name__ == "__main__":
    main()
