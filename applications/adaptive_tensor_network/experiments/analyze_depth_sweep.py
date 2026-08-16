"""Analysis for the depth sweep, computed entirely from
results/depth_sweep_raw.json - never from in-memory state of the run, so
this script is independently re-runnable and auditable.

Reuses the Level 1 statistics (`metrics.bootstrap_ci`,
`metrics.paired_effect_size`) so the numbers are directly comparable to
LEVEL1_FINDINGS.md rather than computed by a different procedure.

Three curves, per (regime, depth):

  A(k)  paired error reduction of pathwise_global against each baseline,
        on `relative_root_error` (true error divided by the root's own RMS
        value scale) so magnitudes are comparable across depths whose root
        scales differ. At fixed (depth, regime, seed, budget) the scale is
        a shared constant, so this normalization cannot change the sign of
        a paired difference -- only make it comparable across k.
  T(k)  certificate tightness = root_actual_sup / root_certificate_bound.
  H(k)  dispersion of the pure path-transport weights w_v.

The `ablation_random_path_coefficients` comparison is the decisive
diagnostic: Level 1 found real path amplifications statistically
indistinguishable from random positive coefficients of similar scale. If
the real coefficients separate from random ones at depth, the path
structure is carrying information there that it did not carry at k=3.
"""

from __future__ import annotations

import json
import statistics
import sys
from collections import defaultdict
from pathlib import Path

SRC = Path(__file__).resolve().parents[1] / "src"
sys.path.insert(0, str(SRC))

from metrics import bootstrap_ci, paired_effect_size  # noqa: E402

RESULTS_DIR = Path(__file__).resolve().parents[1] / "results"

BASELINES = ["uniform", "local_error_greedy", "singular_energy"]
ABLATIONS = ["ablation_local_source_only", "ablation_random_path_coefficients"]


def load_records() -> list[dict]:
    return json.loads((RESULTS_DIR / "depth_sweep_raw.json").read_text(encoding="utf-8"))


def by_config(records: list[dict]) -> dict:
    """(regime, depth) -> (seed, budget) -> method -> record."""
    out: dict = defaultdict(lambda: defaultdict(dict))
    for r in records:
        out[(r["regime"], r["depth"])][(r["seed"], r["budget"])][r["method"]] = r
    return out


def paired_comparison(configs: dict, reference: str, other: str, field: str) -> dict:
    """Positive mean means `reference` beats `other` (lower error)."""
    diffs, ref_vals, other_vals = [], [], []
    for methods in configs.values():
        if reference in methods and other in methods:
            diffs.append(methods[other][field] - methods[reference][field])
            ref_vals.append(methods[reference][field])
            other_vals.append(methods[other][field])
    if not diffs:
        return {"n": 0}
    mean, lo, hi = bootstrap_ci(diffs)
    return {
        "n_paired": len(diffs),
        "mean_error_reduction": mean,
        "ci_95_lower": lo,
        "ci_95_upper": hi,
        "pathwise_wins_at_95": lo > 0,
        "baseline_wins_at_95": hi < 0,
        "cohens_d": paired_effect_size(other_vals, ref_vals),
    }


def summarize(values: list[float]) -> dict:
    clean = [v for v in values if v == v and abs(v) != float("inf")]
    if not clean:
        return {"n": 0}
    return {
        "n": len(clean),
        "mean": statistics.fmean(clean),
        "median": statistics.median(clean),
        "min": min(clean),
        "max": max(clean),
    }


