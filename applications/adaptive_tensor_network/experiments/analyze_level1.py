"""Analysis for the Level 1 campaign (mission AI5/AI7), computed entirely
from results/level1_raw.json - never from in-memory state of the run
itself, so this script is independently re-runnable and auditable.

Implements the tests preregistered in PREREGISTRATION.md.
"""

from __future__ import annotations

import json
import sys
from collections import defaultdict
from pathlib import Path

SRC = Path(__file__).resolve().parents[1] / "src"
sys.path.insert(0, str(SRC))

from metrics import bootstrap_ci, paired_effect_size, pearson_corr, spearman_corr  # noqa: E402

RESULTS_DIR = Path(__file__).resolve().parents[1] / "results"

MAIN_METHODS = ["uniform", "singular_energy", "local_error_greedy", "random", "gradient_based", "pathwise_global"]
COMPARISON_BASELINES = ["uniform", "singular_energy", "local_error_greedy"]


def load_records() -> list[dict]:
    return json.loads((RESULTS_DIR / "level1_raw.json").read_text(encoding="utf-8"))


def index_by(records: list[dict], keys: tuple[str, ...]) -> dict:
    out = defaultdict(dict)
    for r in records:
        group_key = tuple(r[k] for k in keys[:-1])
        out[group_key][r[keys[-1]]] = r
    return out


def primary_hypothesis(records: list[dict]) -> dict:
    """Paired comparison: for each (topology, seed, budget), is
    pathwise_global's true_root_error lower than each baseline's, at the
    SAME budget?"""

    by_config = index_by(records, ("topology", "seed", "budget", "method"))
    results = {}
    for baseline in COMPARISON_BASELINES:
        paired_diffs = []  # baseline_error - pathwise_error; positive means pathwise better
        for config_key, methods in by_config.items():
            if "pathwise_global" in methods and baseline in methods:
                paired_diffs.append(methods[baseline]["true_root_error"] - methods["pathwise_global"]["true_root_error"])
        mean, lo, hi = bootstrap_ci(paired_diffs)
        effect = paired_effect_size(
            [methods[baseline]["true_root_error"] for methods in by_config.values() if baseline in methods and "pathwise_global" in methods],
            [methods["pathwise_global"]["true_root_error"] for methods in by_config.values() if baseline in methods and "pathwise_global" in methods],
        )
        results[baseline] = {
            "n_paired_configs": len(paired_diffs),
            "mean_error_reduction": mean,
            "ci_95_lower": lo,
            "ci_95_upper": hi,
            "supported_at_95": lo > 0,
            "cohens_d": effect,
        }
    return results


def secondary_hypothesis(records: list[dict], tolerances: list[float]) -> dict:
    """For each tolerance, find the minimum rank budget at which each
    method's true error drops below it, per (topology, seed); compare
    paired budgets."""

    by_config = index_by(records, ("topology", "seed", "method", "budget"))
    results = {}
    for tau in tolerances:
        method_min_budget = defaultdict(dict)  # method -> (topology,seed) -> min budget achieving tau
        for (topology, seed, method), budgets in by_config.items():
            achieving = [b for b, r in budgets.items() if r["true_root_error"] < tau]
            if achieving:
                method_min_budget[method][(topology, seed)] = min(achieving)
        per_baseline = {}
        for baseline in COMPARISON_BASELINES:
            paired = []
            for key in method_min_budget.get("pathwise_global", {}):
                if key in method_min_budget.get(baseline, {}):
                    paired.append(method_min_budget[baseline][key] - method_min_budget["pathwise_global"][key])
            if paired:
                mean, lo, hi = bootstrap_ci(paired)
                per_baseline[baseline] = {
                    "n_paired": len(paired),
                    "mean_budget_savings": mean,
                    "ci_95_lower": lo,
                    "ci_95_upper": hi,
                }
            else:
                per_baseline[baseline] = {"n_paired": 0, "note": "no configs where both methods reached this tolerance"}
        results[str(tau)] = per_baseline
    return results


