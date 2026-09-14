"""PMT-TN benchmark V1 analysis: hypothesis tables H1-H8 and figures 1-6 (preregistration §7).

usage: python analyze.py [DATE]    (default 2026-09-13)
Reads artifacts/pmt_tn_benchmark/<DATE>-v1/<campaign>/runs.jsonl for the registered campaigns and writes
artifacts/pmt_tn_benchmark/<DATE>-v1/analysis/{tables.json, figures/*.png, artifact_hashes.json}.
The analysis directory is rewritten on each call (it is derived data; the inputs are hashed in tables.json).
"""
from __future__ import annotations

import hashlib
import json
import math
import sys
from collections import defaultdict
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
sys.path.insert(0, str(HERE))

import certificate as cert  # noqa: E402

CAMPAIGNS = ["F1", "F2", "F3", "F4", "F6", "F7", "F7R", "F8"]
LARGEST_RANK = {"F2": 6, "F3": 8, "F4": 3}
VALID = ("WITHIN_CERTIFICATE", "REPLAY_TRIGGERED", "THEOREM_R_COUNTEREXAMPLE_CANDIDATE")


def load(base):
    data, hashes = {}, {}
    for c in CAMPAIGNS:
        p = base / c / "runs.jsonl"
        if p.exists() and (base / c / "final_metrics.json").exists():
            data[c] = [json.loads(l) for l in p.open(encoding="utf-8")]
            hashes[c] = hashlib.sha256(p.read_bytes()).hexdigest()
    return data, hashes


def q(xs, p):
    xs = [x for x in xs if x is not None and math.isfinite(x)]
    return float(np.quantile(xs, p)) if xs else None


def spearman(a, b):
    from scipy.stats import spearmanr
    if len(a) < 3 or np.ptp(a) == 0 or np.ptp(b) == 0:
        return None
    return float(spearmanr(a, b).statistic)


def h1_table(data):
    rows = {}
    for c, recs in data.items():
        if c == "F8":
            continue
        valid = [r for r in recs if r["label"] in VALID]
        ratios = [r["ratio_obs_to_BR"] for r in valid]
        rows[c] = {"runs": len(recs), "valid": len(valid),
                   "labels": {l: sum(r["label"] == l for r in recs) for l in sorted({r["label"] for r in recs})},
                   "replay_triggered": sum(r["label"] == "REPLAY_TRIGGERED" or "replay" in r for r in recs),
                   "counterexample_candidates": sum(r["label"] == "THEOREM_R_COUNTEREXAMPLE_CANDIDATE" for r in recs),
                   "ratio_max": max(ratios) if ratios else None,
                   "min_slack": (1 - max(ratios)) if ratios else None,
                   "invalid_projector": sum(r["label"] == "INVALID_PROJECTOR" for r in recs)}
    return rows


def h2_table(recs):
    eq = [r["ratio_obs_to_BR"] for r in recs if r["variant"] == "equal_angles"]
    un = [r["ratio_obs_to_BR"] for r in recs if r["variant"] == "unequal_angles"]
    return {"equal_n": len(eq), "equal_max_abs_dev": max(abs(x - 1) for x in eq), "unequal_n": len(un),
            "unequal_max": max(un), "pass": max(abs(x - 1) for x in eq) <= 1e-9 and max(un) <= 1 + 1e-10}


def h3_table(recs):
    ok_label = all(r["label"] == "EXPECTED_VIOLATION_NEGATIVE_CONTROL" for r in recs)
    rel = [abs(r["ratio_obs_to_BR"] - r["analytic_ratio"]) / r["analytic_ratio"] for r in recs]
    flags = all(r["validator_flag"] for r in recs)
    return {"n": len(recs), "all_labelled": ok_label, "max_rel_err_vs_analytic": max(rel), "all_validators_flag": flags,
            "pass": ok_label and max(rel) <= 1e-9 and flags}