def main() -> None:
    records = load_records()
    print(f"Loaded {len(records)} raw records.\n")
    configs = by_config(records)

    report: dict = {"per_regime_depth": {}}

    for (regime, depth) in sorted(configs, key=lambda x: (x[0], x[1])):
        group = configs[(regime, depth)]
        flat = [r for methods in group.values() for r in methods.values()]

        entry: dict = {
            "A_allocator_advantage": {
                baseline: paired_comparison(group, "pathwise_global", baseline, "relative_root_error")
                for baseline in BASELINES
            },
            "A_vs_ablations": {
                ablation: paired_comparison(group, "pathwise_global", ablation, "relative_root_error")
                for ablation in ABLATIONS
            },
            "T_certificate_tightness": {
                "A_scalar_frobenius": summarize([r["certificate_tightness"] for r in flat]),
                "B_restricted_gain": summarize([r["cert_b_tightness"] for r in flat]),
                "C_gram_aware": summarize([r["cert_c_tightness"] for r in flat]),
            },
            "certificate_always_holds": {
                "A": all(r["certificate_holds"] for r in flat),
                "B": all(r["cert_b_holds"] for r in flat),
                "C": all(r["cert_c_holds"] for r in flat),
            },
            "H_weight_dispersion": {
                "cv": summarize([r["w_cv"] for r in flat]),
                "n_eff": summarize([r["w_n_eff"] for r in flat]),
                "n_eff_over_k": summarize([r["w_n_eff"] / r["n_nodes"] for r in flat]),
            },
            "majorant_ratio_true_over_predicted": summarize([
                r["true_root_error"] / r["predicted_majorant"]
                for r in flat
                if r["method"] == "pathwise_global" and r["predicted_majorant"] > 0
            ]),
        }
        report["per_regime_depth"][f"{regime}_k{depth}"] = entry

    out_path = RESULTS_DIR / "depth_sweep_analysis.json"
    out_path.write_text(json.dumps(report, indent=2), encoding="utf-8")

    # Console summary: the three curves, one table per regime.
    for regime in ("iid", "heterogeneous"):
        print(f"\n=== regime: {regime} ===")
        print(f"{'k':>4} {'A vs uniform':>22} {'A vs local_greedy':>24} "
              f"{'A vs random_coef':>22} {'w_CV':>7} {'Neff/k':>7}")
        for depth in sorted({d for (rg, d) in configs if rg == regime}):
            e = report["per_regime_depth"][f"{regime}_k{depth}"]

            def fmt(block: dict) -> str:
                if block.get("n_paired", 0) == 0:
                    return "n/a"
                mark = "+" if block["pathwise_wins_at_95"] else ("-" if block["baseline_wins_at_95"] else "0")
                return f"{block['mean_error_reduction']:+.4f}[{block['ci_95_lower']:+.4f},{block['ci_95_upper']:+.4f}]{mark}"

            uni = fmt(e["A_allocator_advantage"]["uniform"])
            grd = fmt(e["A_allocator_advantage"]["local_error_greedy"])
            rnd = fmt(e["A_vs_ablations"]["ablation_random_path_coefficients"])
            cv = e["H_weight_dispersion"]["cv"]["mean"]
            ne = e["H_weight_dispersion"]["n_eff_over_k"]["mean"]
            print(f"{depth:4d} {uni:>22} {grd:>24} {rnd:>22} {cv:7.3f} {ne:7.3f}")

    print("\n(+ = pathwise significantly better, - = baseline significantly better, "
          "0 = CI includes zero)")

    # T(k): median tightness of each composition rule, plus soundness.
    print("\n=== T(k): certificate tightness (median E_real / B_cert; 1.0 = exact) ===")
    print(f"{'regime':>15} {'k':>4} {'A scalar/Frob':>15} {'B restricted':>15} "
          f"{'C gram-aware':>15} {'B/A':>10} {'C/B':>7} {'sound':>9}")
    for regime in ("iid", "heterogeneous"):
        for depth in sorted({d for (rg, d) in configs if rg == regime}):
            e = report["per_regime_depth"][f"{regime}_k{depth}"]
            t = e["T_certificate_tightness"]
            a, b, c = (t[key]["median"] for key in
                       ("A_scalar_frobenius", "B_restricted_gain", "C_gram_aware"))
            holds = e["certificate_always_holds"]
            sound = "ALL HOLD" if all(holds.values()) else f"VIOLATED {holds}"
            print(f"{regime:>15} {depth:4d} {a:15.2e} {b:15.2e} {c:15.2e} "
                  f"{b / a:10.1e} {c / b:7.3f} {sound:>9}")
    print(f"\nWrote analysis to {out_path}")


if __name__ == "__main__":
    main()
