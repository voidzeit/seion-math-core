"""Reproduce canonical controls and execute a bounded, seeded CPU k4 study."""

from __future__ import annotations

import argparse
from datetime import datetime, timezone
import hashlib
import importlib.metadata
import json
import math
import os
from pathlib import Path
import platform
import shutil
import subprocess
import sys
import warnings

import numpy as np

from seion_core.pmt import (chain_w3_extremizer, branching_w3_extremizer,
                            evaluate_pmt, projected_closure_bracket, w3)
from seion_core.pmt.chain import audit_chain, chain_as_pmt, evaluate_chain, planar_chain
from seion_core.pmt.phase import gated_phase_tree
from research.math_closure.k4_exploration.chain_analysis import chain4_formula
from research.math_closure.k4_exploration.chain_gram_sdp import solve_chain_sdp
from research.math_closure.k4_exploration.chain_search import search_chain

ROOT = Path(__file__).resolve().parents[1]


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def dump(path, value):
    path.write_text(json.dumps(value, indent=2, allow_nan=False)+"\n", encoding="utf-8")


def git(*args):
    return subprocess.check_output(["git", *args], cwd=ROOT, text=True).strip()


def reproduce(config):
    controls = []
    for eta in config["etas"]:
        aa, pp, x = planar_chain([eta])
        model, leaves = chain_as_pmt(aa, pp, x)
        controls.append({"contract": "C2", "eta": eta,
                         "observed": evaluate_pmt(model, leaves).errors.projected/eta,
                         "expected": 1., "audit": audit_chain(aa, pp, x, eta)})
        for name, builder in [("M14_chain", chain_w3_extremizer), ("M15_branch", branching_w3_extremizer)]:
            witness = builder(eta)
            controls.append({"contract": name, "eta": eta,
                             "observed": witness.evaluate().errors.projected/eta,
                             "expected": w3(eta)})
        for k in (2, 3, 4, 6):
            shape = None
            for j in range(k):
                shape = (shape, None) if j % 2 == 0 else (shape, None, None)
            model, leaves = gated_phase_tree(shape, eta)
            controls.append({"contract": "M19_gated_ambient_leaves", "k": k, "eta": eta,
                             "observed": evaluate_pmt(model, leaves).errors.projected,
                             "expected": abs(math.sin((k-1)*math.asin(eta)))})
    negative = {"contract": "ungated_M18_M19_under_canonical_ambient_leaves",
                "eta": .2, "trajectory_defect": .2,
                "global_bottom_defect": float(np.linalg.norm(np.array([[.2, math.sqrt(.96)],
                                                                       [math.sqrt(.96), -.2]]), 2)),
                "status": "REJECTED_INADMISSIBLE", "historical_evidence_preserved": True}
    return controls, negative


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", default="experiments/configs/PMT_K4_CHAIN_GRAM_V1.json")
    parser.add_argument("--output", required=True)
    args = parser.parse_args()
    config_path = ROOT/args.config
    config = json.loads(config_path.read_text(encoding="utf-8"))
    out = ROOT/args.output
    out.mkdir(parents=True, exist_ok=False)
    dump(out/"config.json", config)
    sources = [Path(__file__), config_path]
    for directory in [ROOT/"src/seion_core/pmt", ROOT/"src/seion_core/research_v3",
                      ROOT/"research/math_closure/k4_exploration", ROOT/"tests/pmt"]:
        sources += sorted(directory.glob("*.py"))
    sources += [ROOT/"research/math_closure/k4_exploration/CHAIN_GRAM_REPORT.md",
                ROOT/"papers/projected_multilinear_trees/CANONICAL_FORMALIZATION.md"]
    manifest = {"run_id": out.name, "created_utc": datetime.now(timezone.utc).isoformat(),
                "command": subprocess.list2cmdline([sys.executable, *sys.argv]),
                "branch": git("branch", "--show-current"), "commit": git("rev-parse", "HEAD"),
                "dirty_worktree": git("status", "--porcelain"), "python": sys.version,
                "platform": platform.platform(), "device": "cpu", "precision": "float64",
                "packages": {name: importlib.metadata.version(name) for name in
                             ["numpy", "scipy", "cvxpy", "clarabel", "sympy", "pytest", "PyYAML"]},
                "thread_environment": {key: os.environ.get(key) for key in ["OPENBLAS_NUM_THREADS", "OMP_NUM_THREADS"]},
                "source_hashes": {str(p.relative_to(ROOT)).replace("\\", "/"): digest(p) for p in sources},
                "status": "RUNNING", "authority": "observed"}
    for source in sources:
        snapshot = out/"source_snapshot"/source.relative_to(ROOT)
        snapshot.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(source, snapshot)
    dump(out/"run_manifest.json", manifest)
    try:
        controls, negative = reproduce(config)
        dump(out/"reproduction.json", {"controls": controls, "negative_control": negative})
        candidates = []
        for eta in config["etas"]:
            for dim, rank in config["dimensions_ranks"]:
                for seed in config["seeds"]:
                    candidate = search_chain(eta, dim, rank, seed, config["max_iterations"],
                                             config.get("optimizer", "SLSQP"))
                    candidates.append(candidate)
                    # Incremental preservation includes failed/nonconverged optimizer exits.
                    dump(out/"candidates.json", candidates)
            print(f"search eta={eta:.6g} completed", flush=True)
        sdps = []
        for n in (1, 2, 3):
            for eta in config["etas"]:
                with warnings.catch_warnings(record=True) as caught:
                    warnings.simplefilter("always")
                    row = solve_chain_sdp(eta, n, config["sdp_solver"])
                row["warnings"] = [str(w.message) for w in caught]
                sdps.append(row)
                dump(out/"sdp.json", sdps)
        witnesses = []
        for eta in sorted(set(config["etas"]+config["asymptotic_etas"])):
            t = min(eta, math.sqrt(3/7))
            aa, pp, x = planar_chain([t]*3)
            tr = evaluate_chain(aa, pp, x)
            model, leaves = chain_as_pmt(aa, pp, x)
            witnesses.append({"eta": eta, "effective_leakage": t,
                              "construction_status": "CERTIFIED_WITNESS",
                              "certificate_basis": "explicit analytic family, report section 6",
                              "approval_status": "PENDING_INDEPENDENT_REVIEW",
                              "floating_audit": audit_chain(aa, pp, x, eta),
                              "typed_projected_error": evaluate_pmt(model, leaves).errors.projected,
                              "target_normalized": chain4_formula(eta),
                              "phase_reference_normalized": abs(math.sin(3*math.asin(eta)))/eta,
                              "second_order_quotient": (3-chain4_formula(eta))/eta**2,
                              "source_gram_at_stage3": tr.grams[2].tolist(),
                              "operators": [a.tolist() for a in aa]})
        dump(out/"analytic_witnesses.json", witnesses)
        metrics = {"reproduction_max_absolute_residual": max(abs(r["observed"]-r["expected"]) for r in controls),
                   "reproduction_control_count": len(controls), "candidate_count": len(candidates),
                   "candidate_optimizer_nonconverged_count": sum(not r["optimizer_success"] for r in candidates),
                   "candidate_inadmissible_after_global_rescale_count": sum(r["status"] != "NUMERICAL_CANDIDATE" for r in candidates),
                   "candidate_max_excess_over_formula": max(r["audit"]["normalized_error"]-chain4_formula(r["eta"]) for r in candidates),
                   "sdp_max_k4_formula_gap_absolute": max(abs(r["normalized_error"]-chain4_formula(r["eta"])) for r in sdps if r["active_stages"] == 3),
                   "sdp_warning_count": sum(bool(r["warnings"]) for r in sdps),
                   "sdp_minimum_psd_eigenvalue": min(v for r in sdps for s in r["stages"] for v in s["minimum_eigenvalues"]),
                   "finite_eta_sharpness_authority": "ADVISORY_ANALYTIC_PROOF_NOT_SOLVER_CERTIFICATION",
                   "topology_comparison": "OPEN; no equality inferred from chain"}
        dump(out/"final_metrics.json", metrics)
        dump(out/"certificate.json", {"status": "OBSERVED_WITH_ANALYTIC_PROOF_DRAFT",
                                     "proof_location": config["proof_report"],
                                     "numeric_status": "NUMERICAL_CANDIDATE",
                                     "interval_sdp_certificate": None,
                                     "novelty": "NOT_ESTABLISHED", "human_approval": False,
                                     "tolerance": config["tolerance"],
                                     "reproduction_pass": metrics["reproduction_max_absolute_residual"] < config["tolerance"]})
        manifest["status"] = "COMPLETE"
    except Exception as exc:
        manifest["status"] = "FAILED_RUNTIME"
        dump(out/"failure.json", {"type": type(exc).__name__, "message": str(exc)})
        raise
    finally:
        manifest["finished_utc"] = datetime.now(timezone.utc).isoformat()
        dump(out/"run_manifest.json", manifest)
        dump(out/"artifact_hashes.json", {str(p.relative_to(out)).replace("\\", "/"): digest(p)
                                        for p in sorted(out.rglob("*"))
                                        if p.is_file() and p.name != "artifact_hashes.json"})
    print(json.dumps(metrics, indent=2))


if __name__ == "__main__":
    main()