def h4_table(recs):
    groups = defaultdict(list)
    for r in recs:
        groups[(r["variant"], r["n"], r["chi"], r["seed"], r["rank"])].append(r)
    argmin_eta, argmin_E, same, rhos = defaultdict(int), defaultdict(int), 0, []
    per_topology = defaultdict(lambda: {"eta": [], "E": [], "ratio": []})
    for g, rs in groups.items():
        e = min(rs, key=lambda r: r["eta_hat"]); f = min(rs, key=lambda r: r["E_obs"])
        tk = lambda r: "random" if r["topology"].startswith("random") else r["topology"]
        argmin_eta[tk(e)] += 1; argmin_E[tk(f)] += 1; same += e["topology"] == f["topology"]
        rho = spearman([r["eta_hat"] for r in rs], [r["E_obs"] for r in rs])
        if rho is not None:
            rhos.append(rho)
        for r in rs:
            t = "random" if r["topology"].startswith("random") else r["topology"]
            per_topology[t]["eta"].append(r["eta_hat"]); per_topology[t]["E"].append(r["E_obs"] / max(r["F_norm"], 1e-300))
            per_topology[t]["ratio"].append(r["ratio_obs_to_BR"])
    return {"groups": len(groups), "argmin_eta_hat_by_topology": dict(argmin_eta), "argmin_E_by_topology": dict(argmin_E),
            "argmin_eta_equals_argmin_E_fraction": same / len(groups),
            "spearman_eta_vs_E_within_group_median": q(rhos, 0.5),
            "per_topology_medians": {t: {"eta_hat": q(v["eta"], 0.5), "E_rel": q(v["E"], 0.5), "ratio": q(v["ratio"], 0.5)}
                                     for t, v in per_topology.items()},
            "note": "cost proxy (n-1) r chi^2 is identical across bracketings, so the equal-cost comparison is per group"}


def h5_table(recs):
    best = [r for r in recs if r.get("is_best_restart")]
    rows = []
    for r in best:
        near_sharp = (r["label"] in VALID and r["ratio_obs_to_BR"] >= 0.9 and r["chi"] == 3 and r["d_span"] == 3
                      and r["M_gap_rel"] <= 1e-2)
        rows.append({"variant": r["variant"], "topology": r["topology"], "k": r["k_param"], "chi": r["chi"], "rank": r["rank"],
                     "ratio_rigorous": r["ratio_obs_to_BR"], "ratio_est": r["ratio_est"], "M_up": r["M_up"], "M_low": r["M_low"],
                     "M_gap_rel": r["M_gap_rel"], "d_span": r["d_span"], "eta_hat": r["eta_hat"],
                     "near_sharp_non_witness": near_sharp,
                     "estimate_only": (r["ratio_est"] >= 0.9 and r["ratio_obs_to_BR"] < 0.9)})
    best_by_topology = {}
    for v in ("coiso", "opnorm"):
        for t in ("chain", "balanced", "star", "random"):
            rs = [x for x in rows if x["variant"] == v and x["topology"] == t]
            if rs:
                best_by_topology[f"{v}/{t}"] = {"ratio_rigorous_max": max(x["ratio_rigorous"] for x in rs),
                                                "ratio_est_max": max(x["ratio_est"] for x in rs),
                                                "near_sharp_non_witness_configs": sum(x["near_sharp_non_witness"] for x in rs)}
    return {"configs": rows, "best_by_variant_topology": best_by_topology,
            "near_sharp_non_witness_total": sum(x["near_sharp_non_witness"] for x in rows)}


def eta_c(k):
    ts = np.linspace(1e-6, math.pi / 2, 40001)
    return math.sin(float(ts[int(np.argmax([cert.g(t, k - 1) for t in ts]))]))


def h6_table(recs):
    out = {}
    for t in ("chain", "balanced"):
        for k in sorted({r["k_param"] for r in recs}):
            rs = [r for r in recs if r["topology"] == t and r["k_param"] == k and r["label"] in VALID]
            if not rs:
                continue
            curve = []
            for et in sorted({r["eta_target"] for r in rs}):
                feas = [r for r in rs if r["eta_target"] == et and r["eta_hat"] <= et * (1 + 1e-3) + 1e-6]
                b = max(feas, key=lambda r: r["E_obs"]) if feas else None
                curve.append({"eta_target": et, "feasible_restarts": len(feas), "E_best": b["E_obs"] if b else None,
                              "eta_hat": b["eta_hat"] if b else None, "G_k_eta_target": cert.G_k(k, et),
                              "M_hat": b["M_hat"] if b else None})
            ec = eta_c(k)
            Es = [c["E_best"] for c in curve if c["E_best"] is not None]
            monotone = all(Es[i + 1] >= Es[i] * (1 - 1e-3) for i in range(len(Es) - 1))
            above = [c["E_best"] for c in curve if c["eta_target"] >= ec and c["E_best"] is not None]
            flat = (max(above) - min(above)) / max(above) <= 0.02 if len(above) >= 2 else None
            out[f"{t}/k{k}"] = {"eta_c": ec, "G_k_eta_c": cert.G_k(k, min(ec, 1.0)), "curve": curve,
                                "non_decreasing": monotone, "flat_within_2pct_above_eta_c": flat}
    return out


