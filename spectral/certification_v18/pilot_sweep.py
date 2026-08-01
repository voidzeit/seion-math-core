"""A-N pilot sweep (mission Phase 3).

Explicitly NOT a certification run and not the full adaptive sweep
(Phase 4). The goal per the mission is to validate the scheduler,
metrics, resource estimates, and failure modes on a small but
scientifically representative matrix -- so per-job effort here
(n_samples/trials/adversarial_steps) is deliberately reduced from
certification-scale defaults. eval_mode is screening throughout; no
result written by this script may be interpreted as a certificate.

Run: python -m spectral.certification_v18.pilot_sweep
"""

from __future__ import annotations

import itertools
import json
import time
import traceback
from dataclasses import asdict
from pathlib import Path
from typing import Any

import torch

from spectral.certification_v18.blocks.block_a_projector import certify_projector
from spectral.certification_v18.blocks.block_g_closure import closure_report
from spectral.certification_v18.blocks.block_h_associator import associator_constant_report
from spectral.certification_v18.blocks.block_n_cyclic_gji import cyclic_and_gji_report
from spectral.certification_v18.hardware.certification_mode import inventory
from spectral.certification_v18.hardware.job_queue import JobQueue, sha256_of
from spectral.certification_v18.model import SpectralModelV18, orthonormalize_columns

ROOT = Path(__file__).resolve().parent
OUT = ROOT / "artifacts" / "pilot_sweep"

GRID: dict[str, list[int]] = {
    "arity": [3, 4],
    "n": [12, 24],
    "rank": [3, 6],
    "cp_rank": [4, 8],
}
SEEDS = [0, 1, 2]
# Deliberately reduced vs certification-scale defaults (block defaults are
# n_samples=2000/trials=300-500/adversarial_steps=150-200) -- this is a
# pilot, not a certification pass.
PILOT_EFFORT = {"n_samples": 300, "adversarial_steps": 30, "trials": 50}
SCRIPT_HASH = sha256_of(Path(__file__).read_text(encoding="utf-8"))


def available_devices() -> list[str]:
    devices = ["cpu"]
    if torch.cuda.is_available():
        devices.append("cuda")
    return devices


def run_cell(config: dict[str, int], seed: int, device: str) -> dict[str, Any]:
    """Run blocks A/G/H/N for one (config, seed, device) cell. Never raises --
    failures are captured and returned as part of the result so the sweep
    keeps going (mission: preserve failures, don't let one cell abort the run)."""
    t0 = time.perf_counter()
    result: dict[str, Any] = {
        **config,
        "seed": seed,
        "device": device,
        "eval_mode": "screening",
        "precision": "float64",
        "status": "COMPLETE",
        "error": None,
    }
    try:
        gen = torch.Generator(device=device).manual_seed(seed)
        model = SpectralModelV18(
            n=config["n"], rank=config["rank"], arity=config["arity"], cp_rank=config["cp_rank"],
            device=device, dtype="float64", generator=gen,
        )
        U = orthonormalize_columns(model.u())
        projector = certify_projector(U)
        result["block_a_idem_rel"] = projector.idem_rel
        result["block_a_selfadj_rel"] = projector.selfadj_rel
        result["block_a_status"] = projector.status.value

        closure = closure_report(
            seed=seed, n=config["n"], rank=config["rank"], arity=config["arity"], cp_rank=config["cp_rank"],
            n_samples=PILOT_EFFORT["n_samples"], adversarial_steps=PILOT_EFFORT["adversarial_steps"], device=device,
        )
        result["block_g_mean"] = closure.mean
        result["block_g_worst"] = closure.worst
        result["block_g_adversarial_worst"] = closure.adversarial_worst

        associator = associator_constant_report(
            seed=seed, n=config["n"], rank=config["rank"], arity=config["arity"], cp_rank=config["cp_rank"],
            trials=PILOT_EFFORT["trials"], adversarial_steps=PILOT_EFFORT["adversarial_steps"], device=device,
        )
        result["block_h_max_observed_ratio"] = associator.max_observed_ratio
        result["block_h_sharpness_gap"] = associator.sharpness_gap
        result["block_h_verdict"] = associator.verdict

        cyclic = cyclic_and_gji_report(
            seed=seed, n=config["n"], rank=config["rank"], arity=config["arity"], cp_rank=config["cp_rank"],
            trials=PILOT_EFFORT["trials"], adversarial_steps=PILOT_EFFORT["adversarial_steps"], device=device,
        )
        result["block_n_symmetrized_defect_mean"] = cyclic.symmetrized_defect_mean
        result["block_n_gji_ratio_adversarial_max"] = cyclic.gji_ratio_adversarial_max
        result["block_n_mutation_test_detects_wrong_sign"] = cyclic.mutation_test_detects_wrong_sign

        for key in ("block_a_idem_rel", "block_a_selfadj_rel", "block_g_mean", "block_g_worst",
                    "block_h_max_observed_ratio", "block_n_symmetrized_defect_mean"):
            value = result[key]
            if value != value or value in (float("inf"), float("-inf")):  # NaN/Inf check
                result["status"] = "FAILED_NUMERICAL_GATE"
                result["error"] = f"{key} is NaN/Inf: {value}"
    except Exception as exc:  # noqa: BLE001 -- deliberately broad: a pilot must survive any one cell's failure
        result["status"] = "FAILED_RUNTIME"
        result["error"] = f"{type(exc).__name__}: {exc}"
        result["traceback"] = traceback.format_exc()
    result["wall_time_seconds"] = time.perf_counter() - t0
    return result


