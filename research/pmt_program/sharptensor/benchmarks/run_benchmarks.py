"""Confirmatory SharpTensor 0.1 benchmarks (preregistered in ``prereg_config.json``).

Usage (from the repository root)::

    py -3.12 -m research.pmt_program.sharptensor.benchmarks.run_benchmarks

The script refuses to run if the SHA-256 of ``prereg_config.json`` differs from ``FREEZE.json``.
Results are written to ``results/benchmarks_v1.json`` and ``results/BENCHMARK_REPORT_v1.md``.
"""

from __future__ import annotations

import hashlib
import json
import math
import platform
import sys
import time
from pathlib import Path

import numpy as np

from ..certificate import certify
from ..models import HTTree, MatProdTree, MpoMpsChain
from ..planner import plan_certified_search, plan_theorem_r

HERE = Path(__file__).resolve().parent
MODELS = {"MatProdTree": MatProdTree, "MpoMpsChain": MpoMpsChain, "HTTree": HTTree}


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def summarise(res, cert):
    run = res.run
    lam = cert["theorem_r"].get("lambda_T")
    r_norm = cert["R_root_norm"]
    return {
        "ranks": {n.name: n.rank for n in run.nodes},
        "stored_bytes": res.accounting.stored,
        "counted_flops": res.accounting.flops,
        "wall_seconds": res.seconds,
        "actual_error": res.actual_error,
        "bounds": cert["bounds"],
        "best": cert["best"],
        "best_bound": cert["absolute_error_upper"],
        "relative_error_upper": cert["relative_error_upper"],
        "relative_by_certificate": cert["relative_by_certificate"],
        "tightness": cert.get("tightness"),
        "sound": cert.get("sound"),
        "sound_each": {k: bool(res.actual_error <= v * (1 + 1e-9) + 1e-12) for k, v in cert["bounds"].items()},
        "prod_M": cert["theorem_r"].get("prod_M"),
        "lambda_T": lam,
        "R_root_norm": r_norm,
        "R_root_over_Lambda_T": (r_norm / lam) if lam else None,
        "gbox": {k: cert["theorem_r"].get(k) for k in ("gbox_lower", "gbox_upper", "sum_eta")},
    }


def m_tightness(model):
    if isinstance(model, MatProdTree):
        lower = model.M_lower_estimate()
        return {"M_bound": 1.0, "M_lower_estimate": lower, "ratio": 1.0 / lower if lower > 0 else math.inf}
    if isinstance(model, MpoMpsChain):
        return {"M_bound": 1.0, "M_lower_estimate": 1.0, "ratio": 1.0,
                "note": "contraction over one index attains 1 on rank-one unit inputs"}
    if isinstance(model, HTTree):
        out = {}
        for name in model.internal:
            b = model.M_bound(name)
            lo = model.M_lower_estimate(name)
            out[name] = {"M_bound": b, "M_lower_estimate": lo, "ratio": b / lo if lo > 0 else math.inf}
        return out
    return {}


def jsonable(x):
    if isinstance(x, dict):
        return {str(k): jsonable(v) for k, v in x.items()}
    if isinstance(x, (list, tuple)):
        return [jsonable(v) for v in x]
    if isinstance(x, float):
        if math.isinf(x):
            return "inf"
        if math.isnan(x):
            return "nan"
        return x
    if isinstance(x, (np.floating,)):
        return jsonable(float(x))
    if isinstance(x, (np.integer,)):
        return int(x)
    return x


def main():
    cfg_path = HERE / "prereg_config.json"
    freeze = json.loads((HERE / "FREEZE.json").read_text(encoding="utf-8"))
    digest = sha256(cfg_path)
    if digest != freeze["prereg_config.json"]:
        sys.exit(f"prereg_config.json hash mismatch: {digest} != {freeze['prereg_config.json']}")
    cfg = json.loads(cfg_path.read_text(encoding="utf-8"))
    code = {f.name: sha256(f) for f in sorted((HERE.parent).glob("*.py"))}
    out = {"config_sha256": digest, "code_sha256": code, "python": sys.version.split()[0], "numpy": np.__version__,
           "platform": platform.platform(), "started": time.strftime("%Y-%m-%dT%H:%M:%S"), "benchmarks": {}}
    for b in cfg["benchmarks"]:
        t0 = time.perf_counter()
        model = MODELS[b["model"]](**b["params"])
        full = model.execute(None)
        cfull = certify(full.run, tol=cfg["tol_gbox"], actual_error=full.actual_error)
        entry = {"role": b["role"], "params": b["params"], "full": summarise(full, cfull),
                 "M_tightness": m_tightness(model), "sweep": {}, "planners": {}}
        if isinstance(model, MatProdTree):
            dense = model.dense_cost()
            entry["dense_uncompressed"] = {"stored_bytes": dense.stored, "counted_flops": dense.flops}
        r_full = cfull["R_root_norm"]
        for f in cfg["rank_fractions"]:
            ranks = {n: max(1, math.ceil(f * full.full_ranks[n])) for n in model.internal}
            res = model.execute(ranks)
            cert = certify(res.run, tol=cfg["tol_gbox"], actual_error=res.actual_error)
            entry["sweep"][str(f)] = summarise(res, cert)
        for delta in cfg["planner_deltas"]:
            eps = delta * r_full
            a = plan_theorem_r(model, eps)
            s = plan_certified_search(model, eps, which="best")
            entry["planners"][str(delta)] = {
                "eps": eps,
                "theorem_r": {"met": a["met"], "iterations": len(a["history"]), **summarise(a["result"], a["certificate"])},
                "certified_search": {"met": s["met"], "steps": s["steps"], **summarise(s["result"], s["certificate"])},
            }
        sd = str(cfg["success_delta"])
        plan = entry["planners"][sd]["certified_search"]
        rel = plan["relative_error_upper"]
        entry["success"] = {
            "S1_memory": plan["stored_bytes"] < entry["full"]["stored_bytes"],
            "S2_compute": plan["counted_flops"] < entry["full"]["counted_flops"],
            "S3_non_vacuous": isinstance(rel, float) and rel <= 1.0,
            "memory_ratio": entry["full"]["stored_bytes"] / plan["stored_bytes"],
            "flops_ratio": entry["full"]["counted_flops"] / plan["counted_flops"],
        }
        all_sound = all(v["sound"] for v in entry["sweep"].values()) and all(
            p[k]["sound"] for p in entry["planners"].values() for k in ("theorem_r", "certified_search"))
        entry["all_runs_sound"] = all_sound and entry["full"]["sound"]
        entry["seconds"] = time.perf_counter() - t0
        out["benchmarks"][b["id"]] = entry
        print(b["id"], "done", f"{entry['seconds']:.1f}s", entry["success"], "sound", entry["all_runs_sound"], flush=True)
    required = ["B1a", "B2", "B3"]
    out["TRL4_criterion_met"] = all(all(out["benchmarks"][i]["success"][k] for k in ("S1_memory", "S2_compute", "S3_non_vacuous"))
                                    for i in required)
    out["finished"] = time.strftime("%Y-%m-%dT%H:%M:%S")
    res_dir = HERE / "results"
    res_dir.mkdir(exist_ok=True)
    (res_dir / "benchmarks_v1.json").write_text(json.dumps(jsonable(out), indent=2), encoding="utf-8")
    print("TRL4 criterion met:", out["TRL4_criterion_met"])


if __name__ == "__main__":
    main()
