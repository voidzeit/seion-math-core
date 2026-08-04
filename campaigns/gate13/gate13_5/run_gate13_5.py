"""Gate 13.5 orchestrator (``campaigns/gate13/gate13_5/preregistration.md``).

Invokes the real ``python -m seion_kgr.train`` CLI in sequence for the
frozen A0-A3 ablation matrix -- not a bespoke reimplementation of training,
the same entrypoint a manual campaign would call (precedent:
``tests/kgr/test_gate13_3b_attribution_real_run.py``'s docstring). Chains
``--init_from_checkpoint`` so A1/A2/A3 start from that seed's A0 weights,
and always passes ``--skip_test_eval`` for Stage 3/4 (test-set discipline,
preregistration.md sec10) -- the separate ``evaluate-test-frozen`` stage
opens test exactly once, over the frozen best checkpoints, after all
Stage 4 runs and their best-epoch selection are complete.

Usage (from repo root)::

    python campaigns/gate13/gate13_5/run_gate13_5.py static-validation
    python campaigns/gate13/gate13_5/run_gate13_5.py smoke
    python campaigns/gate13/gate13_5/run_gate13_5.py pilot
    python campaigns/gate13/gate13_5/run_gate13_5.py full
    python campaigns/gate13/gate13_5/run_gate13_5.py evaluate-test-frozen
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import subprocess
import sys
import time
from pathlib import Path
from typing import Any, Dict, List, Optional

CAMPAIGN_DIR = Path(__file__).resolve().parent
REPO_ROOT = CAMPAIGN_DIR.parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))  # this script lives under campaigns/, not the seion_kgr package
RUNS_DIR = CAMPAIGN_DIR / "runs"
REGISTRY_PATH = CAMPAIGN_DIR / "run_registry.csv"
FREEZE_PATH = CAMPAIGN_DIR / "configuration_freeze.json"

FB_DIR = REPO_ROOT / "data" / "FB15K-237"
WN_DIR = REPO_ROOT / "data" / "WN18RR"

REGISTRY_FIELDS = [
    "execution_id", "config_id", "seed", "stage", "commit_sha", "configuration_id",
    "dataset_train_sha256", "dataset_valid_sha256", "dataset_test_sha256",
    "checkpoint_sha256", "evaluator_identity", "environment_path", "out_dir",
    "wall_sec", "gpu_peak_mb", "status", "test_eval_skipped", "started_utc",
]

MATRIX = {
    "A0": {"enable_path": False, "enable_seion": False},
    "A1": {"enable_path": True, "enable_seion": False},
    "A2": {"enable_path": False, "enable_seion": True},
    "A3": {"enable_path": True, "enable_seion": True},
}


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        while True:
            block = f.read(1 << 20)
            if not block:
                break
            h.update(block)
    return h.hexdigest()


def load_freeze() -> Dict[str, Any]:
    return json.loads(FREEZE_PATH.read_text())


def append_registry_row(row: Dict[str, Any]) -> None:
    is_new = not REGISTRY_PATH.is_file()
    with REGISTRY_PATH.open("a", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=REGISTRY_FIELDS)
        if is_new:
            writer.writeheader()
        writer.writerow({k: row.get(k, "") for k in REGISTRY_FIELDS})


def run_one(
    config_id: str,
    seed: int,
    out_dir: Path,
    stage: str,
    *,
    train_path: Path,
    valid_path: Path,
    test_path: Path,
    epochs: int,
    batch_size: int,
    dim: int,
    eval_max_queries: int,
    gate_g_max: float,
    init_from_checkpoint: Optional[Path] = None,
    skip_test_eval: bool = True,
    cpu: bool = False,
    extra_smoke_note: Optional[str] = None,
) -> Dict[str, Any]:
    freeze = load_freeze()
    cfg = MATRIX[config_id]
    if out_dir.exists() and any(out_dir.iterdir()):
        raise FileExistsError(f"{out_dir} already exists and is not empty -- refusing to silently reuse it")

    cmd = [
        sys.executable, "-m", "seion_kgr.train",
        "--train", str(train_path), "--valid", str(valid_path), "--test", str(test_path),
        "--out_dir", str(out_dir),
        "--dim", str(dim), "--base_expert", "tucker",
        "--batch_size", str(batch_size),
        "--entity_block_eval", str(freeze["entity_block_eval"]),
        "--neg_k", str(freeze["neg_k"]),
        "--adversarial_temperature", str(freeze["adversarial_temperature"]),
        "--n3_weight", str(freeze["n3_weight"]),
        "--lr", str(freeze["lr"]),
        "--weight_decay", str(freeze["weight_decay"]),
        "--grad_clip", str(freeze["grad_clip"]),
        "--router_lr_multiplier", str(freeze["router_lr_multiplier"]),
        "--epochs", str(epochs),
        "--eval_every", str(freeze["eval_every"]),
        "--eval_max_queries", str(eval_max_queries),
        "--eval_subset", str(freeze["eval_subset"]),
        "--gate_g_max", str(gate_g_max),
        "--seed", str(seed),
    ]
    if cfg["enable_path"]:
        cmd += [
            "--enable_path",
            "--path_backend", freeze["path_backend"],
            "--path_selector_mode", freeze["path_selector_mode"],
            "--path_rank", str(freeze["path_rank"]),
            "--path_layers", str(freeze["path_layers"]),
            "--path_max_neighbors", str(freeze["path_max_neighbors"]),
            "--path_proj_rank", str(freeze["path_proj_rank"]),
        ]
    if cfg["enable_seion"]:
        cmd += ["--enable_seion", "--seion_rank", str(freeze["seion_rank"])]
    if init_from_checkpoint is not None:
        cmd += ["--init_from_checkpoint", str(init_from_checkpoint)]
    if skip_test_eval:
        cmd += ["--skip_test_eval"]
    if cpu:
        cmd += ["--cpu"]

    print(f"[{stage}] {config_id} seed={seed} gate_g_max={gate_g_max} -> {out_dir}", flush=True)
    print(" ".join(cmd), flush=True)
    started = time.time()
    proc = subprocess.run(cmd, cwd=str(REPO_ROOT))
    wall = time.time() - started

    status = "COMPLETED" if proc.returncode == 0 else f"FAILED(returncode={proc.returncode})"
    run_manifest_path = out_dir / "run_manifest.json"
    final_metrics_path = out_dir / "final_metrics.json"
    execution_id = configuration_id = None
    gpu_peak_mb = wall_sec = None
    test_eval_skipped = skip_test_eval
    if run_manifest_path.is_file():
        rm = json.loads(run_manifest_path.read_text())
        execution_id = rm.get("execution_id")
        configuration_id = rm.get("configuration_id")
    if final_metrics_path.is_file():
        fm = json.loads(final_metrics_path.read_text())
        gpu_peak_mb = fm.get("gpu_peak_mb")
        wall_sec = fm.get("wall_sec")
        test_eval_skipped = fm.get("test_eval_skipped", skip_test_eval)
        if fm.get("status") == "COMPLETED" and proc.returncode == 0:
            status = "COMPLETED"

    best_ckpt = out_dir / "best.pt"
    checkpoint_sha256 = sha256_file(best_ckpt) if best_ckpt.is_file() else None

    row = {
        "execution_id": execution_id, "config_id": config_id, "seed": seed, "stage": stage,
        "commit_sha": None,  # filled by caller (git rev-parse at orchestration time, stable across the whole stage)
        "configuration_id": configuration_id,
        "dataset_train_sha256": sha256_file(train_path), "dataset_valid_sha256": sha256_file(valid_path),
        "dataset_test_sha256": sha256_file(test_path),
        "checkpoint_sha256": checkpoint_sha256,
        "evaluator_identity": "seion_kgr.evaluate.evaluate (blocked filtered evaluator)",
        "environment_path": str((out_dir / "environment.json").relative_to(REPO_ROOT)) if (out_dir / "environment.json").is_file() else None,
        "out_dir": str(out_dir.relative_to(REPO_ROOT)),
        "wall_sec": wall_sec if wall_sec is not None else wall,
        "gpu_peak_mb": gpu_peak_mb,
        "status": status,
        "test_eval_skipped": test_eval_skipped,
        "started_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime(started)),
    }
    return {"row": row, "returncode": proc.returncode, "out_dir": out_dir}


def git_commit_sha() -> str:
    return subprocess.run(
        ["git", "rev-parse", "HEAD"], cwd=str(REPO_ROOT), capture_output=True, text=True, check=True,
    ).stdout.strip()


# ---------------------------------------------------------------------------
# Stage 1: static validation (no GPU training)


def stage_static_validation() -> None:
    freeze = load_freeze()
    checks: List[Dict[str, Any]] = []

    def check(name: str, ok: bool, detail: str = "") -> None:
        checks.append({"name": name, "passed": bool(ok), "detail": detail})
        print(f"[{'PASS' if ok else 'FAIL'}] {name} {detail}", flush=True)

    dm = json.loads((CAMPAIGN_DIR / "dataset_manifest.json").read_text())
    for ds, splits in dm["splits"].items():
        for split, info in splits.items():
            p = REPO_ROOT / info["path"]
            check(f"dataset_exists:{ds}:{split}", p.is_file(), str(p))
            if p.is_file():
                actual = sha256_file(p)
                check(f"dataset_hash_matches:{ds}:{split}", actual == info["sha256"], f"expected={info['sha256']} actual={actual}")

    import torch
    check("cuda_available", torch.cuda.is_available(), torch.cuda.get_device_name(0) if torch.cuda.is_available() else "no CUDA device")

    from seion_kgr.data import load_knowledge_graph
    from seion_kgr.evaluate import evaluate as evaluate_fn
    check("evaluator_importable", evaluate_fn is not None, "seion_kgr.evaluate.evaluate")

    # deterministic seed check: two tiny loads must hash identically
    kg1 = load_knowledge_graph(str(FB_DIR / "train.txt"), str(FB_DIR / "valid.txt"), str(FB_DIR / "test.txt"))
    kg2 = load_knowledge_graph(str(FB_DIR / "train.txt"), str(FB_DIR / "valid.txt"), str(FB_DIR / "test.txt"))
    check("dataset_load_deterministic", (kg1.train == kg2.train).all() and kg1.num_entities == kg2.num_entities)

    for name in ("enable_path", "enable_seion", "init_from_checkpoint", "skip_test_eval", "gate_g_max"):
        from seion_kgr.train import build_parser
        parser_dest = {a.dest for a in build_parser()._actions}
        check(f"train_cli_flag_present:{name}", name in parser_dest)

    result = {"checks": checks, "all_passed": all(c["passed"] for c in checks), "commit_sha": git_commit_sha()}
    (CAMPAIGN_DIR / "static_validation_result.json").write_text(json.dumps(result, indent=2))
    print(json.dumps({"all_passed": result["all_passed"]}, indent=2))
    if not result["all_passed"]:
        raise SystemExit("Stage 1 static validation FAILED -- see static_validation_result.json")


# ---------------------------------------------------------------------------
# Stage 2: tiny smoke (ENGINEERING_SMOKE_ONLY)


def _write_smoke_subsample(dst_dir: Path, src_dir: Path, n_train: int = 3000, n_eval: int = 100) -> Path:
    dst_dir.mkdir(parents=True, exist_ok=True)
    for split, n in (("train", n_train), ("valid", n_eval), ("test", n_eval)):
        lines = (src_dir / f"{split}.txt").read_text(encoding="utf-8").splitlines()[:n]
        (dst_dir / f"{split}.txt").write_text("\n".join(lines) + "\n", encoding="utf-8")
    return dst_dir


def stage_smoke(cpu: bool = True) -> None:
    commit = git_commit_sha()
    smoke_data = _write_smoke_subsample(RUNS_DIR / "smoke_data", FB_DIR)
    for config_id in ("A0", "A1", "A2", "A3"):
        out_dir = RUNS_DIR / "smoke" / config_id
        result = run_one(
            config_id, seed=1, out_dir=out_dir, stage="ENGINEERING_SMOKE_ONLY",
            train_path=smoke_data / "train.txt", valid_path=smoke_data / "valid.txt", test_path=smoke_data / "test.txt",
            epochs=1, batch_size=64, dim=16, eval_max_queries=50, gate_g_max=1.0, skip_test_eval=True, cpu=cpu,
        )
        result["row"]["commit_sha"] = commit
        append_registry_row(result["row"])
        if result["returncode"] != 0:
            raise SystemExit(f"Stage 2 smoke run {config_id} FAILED (returncode={result['returncode']}) -- see {out_dir}")
    print("Stage 2 smoke: all 4 configs COMPLETED (ENGINEERING_SMOKE_ONLY -- no scientific interpretation)")


# ---------------------------------------------------------------------------
# Stage 3: one-seed full-FB15K-237 pilot + gate_g_max predictive-profile selection


def stage_pilot(cpu: bool = False) -> None:
    commit = git_commit_sha()
    freeze = load_freeze()
    train_path, valid_path, test_path = FB_DIR / "train.txt", FB_DIR / "valid.txt", FB_DIR / "test.txt"

    # gate_g_max selection: A3 (both branches active) at each candidate, reduced epoch budget, validation MRR only.
    selection_results = []
    for g in freeze["gate_g_max_candidates"]:
        out_dir = RUNS_DIR / "pilot" / f"gate_g_max_selection_A3_g{g}"
        result = run_one(
            "A3", seed=1, out_dir=out_dir, stage="GATE_G_MAX_SELECTION",
            train_path=train_path, valid_path=valid_path, test_path=test_path,
            epochs=6, batch_size=freeze["batch_size"], dim=freeze["dim"], eval_max_queries=0,
            gate_g_max=g, skip_test_eval=True, cpu=cpu,
        )
        result["row"]["commit_sha"] = commit
        append_registry_row(result["row"])
        if result["returncode"] != 0:
            raise SystemExit(f"gate_g_max selection run g={g} FAILED -- see {out_dir}")
        metrics_path = out_dir / "metrics.jsonl"
        best_valid_mrr = None
        if metrics_path.is_file():
            for line in metrics_path.read_text().splitlines():
                rec = json.loads(line)
                mrr = (rec.get("valid") or {}).get("combined", {}).get("MRR")
                if mrr is not None and (best_valid_mrr is None or mrr > best_valid_mrr):
                    best_valid_mrr = mrr
        selection_results.append({"gate_g_max": g, "best_valid_mrr": best_valid_mrr, "out_dir": str(out_dir.relative_to(REPO_ROOT))})

    selection_results_valid = [r for r in selection_results if r["best_valid_mrr"] is not None]
    if not selection_results_valid:
        raise SystemExit("gate_g_max selection produced no valid MRR readings -- cannot freeze a value, stopping before Stage 4")
    winner = max(selection_results_valid, key=lambda r: r["best_valid_mrr"])

    freeze["gate_g_max_selected"] = winner["gate_g_max"]
    freeze["gate_g_max_selection_run"] = winner["out_dir"]
    FREEZE_PATH.write_text(json.dumps(freeze, indent=2))
    (CAMPAIGN_DIR / "gate_g_max_selection.json").write_text(json.dumps({
        "candidates": selection_results, "selected": winner, "selection_procedure": "max validation MRR, A3, seed 1, reduced 6-epoch budget",
    }, indent=2))
    print(f"gate_g_max selected: {winner['gate_g_max']} (validation MRR={winner['best_valid_mrr']})", flush=True)

    # A0-A3 pilot at the now-frozen gate_g_max, full epoch budget, seed 1
    a0_out = RUNS_DIR / "pilot" / "seed1_A0"
    result_a0 = run_one(
        "A0", seed=1, out_dir=a0_out, stage="PILOT",
        train_path=train_path, valid_path=valid_path, test_path=test_path,
        epochs=freeze["epochs"], batch_size=freeze["batch_size"], dim=freeze["dim"], eval_max_queries=0,
        gate_g_max=freeze["gate_g_max_selected"], skip_test_eval=True, cpu=cpu,
    )
    result_a0["row"]["commit_sha"] = commit
    append_registry_row(result_a0["row"])
    if result_a0["returncode"] != 0:
        raise SystemExit(f"Pilot A0 FAILED -- see {a0_out}")
    a0_checkpoint = a0_out / "best.pt"

    for config_id in ("A1", "A2", "A3"):
        out_dir = RUNS_DIR / "pilot" / f"seed1_{config_id}"
        result = run_one(
            config_id, seed=1, out_dir=out_dir, stage="PILOT",
            train_path=train_path, valid_path=valid_path, test_path=test_path,
            epochs=freeze["epochs"], batch_size=freeze["batch_size"], dim=freeze["dim"], eval_max_queries=0,
            gate_g_max=freeze["gate_g_max_selected"], init_from_checkpoint=a0_checkpoint, skip_test_eval=True, cpu=cpu,
        )
        result["row"]["commit_sha"] = commit
        append_registry_row(result["row"])
        if result["returncode"] != 0:
            raise SystemExit(f"Pilot {config_id} FAILED -- see {out_dir}")
    print("Stage 3 pilot: A0-A3 seed=1 COMPLETED. Inspect runtime/VRAM/gate diagnostics before authorizing Stage 4.")


# ---------------------------------------------------------------------------
# Stage 4: complete screening, seeds 1-3, A0-A3


def stage_full(cpu: bool = False, seeds: Optional[List[int]] = None) -> None:
    commit = git_commit_sha()
    freeze = load_freeze()
    if freeze.get("gate_g_max_selected") is None:
        raise SystemExit("gate_g_max_selected is null in configuration_freeze.json -- run Stage 3 (pilot) first")
    train_path, valid_path, test_path = FB_DIR / "train.txt", FB_DIR / "valid.txt", FB_DIR / "test.txt"
    seeds = seeds or freeze["seeds"]

    # update seed_pairing_manifest.json's a0_checkpoint fields as A0 runs complete
    pairing_path = CAMPAIGN_DIR / "seed_pairing_manifest.json"
    pairing = json.loads(pairing_path.read_text())

    for seed in seeds:
        a0_out = RUNS_DIR / "full" / f"seed{seed}_A0"
        result_a0 = run_one(
            "A0", seed=seed, out_dir=a0_out, stage="SCREENING",
            train_path=train_path, valid_path=valid_path, test_path=test_path,
            epochs=freeze["epochs"], batch_size=freeze["batch_size"], dim=freeze["dim"], eval_max_queries=0,
            gate_g_max=freeze["gate_g_max_selected"], skip_test_eval=True, cpu=cpu,
        )
        result_a0["row"]["commit_sha"] = commit
        append_registry_row(result_a0["row"])
        if result_a0["returncode"] != 0:
            raise SystemExit(f"Stage 4 A0 seed={seed} FAILED -- see {a0_out}")
        a0_checkpoint = a0_out / "best.pt"
        for pair in pairing["pairs"]:
            if pair["seed"] == seed:
                pair["a0_checkpoint"] = str(a0_checkpoint.relative_to(REPO_ROOT))
        pairing_path.write_text(json.dumps(pairing, indent=2))

        for config_id in ("A1", "A2", "A3"):
            out_dir = RUNS_DIR / "full" / f"seed{seed}_{config_id}"
            result = run_one(
                config_id, seed=seed, out_dir=out_dir, stage="SCREENING",
                train_path=train_path, valid_path=valid_path, test_path=test_path,
                epochs=freeze["epochs"], batch_size=freeze["batch_size"], dim=freeze["dim"], eval_max_queries=0,
                gate_g_max=freeze["gate_g_max_selected"], init_from_checkpoint=a0_checkpoint, skip_test_eval=True, cpu=cpu,
            )
            result["row"]["commit_sha"] = commit
            append_registry_row(result["row"])
            if result["returncode"] != 0:
                raise SystemExit(f"Stage 4 {config_id} seed={seed} FAILED -- see {out_dir}")
    print(f"Stage 4 screening COMPLETE: seeds={seeds} x A0-A3 = {len(seeds) * 4} runs")


# ---------------------------------------------------------------------------
# Test-set discipline: open test exactly once, over the frozen best checkpoints


def stage_evaluate_test_frozen(cpu: bool = False) -> None:
    """Reloads each Stage-4 run's best.pt (already selected by validation
    MRR inside train.py's own checkpointing) and evaluates it on test
    exactly once. Uses seion_kgr.evaluate.evaluate directly (same function
    train.py itself calls) rather than a reimplementation."""
    import torch

    from seion_kgr.data import load_knowledge_graph
    from seion_kgr.evaluate import evaluate as evaluate_fn
    from seion_kgr.frontier_ops import build_csr_adjacency
    from seion_kgr.reasoner import Adjacency
    from seion_kgr.run_attribution import _rebuild_model
    from seion_kgr import reproducibility as repro

    freeze = load_freeze()
    train_path, valid_path, test_path = FB_DIR / "train.txt", FB_DIR / "valid.txt", FB_DIR / "test.txt"
    kg = load_knowledge_graph(str(train_path), str(valid_path), str(test_path))
    device = torch.device("cpu" if cpu or not torch.cuda.is_available() else "cuda")

    results = []
    for seed in freeze["seeds"]:
        for config_id in ("A0", "A1", "A2", "A3"):
            out_dir = RUNS_DIR / "full" / f"seed{seed}_{config_id}"
            ckpt_path = out_dir / "best.pt"
            if not ckpt_path.is_file():
                raise SystemExit(f"missing frozen checkpoint: {ckpt_path} -- run Stage 4 for all seeds/configs first")
            ckpt = repro.load_checkpoint(str(ckpt_path))
            model = _rebuild_model(ckpt["args"], kg).to(device)
            model.load_state_dict(ckpt["model_state"])
            model.eval()
            adjacency = None
            if ckpt["args"].get("enable_path"):
                adjacency = Adjacency.build(kg)
                if ckpt["args"].get("path_backend") == "batched":
                    adjacency = build_csr_adjacency(adjacency, kg.num_entities).to(device)
            test_metrics = evaluate_fn(model, kg, "test", device, 64, freeze["entity_block_eval"], adjacency, 1.0, seed)
            results.append({
                "seed": seed, "config_id": config_id, "checkpoint": str(ckpt_path.relative_to(REPO_ROOT)),
                "checkpoint_sha256": sha256_file(ckpt_path), "test": test_metrics,
            })
            print(f"test-eval seed={seed} {config_id}: MRR={test_metrics['combined']['MRR']:.4f}", flush=True)

    out = {
        "opened_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "commit_sha": git_commit_sha(),
        "note": "Test opened exactly once, over all Stage 4 frozen (validation-selected) checkpoints. Any subsequent re-open must be logged in deviations_log.md.",
        "results": results,
    }
    (CAMPAIGN_DIR / "test_evaluation_frozen.json").write_text(json.dumps(out, indent=2, default=str))
    print("Test-set opened once, results written to test_evaluation_frozen.json")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("stage", choices=["static-validation", "smoke", "pilot", "full", "evaluate-test-frozen"])
    parser.add_argument("--cpu", action="store_true", help="force CPU even if CUDA is available (debugging only)")
    parser.add_argument("--seeds", type=int, nargs="*", default=None, help="override seeds for the 'full' stage")
    args = parser.parse_args()

    RUNS_DIR.mkdir(parents=True, exist_ok=True)

    if args.stage == "static-validation":
        stage_static_validation()
    elif args.stage == "smoke":
        stage_smoke(cpu=args.cpu)
    elif args.stage == "pilot":
        stage_pilot(cpu=args.cpu)
    elif args.stage == "full":
        stage_full(cpu=args.cpu, seeds=args.seeds)
    elif args.stage == "evaluate-test-frozen":
        stage_evaluate_test_frozen(cpu=args.cpu)


if __name__ == "__main__":
    main()
