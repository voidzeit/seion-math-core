"""Analysis for M32, computed entirely from results/surrogate_prediction_raw.json.

Reports, per experiment and regime, for each surrogate:
  R2       1 - SS_res/SS_tot against the measured Delta-E
  rho      Spearman, i.e. can it rank bundles
  sign     fraction of bundles whose sign of Delta-E is predicted
  regret   normalized gap between the best bundle and the one the surrogate picks

The three informative increments in M32B are
  linear -> diagonal        importance of per-coordinate curvature
  diagonal -> full pairwise importance of inter-node coupling
  full -> low-rank pairwise what compressing the coupling costs
"""

from __future__ import annotations

import json
import statistics
import sys
from collections import defaultdict
from pathlib import Path

import numpy as np

SRC = Path(__file__).resolve().parents[1] / "src"
sys.path.insert(0, str(SRC))

from metrics import spearman_corr  # noqa: E402

RESULTS_DIR = Path(__file__).resolve().parents[1] / "results"
MODELS_A = ["L", "P", "Pq"]
MODELS_B = ["L", "D2", "F2", "Fq"]
LABELS = {"L": "linear", "P": "pairwise", "Pq": "pairwise-lowrank",
          "D2": "diagonal", "F2": "diag+pairwise", "Fq": "diag+lowrank"}


def score(rows: list[dict], model: str) -> dict:
    truth = np.array([r["true"] for r in rows])
    pred = np.array([r[model] for r in rows])
    ss_tot = float(np.sum((truth - truth.mean()) ** 2))
    ss_res = float(np.sum((truth - pred) ** 2))
    best_true = int(np.argmin(truth))          # most error reduction = most negative
    picked = int(np.argmin(pred))
    spread = float(truth.max() - truth.min())
    return {
        "R2": 1.0 - ss_res / ss_tot if ss_tot > 0 else float("nan"),
        "rho": spearman_corr(list(pred), list(truth)),
        "sign": float(np.mean(np.sign(pred) == np.sign(truth))),
        "regret": (truth[picked] - truth[best_true]) / spread if spread > 0 else 0.0,
    }


def main() -> None:
    records = json.loads((RESULTS_DIR / "surrogate_prediction_raw.json").read_text(encoding="utf-8"))
    print(f"Loaded {len(records)} raw records.\n")

    report: dict = {}
    for experiment, models in (("A_binary", MODELS_A), ("B_multi", MODELS_B)):
        print(f"=== {experiment} "
              f"({'Delta_v in {0,1}: diagonal inert' if experiment == 'A_binary' else 'Delta_v in {0,1,2}: diagonal active'}) ===")
        print(f"{'D':>4} {'regime':>14} {'model':>18} {'R2':>8} {'rho':>7} {'sign':>7} {'regret':>8}")
        for dim in sorted({r["dim"] for r in records}):
            for regime in ("iid", "heterogeneous"):
                # group by configuration so R2 is not inflated by pooling
                groups = defaultdict(list)
                for r in records:
                    if r["experiment"] == experiment and r["dim"] == dim and r["regime"] == regime:
                        groups[(r["family"], r["seed"], r["budget_fraction"])].append(r)
                if not groups:
                    continue
                for model in models:
                    per_config = [score(rows, model) for rows in groups.values()]
                    entry = {
                        key: statistics.fmean([c[key] for c in per_config
                                               if c[key] == c[key]])
                        for key in ("R2", "rho", "sign", "regret")
                    }
                    report[f"{experiment}_D{dim}_{regime}_{model}"] = entry
                    print(f"{dim:4d} {regime:>14} {LABELS[model]:>18} "
                          f"{entry['R2']:8.3f} {entry['rho']:7.3f} "
                          f"{entry['sign']:7.3f} {entry['regret']:8.3f}")
        print()

    print("=== informative increments in R2 (heterogeneous) ===")
    for dim in sorted({r["dim"] for r in records}):
        def get(exp, model):
            return report.get(f"{exp}_D{dim}_heterogeneous_{model}", {}).get("R2", float("nan"))
        print(f"D={dim:2d}  A: linear {get('A_binary','L'):+.3f} -> pairwise "
              f"{get('A_binary','P'):+.3f} -> lowrank {get('A_binary','Pq'):+.3f}")
        print(f"D={dim:2d}  B: linear {get('B_multi','L'):+.3f} -> diagonal "
              f"{get('B_multi','D2'):+.3f} -> +pairwise {get('B_multi','F2'):+.3f} "
              f"-> +lowrank {get('B_multi','Fq'):+.3f}")

    (RESULTS_DIR / "surrogate_prediction_analysis.json").write_text(
        json.dumps(report, indent=2), encoding="utf-8"
    )
    print("\nWrote analysis to results/surrogate_prediction_analysis.json")


if __name__ == "__main__":
    main()
