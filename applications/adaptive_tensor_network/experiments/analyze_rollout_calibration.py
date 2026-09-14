"""Analysis for M35c: rollout against the true terminal optimum at m = 8.

Reports, per base policy and lookahead depth h:

    R_T   = E_T - E_terminal_star          true terminal regret
    Gamma = R_T^rollout / R_T^base         both regrets share the same valid
                                           reference, so the ratio is well posed
    profile rank / percentile among all 235,348 admissible terminal profiles

Also computes A_action, the per-step action-agreement rate between policy
pairs, which M35b flagged as missing: identical terminal profiles do not imply
identical action sequences when E is path-independent.
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


def main() -> None:
    payload = json.loads((RESULTS_DIR / "rollout_calibration_raw.json").read_text(encoding="utf-8"))
    oracle = json.loads((RESULTS_DIR / "terminal_oracle_m8_raw.json").read_text(encoding="utf-8"))

    values_cache = {}

    def landscape(seed):
        if seed not in values_cache:
            path = RESULTS_DIR / f"terminal_oracle_m8_values_seed{seed}.npy"
            values_cache[seed] = np.load(path) if path.exists() else None
        return values_cache[seed]

    def star(seed):
        info = oracle["seeds"].get(str(seed))
        return info["E_terminal_star"] if info and info.get("path_independent") else None

    runs = payload["runs"]
    base_regret = {}
    for run in runs:
        if run["lookahead"] == 0:
            reference = star(run["seed"])
            if reference is not None:
                base_regret[(run["seed"], run["base_policy"])] = \
                    run["terminal_error"] - reference

    grouped = defaultdict(list)
    for run in runs:
        grouped[(run["base_policy"], run["lookahead"])].append(run)

    rows = []
    print("=== M35c: rollout at m = 8 against the exact terminal optimum ===")
    print("h = 0 is the base policy itself; h = 1 is exhaustive step-greedy "
          "over all 56 bundles\n")
    print(f"{'base policy':>22} {'h':>3} {'E_T':>10} {'true regret':>12} "
          f"{'G_ratmean':>8} {'G_meanrat':>8} {'paired CI95':>16} "
          f"{'rank':>8} {'pctile':>8} {'evals':>8}")
    for (policy, lookahead) in sorted(grouped, key=lambda k: (k[0], k[1])):
        selected = grouped[(policy, lookahead)]
        regrets, gammas, ranks, pcts = [], [], [], []
        for run in selected:
            reference = star(run["seed"])
            if reference is None:
                continue
            regret = run["terminal_error"] - reference
            regrets.append(regret)
            denominator = base_regret.get((run["seed"], run["base_policy"]))
            if denominator and denominator > 1e-12:
                gammas.append(regret / denominator)
            values = landscape(run["seed"])
            if values is not None:
                rank = int(np.sum(values < run["terminal_error"] - 1e-12))
                ranks.append(rank)
                pcts.append(100.0 * rank / len(values))
        if not regrets:
            continue
        # Two distinct estimands, both reported because mean(X)/mean(Y) is not
        # mean(X/Y) and quoting one as if it were the other invites suspicion.
        denominators = [base_regret.get((r["seed"], r["base_policy"]))
                        for r in selected]
        denominators = [d for d in denominators if d and d > 1e-12]
        gamma_ratio_of_means = (statistics.fmean(regrets) / statistics.fmean(denominators)
                                if denominators else float("nan"))
        gamma_mean_of_ratios = statistics.fmean(gammas) if gammas else float("nan")
        if gammas:
            _, g_lo, g_hi = bootstrap_ci(gammas)
        else:
            g_lo = g_hi = float("nan")
        entry = {
            "base_policy": policy, "lookahead": lookahead, "n": len(regrets),
            "E_T": statistics.fmean([r["terminal_error"] for r in selected]),
            "true_regret": statistics.fmean(regrets),
            "gamma_ratio_of_means": gamma_ratio_of_means,
            "gamma_mean_of_paired_ratios": gamma_mean_of_ratios,
            "gamma_paired_ci95": [g_lo, g_hi],
            "rank": statistics.fmean(ranks) if ranks else float("nan"),
            "percentile": statistics.fmean(pcts) if pcts else float("nan"),
            "evaluations": statistics.fmean([r["evaluations"] for r in selected]),
        }
        rows.append(entry)
        print(f"{policy:>22} {lookahead:3d} {entry['E_T']:10.5f} "
              f"{entry['true_regret']:12.6f} {gamma_ratio_of_means:8.4f} "
              f"{gamma_mean_of_ratios:8.4f} [{g_lo:6.3f},{g_hi:6.3f}] "
              f"{entry['rank']:8.0f} {entry['percentile']:7.3f}% "
              f"{entry['evaluations']:8.0f}")

    # Seed-matched: does full lookahead beat h=1 (step-greedy)?
    print("\n  seed-matched true regret, h=1 minus h (positive = lookahead helps):")
    for policy in sorted({r["base_policy"] for r in runs if r["lookahead"] > 0}):
        one = {r["seed"]: r["terminal_error"] for r in runs
               if r["base_policy"] == policy and r["lookahead"] == 1}
        for lookahead in sorted({r["lookahead"] for r in runs if r["lookahead"] > 1}):
            paired = [one[r["seed"]] - r["terminal_error"] for r in runs
                      if r["base_policy"] == policy and r["lookahead"] == lookahead
                      and r["seed"] in one]
            if not paired:
                continue
            mean, lo, hi = bootstrap_ci(paired)
            mark = "+" if lo > 0 else ("-" if hi < 0 else "0")
            print(f"    {policy:>22} h={lookahead}: {mean:+.6f} "
                  f"[{lo:+.6f},{hi:+.6f}] {mark}")

    # A_action between policy pairs sharing seeds
    print("\n  A_action (per-step action agreement) between rollout depths:")
    by_seed = defaultdict(dict)
    for run in runs:
        by_seed[run["seed"]][(run["base_policy"], run["lookahead"])] = run["actions"]
    for policy in sorted({r["base_policy"] for r in runs}):
        for lookahead in sorted({r["lookahead"] for r in runs if r["lookahead"] > 1}):
            scores = []
            for seed, entries in by_seed.items():
                a = entries.get((policy, 1))
                b = entries.get((policy, lookahead))
                if a and b and len(a) == len(b):
                    scores.append(statistics.fmean(
                        [1.0 if sorted(x) == sorted(y) else 0.0 for x, y in zip(a, b)]))
            if scores:
                print(f"    {policy:>22} h=1 vs h={lookahead}: "
                      f"{statistics.fmean(scores):.3f}")

    with (RESULTS_DIR / "m35c_rollout_table.csv").open("w", newline="",
                                                       encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)
    (RESULTS_DIR / "m35c_analysis.json").write_text(
        json.dumps(rows, indent=2), encoding="utf-8")
    print("\nWrote results/m35c_analysis.json and results/m35c_rollout_table.csv")


if __name__ == "__main__":
    main()