def h7_table(data):
    out = {}
    for c, r_max in LARGEST_RANK.items():
        if c not in data:
            continue
        rs = [r for r in data[c] if r["rank"] == r_max and r["label"] in VALID and r["F_norm"] > 0]
        rel = [r["B_R"] / r["F_norm"] for r in rs]
        relf = [r["B_R_full"] / r["F_norm"] for r in rs if r.get("B_R_full") is not None]
        allr = [r["B_R"] / r["F_norm"] for r in data[c] if r["label"] in VALID and r["F_norm"] > 0]
        out[c] = {"largest_rank": r_max, "runs": len(rs), "fraction_BR_over_F_lt_1": sum(x < 1 for x in rel) / len(rel) if rel else None,
                  "median_BR_over_F": q(rel, 0.5), "fraction_BR_full_over_F_lt_1": sum(x < 1 for x in relf) / len(relf) if relf else None,
                  "fraction_all_ranks_BR_over_F_lt_1": sum(x < 1 for x in allr) / len(allr) if allr else None,
                  "median_E_over_F": q([r["E_obs"] / r["F_norm"] for r in rs], 0.5),
                  "pass_50pct": (sum(x < 1 for x in rel) / len(rel) >= 0.5) if rel else None}
    return out


def h8_table(data):
    out = {}
    for c, recs in data.items():
        if c in ("F8",):
            continue
        rs = [r for r in recs if r["label"] in VALID and r["B_naive"] > 0]
        if not rs:
            continue
        keta = np.array([r["k"] * r["eta_hat"] for r in rs]); gain = np.array([r["gain_BR_over_naive"] for r in rs])
        bins = [0, 0.5, 1, 2, 4, 8, 1e9]
        out[c] = {"gain_median": q(list(gain), 0.5), "gain_min": float(gain.min()),
                  "by_k_eta_bin": {f"[{bins[i]},{bins[i+1]})": q(list(gain[(keta >= bins[i]) & (keta < bins[i + 1])]), 0.5)
                                   for i in range(len(bins) - 1)}}
    return out


