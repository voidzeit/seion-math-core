"""Analyze the fixed-size V1B precision extension and pooled V1+V1B view."""

from __future__ import annotations

import json
from pathlib import Path

import numpy as np


APP = Path(__file__).resolve().parents[1]
RESULTS = APP / "results"
OUTPUT = RESULTS / "threshold_gate_v1b_summary.json"
FINDINGS = RESULTS / "THRESHOLD_GATE_V1B_FINDINGS.md"


def ci(values: np.ndarray, seed: int) -> tuple[float, float]:
    rng = np.random.default_rng(seed)
    indices = rng.integers(0, len(values), size=(100_000, len(values)))
    return tuple(float(x) for x in np.quantile(values[indices].mean(axis=1), [0.025, 0.975]))


def comparisons(runs: list[dict], label: str) -> list[dict]:
    output = []
    for m in (8, 10):
        fo = {
            record["seed"]: record
            for record in runs
            if record["m"] == m and record["policy"] == "measured_first_order"
        }
        for offset, threshold in enumerate(("threshold_static", "threshold_adaptive")):
            baseline = {
                record["seed"]: record
                for record in runs
                if record["m"] == m and record["policy"] == threshold
            }
            if set(fo) != set(baseline):
                raise ValueError(f"seed mismatch for {label} m={m} {threshold}")
            values = np.array(
                [
                    (baseline[seed]["terminal_error"] - fo[seed]["terminal_error"])
                    / fo[seed]["base_error"]
                    for seed in sorted(fo)
                ]
            )
            interval = ci(values, seed=m * 100 + offset + (10_000 if label == "pooled" else 0))
            if interval[0] > 0:
                verdict = "FO_WINS"
            elif interval[1] < 0:
                verdict = "THRESHOLD_WINS"
            elif interval[0] >= -0.01 and interval[1] <= 0.01:
                verdict = "PRACTICAL_TIE"
            else:
                verdict = "INCONCLUSIVE"
            output.append(
                {
                    "sample": label,
                    "m": m,
                    "threshold": threshold,
                    "seed_count": len(values),
                    "mean_normalized_delta_threshold_minus_fo": float(values.mean()),
                    "median_normalized_delta_threshold_minus_fo": float(np.median(values)),
                    "ci95": list(interval),
                    "fo_win_count": int(np.sum(values > 0)),
                    "threshold_win_count": int(np.sum(values < 0)),
                    "verdict": verdict,
                }
            )
    return output


def main() -> None:
    v1 = json.loads((RESULTS / "threshold_gate_m8_m10_raw.json").read_text(encoding="utf-8"))["runs"]
    v1b = json.loads((RESULTS / "threshold_gate_v1b_raw.json").read_text(encoding="utf-8"))["runs"]
    v1_primary = [
        record
        for record in v1
        if record["policy"] in {"threshold_static", "threshold_adaptive", "measured_first_order"}
    ]
    extension = comparisons(v1b, "v1b_new_seeds")
    pooled = comparisons(v1_primary + v1b, "pooled")

    extension_verdicts = [item["verdict"] for item in extension]
    extension_gate = (
        "GO_FO_EQUAL_RANK"
        if all(value == "FO_WINS" for value in extension_verdicts)
        else "MIXED_OR_INCONCLUSIVE"
    )
    pooled_by_m = {
        m: {item["verdict"] for item in pooled if item["m"] == m} for m in (8, 10)
    }
    if pooled_by_m[10] == {"FO_WINS"} and pooled_by_m[8] != {"FO_WINS"}:
        combined_decision = "DOMAIN_LIMITED_FO_ADVANTAGE_AT_M10_NO_GENERAL_GO"
    else:
        combined_decision = "NO_GENERAL_GO"

    payload = {
        "status": "V1B_FIXED_SIZE_EXTENSION_COMPLETE",
        "extension_preregistered_gate": extension_gate,
        "combined_decision": combined_decision,
        "extension_only": extension,
        "pooled_same_design_descriptive": pooled,
        "interpretation": [
            "V1B was declared only after V1 was inconclusive and is reported separately.",
            "The pooled rows combine identical fixed-basis designs for precision but do not rewrite the V1 result.",
            "Positive delta means lower FO terminal error; exact oracle cancels from the paired contrast.",
            "No screened-rollout gate is opened because FO did not achieve the predeclared general GO at both sizes.",
        ],
    }
    OUTPUT.write_text(json.dumps(payload, indent=2), encoding="utf-8")

    lines = [
        "# ATN threshold gate V1B findings",
        "",
        "V1B was declared after V1 returned an inconclusive five-seed interval and before these 30 new seeds were executed. It is a fixed-size precision extension, not optional stopping.",
        "",
        f"Preregistered V1B extension gate: **{extension_gate}**.  ",
        f"Combined project decision: **{combined_decision}**.",
        "",
        "Positive delta means FO has lower terminal error. Values are normalized by initial error.",
        "",
        "## V1B new seeds only",
        "",
        "| m | threshold | n | mean delta | median | CI95 | FO wins | threshold wins | verdict |",
        "|---:|---|---:|---:|---:|---:|---:|---:|---|",
    ]
    for item in extension:
        lines.append(
            f"| {item['m']} | {item['threshold']} | {item['seed_count']} | "
            f"{item['mean_normalized_delta_threshold_minus_fo']:.6f} | "
            f"{item['median_normalized_delta_threshold_minus_fo']:.6f} | "
            f"[{item['ci95'][0]:.6f}, {item['ci95'][1]:.6f}] | "
            f"{item['fo_win_count']} | {item['threshold_win_count']} | {item['verdict']} |"
        )
    lines.extend(
        [
            "",
            "## Pooled V1 + V1B, identical design",
            "",
            "These rows improve precision but do not retroactively change V1's preregistered outcome.",
            "",
            "| m | threshold | n | mean delta | median | CI95 | FO wins | threshold wins | verdict |",
            "|---:|---|---:|---:|---:|---:|---:|---:|---|",
        ]
    )
    for item in pooled:
        lines.append(
            f"| {item['m']} | {item['threshold']} | {item['seed_count']} | "
            f"{item['mean_normalized_delta_threshold_minus_fo']:.6f} | "
            f"{item['median_normalized_delta_threshold_minus_fo']:.6f} | "
            f"[{item['ci95'][0]:.6f}, {item['ci95'][1]:.6f}] | "
            f"{item['fo_win_count']} | {item['threshold_win_count']} | {item['verdict']} |"
        )
    lines.extend(
        [
            "",
            "## Decision",
            "",
            "FO does **not** clear the requested general gate: at m=8 its mean advantage is essentially zero and both intervals remain inconclusive. In the pooled m=10 sample, FO has a positive mean advantage over both thresholds with intervals above zero, so the value is regime-dependent rather than absent.",
            "",
            "Threshold remains dramatically cheaper (1 forward static, 12 adaptive, versus 60/72 for FO) and is itself Pareto-optimal. Consequently Paper C cannot claim that FO generally beats a real cutoff. The defensible engineering conclusion is a dispatch hypothesis: cutoff for the smaller/easier regime and FO only where downstream complexity justifies its measurement cost. That hypothesis requires held-out dispatch validation before promotion.",
            "",
            "Per the declared order, screened rollout is not started in this pass because the global FO-versus-threshold gate did not return GO.",
        ]
    )
    FINDINGS.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(json.dumps(payload, indent=2))


if __name__ == "__main__":
    main()
