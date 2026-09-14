"""Analyze ATN_THRESHOLD_GATE_V1 from its preserved raw JSON artifact."""

from __future__ import annotations

import csv
import json
from pathlib import Path

import numpy as np


APP = Path(__file__).resolve().parents[1]
RESULTS = APP / "results"
RAW = RESULTS / "threshold_gate_m8_m10_raw.json"
SUMMARY = RESULTS / "threshold_gate_summary.csv"
FINDINGS = RESULTS / "THRESHOLD_GATE_V1_FINDINGS.md"
POLICIES = (
    "uniform",
    "threshold_static",
    "threshold_adaptive",
    "measured_first_order",
    "full_pairwise",
    "rollout_first_order_h6",
)


def paired_bootstrap_ci(values: np.ndarray, *, seed: int, draws: int = 100_000) -> tuple[float, float]:
    rng = np.random.default_rng(seed)
    indices = rng.integers(0, len(values), size=(draws, len(values)))
    means = values[indices].mean(axis=1)
    lo, hi = np.quantile(means, [0.025, 0.975])
    return float(lo), float(hi)


def dominated(row: dict, rows: list[dict], cost: str) -> bool:
    return any(
        other["mean_true_terminal_regret"] <= row["mean_true_terminal_regret"]
        and other[cost] <= row[cost]
        and (
            other["mean_true_terminal_regret"] < row["mean_true_terminal_regret"]
            or other[cost] < row[cost]
        )
        for other in rows
        if other is not row
    )


def oracle_stars(m: int) -> dict[int, float]:
    name = "terminal_oracle_m8_raw.json" if m == 8 else "terminal_oracle_m10_parallel_raw.json"
    payload = json.loads((RESULTS / name).read_text(encoding="utf-8"))
    return {int(seed): float(record["E_terminal_star"]) for seed, record in payload["seeds"].items()}


