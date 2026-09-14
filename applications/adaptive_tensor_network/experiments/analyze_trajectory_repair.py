"""Analysis for M35, from results/trajectory_repair_raw.json.

The repair coefficient

    A_T = 1 - R_T^terminal / sum_t R_t^inst

compares what a method gave up step by step against what actually survived to
the end of the trajectory.

    A_T ~ 1   the loop repaired almost everything it gave up: re-measuring U
              substitutes for modelling the interaction
    A_T ~ 0   losses compounded; the interaction is operationally necessary
    A_T > 1   the method ended BETTER than the step-greedy oracle, which is
              possible because step-greedy is not globally optimal
"""

from __future__ import annotations

import json
import statistics
import sys
from collections import defaultdict
from pathlib import Path

SRC = Path(__file__).resolve().parents[1] / "src"
sys.path.insert(0, str(SRC))

RESULTS_DIR = Path(__file__).resolve().parents[1] / "results"
METHODS = ("first_order", "full_pairwise", "lowrank_pairwise")


def main() -> None:
    records = json.loads((RESULTS_DIR / "trajectory_repair_raw.json").read_text(encoding="utf-8"))
    print(f"Loaded {len(records)} trials.\n")

    grouped = defaultdict(list)
    for record in records:
        grouped[record["m_target"]].append(record)

    report = {}
    print(f"{'m':>4} {'method':>18} {'final':>9} {'vs oracle':>10} "
          f"{'sum R_inst':>11} {'R_term':>9} {'A_T':>7} {'evals':>8}")
    for m_target in sorted(grouped):
        rows = grouped[m_target]
        oracle_final = [r["methods"]["step_oracle"]["trajectory"][-1] for r in rows]
        oracle_sum = statistics.fmean(
            [sum(r["methods"]["step_oracle"]["instant_regret"]) for r in rows])
        for method in METHODS:
            finals, terminals, sums, repairs, evaluations = [], [], [], [], []
            for record, oracle_end in zip(rows, oracle_final):
                data = record["methods"][method]
                final = data["trajectory"][-1]
                total = sum(data["instant_regret"])
                terminal = final - oracle_end
                finals.append(final)
                terminals.append(terminal)
                sums.append(total)
                evaluations.append(data["evaluations"])
                if total > 1e-12:
                    repairs.append(1.0 - terminal / total)
            entry = {
                "final": statistics.fmean(finals),
                "vs_oracle": statistics.fmean(terminals),
                "sum_instant_regret": statistics.fmean(sums),
                "A_T": statistics.fmean(repairs) if repairs else float("nan"),
                "evaluations": statistics.fmean(evaluations),
            }
            report[f"m{m_target}_{method}"] = entry
            print(f"{m_target:4d} {method:>18} {entry['final']:9.4f} "
                  f"{entry['vs_oracle']:+10.5f} {entry['sum_instant_regret']:11.5f} "
                  f"{entry['vs_oracle']:9.5f} {entry['A_T']:7.3f} "
                  f"{entry['evaluations']:8.0f}")
        print(f"{m_target:4d} {'step_oracle':>18} "
              f"{statistics.fmean(oracle_final):9.4f} {0.0:+10.5f} "
              f"{oracle_sum:11.5f}")
        print()

    print("sum R_inst = what the method gave up step by step along its own path")
    print("R_term     = what survived to the end, against the step-greedy oracle")
    print("A_T        = 1 - R_term / sum R_inst;  ~1 means the loop repaired it")

    (RESULTS_DIR / "trajectory_repair_analysis.json").write_text(
        json.dumps(report, indent=2), encoding="utf-8"
    )
    print("\nWrote analysis to results/trajectory_repair_analysis.json")


if __name__ == "__main__":
    main()
