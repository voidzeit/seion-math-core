"""M38A: does the M35c lookahead result survive at m = 10?

EXPERIMENTAL.

M35c found, at m = 8 against the exact terminal optimum, that exhaustive
one-step optimization is significantly WORSE than the base policy it replaces
(Gamma = 1.69, paired CI [1.05, 2.87]) while full-horizon rollout closes ~90%
of the regret. That was five exact landscapes at one problem size. M38-0
produced an exact optimum at m = 10 -- 3,039,400 terminal profiles, unique
optimum in all five seeds -- so the claim can now be tested at a second size
with the same kind of reference rather than a proxy.

Both Gamma estimands are reported, as in the audited M35c analysis:
ratio-of-means and mean-of-paired-ratios with a paired bootstrap CI. They
answer different questions and quoting one as the other invites suspicion.
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


def oracle_for(m: int) -> tuple[dict, dict]:
    """Return {seed: E*} and {seed: values array path} for a problem size."""
    if m == 8:
        payload = json.loads((RESULTS_DIR / "terminal_oracle_m8_raw.json")
                             .read_text(encoding="utf-8"))
        stars = {int(s): e["E_terminal_star"] for s, e in payload["seeds"].items()
                 if e.get("path_independent")}
        paths = {s: RESULTS_DIR / f"terminal_oracle_m8_values_seed{s}.npy" for s in stars}
    else:
        payload = json.loads((RESULTS_DIR / f"terminal_oracle_m{m}_parallel_raw.json")
                             .read_text(encoding="utf-8"))
        stars = {int(s): e["E_terminal_star"] for s, e in payload["seeds"].items()}
        paths = {s: RESULTS_DIR / f"terminal_oracle_m{m}_parallel_values_seed{s}.npy"
                 for s in stars}
    return stars, paths


def summarize(m: int) -> list[dict]:
    path = RESULTS_DIR / f"rollout_calibration_m{m}_raw.json"
    if not path.exists():
        return []
    runs = json.loads(path.read_text(encoding="utf-8"))["runs"]
    stars, value_paths = oracle_for(m)

    base_regret = {}
    for run in runs:
        if run["lookahead"] == 0 and run["seed"] in stars:
            base_regret[(run["seed"], run["base_policy"])] = \
                run["terminal_error"] - stars[run["seed"]]

    cache: dict[int, np.ndarray] = {}

    def landscape(seed: int):
        if seed not in cache and value_paths[seed].exists():
            cache[seed] = np.load(value_paths[seed])
        return cache.get(seed)

    grouped = defaultdict(list)
    for run in runs:
        grouped[(run["base_policy"], run["lookahead"])].append(run)

    rows = []
    for key in sorted(grouped, key=lambda k: (k[0], k[1])):
        policy, lookahead = key
        selected = [r for r in grouped[key] if r["seed"] in stars]
        if not selected:
            continue
        regrets, gammas, ranks, pcts = [], [], [], []
        for run in selected:
            regret = run["terminal_error"] - stars[run["seed"]]
            regrets.append(regret)
            denominator = base_regret.get((run["seed"], run["base_policy"]))
            if denominator and denominator > 1e-12:
                gammas.append(regret / denominator)
            values = landscape(run["seed"])
            if values is not None:
                rank = int(np.sum(values < run["terminal_error"] - 1e-12))
                ranks.append(rank)
                pcts.append(100.0 * rank / len(values))
        denominators = [base_regret.get((r["seed"], r["base_policy"])) for r in selected]
        denominators = [d for d in denominators if d and d > 1e-12]
        g_lo = g_hi = float("nan")
        if gammas:
            _, g_lo, g_hi = bootstrap_ci(gammas)
        rows.append({
            "m": m, "base_policy": policy, "lookahead": lookahead, "n": len(regrets),
            "E_T": statistics.fmean([r["terminal_error"] for r in selected]),
            "true_regret": statistics.fmean(regrets),
            "gamma_ratio_of_means": (statistics.fmean(regrets) / statistics.fmean(denominators)
                                     if denominators else float("nan")),
            "gamma_mean_of_ratios": statistics.fmean(gammas) if gammas else float("nan"),
            "gamma_ci_lo": g_lo, "gamma_ci_hi": g_hi,
            "profile_rank": statistics.fmean(ranks) if ranks else float("nan"),
            "percentile": statistics.fmean(pcts) if pcts else float("nan"),
            "evaluations": statistics.fmean([r["evaluations"] for r in selected]),
        })
    return rows


def main() -> None:
    rows = []
    for m in (8, 10):
        rows.extend(summarize(m))
    if not rows:
        print("no rollout data found")
        return

    print("=== M38A: rollout against the exact terminal optimum, m = 8 vs m = 10 ===")
    print("h = 0 is the base policy alone; h = 1 is exhaustive step-greedy\n")
    print(f"{'m':>3} {'base policy':>22} {'h':>3} {'true regret':>12} "
          f"{'G_rm':>7} {'G_mr':>7} {'paired CI95':>17} {'rank':>10} {'pctile':>8} {'evals':>8}")
    for row in rows:
        print(f"{row['m']:3d} {row['base_policy']:>22} {row['lookahead']:3d} "
              f"{row['true_regret']:12.6f} {row['gamma_ratio_of_means']:7.4f} "
              f"{row['gamma_mean_of_ratios']:7.4f} "
              f"[{row['gamma_ci_lo']:6.3f},{row['gamma_ci_hi']:6.3f}] "
              f"{row['profile_rank']:10.0f} {row['percentile']:7.4f}% "
              f"{row['evaluations']:8.0f}")

    print("\n=== the M35c claims, retested at m = 10 ===")
    for claim, selector in (
        ("h=1 worse than base (Gamma > 1)", lambda r: r["lookahead"] == 1),
        ("full horizon recovers the gap", lambda r: r["lookahead"] == 6),
    ):
        print(f"\n  {claim}:")
        for row in rows:
            if selector(row) and row["base_policy"] == "measured_first_order":
                excludes = (row["gamma_ci_lo"] > 1.0 or row["gamma_ci_hi"] < 1.0)
                verdict = ("CI excludes 1" if excludes else "CI includes 1 — not significant")
                print(f"    m={row['m']:2d}  Gamma = {row['gamma_mean_of_ratios']:.4f} "
                      f"[{row['gamma_ci_lo']:.3f}, {row['gamma_ci_hi']:.3f}]  -> {verdict}")

    with (RESULTS_DIR / "m38_horizon_scaling.csv").open("w", newline="",
                                                        encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)
    print("\nWrote results/m38_horizon_scaling.csv")


if __name__ == "__main__":
    main()