def main() -> None:
    payload = json.loads(RAW.read_text(encoding="utf-8"))
    runs = payload["runs"]
    rows = []
    comparisons = []

    for m in (8, 10):
        stars = oracle_stars(m)
        expected_seeds = set(stars)
        m_rows = []
        for policy in POLICIES:
            selected = [record for record in runs if record["m"] == m and record["policy"] == policy]
            if {record["seed"] for record in selected} != expected_seeds:
                raise ValueError(f"incomplete {policy} records at m={m}")
            rank_budgets = {record["rank_budget"] for record in selected}
            if len(rank_budgets) != 1:
                raise ValueError(f"rank budget drift for {policy} at m={m}")
            row = {
                "problem_size_m": m,
                "policy": policy,
                "seed_count": len(selected),
                "mean_terminal_error": float(np.mean([record["terminal_error"] for record in selected])),
                "mean_true_terminal_regret": float(
                    np.mean([record["terminal_error"] - stars[record["seed"]] for record in selected])
                ),
                "mean_terminal_over_initial": float(
                    np.mean([record["terminal_error"] / record["base_error"] for record in selected])
                ),
                "rank_budget": next(iter(rank_budgets)),
                "mean_forward_evaluations": float(np.mean([record["forward_evaluations"] for record in selected])),
                "mean_memory_proxy_bytes": float(np.mean([record["memory_proxy_bytes"] for record in selected])),
                "mean_wall_seconds": float(np.mean([record["wall_seconds"] for record in selected])),
            }
            rows.append(row)
            m_rows.append(row)

        for row in m_rows:
            row["pareto_error_forward_evaluations"] = not dominated(row, m_rows, "mean_forward_evaluations")
            row["pareto_error_memory_proxy"] = not dominated(row, m_rows, "mean_memory_proxy_bytes")
            row["pareto_error_wall_seconds"] = not dominated(row, m_rows, "mean_wall_seconds")

        fo = {record["seed"]: record for record in runs if record["m"] == m and record["policy"] == "measured_first_order"}
        for index, threshold in enumerate(("threshold_static", "threshold_adaptive")):
            baseline = {record["seed"]: record for record in runs if record["m"] == m and record["policy"] == threshold}
            normalized = np.array(
                [
                    (baseline[seed]["terminal_error"] - fo[seed]["terminal_error"])
                    / fo[seed]["base_error"]
                    for seed in sorted(expected_seeds)
                ],
                dtype=float,
            )
            ci = paired_bootstrap_ci(normalized, seed=m * 100 + index)
            if ci[0] > 0:
                verdict = "FO_WINS"
            elif ci[1] < 0:
                verdict = "THRESHOLD_WINS"
            elif ci[0] >= -0.01 and ci[1] <= 0.01:
                verdict = "PRACTICAL_TIE"
            else:
                verdict = "INCONCLUSIVE"
            comparisons.append(
                {
                    "m": m,
                    "threshold": threshold,
                    "mean_normalized_delta_threshold_minus_fo": float(normalized.mean()),
                    "ci95": ci,
                    "all_seed_deltas_positive": bool(np.all(normalized > 0)),
                    "verdict": verdict,
                }
            )

    verdicts = {(item["m"], item["threshold"]): item["verdict"] for item in comparisons}
    if all(value == "FO_WINS" for value in verdicts.values()):
        overall = "GO_FO_EQUAL_RANK"
    elif all(
        verdicts[(m, threshold)] == "THRESHOLD_WINS"
        for m in (8, 10)
        for threshold in ("threshold_static", "threshold_adaptive")
    ):
        overall = "STOP_FO_COMPETITIVE"
    elif not any(value == "FO_WINS" for value in verdicts.values()) and all(
        abs(item["mean_normalized_delta_threshold_minus_fo"]) <= 0.01 for item in comparisons
    ):
        overall = "THRESHOLD_CAPTURES_CHEAP_VALUE"
    else:
        overall = "MIXED_OR_INCONCLUSIVE"

    with SUMMARY.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)

    lines = [
        "# ATN threshold gate V1 findings",
        "",
        "Status: **EXPERIMENTAL, FIXED-BASIS SYNTHETIC GATE**. Nothing here is a theorem or a real-system hardware claim.",
        "",
        f"Overall preregistered gate: **{overall}**.",
        "",
        "## Primary paired comparison",
        "",
        "Positive delta means FO has lower terminal error. Deltas are normalized by each instance's initial error.",
        "",
        "| m | threshold | mean normalized delta | paired CI95 | all seeds FO-better | verdict |",
        "|---:|---|---:|---:|---:|---|",
    ]
    for item in comparisons:
        lines.append(
            f"| {item['m']} | {item['threshold']} | "
            f"{item['mean_normalized_delta_threshold_minus_fo']:.6f} | "
            f"[{item['ci95'][0]:.6f}, {item['ci95'][1]:.6f}] | "
            f"{str(item['all_seed_deltas_positive']).lower()} | {item['verdict']} |"
        )

    lines.extend(
        [
            "",
            "## Error-cost means",
            "",
            "All policies have the same terminal rank budget within each problem size.",
            "",
            "| m | policy | regret | evals | memory proxy (bytes) | wall s | Pareto eval | Pareto memory | Pareto wall |",
            "|---:|---|---:|---:|---:|---:|---:|---:|---:|",
        ]
    )
    for row in rows:
        lines.append(
            f"| {row['problem_size_m']} | {row['policy']} | "
            f"{row['mean_true_terminal_regret']:.6f} | "
            f"{row['mean_forward_evaluations']:.1f} | "
            f"{row['mean_memory_proxy_bytes']:.1f} | "
            f"{row['mean_wall_seconds']:.6f} | "
            f"{str(row['pareto_error_forward_evaluations']).lower()} | "
            f"{str(row['pareto_error_memory_proxy']).lower()} | "
            f"{str(row['pareto_error_wall_seconds']).lower()} |"
        )

    lines.extend(
        [
            "",
            "## Interpretation boundary",
            "",
            "- `GO_FO_EQUAL_RANK` means a terminal-quality advantage over both cutoff variants at the same rank budget in both exact synthetic landscapes.",
            "- It does not mean FO dominates cutoff in evaluations or wall time; those currencies remain explicit Pareto tradeoffs.",
            "- Adaptive cutoff changes its local energy signal but not the projector bases, because basis refitting would invalidate the exact terminal oracle.",
            "- The memory quantity is an analytical compressed-coordinate proxy, not measured RSS or VRAM.",
            "- Wall times are single CPU observations and do not support small-difference or hardware claims.",
            "- A production basis-refitting cutoff and real TT/MPS/TTN workload remain mandatory before a technology claim.",
            "",
            "Raw source: `threshold_gate_m8_m10_raw.json`. Registered design: `experiments/configs/ATN_THRESHOLD_GATE_V1.yaml`.",
        ]
    )
    FINDINGS.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(json.dumps({"overall_gate": overall, "comparisons": comparisons}, indent=2))
    print(f"wrote {SUMMARY} and {FINDINGS}")


if __name__ == "__main__":
    main()
