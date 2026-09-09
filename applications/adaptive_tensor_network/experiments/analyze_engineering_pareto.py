"""Build the observed error--cost Pareto table for M35b/M38.

This is a descriptive generator.  It reads preserved raw artifacts and does
not promote the resulting finite synthetic observations to general claims.
"""

from __future__ import annotations

import csv
import json
from pathlib import Path
from statistics import mean


HERE = Path(__file__).resolve().parent
RESULTS = HERE.parent / "results"
OUTPUT = RESULTS / "engineering_pareto_front.csv"


def _load(name: str):
    return json.loads((RESULTS / name).read_text(encoding="utf-8"))


def _dominated(row: dict, rows: list[dict], cost_key: str) -> bool:
    return any(
        other["mean_true_terminal_regret"] <= row["mean_true_terminal_regret"]
        and other[cost_key] <= row[cost_key]
        and (
            other["mean_true_terminal_regret"] < row["mean_true_terminal_regret"]
            or other[cost_key] < row[cost_key]
        )
        for other in rows
        if other is not row
    )


def _rows_for_size(m: int) -> list[dict]:
    oracle_name = (
        "terminal_oracle_m8_raw.json"
        if m == 8
        else "terminal_oracle_m10_parallel_raw.json"
    )
    oracle = _load(oracle_name)
    stars = {int(seed): record["E_terminal_star"] for seed, record in oracle["seeds"].items()}
    policy_runs = _load(f"policy_scaling_m{m}.json")["runs"]
    rollout_runs = _load(f"rollout_calibration_m{m}_raw.json")["runs"]

    groups: list[tuple[str, str, list[dict]]] = []
    for policy in sorted({record["policy"] for record in policy_runs}):
        selected = [
            record
            for record in policy_runs
            if record["policy"] == policy and record["seed"] in stars
        ]
        groups.append((policy, f"policy_scaling_m{m}.json", selected))

    for horizon in sorted(
        {
            record["lookahead"]
            for record in rollout_runs
            if record["base_policy"] == "measured_first_order"
        }
    ):
        if horizon == 0:
            # The policy-scaling row above is the same terminal policy and has
            # the campaign's canonical evaluation accounting.
            continue
        selected = [
            record
            for record in rollout_runs
            if record["base_policy"] == "measured_first_order"
            and record["lookahead"] == horizon
        ]
        groups.append(
            (
                f"rollout_first_order_h{horizon}",
                f"rollout_calibration_m{m}_raw.json",
                selected,
            )
        )

    rows = []
    for method, source, records in groups:
        if set(record["seed"] for record in records) != set(stars):
            raise ValueError(f"{method} at m={m} does not cover the exact-oracle seeds")
        rows.append(
            {
                "problem_size_m": m,
                "method": method,
                "source_artifact": source,
                "seed_count": len(records),
                "rank_budget_contract": "same start; b=3 for T=6 rounds",
                "mean_terminal_error": mean(record["terminal_error"] for record in records),
                "mean_true_terminal_regret": mean(
                    record["terminal_error"] - stars[record["seed"]]
                    for record in records
                ),
                "mean_terminal_over_initial": mean(
                    record["terminal_error"] / record["base_error"]
                    for record in records
                ),
                "mean_forward_evaluations": mean(record["evaluations"] for record in records),
                "mean_wall_seconds": mean(record["wall_seconds"] for record in records),
                "pareto_error_forward_evaluations": False,
                "pareto_error_wall_seconds": False,
                "scope": "synthetic heterogeneous D=16 chain; exact terminal oracle",
            }
        )

    for row in rows:
        row["pareto_error_forward_evaluations"] = not _dominated(
            row, rows, "mean_forward_evaluations"
        )
        row["pareto_error_wall_seconds"] = not _dominated(
            row, rows, "mean_wall_seconds"
        )
    return rows


def main() -> None:
    rows = _rows_for_size(8) + _rows_for_size(10)
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    with OUTPUT.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)
    print(f"wrote {len(rows)} rows to {OUTPUT}")


if __name__ == "__main__":
    main()
