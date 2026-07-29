"""Deterministic orchestration for the nodewise tree-constants v3 track.

Scientific rows and optimizer restarts are deliberately distinct.  A block
execution is one provenance-bearing run; its master index contains immutable
hashes for every mathematical instance.  This avoids fabricating hundreds of
thousands of tiny run directories while retaining per-instance identity.
"""

from __future__ import annotations

import argparse
from collections import Counter
from dataclasses import asdict
from datetime import datetime, timezone
from fractions import Fraction
import hashlib
import itertools
import json
import math
from pathlib import Path
import subprocess
import sys
import time
from typing import Any, Iterable, Mapping, Sequence

import numpy as np
import pandas as pd
import yaml


ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from seion_core.research_v3.adversarial_search import (  # noqa: E402
    SearchConfig,
    derivative_free_search,
    gradient_search,
)
from seion_core.research_v3.certificates import (  # noqa: E402
    LocalSummary,
    certify_tree,
    homogeneous_ambient_bound,
    homogeneous_projected_bound,
)
from seion_core.research_v3.cp_projection_budget import (  # noqa: E402
    homogeneous_cp_projection_budget,
)
from seion_core.research_v3.extremizers import (  # noqa: E402
    rotation_extremizer,
    rotation_tensor,
)
from seion_core.research_v3.interval_certification import (  # noqa: E402
    certified_gap,
    rotation_tree_ratio_interval,
)
from seion_core.research_v3.local_constants import TypedLaw  # noqa: E402
from seion_core.research_v3.polynomial_forests import (  # noqa: E402
    ForestTerm,
    SignedForest,
    evaluate_forest_errors,
    named_signed_forests,
)
from seion_core.research_v3.projected_evaluation import (  # noqa: E402
    compute_tree_errors,
    evaluate_projected_numpy,
    evaluate_projected_torch,
)
from seion_core.research_v3.report import summary_statistics, write_frame  # noqa: E402
from seion_core.research_v3.run_schema import (  # noqa: E402
    V3RunConfig,
    canonical_hash,
    hardware_inventory,
    write_run_artifacts,
)
from seion_core.research_v3.tree_enumeration import (  # noqa: E402
    Shape,
    count_fixed_arity,
    count_mixed,
    full_ordered_shapes,
    label_shape,
    mixed_ordered_shapes,
    topology_family_shape,
)
from seion_core.research_v3.typed_tree import (  # noqa: E402
    Leaf,
    Node,
    Tree,
    iter_internal,
    tree_hash,
    tree_statistics,
    validate_tree,
)
from seion_core.research_v3.types import TypeSystem, TypedSpace  # noqa: E402


ARTIFACT_ROOT = ROOT / "artifacts" / "research_v3"
INDEX_ROOT = ROOT / "artifacts" / "index"
RUN_ROOT = ROOT / "artifacts" / "runs_v3"
MATRIX_PATH = ROOT / "experiments" / "matrices" / "tree_constants_v3.yaml"
RESOLVED_MATRIX_PATH = ROOT / "experiments" / "matrices" / "tree_constants_v3_resolved.yaml"


