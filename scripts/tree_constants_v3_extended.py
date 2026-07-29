"""Resumable extended-work scheduler for the v3 tree-constant track.

The base A--I matrix is complete independently of this program. This module
materializes every requested nested optimizer trajectory and every block-J
performance cell, executes bounded chunks, and keeps pending work visible.
It never upgrades an empirical optimizer value to a certified optimum.
"""

from __future__ import annotations

import argparse
from datetime import datetime, timezone
import hashlib
import itertools
import json
from pathlib import Path
import subprocess
import sys
import time
from typing import Any

import numpy as np
import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from seion_core.research_v3.adversarial_search import SearchConfig, gradient_search
from seion_core.research_v3.run_schema import (
    V3RunConfig,
    canonical_hash,
    write_run_artifacts,
)
from seion_core.research_v3.tree_enumeration import label_shape, topology_family_shape


ARTIFACT_ROOT = ROOT / "artifacts" / "research_v3"
RUN_ROOT = ROOT / "artifacts" / "runs_v3"
BLOCK_B_PATH = ARTIFACT_ROOT / "block_B.parquet"
SCHEDULE_B_PATH = ARTIFACT_ROOT / "extended_optimizer_schedule_v3.parquet"
SCHEDULE_J_PATH = ARTIFACT_ROOT / "extended_performance_schedule_v3.parquet"
RESULTS_PATH = ARTIFACT_ROOT / "extended_optimizer_results_v3.parquet"
RESULTS_CSV_PATH = ARTIFACT_ROOT / "extended_optimizer_results_v3.csv"
PROGRESS_PATH = ARTIFACT_ROOT / "extended_progress_v3.json"
PROGRESS_MD_PATH = ARTIFACT_ROOT / "extended_progress_v3.md"


def _utc() -> str:
    return datetime.now(timezone.utc).isoformat()


def _commit() -> str:
    return subprocess.run(
        ["git", "rev-parse", "HEAD"],
        cwd=ROOT,
        check=True,
        text=True,
        capture_output=True,
    ).stdout.strip()


def _write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(value, indent=2, sort_keys=True, default=str) + "\n",
        encoding="utf-8",
    )


def _trajectory_hash(instance_hash: str, seed: int, restart: int) -> str:
    payload = f"{instance_hash}:{seed}:{restart}".encode("ascii")
    return hashlib.sha256(payload).hexdigest()