def figures(data, figdir, h6):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    figdir.mkdir(parents=True, exist_ok=True)
    rng = np.random.default_rng(0)
    fams = [c for c in data if c not in ("F8", "F7R")]

    # 1. (k, eta) plane coloured by ratio
    fig, axes = plt.subplots(1, len(fams), figsize=(3.2 * len(fams), 3.2), sharey=True, squeeze=False)
    for ax, c in zip(axes[0], fams):
        rs = [r for r in data[c] if r["label"] in VALID]
        if len(rs) > 4000:
            rs = [rs[i] for i in rng.choice(len(rs), 4000, replace=False)]
        k = np.array([r["k"] for r in rs]) + rng.uniform(-0.3, 0.3, len(rs))
        sc = ax.scatter(k, [r["eta_hat"] for r in rs], c=[r["ratio_obs_to_BR"] for r in rs], s=4, cmap="viridis", vmin=0, vmax=1)
        ax.set_title(c); ax.set_xlabel("k")
    axes[0][0].set_ylabel("eta_hat")
    fig.colorbar(sc, ax=axes[0].tolist(), label="E_obs / B_R")
    fig.savefig(figdir / "fig1_k_eta_ratio.png", dpi=130, bbox_inches="tight"); plt.close(fig)

    # 2. F1 per bracketing
    if "F1" in data:
        tops = ["left", "right", "balanced", "random"]
        fig, axes = plt.subplots(1, 3, figsize=(11, 3.2))
        for ax, key, lab in zip(axes, ["eta_hat", "E_rel", "ratio_obs_to_BR"], ["eta_hat", "E_obs/||F||", "E_obs/B_R"]):
            vals = []
            for t in tops:
                rs = [r for r in data["F1"] if (r["topology"].startswith(t)) and r["F_norm"] > 0]
                vals.append([r["E_obs"] / r["F_norm"] if key == "E_rel" else r[key] for r in rs])
            ax.boxplot(vals, showfliers=False); ax.set_xticks(range(1, 5), tops); ax.set_ylabel(lab)
            if key != "eta_hat":
                ax.set_yscale("log")
        fig.tight_layout(); fig.savefig(figdir / "fig2_F1_bracketing.png", dpi=130); plt.close(fig)

    # 3. gain vs k eta
    fig, ax = plt.subplots(figsize=(5, 3.5))
    for c in fams:
        rs = [r for r in data[c] if r["label"] in VALID and r["B_naive"] > 0]
        if len(rs) > 3000:
            rs = [rs[i] for i in rng.choice(len(rs), 3000, replace=False)]
        ax.scatter([r["k"] * r["eta_hat"] for r in rs], [r["gain_BR_over_naive"] for r in rs], s=3, label=c, alpha=0.6)
    ax.set_xscale("log"); ax.set_xlabel("k * eta_hat"); ax.set_ylabel("B_R / B_naive"); ax.legend(markerscale=3, fontsize=7)
    fig.tight_layout(); fig.savefig(figdir / "fig3_gain.png", dpi=130); plt.close(fig)

    # 4. deflation histograms
    fig, ax = plt.subplots(figsize=(5, 3.5))
    for c in fams:
        d = [r["deflation"] for r in data[c] if r["label"] in VALID and r["deflation"] > 0]
        ax.hist(np.log10(d), bins=60, histtype="step", label=c, density=True)
    ax.set_xlabel("log10 deflation ||F_r|| / (M^k L)"); ax.legend(fontsize=7)
    fig.tight_layout(); fig.savefig(figdir / "fig4_deflation.png", dpi=130); plt.close(fig)

    # 5. F1 cost vs certificate
    if "F1" in data:
        fig, ax = plt.subplots(figsize=(5, 3.5))
        rs = [r for r in data["F1"] if r["F_norm"] > 0]
        ax.scatter([r["cost_proxy_factored"] for r in rs], [r["B_R"] / r["F_norm"] for r in rs], s=3, alpha=0.3, label="B_R/||F||")
        ax.scatter([r["cost_proxy_factored"] for r in rs], [max(r["E_obs"], 1e-18) / r["F_norm"] for r in rs], s=3, alpha=0.3, label="E_obs/||F||")
        ax.set_xscale("log"); ax.set_yscale("log"); ax.set_xlabel("cost proxy (n-1) r chi^2"); ax.legend(fontsize=7, markerscale=3)
        fig.tight_layout(); fig.savefig(figdir / "fig5_F1_cost.png", dpi=130); plt.close(fig)

    # 6. H6 regime curves
    if h6:
        fig, ax = plt.subplots(figsize=(5, 3.5))
        for key, v in h6.items():
            cur = [c for c in v["curve"] if c["E_best"] is not None]
            line, = ax.plot([c["eta_target"] for c in cur], [c["E_best"] for c in cur], "o-", ms=3, label=key)
            et = np.linspace(0.02, 1, 60)
            ax.plot(et, [cert.G_k(int(key.split("k")[1]), e) for e in et], "--", color=line.get_color(), lw=0.8)
            ax.axvline(v["eta_c"], color=line.get_color(), lw=0.5, ls=":")
        ax.set_xlabel("eta target"); ax.set_ylabel("max E_obs (M = L = 1)"); ax.legend(fontsize=6)
        fig.tight_layout(); fig.savefig(figdir / "fig6_F7R_regime.png", dpi=130); plt.close(fig)


def main():
    date = sys.argv[1] if len(sys.argv) > 1 else "2026-09-13"
    base = ROOT / "artifacts" / "pmt_tn_benchmark" / f"{date}-v1"
    data, hashes = load(base)
    tables = {"inputs_sha256": hashes, "H1": h1_table(data)}
    if "F6" in data:
        tables["H2"] = h2_table(data["F6"])
    if "F8" in data:
        tables["H3"] = h3_table(data["F8"])
    if "F1" in data:
        tables["H4"] = h4_table(data["F1"])
    if "F7" in data:
        tables["H5"] = h5_table(data["F7"])
    h6 = h6_table(data["F7R"]) if "F7R" in data else {}
    tables["H6"] = h6
    tables["H7"] = h7_table(data)
    tables["H8"] = h8_table(data)
    out = base / "analysis"
    out.mkdir(exist_ok=True)
    with open(out / "tables.json", "w", encoding="utf-8", newline="\n") as fh:
        json.dump(tables, fh, indent=1)
    figures(data, out / "figures", h6)
    hs = {p.relative_to(out).as_posix(): hashlib.sha256(p.read_bytes()).hexdigest()
          for p in sorted(out.rglob("*")) if p.is_file() and p.name != "artifact_hashes.json"}
    with open(out / "artifact_hashes.json", "w", encoding="utf-8", newline="\n") as fh:
        json.dump(hs, fh, indent=1)
    print(json.dumps({k: v for k, v in tables.items() if k in ("H1", "H2", "H3", "H7")}, indent=1))


if __name__ == "__main__":
    main()
