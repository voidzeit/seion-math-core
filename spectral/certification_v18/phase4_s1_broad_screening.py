"""A-N adaptive sweep, Stage S1 -- broad GPU/CPU screening (mission Phase 4).

Wider than the Phase 3 pilot (spectral/certification_v18/pilot_sweep.py):
n extends to 96 (the pilot only tested n<=24, where GPU was 2.97x slower
than CPU purely from kernel-launch overhead -- this stage exists to find
out whether that reverses at larger scale, or whether it doesn't within
the tested range). 5 seeds per mission's suggested S1 axis (the pilot
used 3). Still eval_mode=screening throughout -- this stage validates
scale/scheduling behavior, it does not certify anything.

Scope reduction from the mission's full suggested S1 grid, stated
explicitly rather than silently: arity restricted to {3,4} (dropped 5),
cp_rank to {4,8} (dropped 16,32), no complex-field axis, only blocks
A/G/H/N (the ones with GPU support after the Phase 3 device-parameter
fix; D/I/K/L and the rest remain CPU-only and out of scope for this
stage). A full mission-scale S1 sweep (n to 96 with all axes) would run
for many hours; this stage is deliberately bounded to answer the
specific open question the pilot raised (does GPU ever win at larger n)
rather than exhaustively covering the whole suggested grid in one pass.

Run: python -m spectral.certification_v18.phase4_s1_broad_screening
"""

from __future__ import annotations

import itertools
import json
import time
from pathlib import Path
from typing import Any

import torch

from spectral.certification_v18.hardware.certification_mode import inventory
from spectral.certification_v18.hardware.job_queue import JobQueue, sha256_of
from spectral.certification_v18.pilot_sweep import PILOT_EFFORT, available_devices, run_cell

ROOT = Path(__file__).resolve().parent
OUT = ROOT / "artifacts" / "phase4_s1_broad_screening"

GRID: dict[str, list[int]] = {
    "arity": [3, 4],
    "n": [12, 24, 48, 96],
    "rank": [3, 6],
    "cp_rank": [4, 8],
}
SEEDS = [0, 1, 2, 3, 4]
SCRIPT_HASH = sha256_of(Path(__file__).read_text(encoding="utf-8"))


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

    for index, (config, seed, device) in enumerate(cells):
        scientific_instance_id = "s1_" + sha256_of({**config, "seed": seed})[:16]
        job = queue.submit(
            scientific_instance_id=scientific_instance_id,
            seed=seed, precision="float64", hardware=f"{device}:{hw.gpu_name or hw.torch_version}",
            config={**config, "device": device, "eval_mode": "screening", "stage": "S1"}, script_hash=SCRIPT_HASH,
        )
        queue.mark(job.execution_id, "RUNNING")
        cell_result = run_cell(config, seed, device)
        cell_result["scientific_instance_id"] = scientific_instance_id
        cell_result["execution_id"] = job.execution_id
        cell_result["stage"] = "S1"
        results.append(cell_result)
        if cell_result["status"] != "COMPLETE":
            failures.append(cell_result)
            queue.mark(job.execution_id, cell_result["status"], error=cell_result["error"])
        else:
            queue.mark(job.execution_id, "COMPLETED", output_hashes={"result": sha256_of(cell_result)})
        if (index + 1) % 20 == 0:
            elapsed = time.perf_counter() - sweep_t0
            print(f"[{index + 1}/{len(cells)}] elapsed={elapsed:.0f}s", flush=True)

    sweep_wall_time = time.perf_counter() - sweep_t0

    import pandas as pd

    df = pd.DataFrame([{k: v for k, v in r.items() if k != "traceback"} for r in results])
    df.to_parquet(OUT / "s1_results.parquet", index=False)

    with (OUT / "s1_failures.jsonl").open("w", encoding="utf-8") as f:
        for failure in failures:
            f.write(json.dumps(failure) + "\n")

    by_device_n = df.groupby(["device", "n"])["wall_time_seconds"].agg(["count", "mean"]).reset_index()
    crossover_rows = by_device_n.to_dict("records")
    crossover_found = False
    for n_value in sorted(df["n"].unique()):
        cpu_mean = by_device_n[(by_device_n["device"] == "cpu") & (by_device_n["n"] == n_value)]["mean"]
        cuda_mean = by_device_n[(by_device_n["device"] == "cuda") & (by_device_n["n"] == n_value)]["mean"]
        if len(cpu_mean) and len(cuda_mean) and float(cuda_mean.iloc[0]) < float(cpu_mean.iloc[0]):
            crossover_found = True

    resource_report = OUT / "s1_resource_report.md"
    resource_report.write_text(
        "# Phase 4 S1 broad-screening resource report\n\n"
        f"- Hardware: {hw.gpu_name or 'no GPU'}, CUDA {hw.cuda_version}, torch {hw.torch_version}, "
        f"{hw.cpu_logical_cores} logical CPU cores\n"
        f"- Total cells: {len(cells)}\n"
        f"- Completed: {len(results) - len(failures)}\n"
        f"- Failed: {len(failures)}\n"
        f"- Total sweep wall time: {sweep_wall_time:.1f}s\n\n"
        "## Wall time by device x n (mean seconds/cell)\n\n"
        + "\n".join(f"- device={row['device']}, n={row['n']}: count={row['count']}, mean={row['mean']:.3f}s" for row in crossover_rows)
        + f"\n\n## GPU/CPU crossover within tested range (n up to {max(GRID['n'])})\n\n"
        + ("A crossover WAS found: GPU became faster than CPU at some tested n." if crossover_found
           else f"No crossover found up to n={max(GRID['n'])}: CPU remained faster than or comparable to "
                f"GPU at every tested scale in this run. This extends, not just repeats, the Phase 3 pilot's "
                f"finding (which only tested up to n=24) -- the pilot's conclusion holds at 4x the ambient "
                f"dimension tested here."),
        encoding="utf-8",
    )

    grid_manifest = {
        "version": 1, "stage": "S1", "grid": GRID, "seeds": SEEDS, "devices": devices,
        "effort": PILOT_EFFORT, "blocks_covered": ["A", "G", "H", "N"], "eval_mode": "screening",
        "scope_reduction_note": (
            "arity restricted to {3,4} (mission suggests up to 5), cp_rank to {4,8} "
            "(mission suggests up to 32), only blocks with GPU support (A/G/H/N) -- "
            "not the full mission-scale S1 grid, see module docstring."
        ),
    }
    (OUT / "s1_manifest.yaml").write_text(__import__("yaml").safe_dump(grid_manifest, sort_keys=False), encoding="utf-8")

    return {
        "cells": len(cells), "completed": len(results) - len(failures), "failed": len(failures),
        "wall_time_seconds": sweep_wall_time, "crossover_found": crossover_found, "output_dir": str(OUT),
    }


if __name__ == "__main__":
    summary = main()
    print(json.dumps(summary, indent=2))