def calibration_and_correlation(records: list[dict]) -> dict:
    """Ratio true_error/majorant (calibration) for pathwise_global, and
    Spearman/Pearson correlation between predicted majorant and true
    error across all methods/configs (a proxy for "predicted node
    contribution vs measured marginal benefit" at the whole-tree level,
    since AI5 asks for this at the per-node level too - see
    per_node_correlation below for that)."""

    ratios = []
    predicted = []
    actual = []
    for r in records:
        if r["method"] == "pathwise_global" and r["predicted_majorant"] not in (None, 0):
            ratios.append(r["true_root_error"] / r["predicted_majorant"])
        if r["predicted_majorant"] is not None:
            predicted.append(r["predicted_majorant"])
            actual.append(r["true_root_error"])
    return {
        "pathwise_global_ratio_true_to_majorant": {
            "mean": sum(ratios) / len(ratios) if ratios else None,
            "min": min(ratios) if ratios else None,
            "max": max(ratios) if ratios else None,
            "n": len(ratios),
            "note": "ratio <= 1 everywhere confirms the majorant is a genuine upper bound, not just a heuristic score",
        },
        "majorant_vs_true_error_correlation": {
            "pearson": pearson_corr(predicted, actual),
            "spearman": spearman_corr(predicted, actual),
            "n": len(predicted),
        },
    }


def regret_vs_oracle(records: list[dict]) -> dict:
    by_config = index_by(records, ("topology", "seed", "budget", "method"))
    regrets = defaultdict(list)
    for config_key, methods in by_config.items():
        if "oracle" not in methods:
            continue
        oracle_error = methods["oracle"]["true_root_error"]
        for method in MAIN_METHODS:
            if method in methods:
                regrets[method].append(methods[method]["true_root_error"] - oracle_error)
    return {
        method: {
            "mean_regret": sum(vals) / len(vals),
            "max_regret": max(vals),
            "n": len(vals),
        }
        for method, vals in regrets.items()
    }


def ablation_comparison(records: list[dict]) -> dict:
    by_config = index_by(records, ("topology", "seed", "budget", "method"))
    ablation_methods = [
        "ablation_local_source_only", "ablation_path_amplification_only",
        "ablation_universal_coarse_k_minus_1", "ablation_root_residual_negative_control",
        "ablation_random_path_coefficients",
    ]
    results = {}
    for ablation in ablation_methods:
        paired_diffs = []
        for methods in by_config.values():
            if ablation in methods and "pathwise_global" in methods:
                paired_diffs.append(methods[ablation]["true_root_error"] - methods["pathwise_global"]["true_root_error"])
        if paired_diffs:
            mean, lo, hi = bootstrap_ci(paired_diffs)
            results[ablation] = {
                "mean_error_vs_pathwise_global": mean,
                "ci_95_lower": lo,
                "ci_95_upper": hi,
                "pathwise_global_better": lo > 0,
                "n": len(paired_diffs),
            }
    return results


def main() -> None:
    records = load_records()
    print(f"Loaded {len(records)} raw records.\n")

    primary = primary_hypothesis(records)
    secondary = secondary_hypothesis(records, tolerances=[0.5, 1.0, 2.0])
    calibration = calibration_and_correlation(records)
    regret = regret_vs_oracle(records)
    ablations = ablation_comparison(records)

    report = {
        "primary_hypothesis": primary,
        "secondary_hypothesis": secondary,
        "calibration_and_correlation": calibration,
        "regret_vs_oracle": regret,
        "ablation_comparison": ablations,
    }

    out_path = RESULTS_DIR / "level1_analysis.json"
    out_path.write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(json.dumps(report, indent=2))
    print(f"\nWrote analysis to {out_path}")


if __name__ == "__main__":
    main()