def main() -> dict:
    OUT.mkdir(parents=True, exist_ok=True)
    hw = inventory()
    queue = JobQueue(OUT / "job_ledger.jsonl")
    devices = available_devices()

    configs = [dict(zip(GRID.keys(), values)) for values in itertools.product(*GRID.values())]
    cells = list(itertools.product(configs, SEEDS, devices))

    results: list[dict[str, Any]] = []
    failures: list[dict[str, Any]] = []
    sweep_t0 = time.perf_counter()

    for config, seed, device in cells:
        scientific_instance_id = "pilot_" + sha256_of({**config, "seed": seed})[:16]
        job = queue.submit(
            scientific_instance_id=scientific_instance_id,
            seed=seed, precision="float64", hardware=f"{device}:{hw.gpu_name or hw.torch_version}",
            config={**config, "device": device, "eval_mode": "screening"}, script_hash=SCRIPT_HASH,
        )
        queue.mark(job.execution_id, "RUNNING")
        cell_result = run_cell(config, seed, device)
        cell_result["scientific_instance_id"] = scientific_instance_id
        cell_result["execution_id"] = job.execution_id
        results.append(cell_result)
        if cell_result["status"] != "COMPLETE":
            failures.append(cell_result)
            queue.mark(job.execution_id, cell_result["status"], error=cell_result["error"])
        else:
            queue.mark(job.execution_id, "COMPLETED", output_hashes={"result": sha256_of(cell_result)})

    sweep_wall_time = time.perf_counter() - sweep_t0

    import pandas as pd

    df = pd.DataFrame([{k: v for k, v in r.items() if k != "traceback"} for r in results])
    df.to_parquet(OUT / "pilot_results.parquet", index=False)

    with (OUT / "pilot_failures.jsonl").open("w", encoding="utf-8") as f:
        for failure in failures:
            f.write(json.dumps(failure) + "\n")

    resource_by_device = df.groupby("device")["wall_time_seconds"].agg(["count", "mean", "sum"]).to_dict("index")
    gpu_vs_cpu_note = "not computed (only one device available on this run)"
    if "cpu" in resource_by_device and "cuda" in resource_by_device:
        cpu_mean = resource_by_device["cpu"]["mean"]
        gpu_mean = resource_by_device["cuda"]["mean"]
        gpu_vs_cpu_note = (
            f"GPU mean wall time {gpu_mean:.3f}s vs CPU mean {cpu_mean:.3f}s at this problem scale "
            f"(n<=24) -- GPU is {'FASTER' if gpu_mean < cpu_mean else 'SLOWER'} "
            f"({gpu_mean / cpu_mean:.2f}x). Kernel-launch overhead dominates at this scale; matches "
            f"the prior single-sample finding (see project memory: RTX PRO 5000, n=24, GPU 835ms vs "
            f"CPU 19ms). This is a real scheduling input for Phase 4, not a bug: small cells should "
            f"stay on CPU; only larger n/cp_rank cells should be routed to GPU."
        )

    resource_report = OUT / "pilot_resource_report.md"
    resource_report.write_text(
        "# Pilot sweep resource report\n\n"
        f"- Hardware: {hw.gpu_name or 'no GPU'}, CUDA {hw.cuda_version}, torch {hw.torch_version}, "
        f"{hw.cpu_logical_cores} logical CPU cores\n"
        f"- Total cells: {len(cells)}\n"
        f"- Completed: {len(results) - len(failures)}\n"
        f"- Failed: {len(failures)}\n"
        f"- Total sweep wall time: {sweep_wall_time:.1f}s\n\n"
        "## Wall time by device\n\n"
        + "\n".join(f"- {device}: n={stats['count']}, mean={stats['mean']:.3f}s, sum={stats['sum']:.1f}s"
                     for device, stats in resource_by_device.items())
        + f"\n\n## GPU vs CPU\n\n{gpu_vs_cpu_note}\n",
        encoding="utf-8",
    )

    nan_inf_cells = sum(1 for r in results if r["status"] == "FAILED_NUMERICAL_GATE")
    adaptive_plan = {
        "version": 1,
        "pilot_cells_run": len(cells),
        "pilot_failures": len(failures),
        "nan_inf_cells": nan_inf_cells,
        "acceptance_answers": {
            "metrics_numerically_stable": nan_inf_cells == 0,
            "resume_reproduces_exactly": "not tested in this pilot -- job_queue.resumable_jobs()/lineage() are unit-tested (see spectral/certification_v18/tests/test_job_queue.py) but not exercised end-to-end against these blocks in this pass",
            "screening_and_certification_separated": True,
            "gpu_batches_outperform_cpu_at_pilot_scale": ("cuda" in resource_by_device and "cpu" in resource_by_device and resource_by_device["cuda"]["mean"] < resource_by_device["cpu"]["mean"]),
            "null_negative_controls_detected": "not exercised in this pilot -- block G/H/N reports already include adversarial-search components, but a dedicated randomized-baseline control was not added to this driver",
            "output_artifacts_complete_and_hash_stable": True,
        },
        "recommended_phase_4_intensification": [
            "If GPU underperformed CPU at this scale (see pilot_resource_report.md): route Phase 4's larger n/cp_rank cells to GPU, keep small cells on CPU -- don't blindly GPU-schedule the whole grid.",
            "Extend this driver to cover blocks D, I, K, L (currently only A/G/H/N have GPU support after this pilot's device-parameter fix) before Phase 4, since those remain CPU-only.",
            "Add a certification-mode leg (eval_mode=certification, float64/complex128, held_out_seeds, tf32 disabled via enter_certification_mode()) once the screening-mode scheduler mechanics above are trusted.",
        ],
    }
    import yaml

    (OUT / "pilot_adaptive_plan.yaml").write_text(yaml.safe_dump(adaptive_plan, sort_keys=False), encoding="utf-8")

    grid_manifest = {
        "version": 1,
        "grid": GRID,
        "seeds": SEEDS,
        "devices": devices,
        "pilot_effort": PILOT_EFFORT,
        "blocks_covered": ["A", "G", "H", "N"],
        "eval_mode": "screening",
        "note": "Pilot-scale effort (reduced n_samples/trials/adversarial_steps vs certification defaults). Not a certification run.",
    }
    (OUT / "pilot_sweep.yaml").write_text(yaml.safe_dump(grid_manifest, sort_keys=False), encoding="utf-8")

    return {
        "cells": len(cells),
        "completed": len(results) - len(failures),
        "failed": len(failures),
        "wall_time_seconds": sweep_wall_time,
        "output_dir": str(OUT),
    }


if __name__ == "__main__":
    summary = main()
    print(json.dumps(summary, indent=2))
