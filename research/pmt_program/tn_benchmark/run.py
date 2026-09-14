"""PMT-TN benchmark V1 runner: evaluates instances, applies the certificate, writes artifacts.

usage: python run.py FAMILY [--quick]
Artifacts: artifacts/pmt_tn_benchmark/<date>-v1/<FAMILY>/{runs.jsonl, run_manifest.json,
final_metrics.json, artifact_hashes.json, replay/}. Existing directories are never overwritten.
"""
from __future__ import annotations

import datetime as dt
import hashlib
import json
import os
import math
import platform
import subprocess
import sys
import time
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
sys.path.insert(0, str(HERE))

import certificate as cert  # noqa: E402
from pmt_eval import evaluate, check_projector_orthogonal  # noqa: E402


def git_commit() -> str:
    try:
        return subprocess.run(["git", "rev-parse", "HEAD"], cwd=ROOT, capture_output=True, text=True).stdout.strip()
    except Exception:
        return "unknown"


def per_node_angle_expression(eta_nodes: dict) -> float:
    """Exploratory (not a certificate): |1 - prod_v cos th_v e^{i th_v}| with sin th_v = eta_v."""
    z = 1.0 + 0j
    for v, e in eta_nodes.items():
        e = min(max(e, 0.0), 1.0)
        th = math.asin(e)
        z *= math.cos(th) * complex(math.cos(th), math.sin(th))
    return abs(1 - z)


def run_instance(inst: dict, rng) -> dict:
    out = evaluate(inst["nodes"], inst["root"])
    checks = {}
    if inst.get("check_projectors", True):
        worst = {"idempotence_defect": 0.0, "symmetry_defect": 0.0, "orthogonal": True}
        for v, nd in inst["nodes"].items():
            if nd.is_root:
                continue
            shape = nd.extra.get("output_shape")
            if shape is None:
                continue
            chk = check_projector_orthogonal(out["projectors"][v], shape, rng, trials=4)
            worst["idempotence_defect"] = max(worst["idempotence_defect"], chk["idempotence_defect"])
            worst["symmetry_defect"] = max(worst["symmetry_defect"], chk["symmetry_defect"])
            worst["orthogonal"] = worst["orthogonal"] and chk["orthogonal"]
        checks["projectors"] = worst
    c = cert.certificate(out["k"], out["eta_hat"], out["M_hat"], out["leaf_product"], out["E_obs"],
                         out["F_norm"], inst["M_provenance"])
    label = cert.classify(c, inst.get("expected_violation", False))
    if checks.get("projectors") and not checks["projectors"]["orthogonal"] and not inst.get("expected_violation", False):
        label = "INVALID_PROJECTOR"
    rec = dict(inst["meta"])
    rec.update(c.to_dict())
    rec.update({"label": label, "checks": checks,
                "eta_full": inst.get("eta_full"),
                "B_R_full": (cert.G_k(out["k"], min(max(inst["eta_full"], 1e-300), 1.0)) * out["M_hat"] ** out["k"] * out["leaf_product"])
                if inst.get("eta_full") is not None and out["k"] > 1 else None,
                "per_node_angle_expression_exploratory": per_node_angle_expression(
                    {v: e for v, e in out["eta_nodes"].items() if not out["records"][v]["is_root"]}),
                "eta_nodes_max_min": [max(out["eta_nodes"].values()), min(out["eta_nodes"].values())]})
    if label == "REPLAY_TRIGGERED" and "replay" in inst:
        rec["replay"] = inst["replay"](out, c)
    return rec


def summarize(records: list) -> dict:
    labels = {}
    for r in records:
        labels[r["label"]] = labels.get(r["label"], 0) + 1
    valid = [r for r in records if r["label"] in ("WITHIN_CERTIFICATE", "REPLAY_TRIGGERED")]
    ratios = [r["ratio_obs_to_BR"] for r in valid if math.isfinite(r["ratio_obs_to_BR"])]
    gains = [r["gain_BR_over_naive"] for r in valid if r["B_naive"] > 0]
    relcert = [r["relative_certificate"] for r in valid if math.isfinite(r["relative_certificate"])]
    q = lambda xs, p: float(np.quantile(xs, p)) if xs else None
    return {"n_runs": len(records), "labels": labels,
            "ratio_max": max(ratios) if ratios else None, "ratio_median": q(ratios, 0.5),
            "min_slack_1_minus_ratio": (1 - max(ratios)) if ratios else None,
            "gain_median": q(gains, 0.5), "gain_min": min(gains) if gains else None,
            "relative_certificate_median": q(relcert, 0.5),
            "fraction_relative_certificate_lt_1": (sum(x < 1 for x in relcert) / len(relcert)) if relcert else None,
            "deflation_median": q([r["deflation"] for r in valid], 0.5),
            "eta_hat_median": q([r["eta_hat"] for r in valid], 0.5),
            "k_range": [min(r["k"] for r in records), max(r["k"] for r in records)] if records else None}


def main():
    family = sys.argv[1]
    quick = "--quick" in sys.argv
    import importlib
    mod = importlib.import_module({"F1": "families_f1", "F2": "families_f2", "F3": "families_f3",
                                   "F4": "families_f4", "F6": "families_controls_runs",
                                   "F8": "families_controls_runs"}[family])
    date = dt.date.today().isoformat()
    base = Path(os.environ["PMT_TN_OUT"]) if os.environ.get("PMT_TN_OUT") else ROOT / "artifacts" / "pmt_tn_benchmark"
    outdir = base / f"{date}-v1" / (family + ("-quick" if quick else ""))
    if outdir.exists():
        raise SystemExit(f"refusing to overwrite {outdir}")
    outdir.mkdir(parents=True)
    rng = np.random.default_rng(20260914)
    t0 = time.time()
    records = []
    with open(outdir / "runs.jsonl", "w", encoding="utf-8", newline="\n") as fh:
        for inst in mod.instances(family, quick=quick):
            rec = run_instance(inst, rng)
            records.append(rec)
            fh.write(json.dumps(rec) + "\n")
    summary = summarize(records)
    summary["family"] = family
    summary["seconds"] = time.time() - t0
    manifest = {"benchmark": "PMT_TN_BENCHMARK_V1", "family": family, "quick": quick,
                "command": " ".join(sys.argv), "git_commit": git_commit(), "date": date,
                "python": sys.version, "numpy": np.__version__, "platform": platform.platform(),
                "preregistration": "research/pmt_program/tn_benchmark/PREREGISTRATION_PMT_TN_V1.md"}
    for name, obj in (("run_manifest.json", manifest), ("final_metrics.json", summary)):
        with open(outdir / name, "w", encoding="utf-8", newline="\n") as fh:
            json.dump(obj, fh, indent=1)
    hashes = {p.name: hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(outdir.iterdir()) if p.is_file()}
    with open(outdir / "artifact_hashes.json", "w", encoding="utf-8", newline="\n") as fh:
        json.dump(hashes, fh, indent=1)
    print(json.dumps(summary, indent=1))


if __name__ == "__main__":
    main()