def build_schedules(*, force: bool = False) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Materialize the complete requested optimizer and performance schedules."""

    if not BLOCK_B_PATH.is_file():
        raise FileNotFoundError(
            f"{BLOCK_B_PATH} is missing; execute the full-core matrix first"
        )

    if force or not SCHEDULE_B_PATH.is_file():
        base = pd.read_parquet(BLOCK_B_PATH)[
            [
                "scientific_instance_hash",
                "tree_hash",
                "arity",
                "internal_nodes",
                "topology",
                "eta",
                "projected_upper",
            ]
        ].reset_index(drop=True)
        repetitions = 20 * 8
        schedule_b = base.loc[base.index.repeat(repetitions)].reset_index(drop=True)
        schedule_b["seed"] = np.tile(np.repeat(np.arange(20), 8), len(base))
        schedule_b["restart"] = np.tile(np.arange(8), len(base) * 20)
        schedule_b["trajectory_id"] = [
            _trajectory_hash(str(instance), int(seed), int(restart))
            for instance, seed, restart in zip(
                schedule_b["scientific_instance_hash"],
                schedule_b["seed"],
                schedule_b["restart"],
                strict=True,
            )
        ]
        schedule_b["stage"] = "extended"
        schedule_b["required_optimizer"] = "Adam_then_LBFGS"
        schedule_b["status"] = "PENDING"
        schedule_b.to_parquet(SCHEDULE_B_PATH, index=False)
    else:
        schedule_b = pd.read_parquet(SCHEDULE_B_PATH)

    if force or not SCHEDULE_J_PATH.is_file():
        records: list[dict[str, Any]] = []
        for values in itertools.product(
            (2, 4, 8, 16, 32, 64, 128),
            (2, 3, 4),
            (2, 4, 8, 16, 32),
            ("float32", "float64", "complex64", "complex128"),
            (1, 2, 4, 8, 16),
            (1, 16, 128, 1024),
        ):
            dimension, arity, internal_nodes, dtype, cp_rank, number_of_trees = values
            parameters = {
                "dimension": dimension,
                "arity": arity,
                "internal_nodes": internal_nodes,
                "batch_size": "auto_vram_aware",
                "dtype": dtype,
                "cp_rank": cp_rank,
                "number_of_trees": number_of_trees,
            }
            records.append(
                {
                    **parameters,
                    "scientific_instance_hash": canonical_hash(parameters),
                    "stage": "extended",
                    "status": "PENDING",
                }
            )
        schedule_j = pd.DataFrame(records)
        schedule_j.to_parquet(SCHEDULE_J_PATH, index=False)
    else:
        schedule_j = pd.read_parquet(SCHEDULE_J_PATH)

    if len(schedule_b) != 460_800:
        raise RuntimeError(f"optimizer schedule has {len(schedule_b)} rows, expected 460800")
    if schedule_b["trajectory_id"].duplicated().any():
        raise RuntimeError("optimizer schedule contains duplicate trajectory identities")
    if len(schedule_j) != 8_400:
        raise RuntimeError(f"performance schedule has {len(schedule_j)} rows, expected 8400")
    if schedule_j["scientific_instance_hash"].duplicated().any():
        raise RuntimeError("performance schedule contains duplicate scientific identities")
    return schedule_b, schedule_j


def _load_results() -> pd.DataFrame:
    if RESULTS_PATH.is_file():
        return pd.read_parquet(RESULTS_PATH)
    return pd.DataFrame()


def _progress(schedule_b: pd.DataFrame, schedule_j: pd.DataFrame) -> dict[str, Any]:
    results = _load_results()
    completed_ids = set(results.get("trajectory_id", pd.Series(dtype=str)).astype(str))
    failures = (
        int((results["status"] == "FAILED").sum())
        if not results.empty and "status" in results
        else 0
    )
    completed_b = len(completed_ids)
    benchmark_path = ARTIFACT_ROOT / "computational_scaling_summary.json"
    benchmark_cells = 0
    if benchmark_path.is_file():
        benchmark = json.loads(benchmark_path.read_text(encoding="utf-8"))
        benchmark_cells = int(benchmark.get("rows", 0))
    return {
        "schema_version": 3,
        "generated_utc": _utc(),
        "source_commit": _commit(),
        "optimizer": {
            "requested_trajectories": len(schedule_b),
            "completed_trajectories": completed_b,
            "pending_trajectories": len(schedule_b) - completed_b,
            "failed_trajectories": failures,
            "completion_fraction": completed_b / len(schedule_b),
            "schedule": str(SCHEDULE_B_PATH.relative_to(ROOT)),
            "results": str(RESULTS_PATH.relative_to(ROOT)),
        },
        "performance": {
            "requested_scientific_instances": len(schedule_j),
            "completed_extended_instances": 0,
            "pending_extended_instances": len(schedule_j),
            "registered_calibration_cells": benchmark_cells,
            "schedule": str(SCHEDULE_J_PATH.relative_to(ROOT)),
        },
        "resource_gate": "TRIGGERED",
        "release_status": "EXTENDED_PENDING_RESOURCE_GATE",
        "epistemic_note": (
            "Completed optimizer trajectories are empirical lower bounds only; "
            "pending trajectories cannot support optimality or release claims."
        ),
    }


def write_progress(schedule_b: pd.DataFrame, schedule_j: pd.DataFrame) -> dict[str, Any]:
    progress = _progress(schedule_b, schedule_j)
    _write_json(PROGRESS_PATH, progress)
    optimizer = progress["optimizer"]
    performance = progress["performance"]
    PROGRESS_MD_PATH.write_text(
        "\n".join(
            [
                "# V3 extended execution status",
                "",
                f"- Source commit: {progress['source_commit']}",
                f"- Optimizer trajectories requested: **{optimizer['requested_trajectories']:,}**",
                f"- Optimizer trajectories completed: **{optimizer['completed_trajectories']:,}**",
                f"- Optimizer trajectories pending: **{optimizer['pending_trajectories']:,}**",
                f"- Optimizer failures: **{optimizer['failed_trajectories']:,}**",
                f"- Performance cells requested: **{performance['requested_scientific_instances']:,}**",
                f"- Registered benchmark calibration cells: **{performance['registered_calibration_cells']:,}**",
                f"- Release status: {progress['release_status']}",
                "",
                "The schedule is complete and resumable. Pending execution remains a "
                "release blocker; it is not silently sampled or relabeled as exhaustive.",
                "",
            ]
        ),
        encoding="utf-8",
    )
    return progress


def run_chunk(max_trajectories: int, *, adam_steps: int, lbfgs_steps: int) -> dict[str, Any]:
    schedule_b, schedule_j = build_schedules()
    existing = _load_results()
    completed = set(existing.get("trajectory_id", pd.Series(dtype=str)).astype(str))
    pending = schedule_b[~schedule_b["trajectory_id"].isin(completed)].head(max_trajectories)
    if pending.empty:
        return write_progress(schedule_b, schedule_j)

    started = time.perf_counter()
    rows: list[dict[str, Any]] = []
    histories: list[dict[str, Any]] = []
    tensors: list[np.ndarray] = []
    first_tree = None
    for row in pending.to_dict("records"):
        trajectory_start = time.perf_counter()
        try:
            shape = topology_family_shape(
                int(row["internal_nodes"]), int(row["arity"]), str(row["topology"])
            )
            tree = label_shape(shape, repeated_law=True)
            if first_tree is None:
                first_tree = tree
            combined_seed = int(row["seed"]) * 1009 + int(row["restart"])
            result = gradient_search(
                tree,
                SearchConfig(
                    eta=float(row["eta"]),
                    error_type="projected",
                    seeds=(combined_seed,),
                    restarts_per_seed=1,
                    adam_steps=adam_steps,
                    lbfgs_steps=lbfgs_steps,
                    device="cuda",
                    dtype="float64",
                ),
            )
            lower = float(result.best_lower_bound)
            upper = float(row["projected_upper"])
            violation = lower - upper
            status = "COMPLETE" if violation <= 1.0e-8 else "FAILED"
            rows.append(
                {
                    **row,
                    "empirical_lower_bound": lower,
                    "certified_upper_bound": upper,
                    "lower_to_upper_ratio": lower / upper if upper > 0 else 1.0,
                    "bound_violation_margin": upper - lower,
                    "optimizer": result.optimizer,
                    "device": result.device,
                    "adam_steps": adam_steps,
                    "lbfgs_steps": lbfgs_steps,
                    "wall_seconds": time.perf_counter() - trajectory_start,
                    "generated_utc": _utc(),
                    "source_commit": _commit(),
                    "epistemic_status": "EMPIRICAL_LOWER_BOUND",
                    "status": status,
                }
            )
            tensors.append(result.best_tensor)
            for item in result.history:
                histories.append(
                    {
                        "trajectory_id": row["trajectory_id"],
                        "requested_seed": int(row["seed"]),
                        "requested_restart": int(row["restart"]),
                        **item,
                    }
                )
            if status == "FAILED":
                raise RuntimeError(
                    f"empirical lower {lower} exceeds certified upper {upper}"
                )
        except Exception as exc:
            if not rows or rows[-1].get("trajectory_id") != row["trajectory_id"]:
                rows.append(
                    {
                        **row,
                        "empirical_lower_bound": np.nan,
                        "certified_upper_bound": float(row["projected_upper"]),
                        "lower_to_upper_ratio": np.nan,
                        "bound_violation_margin": np.nan,
                        "optimizer": "Adam_then_LBFGS",
                        "device": "cuda_if_available",
                        "adam_steps": adam_steps,
                        "lbfgs_steps": lbfgs_steps,
                        "wall_seconds": time.perf_counter() - trajectory_start,
                        "generated_utc": _utc(),
                        "source_commit": _commit(),
                        "epistemic_status": "EMPIRICAL_LOWER_BOUND",
                        "status": "FAILED",
                        "error": f"{type(exc).__name__}: {exc}",
                    }
                )

    new = pd.DataFrame(rows)
    merged = pd.concat([existing, new], ignore_index=True, sort=False)
    merged = merged.sort_values(["trajectory_id", "generated_utc"]).drop_duplicates(
        "trajectory_id", keep="last"
    )
    merged.to_parquet(RESULTS_PATH, index=False)
    merged.to_csv(RESULTS_CSV_PATH, index=False)

    if first_tree is None:
        raise RuntimeError("extended chunk did not produce a representative tree")
    chunk_hash = canonical_hash(
        {
            "trajectory_ids": list(new["trajectory_id"]),
            "source_commit": _commit(),
            "adam_steps": adam_steps,
            "lbfgs_steps": lbfgs_steps,
        }
    )
    representative_tensor = tensors[0] if tensors else np.empty(0)
    write_run_artifacts(
        RUN_ROOT / f"v3_extended_chunk_{chunk_hash[:16]}",
        repo_root=ROOT,
        config=V3RunConfig(
            block="B_EXTENDED",
            instance_id=chunk_hash,
            method="bounded_resumable_Adam_LBFGS_chunk",
            seed=None,
            precision="float64",
            device="cuda_if_available",
            parameters={
                "trajectory_ids": list(new["trajectory_id"]),
                "adam_steps": adam_steps,
                "lbfgs_steps": lbfgs_steps,
            },
            restarts=len(new),
            stage="extended",
        ),
        tree=first_tree,
        type_signature={"tau": {"ambient_dimension": 2, "reduced_dimension": 1}},
        law_tensors={"best_tensor": representative_tensor},
        local_constants={"M": 1.0, "rho_over_M": "per trajectory"},
        reference_metrics={
            "rows": len(new),
            "failed": int((new["status"] == "FAILED").sum()),
        },
        optimization_history=histories,
        node_contributions=[],
        final_metrics={
            "completed_in_chunk": int((new["status"] == "COMPLETE").sum()),
            "failed_in_chunk": int((new["status"] == "FAILED").sum()),
            "best_empirical_lower": float(new["empirical_lower_bound"].max()),
            "wall_seconds": time.perf_counter() - started,
        },
        certificate={
            "status": "EMPIRICAL_LOWER_BOUND",
            "global_optimality_certified": False,
            "resource_gate": "EXTENDED_PENDING_RESOURCE_GATE",
        },
        command=(
            "python scripts/tree_constants_v3_extended.py run "
            f"--max-trajectories {max_trajectories} "
            f"--adam-steps {adam_steps} --lbfgs-steps {lbfgs_steps}"
        ),
        extremizer={
            "best_lower_bound": {
                "value": float(new["empirical_lower_bound"].max()),
                "status": "EMPIRICAL_LOWER_BOUND",
            },
            "certified_upper_bound": {
                "value": float(new["certified_upper_bound"].max()),
                "status": "CERTIFIED_UPPER_BOUND",
            },
            "optimality_gap": {
                "status": "OPEN",
                "note": "chunk search does not certify a global optimum",
            },
            "tensor": representative_tensor,
            "inputs": np.ones((max(2, int(pending.iloc[0]["arity"])), 1)),
            "independent_recheck": {
                "schedule": str(SCHEDULE_B_PATH.relative_to(ROOT)),
                "results": str(RESULTS_PATH.relative_to(ROOT)),
            },
        },
    )
    progress = write_progress(schedule_b, schedule_j)
    if (new["status"] == "FAILED").any():
        raise RuntimeError("extended chunk contains failed trajectories")
    return progress


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    subparsers = parser.add_subparsers(dest="command", required=True)
    plan = subparsers.add_parser("plan")
    plan.add_argument("--force", action="store_true")
    run = subparsers.add_parser("run")
    run.add_argument("--max-trajectories", type=int, default=4)
    run.add_argument("--adam-steps", type=int, default=30)
    run.add_argument("--lbfgs-steps", type=int, default=8)
    subparsers.add_parser("status")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    if args.command == "plan":
        schedules = build_schedules(force=args.force)
        progress = write_progress(*schedules)
    elif args.command == "run":
        if args.max_trajectories < 0:
            raise ValueError("max-trajectories must be nonnegative")
        if args.max_trajectories == 0:
            schedules = build_schedules()
            progress = write_progress(*schedules)
        else:
            progress = run_chunk(
                args.max_trajectories,
                adam_steps=args.adam_steps,
                lbfgs_steps=args.lbfgs_steps,
            )
    else:
        schedules = build_schedules()
        progress = write_progress(*schedules)
    print(json.dumps(progress, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