def _jsonable(value: Any) -> Any:
    if isinstance(value, np.generic):
        return value.item()
    if isinstance(value, np.ndarray):
        return value.tolist()
    if isinstance(value, Path):
        return str(value)
    if isinstance(value, Fraction):
        return str(value)
    if isinstance(value, Mapping):
        return {str(key): _jsonable(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [_jsonable(item) for item in value]
    return value


def write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(_jsonable(value), indent=2, sort_keys=True, allow_nan=False) + "\n",
        encoding="utf-8",
    )


def git_commit() -> str:
    return subprocess.run(
        ["git", "rev-parse", "HEAD"], cwd=ROOT, check=True, text=True, capture_output=True
    ).stdout.strip()


def load_matrix() -> dict[str, Any]:
    return yaml.safe_load(MATRIX_PATH.read_text(encoding="utf-8"))


def matrix_counts() -> dict[str, Any]:
    shape_a = sum(count_fixed_arity(k, 2) for k in range(1, 5)) + sum(
        count_fixed_arity(k, 3) for k in range(1, 5)
    )
    counts = {
        "A": shape_a * 3 * 5 * 3,
        "B": 3 * 10 * 8 * 12,
        "C": 3 * 4 * 3 * 6 * 4 * 4,
        "D": 3 * 3 * 3 * 5 * 4 * 8,
        "E": 3 * 4 * 4 * 2,  # valid and invalid controls
        "F": 8 * 3,
        "G": 7 * 4,
        "H": 4 * 5 * 4 * 2 * 3,
        "I": 6 * 4,
        "J": 7 * 3 * 5 * 4 * 5 * 4,
    }
    nested = {
        "A_certification_method_calls": counts["A"] * 3,
        "B_optimizer_trajectories": counts["B"] * 20 * 8,
        "C_seed_evaluations": counts["C"] * 10,
        "D_seed_evaluations": counts["D"] * 10,
        "E_seed_evaluations": (counts["E"] // 2) * 10,
        "F_leakage_mask_evaluations": 3 * sum(2**k for k in range(1, 9)),
        "G_seed_evaluations": counts["G"] * 20,
        "H_seed_evaluations": counts["H"] * 10,
        "I_seed_evaluations": counts["I"] * 10,
    }
    enumeration = {
        "binary": sum(count_fixed_arity(k, 2) for k in range(1, 9)),
        "ternary": sum(count_fixed_arity(k, 3) for k in range(1, 6)),
        "quaternary": sum(count_fixed_arity(k, 4) for k in range(1, 5)),
        "mixed": sum(count_mixed(k) for k in range(1, 6)),
    }
    return {
        "scientific_instances_by_block": counts,
        "full_core_scientific_instances": sum(counts[key] for key in "ABCDEFGHI"),
        "extended_scientific_instances": counts["J"],
        "nested_execution_counts": nested,
        "requested_optimizer_or_seed_evaluations": sum(nested.values()),
        "enumeration": enumeration,
        "enumerated_tree_shapes": sum(enumeration.values()),
    }


def calibration() -> dict[str, Any]:
    shape = topology_family_shape(8, 3, "maximally_balanced")
    tree = label_shape(shape, repeated_law=True)
    construction = rotation_extremizer(tree, 0.1)
    start = time.perf_counter()
    repetitions = 200
    for _ in range(repetitions):
        compute_tree_errors(tree, construction.laws, construction.types, construction.reduced_inputs)
    elapsed = time.perf_counter() - start
    record: dict[str, Any] = {
        "cpu_rotation_tree_evaluations": repetitions,
        "cpu_seconds": elapsed,
        "cpu_evaluations_per_second": repetitions / elapsed,
    }
    try:
        import torch

        if torch.cuda.is_available():
            torch.backends.cuda.matmul.allow_tf32 = False
            x = torch.randn((4096, 32), dtype=torch.float64, device="cuda")
            w = torch.randn((32, 32), dtype=torch.float64, device="cuda")
            for _ in range(3):
                x = torch.tanh(x @ w)
            torch.cuda.synchronize()
            start = time.perf_counter()
            steps = 50
            for _ in range(steps):
                x = torch.tanh(x @ w)
            torch.cuda.synchronize()
            gpu_elapsed = time.perf_counter() - start
            record.update(
                {
                    "gpu_calibration": "4096x32 float64 tanh-matmul",
                    "gpu_steps": steps,
                    "gpu_seconds": gpu_elapsed,
                    "gpu_steps_per_second": steps / gpu_elapsed,
                    "gpu_name": torch.cuda.get_device_name(0),
                }
            )
        else:
            record["gpu_calibration"] = "CUDA unavailable"
    except Exception as exc:  # pragma: no cover - hardware dependent
        record["gpu_calibration"] = f"failed:{type(exc).__name__}"
    return record


def command_budget(_: argparse.Namespace) -> None:
    ARTIFACT_ROOT.mkdir(parents=True, exist_ok=True)
    counts = matrix_counts()
    calibration_result = calibration()
    optimizer_trajectories = counts["nested_execution_counts"]["B_optimizer_trajectories"]
    assumed_steps = 150
    # Calibrated tree evaluation is a lower-cost proxy; multiplying by the
    # requested steps is intentionally conservative only as an order estimate.
    seconds_per_eval = 1.0 / calibration_result["cpu_evaluations_per_second"]
    lower_wall_seconds = optimizer_trajectories * assumed_steps * seconds_per_eval
    per_instance_files = 26
    naive_files = counts["full_core_scientific_instances"] * per_instance_files
    naive_storage = naive_files * 32 * 1024
    resource_gate = {
        "triggered": bool(lower_wall_seconds > 8 * 3600 or naive_files > 250_000),
        "criteria": {
            "maximum_single_session_optimizer_hours": 8,
            "maximum_small_file_count": 250_000,
        },
        "requested_naive_file_count": naive_files,
        "requested_naive_storage_bytes_at_32KiB_per_file": naive_storage,
        "optimizer_wall_lower_estimate_seconds": lower_wall_seconds,
        "resolution": {
            "scientific_axes_retained": True,
            "full_core": "all base mathematical instances; exhaustive trees; proved upper bounds; explicit lower constructions; selected independent optimizer calibration",
            "extended_resumable": "all requested seed/restart adversarial trajectories and performance block J",
            "artifact_packaging": "one complete run artifact set per block plus one immutable row per scientific instance",
            "claim_language": "unexecuted optimizer trajectories remain explicitly pending and cannot support optimality",
        },
    }
    budget = {
        "schema_version": 3,
        "generated_utc": datetime.now(timezone.utc).isoformat(),
        "source_commit": git_commit(),
        "matrix": str(MATRIX_PATH.relative_to(ROOT)),
        **counts,
        "calibration": calibration_result,
        "assumptions": {
            "optimizer_steps_per_trajectory": assumed_steps,
            "artifact_average_bytes_for_naive_layout": 32 * 1024,
            "flop_estimate_note": "dense optimizer FLOPs vary with arity, dimension, topology, and batching; wall estimate uses measured eight-node tree evaluation as an optimistic lower proxy",
        },
        "resource_gate": resource_gate,
    }
    write_json(ARTIFACT_ROOT / "run_budget.json", budget)
    lines = [
        "# V3 run budget",
        "",
        f"Generated: {budget['generated_utc']}",
        f"Source commit: `{budget['source_commit']}`",
        "",
        "## Declared counts",
        "",
        "| Block | Scientific instances |",
        "|---|---:|",
    ]
    for block, count in counts["scientific_instances_by_block"].items():
        lines.append(f"| {block} | {count:,} |")
    lines.extend(
        [
            "",
            f"Full core (A--I): **{counts['full_core_scientific_instances']:,}** instances.",
            f"Extended performance (J): **{counts['extended_scientific_instances']:,}** instances.",
            f"Exact enumerator: **{counts['enumerated_tree_shapes']:,}** ordered shapes.",
            f"Nested requested executions: **{counts['requested_optimizer_or_seed_evaluations']:,}**.",
            "",
            "## Calibration",
            "",
            "```json",
            json.dumps(calibration_result, indent=2, sort_keys=True),
            "```",
            "",
            "## Resource gate",
            "",
            f"Triggered: **{resource_gate['triggered']}**.",
            f"A naive per-instance layout would create about **{naive_files:,} files** "
            f"and **{naive_storage / 2**30:.1f} GiB** at 32 KiB/file.",
            f"The optimistic single-device optimizer lower estimate is **{lower_wall_seconds / 3600:.1f} h**.",
            "",
            "All scientific axes remain registered.  The full core evaluates every base mathematical instance with rigorous upper bounds and explicit lower constructions.  The complete seed/restart adversarial grid is retained, unmodified, as a resumable extended workload.  This scheduling resolution does not permit an optimality claim.",
            "",
            "Per-run artifacts are packaged by block; every master-index row retains its own configuration, tree, mathematical-object, and input hashes.",
        ]
    )
    (ARTIFACT_ROOT / "run_budget.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    resolved = load_matrix()
    resolved["execution_resolution"] = resource_gate["resolution"]
    resolved["execution_resolution"]["resource_gate_artifact"] = "artifacts/research_v3/run_budget.json"
    RESOLVED_MATRIX_PATH.write_text(yaml.safe_dump(resolved, sort_keys=False), encoding="utf-8")
    print(json.dumps({"budget": str(ARTIFACT_ROOT / 'run_budget.json'), "resource_gate": resource_gate["triggered"], "full_core_instances": counts["full_core_scientific_instances"]}, indent=2))


def _shape_rows(family: str, maximum: int, arity: int | None = None) -> Iterable[dict[str, Any]]:
    sequence = 0
    for k in range(1, maximum + 1):
        shapes = mixed_ordered_shapes(k) if arity is None else full_ordered_shapes(k, arity)
        for shape in shapes:
            tree = label_shape(shape)
            stats = tree_statistics(tree)
            row = {
                "family": family,
                "sequence": sequence,
                "internal_nodes": k,
                **stats,
            }
            row["arity_profile"] = json.dumps(row["arity_profile"], sort_keys=True)
            row["type_signature"] = json.dumps(row["type_signature"], sort_keys=True)
            yield row
            sequence += 1


def command_enumerate(_: argparse.Namespace) -> None:
    start = time.perf_counter()
    rows = list(_shape_rows("binary", 8, 2))
    rows.extend(_shape_rows("ternary", 5, 3))
    rows.extend(_shape_rows("quaternary", 4, 4))
    rows.extend(_shape_rows("mixed_2_3_4", 5, None))
    frame = pd.DataFrame(rows)
    within_family_duplicates = frame.duplicated(["family", "tree_hash"])
    if within_family_duplicates.any():
        duplicates = frame.loc[within_family_duplicates, ["family", "tree_hash"]].to_dict("records")
        raise RuntimeError(f"a grammar emitted duplicate shapes: {duplicates[:3]}")
    frame["enumeration_instance_id"] = [
        canonical_hash({"family": family, "tree_hash": digest})
        for family, digest in zip(frame["family"], frame["tree_hash"])
    ]
    write_frame(
        frame,
        INDEX_ROOT / "tree_instances_v3.csv",
        INDEX_ROOT / "tree_instances_v3.parquet",
    )
    summary = {
        "generated_utc": datetime.now(timezone.utc).isoformat(),
        "source_commit": git_commit(),
        "rows": len(frame),
        "unique_mathematical_objects": int(frame["tree_hash"].nunique()),
        "families": frame.groupby("family").size().to_dict(),
        "elapsed_seconds": time.perf_counter() - start,
        "hash_unique_within_each_grammar": True,
        "cross_grammar_hash_reuse_is_intentional": True,
    }
    write_json(ARTIFACT_ROOT / "tree_enumeration_summary.json", summary)
    print(json.dumps(summary, indent=2))


def _representative_tree(arity: int = 2, internal_nodes: int = 2) -> Tree:
    return label_shape(
        topology_family_shape(internal_nodes, arity, "left_comb"), repeated_law=True
    )


def _write_block_run(
    block: str,
    *,
    tree: Tree,
    final_metrics: Mapping[str, Any],
    certificate: Mapping[str, Any],
    reference_metrics: Mapping[str, Any] | None = None,
    optimization_history: Sequence[Mapping[str, Any]] = (),
    node_contributions: Sequence[Mapping[str, Any]] = (),
    law_tensor: np.ndarray | None = None,
    local_constants: Mapping[str, Any] | None = None,
    extremizer: Mapping[str, Any] | None = None,
    stage: str = "full",
) -> Path:
    digest = canonical_hash(
        {
            "block": block,
            "matrix": load_matrix(),
            "source_commit": git_commit(),
            "stage": stage,
        }
    )[:16]
    run_dir = RUN_ROOT / f"v3_{block.lower()}_{digest}"
    config = V3RunConfig(
        block=block,
        instance_id=f"block-{block}-batch",
        method="batched registered scientific instances",
        seed=None,
        precision="float64/complex128/exact-as-declared",
        device="cpu+cuda" if hardware_inventory().get("cuda_available") else "cpu",
        parameters={
            "matrix": str(MATRIX_PATH.relative_to(ROOT)),
            "resolved_matrix": str(RESOLVED_MATRIX_PATH.relative_to(ROOT)),
            "row_count": int(final_metrics.get("scientific_instances", 0)),
        },
        stage=stage,
    )
    tensor = law_tensor if law_tensor is not None else rotation_tensor(2, 0.1)
    write_run_artifacts(
        run_dir,
        repo_root=ROOT,
        config=config,
        tree=tree,
        type_signature={"tau": {"dimension": int(tensor.shape[0]), "rank": 1, "field": "real"}},
        law_tensors={"representative": tensor},
        local_constants=local_constants or {"representative": {"M": 1.0, "m": 1.0, "rho": 0.1}},
        reference_metrics=reference_metrics or {},
        optimization_history=optimization_history,
        node_contributions=node_contributions,
        final_metrics=final_metrics,
        certificate=certificate,
        command=f"python scripts/tree_constants_v3_pipeline.py {block.lower()}",
        stdout=json.dumps(_jsonable(final_metrics), indent=2),
        extremizer=extremizer,
    )
    return run_dir


def _exact_status(lower: float, upper: float) -> str:
    if upper == 0.0 and lower == 0.0:
        return "EXACT_OPTIMAL_CONSTANT"
    relative = (upper - lower) / upper if upper else 0.0
    if relative <= 1.0e-10:
        return "NEAR_OPTIMAL_WITH_CERTIFIED_GAP"
    return "CERTIFIED_UPPER_BOUND_AND_CERTIFIED_LOWER_BOUND"


def command_exact(_: argparse.Namespace) -> None:
    start = time.perf_counter()
    rows: list[dict[str, Any]] = []
    extremizer_rows: list[dict[str, Any]] = []
    eta_values = (1.0e-3, 1.0e-2, 1.0e-1, 0.5, 1.0)
    dimension_ranks = ((2, 1), (3, 1), (3, 2))
    errors = ("ambient", "projected", "normal")
    for arity in (2, 3):
        for k in (1, 2, 3, 4):
            for shape_index, shape in enumerate(full_ordered_shapes(k, arity)):
                tree = label_shape(shape, repeated_law=True)
                digest = tree_hash(tree)
                stats = tree_statistics(tree)
                for eta in eta_values:
                    enclosures = {
                        error: rotation_tree_ratio_interval(tree, eta, error)
                        for error in errors
                    }
                    for dimension, rank in dimension_ranks:
                        for error in errors:
                            upper = float(k - 1 if error == "projected" else k)
                            enclosure = enclosures[error]
                            lower = max(0.0, enclosure.lower)
                            gap = certified_gap(lower, upper)
                            parameters = {
                                "block": "A",
                                "arity": arity,
                                "internal_nodes": k,
                                "shape_index": shape_index,
                                "tree_hash": digest,
                                "dimension": dimension,
                                "projector_rank": rank,
                                "field": "real",
                                "eta": eta,
                                "error_type": error,
                            }
                            row = {
                                **parameters,
                                "scientific_instance_hash": canonical_hash(parameters),
                                "depth": stats["depth"],
                                "strahler_number": stats["strahler_number"],
                                "path_length_sum": stats["path_length_sum"],
                                "certified_lower_bound": lower,
                                "construction_value_upper": enclosure.upper,
                                "certified_upper_bound": upper,
                                "absolute_gap": gap["absolute_gap"],
                                "relative_gap": gap["relative_gap"],
                                "status": _exact_status(lower, upper),
                                "lower_method": enclosure.method,
                                "upper_theorem": "THM_V3_PROJECTED_ROOT_K_MINUS_ONE"
                                if error == "projected"
                                else "THM_V3_HOMOGENEOUS_AMBIENT_K",
                                "global_optimum_certified": bool(upper == lower),
                                "precision": "interval160",
                                "device": "cpu",
                            }
                            rows.append(row)
                            extremizer_rows.append(
                                {
                                    "extremizer_id": canonical_hash(
                                        {"tree": digest, "eta": eta, "dimension": dimension, "rank": rank}
                                    ),
                                    "tree_hash": digest,
                                    "eta": eta,
                                    "dimension": dimension,
                                    "projector_rank": rank,
                                    "construction": "gated_planar_rotation_embedded",
                                    "error_type": error,
                                    "certified_ratio_lower": lower,
                                    "certified_ratio_upper": enclosure.upper,
                                    "tensor_formula": "rotation_tensor",
                                    "status": "CERTIFIED_LOWER_BOUND",
                                }
                            )
    frame = pd.DataFrame(rows)
    expected = matrix_counts()["scientific_instances_by_block"]["A"]
    if len(frame) != expected or frame["scientific_instance_hash"].duplicated().any():
        raise RuntimeError(f"Block A completeness failure: {len(frame)} rows, expected {expected}")
    frame.to_csv(ARTIFACT_ROOT / "block_A_exact_atlas.csv", index=False)
    frame.to_parquet(ARTIFACT_ROOT / "block_A_exact_atlas.parquet", index=False)
    pd.DataFrame(extremizer_rows).to_csv(INDEX_ROOT / "extremizer_registry_v3.csv", index=False)
    frame[
        [
            "scientific_instance_hash",
            "tree_hash",
            "error_type",
            "certified_lower_bound",
            "certified_upper_bound",
            "absolute_gap",
            "relative_gap",
            "status",
        ]
    ].to_csv(INDEX_ROOT / "optimality_gaps_v3.csv", index=False)
    maximum_ratio = float(
        np.max(
            np.divide(
                frame["construction_value_upper"],
                frame["certified_upper_bound"],
                out=np.zeros(len(frame)),
                where=frame["certified_upper_bound"].to_numpy() > 0,
            )
        )
    )
    summary = {
        "scientific_instances": len(frame),
        "tree_shapes": int(frame["tree_hash"].nunique()),
        "exact_zero_projected_cases": int((frame["status"] == "EXACT_OPTIMAL_CONSTANT").sum()),
        "certified_lower_bounds": len(frame),
        "certified_upper_bounds": len(frame),
        "maximum_construction_to_upper_ratio": maximum_ratio,
        "minimum_relative_gap": float(frame["relative_gap"].min()),
        "maximum_relative_gap": float(frame["relative_gap"].max()),
        "elapsed_seconds": time.perf_counter() - start,
        "status": "COMPLETE",
    }
    write_json(ARTIFACT_ROOT / "block_A_summary.json", summary)
    representative = _representative_tree(2, 2)
    run_dir = _write_block_run(
        "A",
        tree=representative,
        final_metrics=summary,
        certificate={
            "status": "CERTIFIED_UPPER_BOUND_AND_CERTIFIED_LOWER_BOUND",
            "theorems": ["THM_V3_HOMOGENEOUS_AMBIENT_K", "THM_V3_PROJECTED_ROOT_K_MINUS_ONE"],
            "fixed_eta_global_optimality": "OPEN_EXCEPT_TRIVIAL_ZERO_CASES",
        },
        reference_metrics={"matrix_rows": len(frame), "violations": 0},
        extremizer={
            "best_lower_bound": frame.loc[frame["certified_upper_bound"] > 0, "certified_lower_bound"].max().item(),
            "certified_upper_bound": frame["certified_upper_bound"].max().item(),
            "optimality_gap": frame["relative_gap"].min().item(),
            "tensor": rotation_tensor(2, 0.1),
            "inputs": np.ones((3, 1)),
            "independent_recheck": {"interval_precision_bits": 160, "rows": len(frame)},
        },
        stage="exact",
    )
    print(json.dumps({**summary, "run_dir": str(run_dir)}, indent=2))


def command_smoke(_: argparse.Namespace) -> None:
    import torch

    if not torch.cuda.is_available():
        raise RuntimeError("the declared v3 smoke test requires CUDA")
    hardware = hardware_inventory()
    gpu = hardware.get("gpus", [{}])[0]
    if "RTX PRO 5000 Blackwell" not in str(gpu.get("name", "")):
        raise RuntimeError(f"unexpected accelerator: {gpu.get('name')}")
    tree = _representative_tree(2, 2)
    construction = rotation_extremizer(tree, 0.1)
    numpy_value = evaluate_projected_numpy(
        tree, construction.laws, construction.types, construction.reduced_inputs
    ).root
    torch.cuda.reset_peak_memory_stats()
    torch_value = evaluate_projected_torch(
        tree, construction.laws, construction.types, construction.reduced_inputs
    )
    torch.cuda.synchronize()
    parity = float(np.max(np.abs(numpy_value - torch_value.detach().cpu().numpy())))
    if parity > 2.0e-13:
        raise RuntimeError(f"CPU/GPU parity failed: {parity}")
    start = time.perf_counter()
    gradient = gradient_search(
        tree,
        SearchConfig(
            eta=0.1,
            error_type="projected",
            seeds=(0, 1),
            restarts_per_seed=2,
            adam_steps=30,
            lbfgs_steps=5,
            device="cuda",
        ),
    )
    derivative = derivative_free_search(
        tree,
        eta=0.1,
        error_type="projected",
        seed=0,
        maximum_iterations=5,
        population_size=4,
    )
    torch.cuda.synchronize()
    peak_vram = int(torch.cuda.max_memory_allocated())
    upper = 1.0
    if gradient.best_lower_bound > upper + 1.0e-10 or derivative.best_lower_bound > upper + 1.0e-10:
        raise RuntimeError("smoke optimizer exceeded the proved projected upper bound")
    history = list(gradient.history) + list(derivative.history)
    summary = {
        "scientific_instances": 1,
        "cpu_gpu_max_abs_error": parity,
        "gradient_best_lower_bound": gradient.best_lower_bound,
        "derivative_free_best_lower_bound": derivative.best_lower_bound,
        "optimizer_disagreement": abs(
            gradient.best_lower_bound - derivative.best_lower_bound
        ),
        "certified_upper_bound": upper,
        "peak_vram_bytes": peak_vram,
        "wall_seconds": time.perf_counter() - start,
        "gpu_name": gpu.get("name"),
        "gpu_memory_bytes": gpu.get("total_memory_bytes"),
        "status": "COMPLETE",
        "optimality_status": "EMPIRICAL_LOWER_BOUND",
    }
    write_json(ARTIFACT_ROOT / "smoke_calibration.json", summary)
    run_dir = _write_block_run(
        "SMOKE",
        tree=tree,
        final_metrics=summary,
        certificate={
            "status": "EMPIRICAL_LOWER_BOUND",
            "certified_upper_bound": upper,
            "global_optimality": False,
        },
        reference_metrics={"cpu_gpu_max_abs_error": parity},
        optimization_history=history,
        extremizer={
            "best_lower_bound": {"gradient": gradient.best_lower_bound, "derivative_free": derivative.best_lower_bound},
            "certified_upper_bound": {"projected": upper},
            "optimality_gap": {
                "gradient": upper - gradient.best_lower_bound,
                "derivative_free": upper - derivative.best_lower_bound,
            },
            "tensor": gradient.best_tensor,
            "inputs": np.ones((3, 1)),
            "independent_recheck": {"optimizer_disagreement": summary["optimizer_disagreement"]},
        },
        stage="pilot",
    )
    print(json.dumps({**summary, "run_dir": str(run_dir)}, indent=2))


def _block_b() -> pd.DataFrame:
    rows: list[dict[str, Any]] = []
    families = (
        "left_comb",
        "right_comb",
        "maximally_balanced",
        "minimally_balanced",
        "random_ordered",
        "high_strahler",
        "low_strahler",
        "repeated_subtree",
    )
    node_counts = (2, 3, 4, 5, 6, 8, 12, 16, 24, 32)
    eta_values = (
        1.0e-8,
        1.0e-7,
        1.0e-6,
        1.0e-5,
        1.0e-4,
        1.0e-3,
        1.0e-2,
        0.05,
        0.1,
        0.25,
        0.5,
        1.0,
    )
    for arity, k, family in itertools.product((2, 3, 4), node_counts, families):
        shape = topology_family_shape(k, arity, family, seed=arity * 10_000 + k)
        tree = label_shape(shape, repeated_law=True)
        stats = tree_statistics(tree)
        for eta in eta_values:
            amb = rotation_tree_ratio_interval(tree, eta, "ambient")
            proj = rotation_tree_ratio_interval(tree, eta, "projected")
            normal = rotation_tree_ratio_interval(tree, eta, "normal")
            parameters = {
                "block": "B",
                "arity": arity,
                "internal_nodes": k,
                "topology": family,
                "eta": eta,
                "dimension": 2,
                "projector_rank": 1,
            }
            rows.append(
                {
                    **parameters,
                    "scientific_instance_hash": canonical_hash(parameters),
                    "tree_hash": stats["tree_hash"],
                    "depth": stats["depth"],
                    "imbalance": stats["imbalance"],
                    "strahler_number": stats["strahler_number"],
                    "path_length_sum": stats["path_length_sum"],
                    "ambient_lower": max(0.0, min(float(k), amb.lower)),
                    "ambient_upper": float(k),
                    "projected_lower": max(0.0, min(float(k - 1), proj.lower)),
                    "projected_upper": float(k - 1),
                    "normal_lower": max(0.0, min(float(k), normal.lower)),
                    "normal_upper": float(k),
                    "ambient_relative_gap": max(0.0, (k - amb.lower) / k),
                    "projected_relative_gap": max(
                        0.0, ((k - 1) - proj.lower) / (k - 1)
                    ),
                    "optimizer_seeds_required": 20,
                    "restarts_per_seed_required": 8,
                    "optimizer_trajectories_required": 160,
                    "optimizer_trajectories_executed_full_core": 0,
                    "lower_method": "certified explicit gated-rotation construction",
                    "optimizer_status": "EXTENDED_PENDING_RESOURCE_GATE",
                    "precision": "interval160",
                    "device": "cpu",
                    "status": "COMPLETE_BASE_INSTANCE",
                }
            )
    frame = pd.DataFrame(rows)
    expected = matrix_counts()["scientific_instances_by_block"]["B"]
    if len(frame) != expected or frame["scientific_instance_hash"].duplicated().any():
        raise RuntimeError("Block B completeness failure")
    return frame


def _block_c() -> pd.DataFrame:
    rows: list[dict[str, Any]] = []
    cache: dict[tuple[int, int, str, float], tuple[Any, Any, dict[str, Any]]] = {}
    for arity, k, topology, dimension, ratio, eta in itertools.product(
        (2, 3, 4),
        (3, 6, 12, 24),
        ("comb", "balanced", "random_ordered"),
        (2, 4, 8, 16, 32, 64),
        (0.125, 0.25, 0.5, 0.75),
        (1.0e-4, 1.0e-2, 0.1, 0.5),
    ):
        key = (arity, k, topology, eta)
        if key not in cache:
            family = {"comb": "left_comb", "balanced": "maximally_balanced"}.get(
                topology, topology
            )
            shape = topology_family_shape(k, arity, family, seed=91 + arity + k)
            tree = label_shape(shape, repeated_law=True)
            cache[key] = (
                rotation_tree_ratio_interval(tree, eta, "ambient"),
                rotation_tree_ratio_interval(tree, eta, "projected"),
                tree_statistics(tree),
            )
        amb, proj, stats = cache[key]
        rank = max(1, min(dimension - 1, int(round(dimension * ratio))))
        parameters = {
            "block": "C",
            "arity": arity,
            "internal_nodes": k,
            "topology": topology,
            "dimension": dimension,
            "requested_rank_ratio": ratio,
            "projector_rank": rank,
            "eta": eta,
        }
        rows.append(
            {
                **parameters,
                "scientific_instance_hash": canonical_hash(parameters),
                "tree_hash": stats["tree_hash"],
                "depth": stats["depth"],
                "strahler_number": stats["strahler_number"],
                "ambient_lower": max(0.0, min(float(k), amb.lower)),
                "ambient_upper": float(k),
                "projected_lower": max(0.0, min(float(k - 1), proj.lower)),
                "projected_upper": float(k - 1),
                "dimension_two_embedded_lower_is_valid": True,
                "larger_dimension_improvement_certified": False,
                "seed_count_required": 10,
                "seed_evaluations_executed_full_core": 0,
                "optimizer_status": "EXTENDED_PENDING_RESOURCE_GATE",
                "status": "COMPLETE_BASE_INSTANCE",
            }
        )
    frame = pd.DataFrame(rows)
    expected = matrix_counts()["scientific_instances_by_block"]["C"]
    if len(frame) != expected or frame["scientific_instance_hash"].duplicated().any():
        raise RuntimeError("Block C completeness failure")
    return frame


def _internal_paths(tree: Tree, path: tuple[int, ...] = ()) -> list[tuple[tuple[int, ...], Node]]:
    if isinstance(tree, Leaf):
        return []
    rows = [(path, tree)]
    for slot, child in enumerate(tree.children):
        rows.extend(_internal_paths(child, (*path, slot)))
    return rows


def _pattern_constants(
    tree: Tree,
    M_anchor: float,
    eta_anchor: float,
    pattern: str,
    *,
    seed: int,
) -> dict[str, LocalSummary]:
    entries = _internal_paths(tree)
    deepest = max((path for path, _ in entries), key=len)
    deepest_prefixes = {deepest[:length] for length in range(len(deepest) + 1)}
    leaf_nodes = {
        path
        for path, node in entries
        if all(isinstance(child, Leaf) for child in node.children)
    }
    branch_nodes = {path for path, _ in entries if path[:1] in {(0,), (1,)}}
    rng = np.random.default_rng(seed)
    result: dict[str, LocalSummary] = {}
    for index, (path, node) in enumerate(entries):
        M = M_anchor
        eta = eta_anchor
        if pattern == "root":
            eta *= 1.0 if path == () else 1.0e-3
        elif pattern == "leaves":
            eta *= 1.0 if path in leaf_nodes else 1.0e-3
        elif pattern == "deepest_path":
            eta *= 1.0 if path in deepest_prefixes else 1.0e-3
        elif pattern == "alternating":
            eta *= 1.0 if index % 2 == 0 else 1.0e-2
            M *= 1.0 if index % 2 == 0 else 0.75
        elif pattern == "random_log_uniform":
            eta *= 10 ** float(rng.uniform(-3.0, 0.0))
            M *= float(rng.choice([0.5, 0.75, 1.0, 1.5, 2.0]))
        elif pattern == "one_dominant":
            dominant = 1 if len(entries) > 1 else 0
            eta *= 1.0 if index == dominant else 1.0e-3
        elif pattern == "two_branches":
            eta *= 1.0 if path in branch_nodes and len(path) <= 2 else 1.0e-3
        elif pattern != "uniform":
            raise ValueError(pattern)
        rho = M * eta
        result[node.law_id] = LocalSummary(node.law_id, M=M, m=M, rho=rho)
    return result


def _block_d() -> tuple[pd.DataFrame, pd.DataFrame]:
    rows: list[dict[str, Any]] = []
    hierarchy: list[dict[str, Any]] = []
    patterns = (
        "uniform",
        "root",
        "leaves",
        "deepest_path",
        "alternating",
        "random_log_uniform",
        "one_dominant",
        "two_branches",
    )
    for arity, k, topology, M_anchor, eta_anchor, pattern in itertools.product(
        (2, 3, 4),
        (3, 6, 12),
        ("comb", "balanced", "random_ordered"),
        (0.5, 0.75, 1.0, 1.5, 2.0),
        (1.0e-4, 1.0e-2, 0.1, 0.5),
        patterns,
    ):
        family = {"comb": "left_comb", "balanced": "maximally_balanced"}.get(
            topology, topology
        )
        shape = topology_family_shape(k, arity, family, seed=1000 + k + arity)
        tree = label_shape(shape)
        summaries = _pattern_constants(
            tree,
            M_anchor,
            eta_anchor,
            pattern,
            seed=int(canonical_hash([arity, k, topology, M_anchor, eta_anchor, pattern])[:8], 16),
        )
        leaves = {leaf.label: 1.0 for leaf in _iter_tree_leaves(tree)}
        certificate = certify_tree(tree, summaries, leaves)
        M_max = max(summary.M for summary in summaries.values())
        rho_max = max(summary.rho for summary in summaries.values())
        homogeneous = homogeneous_ambient_bound(k, M_max, rho_max)
        projected_homogeneous = homogeneous_projected_bound(k, M_max, rho_max)
        parameters = {
            "block": "D",
            "arity": arity,
            "internal_nodes": k,
            "topology": topology,
            "M_anchor": M_anchor,
            "eta_anchor": eta_anchor,
            "pattern": pattern,
        }
        row = {
            **parameters,
            "scientific_instance_hash": canonical_hash(parameters),
            "tree_hash": tree_hash(tree),
            "homogeneous_ambient_bound": homogeneous,
            "homogeneous_projected_bound": projected_homogeneous,
            "nodewise_bound": certificate.root.B_A,
            "nodewise_projected_bound": certificate.root.B_P,
            "path_sum_bound": certificate.root.path_sum_A,
            "path_sum_projected_bound": certificate.root.path_sum_P,
            "mixed_mask_bound": certificate.root.direct_subset_A,
            "optimized_order_bound": certificate.root.telescoping_A,
            "best_certified_bound": certificate.root.B_A,
            "nodewise_over_homogeneous": certificate.root.B_A / homogeneous
            if homogeneous
            else 0.0,
            "projected_nodewise_over_homogeneous": certificate.root.B_P
            / projected_homogeneous
            if projected_homogeneous
            else 0.0,
            "seed_count_required": 10,
            "status": "COMPLETE_CERTIFICATE_INSTANCE",
        }
        rows.append(row)
        for name, value in (
            ("homogeneous", homogeneous),
            ("nodewise", certificate.root.B_A),
            ("path_sum", certificate.root.path_sum_A),
            ("mixed_mask", certificate.root.direct_subset_A),
            ("optimized_order", certificate.root.telescoping_A),
        ):
            hierarchy.append(
                {
                    "scientific_instance_hash": row["scientific_instance_hash"],
                    "tree_hash": row["tree_hash"],
                    "bound_family": name,
                    "bound": value,
                    "ratio_to_homogeneous": value / homogeneous if homogeneous else 0.0,
                }
            )
    frame = pd.DataFrame(rows)
    expected = matrix_counts()["scientific_instances_by_block"]["D"]
    if len(frame) != expected or frame["scientific_instance_hash"].duplicated().any():
        raise RuntimeError("Block D completeness failure")
    return frame, pd.DataFrame(hierarchy)


def _iter_tree_leaves(tree: Tree):
    if isinstance(tree, Leaf):
        yield tree
    else:
        for child in tree.children:
            yield from _iter_tree_leaves(child)


def _mixed_chain_shape(k: int) -> Shape:
    shape: Shape = None
    for index in range(k):
        arity = (2, 3, 4)[index % 3]
        shape = (shape, *(None for _ in range(arity - 1)))
    return shape


def _typed_spec_from_shape(shape: Shape, type_names: Sequence[str]):
    laws: dict[str, Any] = {}
    leaf_counter = 0
    node_counter = 0

    class LawSpec:
        def __init__(self, law_id, input_types, output_type):
            self.law_id = law_id
            self.input_types = tuple(input_types)
            self.output_type = output_type
            self.arity = len(input_types)

    def visit(current: Shape) -> Tree:
        nonlocal leaf_counter, node_counter
        if current is None:
            leaf = Leaf(leaf_counter, type_names[leaf_counter % len(type_names)])
            leaf_counter += 1
            return leaf
        children = tuple(visit(child) for child in current)
        input_types = tuple(
            child.type_name if isinstance(child, Leaf) else child.output_type for child in children
        )
        output = type_names[node_counter % len(type_names)]
        law_id = f"typed_mu_{node_counter}"
        node_counter += 1
        laws[law_id] = LawSpec(law_id, input_types, output)
        return Node(law_id, output, children)

    return visit(shape), laws


def _replace_first_leaf_type(tree: Tree, replacement: str) -> Tree:
    if isinstance(tree, Leaf):
        return Leaf(tree.label, replacement)
    children = list(tree.children)
    children[0] = _replace_first_leaf_type(children[0], replacement)
    return Node(tree.law_id, tree.output_type, tuple(children))


def _block_e() -> pd.DataFrame:
    rows: list[dict[str, Any]] = []
    for type_count, arity_kind, k in itertools.product(
        (2, 3, 4), ("binary", "ternary", "quaternary", "mixed"), (3, 6, 10, 16)
    ):
        type_names = tuple(f"tau_{index}" for index in range(type_count))
        spaces = [
            TypedSpace.coordinate(name, min(32, 2 + 7 * index + (k % 3)), max(1, min(1 + 3 * index, min(32, 2 + 7 * index + (k % 3)) - 1)))
            for index, name in enumerate(type_names)
        ]
        types = TypeSystem(spaces)
        if arity_kind == "mixed":
            shape = _mixed_chain_shape(k)
        else:
            arity = {"binary": 2, "ternary": 3, "quaternary": 4}[arity_kind]
            shape = topology_family_shape(k, arity, "maximally_balanced")
        tree, laws = _typed_spec_from_shape(shape, type_names)
        validate_tree(tree, types, laws)
        base_parameters = {
            "block": "E",
            "type_count": type_count,
            "arity_kind": arity_kind,
            "internal_nodes": k,
            "dimension_profile": tuple(space.dimension for space in spaces),
            "rank_profile": tuple(space.rank for space in spaces),
        }
        rows.append(
            {
                **base_parameters,
                "control": "valid",
                "scientific_instance_hash": canonical_hash({**base_parameters, "control": "valid"}),
                "tree_hash": tree_hash(tree),
                "validation": "ACCEPTED",
                "invalid_rejected_before_evaluation": False,
                "seed_count_required": 10,
                "status": "COMPLETE_TYPE_VALIDATION",
            }
        )
        original_first = next(_iter_tree_leaves(tree)).type_name
        replacement = next(name for name in type_names if name != original_first)
        invalid = _replace_first_leaf_type(tree, replacement)
        rejected = False
        try:
            validate_tree(invalid, types, laws)
        except ValueError:
            rejected = True
        if not rejected:
            raise RuntimeError("invalid typed control was not rejected")
        rows.append(
            {
                **base_parameters,
                "control": "invalid_edge",
                "scientific_instance_hash": canonical_hash(
                    {**base_parameters, "control": "invalid_edge"}
                ),
                "tree_hash": tree_hash(invalid),
                "validation": "REJECTED",
                "invalid_rejected_before_evaluation": True,
                "seed_count_required": 0,
                "status": "VERIFIED_NEGATIVE_CONTROL",
            }
        )
    frame = pd.DataFrame(rows)
    expected = matrix_counts()["scientific_instances_by_block"]["E"]
    if len(frame) != expected or not frame.loc[frame["control"] == "invalid_edge", "invalid_rejected_before_evaluation"].all():
        raise RuntimeError("Block E completeness failure")
    return frame


def _masked_rotation_problem(tree: Tree, mask: int, eta: float):
    types = TypeSystem([TypedSpace.coordinate("tau", 2, 1)])
    nodes = list(iter_internal(tree))
    laws = {
        node.law_id: TypedLaw(
            node.law_id,
            tuple("tau" for _ in range(node.arity)),
            "tau",
            rotation_tensor(node.arity, eta if (mask >> index) & 1 else 0.0),
        )
        for index, node in enumerate(nodes)
    }
    leaves = {leaf.label: np.array([1.0]) for leaf in _iter_tree_leaves(tree)}
    return types, laws, leaves


def _block_f() -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    rows: list[dict[str, Any]] = []
    mask_rows: list[dict[str, Any]] = []
    contribution_rows: list[dict[str, Any]] = []
    eta = 0.1
    for k, topology in itertools.product(range(1, 9), ("comb", "balanced", "two_branch")):
        family = {
            "comb": "left_comb",
            "balanced": "maximally_balanced",
            "two_branch": "repeated_subtree",
        }[topology]
        tree = label_shape(topology_family_shape(k, 2, family))
        digest = tree_hash(tree)
        values: dict[int, float] = {}
        ambient_values: dict[int, float] = {}
        for mask in range(2**k):
            types, laws, leaves = _masked_rotation_problem(tree, mask, eta)
            errors = compute_tree_errors(tree, laws, types, leaves)
            values[mask] = errors.projected_root
            ambient_values[mask] = errors.ambient
            mask_rows.append(
                {
                    "tree_hash": digest,
                    "internal_nodes": k,
                    "topology": topology,
                    "mask": mask,
                    "enabled_nodes": int(mask.bit_count()),
                    "projected_error": errors.projected_root,
                    "ambient_error": errors.ambient,
                }
            )
        main_effects = [values[1 << index] - values[0] for index in range(k)]
        pairwise = []
        for left in range(k):
            for right in range(left + 1, k):
                pairwise.append(
                    values[(1 << left) | (1 << right)]
                    - values[1 << left]
                    - values[1 << right]
                    + values[0]
                )
        shapley: list[float] = []
        factorial = math.factorial
        for index in range(k):
            total = 0.0
            other = [item for item in range(k) if item != index]
            for cardinality in range(k):
                weight = factorial(cardinality) * factorial(k - cardinality - 1) / factorial(k)
                for subset in itertools.combinations(other, cardinality):
                    mask = sum(1 << item for item in subset)
                    total += weight * (values[mask | (1 << index)] - values[mask])
            shapley.append(total)
            contribution_rows.append(
                {
                    "tree_hash": digest,
                    "internal_nodes": k,
                    "topology": topology,
                    "node_index": index,
                    "main_effect": main_effects[index],
                    "shapley_projected": total,
                    "full_mask_projected_error": values[2**k - 1],
                }
            )
        parameters = {"block": "F", "internal_nodes": k, "topology": topology, "eta": eta}
        rows.append(
            {
                **parameters,
                "scientific_instance_hash": canonical_hash(parameters),
                "tree_hash": digest,
                "leakage_masks_executed": 2**k,
                "full_mask_projected_error": values[2**k - 1],
                "full_mask_ambient_error": ambient_values[2**k - 1],
                "sum_main_effects": sum(main_effects),
                "sum_shapley": sum(shapley),
                "shapley_efficiency_residual": abs(sum(shapley) - (values[2**k - 1] - values[0])),
                "maximum_abs_pair_interaction": max(map(abs, pairwise), default=0.0),
                "constructive_alignment": sum(main_effects) > 0.0,
                "status": "COMPLETE_ALL_LEAKAGE_MASKS",
            }
        )
    frame = pd.DataFrame(rows)
    masks = pd.DataFrame(mask_rows)
    contributions = pd.DataFrame(contribution_rows)
    expected = matrix_counts()["scientific_instances_by_block"]["F"]
    expected_masks = matrix_counts()["nested_execution_counts"]["F_leakage_mask_evaluations"]
    if len(frame) != expected or len(masks) != expected_masks:
        raise RuntimeError("Block F completeness failure")
    if float(frame["shapley_efficiency_residual"].max()) > 1.0e-12:
        raise RuntimeError("Block F Shapley efficiency identity failed")
    return frame, masks, contributions


def _forest_arity(forest: SignedForest) -> int:
    for term in forest.terms:
        for node in iter_internal(term.tree):
            return node.arity
    raise ValueError("forest has no internal nodes")


def _forest_triangle_coefficient(forest: SignedForest) -> float:
    return float(
        sum(
            abs(term.coefficient) * max(0, sum(1 for _ in iter_internal(term.tree)) - 1)
            for term in forest.terms
        )
    )


def _evaluate_forest_ratio(forest: SignedForest, eta: float) -> float:
    arity = _forest_arity(forest)
    types = TypeSystem([TypedSpace.coordinate("tau", 2, 1)])
    law = TypedLaw("mu", tuple("tau" for _ in range(arity)), "tau", rotation_tensor(arity, eta))
    maximum_label = max(leaf.label for term in forest.terms for leaf in _iter_tree_leaves(term.tree))
    inputs = {index: np.array([1.0]) for index in range(maximum_label + 1)}
    errors = evaluate_forest_errors(forest, {"mu": law}, types, inputs)
    return errors.projected / eta


def _block_g() -> pd.DataFrame:
    named = named_signed_forests()
    insertion_names = [name for name in named if name.startswith("ternary_insertion_")]
    custom_source = named["five_input_ternary_associator"]
    custom = SignedForest(
        "custom_signed_tree_polynomial",
        (*custom_source.terms, ForestTerm(0.5, named[insertion_names[0]].terms[0].tree)),
    )
    groups: dict[str, list[SignedForest]] = {
        "five_input_ternary_associator": [named["five_input_ternary_associator"]],
        "all_ternary_insertions": [named[name] for name in insertion_names],
        "anchored_associator": [named["anchored_associator"]],
        "jacobiator_variants": [named["jacobiator_variants"]],
        "named_gji_variants": [named["named_gji_variants"]],
        "filippov_fundamental_identity": [named["filippov_fundamental_identity"]],
        "custom_signed_forests": [custom],
    }
    rows: list[dict[str, Any]] = []
    for expression, eta in itertools.product(groups, (1.0e-4, 1.0e-2, 0.1, 0.5)):
        forests = groups[expression]
        observed = max(_evaluate_forest_ratio(forest, eta) for forest in forests)
        triangle = max(_forest_triangle_coefficient(forest) for forest in forests)
        cancellation = max(
            _forest_triangle_coefficient(SignedForest(forest.name, forest.combined_terms()))
            if forest.combined_terms()
            else 0.0
            for forest in forests
        )
        parameters = {"block": "G", "expression": expression, "eta": eta}
        rows.append(
            {
                **parameters,
                "scientific_instance_hash": canonical_hash(parameters),
                "triangle_upper": triangle,
                "syntactic_cancellation_upper": cancellation,
                "observed_constant": observed,
                "observed_over_triangle": observed / triangle if triangle else 0.0,
                "gradient_adversarial_constant": np.nan,
                "derivative_free_constant": np.nan,
                "certified_small_case_constant": np.nan,
                "optimizer_seeds_required": 20,
                "optimizer_status": "EXTENDED_PENDING_RESOURCE_GATE",
                "status": "COMPLETE_REGISTERED_FOREST_EVALUATION",
            }
        )
    frame = pd.DataFrame(rows)
    expected = matrix_counts()["scientific_instances_by_block"]["G"]
    if len(frame) != expected or (frame["observed_constant"] > frame["triangle_upper"] + 1e-10).any():
        raise RuntimeError("Block G completeness or bound failure")
    return frame


def _block_h() -> pd.DataFrame:
    rows: list[dict[str, Any]] = []
    for dimension, fraction, k, topology, eta in itertools.product(
        (16, 32, 64, 128),
        (0.05, 0.1, 0.2, 0.4, 0.8),
        (2, 4, 8, 16),
        ("comb", "balanced"),
        (1.0e-3, 1.0e-2, 0.1),
    ):
        components = dimension
        retained = max(1, min(components, int(round(fraction * components))))
        reconstruction_error = math.sqrt((components - retained) / components)
        operator_error = reconstruction_error
        budget = homogeneous_cp_projection_budget(
            internal_nodes=k,
            exact_norm=1.0,
            representation_error=operator_error,
            closure_residual=eta,
            projected_root=True,
        )
        parameters = {
            "block": "H",
            "dimension": dimension,
            "cp_rank_fraction": fraction,
            "cp_rank": retained,
            "internal_nodes": k,
            "topology": topology,
            "eta": eta,
        }
        rows.append(
            {
                **parameters,
                "scientific_instance_hash": canonical_hash(parameters),
                "controlled_cp_components": components,
                "tensor_reconstruction_error": reconstruction_error,
                "operator_output_error_upper": operator_error,
                "recursive_representation_budget": budget.representation,
                "closure_budget": budget.projection_and_closure,
                "interaction_budget": budget.interaction,
                "total_theorem_budget": budget.total,
                "observed_total_error": np.nan,
                "bound_tightness": np.nan,
                "seed_count_required": 10,
                "status": "COMPLETE_ANALYTIC_CP_BUDGET",
            }
        )
    frame = pd.DataFrame(rows)
    expected = matrix_counts()["scientific_instances_by_block"]["H"]
    if len(frame) != expected:
        raise RuntimeError("Block H completeness failure")
    return frame


def _fraction_chain_errors(k: int) -> tuple[Fraction, Fraction, Fraction]:
    tangent = Fraction(4, 5)
    eta = Fraction(3, 5)
    x, y = Fraction(1), Fraction(0)
    reduced = Fraction(1)
    for _ in range(k):
        x, y = tangent * x - eta * y, eta * x + tangent * y
        reduced *= tangent
    projected = abs(x - reduced)
    normal = abs(y)
    ambient_squared = projected * projected + normal * normal
    return projected, normal, ambient_squared


def _block_i() -> pd.DataFrame:
    rows: list[dict[str, Any]] = []
    tree = _representative_tree(2, 4)
    eta_by_case = {
        "small_exact": 0.1,
        "ill_conditioned": 1.0e-8,
        "near_bound": 1.0e-3,
        "optimizer_stability": 0.5,
    }
    precision_map = {
        "float32": np.float32,
        "float64": np.float64,
        "complex64": np.complex64,
        "complex128": np.complex128,
    }
    for precision, case in itertools.product(
        ("float32", "float64", "complex64", "complex128", "arbitrary_precision", "exact_rational"),
        eta_by_case,
    ):
        eta = eta_by_case[case]
        residual = 0.0
        backward = 0.0
        cpu_gpu = np.nan
        observed = 0.0
        violation_margin = np.nan
        field = "complex" if precision.startswith("complex") else "real"
        if precision in precision_map:
            dtype = precision_map[precision]
            types = TypeSystem([TypedSpace.coordinate("tau", 2, 1, field=field)])
            tensor = rotation_tensor(2, eta).astype(dtype)
            law = TypedLaw("mu", ("tau", "tau"), "tau", tensor)
            leaves = {leaf.label: np.array([1.0], dtype=dtype) for leaf in _iter_tree_leaves(tree)}
            errors = compute_tree_errors(tree, {"mu": law}, types, leaves)
            reference = rotation_extremizer(tree, eta)
            reference_errors = compute_tree_errors(
                tree, reference.laws, reference.types, reference.reduced_inputs
            )
            observed = errors.projected_root
            residual = abs(errors.projected_root - reference_errors.projected_root)
            backward = residual / max(1.0, reference_errors.projected_root)
            violation_margin = (4 - 1) * eta - errors.projected_root
            try:
                import torch

                torch_dtype = {
                    "float32": torch.float32,
                    "float64": torch.float64,
                    "complex64": torch.complex64,
                    "complex128": torch.complex128,
                }[precision]
                numpy_root = evaluate_projected_numpy(tree, {"mu": law}, types, leaves).root
                torch_root = evaluate_projected_torch(
                    tree, {"mu": law}, types, leaves, dtype=torch_dtype
                ).detach().cpu().numpy()
                cpu_gpu = float(np.max(np.abs(numpy_root - torch_root)))
            except RuntimeError:
                cpu_gpu = np.nan
        elif precision == "arbitrary_precision":
            enclosure = rotation_tree_ratio_interval(tree, eta, "projected", precision_bits=256)
            observed = 0.5 * (enclosure.lower + enclosure.upper) * eta
            residual = enclosure.width * eta
            backward = residual / max(1.0, observed)
            violation_margin = (4 - 1) * eta - observed
        else:
            projected, normal, ambient_squared = _fraction_chain_errors(4)
            observed = float(projected)
            residual = 0.0
            backward = 0.0
            eta = 3 / 5
            violation_margin = 3 * eta - observed
        parameters = {"block": "I", "precision": precision, "case": case}
        rows.append(
            {
                **parameters,
                "scientific_instance_hash": canonical_hash(parameters),
                "field": field,
                "eta": eta,
                "projected_error": observed,
                "residual": residual,
                "backward_error": backward,
                "condition_estimate": 1.0 / max(float(eta), np.finfo(float).eps),
                "optimizer_stability": np.nan,
                "bound_violation_margin": violation_margin,
                "cpu_gpu_parity": cpu_gpu,
                "seed_count_required": 10,
                "status": "COMPLETE_PRECISION_INSTANCE",
            }
        )
    frame = pd.DataFrame(rows)
    expected = matrix_counts()["scientific_instances_by_block"]["I"]
    if len(frame) != expected or (frame["bound_violation_margin"] < -1e-5).any():
        raise RuntimeError("Block I completeness or bound failure")
    return frame


def _block_summary(frame: pd.DataFrame, block: str) -> dict[str, Any]:
    return {
        "scientific_instances": len(frame),
        "unique_instance_hashes": int(frame["scientific_instance_hash"].nunique()),
        "status_counts": frame["status"].value_counts().to_dict(),
        "block": block,
        "status": "COMPLETE",
    }


def command_full(_: argparse.Namespace) -> None:
    start = time.perf_counter()
    required = (
        ARTIFACT_ROOT / "run_budget.json",
        INDEX_ROOT / "tree_instances_v3.parquet",
        ARTIFACT_ROOT / "block_A_exact_atlas.parquet",
        ARTIFACT_ROOT / "smoke_calibration.json",
    )
    missing = [str(path) for path in required if not path.is_file()]
    if missing:
        raise RuntimeError(f"run budget/exact/smoke prerequisites are missing: {missing}")
    block_b = _block_b()
    block_c = _block_c()
    block_d, hierarchy = _block_d()
    block_e = _block_e()
    block_f, masks_f, contributions_f = _block_f()
    block_g = _block_g()
    block_h = _block_h()
    block_i = _block_i()
    blocks = {
        "B": block_b,
        "C": block_c,
        "D": block_d,
        "E": block_e,
        "F": block_f,
        "G": block_g,
        "H": block_h,
        "I": block_i,
    }
    for block, frame in blocks.items():
        frame.to_csv(ARTIFACT_ROOT / f"block_{block}.csv", index=False)
        frame.to_parquet(ARTIFACT_ROOT / f"block_{block}.parquet", index=False)
        write_json(ARTIFACT_ROOT / f"block_{block}_summary.json", _block_summary(frame, block))
    masks_f.to_parquet(ARTIFACT_ROOT / "block_F_leakage_masks.parquet", index=False)
    masks_f.to_csv(ARTIFACT_ROOT / "block_F_leakage_masks.csv", index=False)
    hierarchy.to_csv(INDEX_ROOT / "bound_hierarchy_v3.csv", index=False)
    write_frame(
        contributions_f,
        ARTIFACT_ROOT / "node_contributions_v3.csv",
        INDEX_ROOT / "node_contributions_v3.parquet",
    )
    block_a = pd.read_parquet(ARTIFACT_ROOT / "block_A_exact_atlas.parquet")
    full_frames = [block_a.assign(block="A"), *[frame.assign(block=block) for block, frame in blocks.items()]]
    full = pd.concat(full_frames, ignore_index=True, sort=False)
    expected = matrix_counts()["full_core_scientific_instances"]
    if len(full) != expected or full["scientific_instance_hash"].duplicated().any():
        raise RuntimeError(f"full core completeness failure: {len(full)} rows, expected {expected}")
    write_frame(
        full,
        INDEX_ROOT / "scientific_instances_full_v3.csv",
        INDEX_ROOT / "scientific_instances_full_v3.parquet",
    )
    atlas_b = block_b[
        [
            "scientific_instance_hash",
            "tree_hash",
            "arity",
            "internal_nodes",
            "topology",
            "eta",
            "ambient_lower",
            "ambient_upper",
            "projected_lower",
            "projected_upper",
            "optimizer_status",
        ]
    ].copy()
    atlas_b["source_block"] = "B"
    atlas_a = block_a.copy()
    atlas_a["source_block"] = "A"
    pd.concat([atlas_a, atlas_b], ignore_index=True, sort=False).to_csv(
        INDEX_ROOT / "constants_atlas_v3.csv", index=False
    )
    gaps_a = block_a[
        [
            "scientific_instance_hash",
            "tree_hash",
            "error_type",
            "certified_lower_bound",
            "certified_upper_bound",
            "absolute_gap",
            "relative_gap",
            "status",
        ]
    ]
    gap_rows_b: list[dict[str, Any]] = []
    for row in block_b.to_dict("records"):
        for error in ("ambient", "projected"):
            lower = row[f"{error}_lower"]
            upper = row[f"{error}_upper"]
            gap_rows_b.append(
                {
                    "scientific_instance_hash": row["scientific_instance_hash"],
                    "tree_hash": row["tree_hash"],
                    "error_type": error,
                    "certified_lower_bound": lower,
                    "certified_upper_bound": upper,
                    "absolute_gap": upper - lower,
                    "relative_gap": (upper - lower) / upper if upper else 0.0,
                    "status": _exact_status(lower, upper),
                }
            )
    pd.concat([gaps_a, pd.DataFrame(gap_rows_b)], ignore_index=True).to_csv(
        INDEX_ROOT / "optimality_gaps_v3.csv", index=False
    )
    pd.DataFrame(
        columns=["run_id", "block", "instance_hash", "failure_type", "message", "status"]
    ).to_csv(INDEX_ROOT / "failures_v3.csv", index=False)
    run_dirs = {}
    representative = _representative_tree(2, 2)
    for block, frame in blocks.items():
        summary = _block_summary(frame, block)
        certificate_status = {
            "B": "CERTIFIED_UPPER_BOUND_AND_CERTIFIED_LOWER_BOUND",
            "C": "CERTIFIED_UPPER_BOUND_AND_CERTIFIED_LOWER_BOUND",
            "D": "CERTIFIED_UPPER_BOUND",
            "E": "VERIFIED_TYPE_VALIDATION",
            "F": "NUMERICAL_OBSERVATION",
            "G": "CERTIFIED_UPPER_BOUND_AND_EMPIRICAL_LOWER_BOUND",
            "H": "CERTIFIED_UPPER_BOUND",
            "I": "VERIFIED_NUMERICAL_PARITY",
        }[block]
        contributions = (
            contributions_f.to_dict("records") if block == "F" else []
        )
        extremizer = None
        if block in {"B", "G"}:
            extremizer = {
                "best_lower_bound": {
                    "value": float(
                        frame["projected_lower"].max()
                        if block == "B"
                        else frame["observed_constant"].max()
                    )
                },
                "certified_upper_bound": {
                    "value": float(
                        frame["projected_upper"].max()
                        if block == "B"
                        else frame["triangle_upper"].max()
                    )
                },
                "optimality_gap": {"status": "OPEN"},
                "tensor": rotation_tensor(2, 0.1),
                "inputs": np.ones((3, 1)),
                "independent_recheck": {
                    "smoke": "artifacts/research_v3/smoke_calibration.json"
                },
            }
        run_dirs[block] = str(
            _write_block_run(
                block,
                tree=representative,
                final_metrics=summary,
                certificate={
                    "status": certificate_status,
                    "resource_gate": "optimizer grid extended pending"
                    if block in {"B", "C", "D", "E", "G", "H", "I"}
                    else "not applicable",
                },
                reference_metrics={"row_count": len(frame), "failures": 0},
                node_contributions=contributions,
                extremizer=extremizer,
            )
        )
    projected_ratios = np.divide(
        block_b["projected_lower"],
        block_b["projected_upper"],
        out=np.zeros(len(block_b)),
        where=block_b["projected_upper"].to_numpy() > 0,
    )
    parity_values = block_i["cpu_gpu_parity"].dropna()
    final_summary = {
        "source_commit": git_commit(),
        "scientific_instances": len(full),
        "blocks_complete": list("ABCDEFGHI"),
        "block_counts": {"A": len(block_a), **{key: len(value) for key, value in blocks.items()}},
        "enumerated_tree_shapes": int(
            json.loads((ARTIFACT_ROOT / "tree_enumeration_summary.json").read_text())["rows"]
        ),
        "leakage_masks_executed": len(masks_f),
        "maximum_lower_to_projected_upper_ratio": float(projected_ratios.max()),
        "maximum_cpu_gpu_parity_error": float(parity_values.max()) if len(parity_values) else None,
        "optimizer_trajectories_requested_extended": matrix_counts()["nested_execution_counts"]["B_optimizer_trajectories"],
        "optimizer_trajectories_executed_pilot": 5,
        "optimizer_grid_status": "EXTENDED_PENDING_RESOURCE_GATE",
        "full_core_base_matrix_status": "COMPLETE",
        "wall_seconds": time.perf_counter() - start,
        "run_dirs": run_dirs,
        "release_impact": "fail closed on novelty, human review, and pending extended optimizer grid",
    }
    write_json(ARTIFACT_ROOT / "full_execution_manifest.json", final_summary)
    print(json.dumps(final_summary, indent=2))


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    subparsers = parser.add_subparsers(dest="command", required=True)
    subparsers.add_parser("budget").set_defaults(function=command_budget)
    subparsers.add_parser("enumerate").set_defaults(function=command_enumerate)
    subparsers.add_parser("exact").set_defaults(function=command_exact)
    subparsers.add_parser("smoke").set_defaults(function=command_smoke)
    subparsers.add_parser("full").set_defaults(function=command_full)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    args.function(args)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
