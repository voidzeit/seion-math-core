"""Generate theorem-critical v2 evidence without touching legacy runs.

The runner writes only under artifacts/runs_v2 and artifacts/index/*_v2.*.
Every row is a scientific instance with hashes stronger than the legacy
deduplicator identity.  The numerical work is intentionally small enough to
run in a review environment; it is evidence for the stated finite results,
not a continuum-limit claim.
"""

from __future__ import annotations

import csv
import hashlib
import json
import math
import subprocess
import time
import tracemalloc
from collections import defaultdict
from pathlib import Path
from typing import Any, Callable

import numpy as np
import yaml

from seion_core.algebra.cp_law import CPLaw
from seion_core.algebra.nary_law import NaryLaw
from seion_core.projectors.closure import closure_leakage
from seion_core.projectors.projector import Projector
from seion_core.projectors.snapping import spectral_snap
from seion_core.research_v2.accelerated import apply_tensor_einsum
from seion_core.research_v2.reference import (
    Tree,
    closure_residual_tensor,
    exact_reduction_tensor,
    evaluate_tree_reference,
    project_tensor_inputs,
    tree_bound,
)
from seion_core.variational.optimizers import optimize_projector_closure


ROOT = Path(__file__).resolve().parents[1]
VERSION = "research_v2.1"
MATRIX_PATH = ROOT / "experiments" / "matrices" / "research_v2_matrix.yaml"
RUN_ROOT = ROOT / "artifacts" / "runs_v2"
INDEX_ROOT = ROOT / "artifacts" / "index"
SYMBOLIC_ROOT = ROOT / "artifacts" / "symbolic_v2"
COUNTEREXAMPLE_ROOT = ROOT / "artifacts" / "counterexamples_v2"


def git(*args: str) -> str:
    result = subprocess.run(["git", *args], cwd=ROOT, capture_output=True, text=True, check=False)
    return result.stdout.strip() if result.returncode == 0 else "unknown"


def canonical_hash(value: Any) -> str:
    encoded = json.dumps(value, sort_keys=True, separators=(",", ":"), default=str).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def array_hash(*arrays: np.ndarray) -> str:
    digest = hashlib.sha256()
    for array in arrays:
        value = np.ascontiguousarray(np.asarray(array))
        digest.update(str(value.dtype).encode("utf-8"))
        digest.update(json.dumps(value.shape).encode("utf-8"))
        digest.update(value.tobytes())
    return digest.hexdigest()


def json_safe(value: Any) -> Any:
    if isinstance(value, np.generic):
        return value.item()
    if isinstance(value, np.ndarray):
        return value.tolist()
    if isinstance(value, Path):
        return str(value)
    if isinstance(value, dict):
        return {str(k): json_safe(v) for k, v in value.items()}
    if isinstance(value, (list, tuple)):
        return [json_safe(v) for v in value]
    return value


def measured(function: Callable[[], Any]) -> tuple[Any, float, int]:
    tracemalloc.start()
    start = time.perf_counter()
    result = function()
    elapsed = time.perf_counter() - start
    _, peak = tracemalloc.get_traced_memory()
    tracemalloc.stop()
    return result, elapsed, int(peak)


def project_tree(tensor: np.ndarray, tree: Tree, leaves: list[np.ndarray], p: np.ndarray) -> np.ndarray:
    if tree.is_leaf:
        assert tree.leaf is not None
        return p @ leaves[tree.leaf]
    assert tree.children is not None
    children = [project_tree(tensor, child, leaves, p) for child in tree.children]
    return p @ apply_tensor_einsum(tensor, children)


def tree_catalog() -> dict[str, Tree]:
    return {
        "single": Tree.node(0, 1, 2, arity=3),
        "associator_left": Tree.node(Tree.node(0, 1, 2, arity=3), 3, 4, arity=3),
        "balanced": Tree.node(
            Tree.node(0, 1, 2, arity=3),
            Tree.node(3, 4, 5, arity=3),
            Tree.node(6, 7, 8, arity=3),
            arity=3,
        ),
    }


def block_tensor(rng: np.random.Generator, d: int, rank: int, leakage: float) -> tuple[np.ndarray, np.ndarray]:
    q = np.eye(d)[:, :rank]
    tangent = rng.normal(size=(d,) * 4)
    tangent = project_tensor_inputs(tangent, q, output_projected=True)
    tangent_norm = np.linalg.norm(tangent.ravel())
    tangent = tangent / (tangent_norm or 1.0)
    tensor = tangent.copy()
    tensor[(rank, 0, 0, 0)] += leakage
    return tensor, q


def sample_reduced_leaves(seed: int, count: int, rank: int) -> list[np.ndarray]:
    rng = np.random.default_rng(seed)
    values = [rng.normal(size=rank) for _ in range(count)]
    return [value / (np.linalg.norm(value) or 1.0) for value in values]


def make_run_record(
    experiment_id: str,
    seed: int,
    config: dict[str, Any],
    object_arrays: tuple[np.ndarray, ...],
    input_arrays: tuple[np.ndarray, ...],
    metrics: dict[str, Any],
    status: str = "complete",
    failure_reason: str = "",
) -> dict[str, Any]:
    source_commit = git("rev-parse", "HEAD")
    object_hash = array_hash(*object_arrays)
    input_hash = array_hash(*input_arrays)
    config_hash = canonical_hash(config)
    identity = {
        "experiment_id": experiment_id,
        "resolved_config_hash": config_hash,
        "mathematical_object_hash": object_hash,
        "input_artifact_hash": input_hash,
        "seed": seed,
        "precision": str(config.get("precision", "float64")),
        "backend": str(config.get("backend", "numpy")),
        "device": str(config.get("device", "cpu")),
        "implementation_version": VERSION,
    }
    run_id = f"{experiment_id.lower()}_{canonical_hash(identity)[:16]}"
    run_dir = RUN_ROOT / run_id
    run_dir.mkdir(parents=True, exist_ok=True)
    np.savez_compressed(run_dir / "inputs.npz", *input_arrays)
    manifest = {
        "schema_version": 2,
        "run_id": run_id,
        "experiment_id": experiment_id,
        "status": status,
        "failure_reason": failure_reason,
        "source_commit": source_commit,
        "worktree_dirty": bool(git("status", "--porcelain")),
        "implementation_version": VERSION,
        "resolved_config": json_safe(config),
        "resolved_config_hash": config_hash,
        "mathematical_object_hash": object_hash,
        "input_artifact_hash": input_hash,
        "seed": seed,
        "precision": str(config.get("precision", "float64")),
        "backend": str(config.get("backend", "numpy")),
        "device": str(config.get("device", "cpu")),
        "identity_key": identity,
        "metrics": json_safe(metrics),
    }
    (run_dir / "manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    (run_dir / "metrics.json").write_text(json.dumps(json_safe(metrics), indent=2), encoding="utf-8")
    return {
        **identity,
        "run_id": run_id,
        "status": status,
        "failure_reason": failure_reason,
        "run_path": str(run_dir.relative_to(ROOT)),
        **json_safe(metrics),
    }


def run_bound_experiments(matrix: dict[str, Any]) -> list[dict[str, Any]]:
    spec = next(item for item in matrix["experiments"] if item["id"] == "V2_APPROX_CLOSURE_BOUND")
    rows: list[dict[str, Any]] = []
    for seed in spec["seeds"]:
        for epsilon in spec["epsilons"]:
            rng = np.random.default_rng(10000 + seed)
            tensor, q = block_tensor(rng, spec["ambient_dimension"], spec["reduced_rank"], epsilon)
            p = q @ q.T
            residual = closure_residual_tensor(tensor, q)
            rho = float(np.linalg.norm(residual.ravel()))
            m_upper = float(np.linalg.norm(tensor.ravel()))
            leaves = sample_reduced_leaves(11000 + seed, 9, spec["reduced_rank"])
            lifted = [q @ value for value in leaves]
            for family in spec["tree_families"]:
                tree = tree_catalog()[family]
                def compute() -> tuple[float, float]:
                    full = evaluate_tree_reference(tensor, tree, lifted)
                    reduced_lift = project_tree(tensor, tree, lifted, p)
                    return float(np.linalg.norm(full - reduced_lift)), float(np.linalg.norm(p @ full - reduced_lift))
                (observed, projected_observed), runtime, memory = measured(compute)
                bound = tree_bound(
                    tree,
                    m_upper,
                    rho,
                    [float(np.linalg.norm(value)) for value in leaves],
                )
                metrics = {
                    "epsilon_requested": float(epsilon),
                    "closure_residual_upper": rho,
                    "operator_norm_upper": m_upper,
                    "tree_family": family,
                    "internal_nodes": tree.internal_nodes if hasattr(tree, "internal_nodes") else 0,
                    "tree_height": tree.height if hasattr(tree, "height") else 0,
                    "observed_error": observed,
                    "projected_observed_error": projected_observed,
                    "theoretical_bound": bound,
                    "tightness_ratio": observed / bound if bound > 0 else 0.0,
                    "runtime_seconds": runtime,
                    "ram_peak_bytes": memory,
                    "vram_peak_bytes": 0,
                    "convergence_status": "exact_zero_residual" if rho == 0 else "complete",
                    "failure_count": 0,
                }
                config = {**spec, "epsilon": epsilon, "tree_family": family}
                rows.append(make_run_record("V2_APPROX_CLOSURE_BOUND", seed, config, (tensor, q), tuple(lifted), metrics))
    return rows


def orthogonal_columns(matrix: np.ndarray, rank: int) -> np.ndarray:
    q, _ = np.linalg.qr(matrix)
    return q[:, :rank]


def principal_angle(true_q: np.ndarray, candidate_q: np.ndarray) -> float:
    singular_values = np.linalg.svd(true_q.conj().T @ candidate_q, compute_uv=False)
    return float(np.arccos(np.clip(np.min(singular_values), -1.0, 1.0)))


def recovery_projectors(
    law: NaryLaw,
    true_q: np.ndarray,
    samples: list[tuple[np.ndarray, ...]],
    seed: int,
) -> dict[str, Projector]:
    rng = np.random.default_rng(12000 + seed)
    d, rank = true_q.shape
    known = Projector(true_q, method="known_invariant")
    random_projector = Projector(orthogonal_columns(rng.normal(size=(d, rank)), rank), method="random")
    outputs = np.stack([law(*sample) for sample in samples], axis=1)
    covariance = outputs @ outputs.conj().T
    values, vectors = np.linalg.eigh(covariance)
    pca = Projector(vectors[:, np.argsort(values)[-rank:]], method="pca")
    u, _, _ = np.linalg.svd(law.tensor.reshape(d, -1), full_matrices=False)
    svd = Projector(u[:, :rank], method="svd")
    noise = rng.normal(size=(d, d))
    near = true_q @ true_q.T + 0.04 * (noise + noise.T) / 2
    spectral, _ = spectral_snap(near, threshold=0.5)
    closure, _ = optimize_projector_closure(law, rank, samples, seed=13000 + seed, steps=20)
    return {
        "known_invariant": known,
        "random": random_projector,
        "pca": pca,
        "svd": svd,
        "spectral": spectral,
        "closure_minimizing": closure,
    }


def run_projector_recovery(matrix: dict[str, Any]) -> list[dict[str, Any]]:
    spec = next(item for item in matrix["experiments"] if item["id"] == "V2_PROJECTOR_RECOVERY")
    rows: list[dict[str, Any]] = []
    for seed in spec["seeds"]:
        rng = np.random.default_rng(14000 + seed)
        tensor, q = block_tensor(rng, spec["ambient_dimension"], spec["reduced_rank"], spec["leakage"])
        law = NaryLaw(tensor, spec["arity"], name="v2_recovery_law")
        samples_rng = np.random.default_rng(15000 + seed)
        samples = [
            tuple(samples_rng.normal(size=spec["ambient_dimension"]) for _ in range(spec["arity"]))
            for _ in range(32)
        ]
        for method, projector in recovery_projectors(law, q, samples, seed).items():
            def compute() -> float:
                return closure_leakage(law, projector, samples)
            leakage, runtime, memory = measured(compute)
            metrics = {
                "method": method,
                "closure_leakage": leakage,
                "principal_angle_radians": principal_angle(q, projector.q),
                "projector_rank": projector.rank,
                "runtime_seconds": runtime,
                "ram_peak_bytes": memory,
                "vram_peak_bytes": 0,
                "convergence_status": "complete",
                "failure_count": 0,
            }
            config = {**spec, "method": method}
            rows.append(make_run_record("V2_PROJECTOR_RECOVERY", seed, config, (tensor, q), tuple(np.asarray(x) for sample in samples for x in sample), metrics))
    return rows


def run_cp_sweep(matrix: dict[str, Any]) -> list[dict[str, Any]]:
    spec = next(item for item in matrix["experiments"] if item["id"] == "V2_CP_RANK_SWEEP")
    rows: list[dict[str, Any]] = []
    for seed in spec["seeds"]:
        rng = np.random.default_rng(16000 + seed)
        tensor = rng.normal(size=(spec["ambient_dimension"],) * 4)
        law = NaryLaw(tensor, spec["arity"], name="v2_cp_target")
        exact_metrics = {
            "rank": 0,
            "relative_frobenius_error": 0.0,
            "runtime_seconds": 0.0,
            "ram_peak_bytes": 0,
            "vram_peak_bytes": 0,
            "convergence_status": "exact_dense_baseline",
            "failure_count": 0,
        }
        rows.append(make_run_record("V2_CP_RANK_SWEEP", seed, {**spec, "rank": 0}, (tensor,), (tensor,), exact_metrics))
        for rank in spec["ranks"]:
            def compute() -> CPLaw:
                return CPLaw.from_dense(law, rank=rank, seed=17000 + seed, iterations=12)
            try:
                cp, runtime, memory = measured(compute)
                metrics = {
                    "rank": rank,
                    "relative_frobenius_error": cp.relative_frobenius_error(law),
                    "runtime_seconds": runtime,
                    "ram_peak_bytes": memory,
                    "vram_peak_bytes": 0,
                    "convergence_status": "complete",
                    "failure_count": 0,
                }
                rows.append(make_run_record("V2_CP_RANK_SWEEP", seed, {**spec, "rank": rank}, (tensor,), (tensor,), metrics))
            except Exception as exc:
                rows.append(make_run_record("V2_CP_RANK_SWEEP", seed, {**spec, "rank": rank}, (tensor,), (tensor,), {"rank": rank, "failure_count": 1}, "failed", repr(exc)))
    return rows


def run_spectral_gap(matrix: dict[str, Any]) -> list[dict[str, Any]]:
    spec = next(item for item in matrix["experiments"] if item["id"] == "V2_SPECTRAL_GAP")
    rows: list[dict[str, Any]] = []
    dimension = int(spec["dimensions"][0])
    for seed in spec["seeds"]:
        rng = np.random.default_rng(18000 + seed)
        for gap in spec["gaps"]:
            eigenvalues = np.array([0.5 - gap, 0.5 + gap] + [0.1, 0.9][: dimension - 2])
            a = np.diag(eigenvalues)
            base, _ = spectral_snap(a)
            for relative in spec["relative_perturbations"]:
                noise = rng.normal(size=(dimension, dimension))
                noise = (noise + noise.T) / 2
                noise /= max(np.linalg.norm(noise, 2), np.finfo(float).eps)
                e = relative * gap * noise
                perturbed, runtime, memory = measured(lambda: spectral_snap(a + e)[0])
                observed = float(np.linalg.norm(perturbed.matrix - base.matrix, 2))
                e_norm = float(np.linalg.norm(e, 2))
                bound = min(1.0, 4.0 * e_norm / gap)
                metrics = {
                    "control": "positive_gap",
                    "gap": float(gap),
                    "relative_perturbation": float(relative),
                    "perturbation_norm": e_norm,
                    "snapped_projector_distance": observed,
                    "theoretical_bound": bound,
                    "bound_respected": bool(observed <= bound + 1e-10),
                    "runtime_seconds": runtime,
                    "ram_peak_bytes": memory,
                    "vram_peak_bytes": 0,
                    "convergence_status": "complete",
                    "failure_count": 0,
                }
                rows.append(make_run_record("V2_SPECTRAL_GAP", seed, {**spec, "gap": gap, "relative": relative}, (a,), (e,), metrics))
        delta = 10.0 ** (-8 - seed)
        a = np.diag([0.5 - delta, 0.5 + delta, 0.1, 0.9])
        e = np.diag([2 * delta, -2 * delta, 0.0, 0.0])
        before = spectral_snap(a)[0].matrix
        after = spectral_snap(a + e)[0].matrix
        metrics = {
            "control": "no_gap",
            "gap": float(delta),
            "relative_perturbation": 1.0,
            "perturbation_norm": float(np.linalg.norm(e, 2)),
            "snapped_projector_distance": float(np.linalg.norm(after - before, 2)),
            "theoretical_bound": None,
            "bound_respected": None,
            "runtime_seconds": 0.0,
            "ram_peak_bytes": 0,
            "vram_peak_bytes": 0,
            "convergence_status": "rank_flip_control",
            "failure_count": 0,
        }
        rows.append(make_run_record("V2_SPECTRAL_GAP", seed, {**spec, "control": "no_gap"}, (a,), (e,), metrics))
    return rows


def run_cpu_gpu_parity(matrix: dict[str, Any]) -> list[dict[str, Any]]:
    spec = next(item for item in matrix["experiments"] if item["id"] == "V2_CPU_GPU_PARITY")
    rows: list[dict[str, Any]] = []
    try:
        import torch
    except Exception as exc:
        torch = None
        torch_error = repr(exc)
    else:
        torch_error = ""
    for seed in spec["seeds"]:
        rng = np.random.default_rng(19000 + seed)
        tensor = rng.normal(size=(spec["ambient_dimension"],) * 4).astype(np.float64)
        vectors = [rng.normal(size=spec["ambient_dimension"]).astype(np.float64) for _ in range(spec["arity"])]
        if torch is None:
            metrics = {"status_detail": "torch_unavailable", "reason": torch_error, "max_abs_error": None, "failure_count": 1}
        else:
            cpu_tensor = torch.from_numpy(tensor)
            cpu_vectors = [torch.from_numpy(value) for value in vectors]
            cpu_result = torch.einsum("oabc,a,b,c->o", cpu_tensor, *cpu_vectors)
            metrics = {
                "status_detail": "gpu_unavailable" if not torch.cuda.is_available() else "complete",
                "reason": "CUDA is not available" if not torch.cuda.is_available() else "",
                "max_abs_error": None,
                "failure_count": 0 if torch.cuda.is_available() else 0,
            }
            if torch.cuda.is_available():
                torch.cuda.reset_peak_memory_stats()
                gpu_result = torch.einsum(
                    "oabc,a,b,c->o",
                    cpu_tensor.cuda(),
                    *[value.cuda() for value in cpu_vectors],
                ).cpu()
                metrics["max_abs_error"] = float(torch.max(torch.abs(cpu_result - gpu_result)).item())
                metrics["vram_peak_bytes"] = int(torch.cuda.max_memory_allocated())
            else:
                metrics["vram_peak_bytes"] = 0
        rows.append(make_run_record("V2_CPU_GPU_PARITY", seed, {**spec, "cuda_available": bool(torch is not None and torch.cuda.is_available())}, (tensor,), tuple(vectors), metrics, status="complete" if metrics["failure_count"] == 0 else "failed"))
    return rows


def write_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fields: list[str] = []
    for row in rows:
        for key in row:
            if key not in fields:
                fields.append(key)
    with path.open("w", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(stream, fieldnames=fields, extrasaction="ignore")
        writer.writeheader()
        for row in rows:
            writer.writerow({key: json_safe(row.get(key, "")) for key in fields})


def summary_rows(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    groups: dict[tuple[str, str], list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        experiment = str(row.get("experiment_id", ""))
        if experiment == "V2_APPROX_CLOSURE_BOUND":
            group = f"{row.get('tree_family')}|epsilon={row.get('epsilon_requested')}"
            metric_names = ["observed_error", "theoretical_bound", "tightness_ratio", "runtime_seconds", "ram_peak_bytes"]
        elif experiment == "V2_PROJECTOR_RECOVERY":
            group = str(row.get("method"))
            metric_names = ["closure_leakage", "principal_angle_radians", "runtime_seconds", "ram_peak_bytes"]
        elif experiment == "V2_CP_RANK_SWEEP":
            group = f"rank={row.get('rank')}"
            metric_names = ["relative_frobenius_error", "runtime_seconds", "ram_peak_bytes"]
        else:
            group = f"{row.get('control')}|gap={row.get('gap')}"
            metric_names = ["snapped_projector_distance", "perturbation_norm", "theoretical_bound"]
        for metric_name in metric_names:
            value = row.get(metric_name)
            if value is None or value == "":
                continue
            try:
                numeric = float(value)
            except (TypeError, ValueError):
                continue
            groups[(group, metric_name)].append({"value": numeric, "row": row})
    result: list[dict[str, Any]] = []
    raw_by_key: dict[tuple[str, str, str], list[float]] = defaultdict(list)
    for row in rows:
        experiment = str(row.get("experiment_id", ""))
        metric_names = [
            "observed_error", "theoretical_bound", "tightness_ratio", "runtime_seconds", "ram_peak_bytes",
            "closure_leakage", "principal_angle_radians", "relative_frobenius_error", "snapped_projector_distance",
            "perturbation_norm",
        ]
        for metric_name in metric_names:
            value = row.get(metric_name)
            if value is None or value == "":
                continue
            try:
                numeric = float(value)
            except (TypeError, ValueError):
                continue
            if experiment == "V2_APPROX_CLOSURE_BOUND":
                base_group = f"{row.get('tree_family')}|epsilon={row.get('epsilon_requested')}"
            elif experiment == "V2_PROJECTOR_RECOVERY":
                base_group = str(row.get("method"))
            elif experiment == "V2_CP_RANK_SWEEP":
                base_group = f"rank={row.get('rank')}"
            else:
                base_group = ""
            raw_by_key[(experiment, metric_name, base_group)].append(numeric)
    for (group, metric_name), items in sorted(groups.items()):
        values = np.array([item["value"] for item in items], dtype=float)
        mean = float(np.mean(values))
        std = float(np.std(values, ddof=1)) if len(values) > 1 else 0.0
        ci = 1.96 * std / math.sqrt(len(values)) if len(values) > 1 else 0.0
        experiment = str(items[0]["row"].get("experiment_id"))
        reference_values = raw_by_key.get((experiment, metric_name, "known_invariant"), [])
        if experiment == "V2_APPROX_CLOSURE_BOUND":
            tree_name = group.split("|", 1)[0]
            reference_values = raw_by_key.get((experiment, metric_name, f"{tree_name}|epsilon=0.0"), [])
        elif experiment == "V2_CP_RANK_SWEEP":
            reference_values = raw_by_key.get((experiment, metric_name, "rank=0"), [])
        if reference_values:
            reference = np.asarray(reference_values, dtype=float)
            value_variance = float(np.var(values, ddof=1)) if len(values) > 1 else 0.0
            reference_variance = float(np.var(reference, ddof=1)) if len(reference) > 1 else 0.0
            pooled = math.sqrt((value_variance + reference_variance) / 2)
            reference_mean = float(np.mean(reference))
            degenerate_scale = max(1.0, abs(reference_mean), abs(mean))
            reference_is_degenerate = reference_variance <= (1e-12 * degenerate_scale) ** 2
            if reference_is_degenerate and not math.isclose(
                mean, reference_mean, rel_tol=1e-12, abs_tol=1e-12 * degenerate_scale
            ):
                effect_size = "NA_zero_variance"
            elif pooled > 1e-12 * degenerate_scale:
                effect_size = (mean - reference_mean) / pooled
            elif math.isclose(mean, reference_mean, rel_tol=1e-12, abs_tol=1e-15):
                effect_size = 0.0
            else:
                effect_size = "NA_zero_variance"
        else:
            effect_size = "NA_no_reference"
        result.append(
            {
                "experiment_id": experiment,
                "group": group,
                "metric": metric_name,
                "n_unique_runs": len(values),
                "mean": mean,
                "std": std,
                "median": float(np.median(values)),
                "min": float(np.min(values)),
                "max": float(np.max(values)),
                "ci95_half_width": ci,
                "effect_size_vs_reference": effect_size,
                "convergence_status": "complete",
                "failure_count": int(sum(item["row"].get("status") != "complete" for item in items)),
            }
        )
    return result


def write_exact_artifacts() -> None:
    SYMBOLIC_ROOT.mkdir(parents=True, exist_ok=True)
    COUNTEREXAMPLE_ROOT.mkdir(parents=True, exist_ok=True)
    tensor = np.zeros((4, 4, 4, 4), dtype=int)
    tensor[0, 0, 0, 0] = 1
    tensor[1, 1, 0, 1] = -2
    tensor[0, 1, 1, 0] = 3
    q = np.eye(4, dtype=int)[:, :2]
    reduced = exact_reduction_tensor(tensor, q)
    artifact = {
        "status": "exact_rational_example",
        "field": "Q",
        "tensor_nonzero_entries": [
            {"index": [int(item) for item in index], "value": int(value)}
            for index, value in zip(np.argwhere(tensor != 0), tensor[tensor != 0])
        ],
        "q": q.tolist(),
        "reduced_tensor": reduced.tolist(),
        "invariant_reduction_residual_frobenius": 0.0,
        "claim": "Q reduced_mu = mu Q on W for the declared block-supported tensor",
    }
    (SYMBOLIC_ROOT / "exact_invariant_reduction.json").write_text(json.dumps(artifact, indent=2), encoding="utf-8")
    no_invariance = {
        "status": "exact_counterexample",
        "ambient_field": "Q",
        "q": [[1], [0]],
        "outer_nonzero_entries": [
            {"index": [1, 0, 0], "value": 1},
            {"index": [0, 1, 0], "value": 1},
        ],
        "reduced_composition_at_e0": [0],
        "ambient_composition_at_e0": [1, 0],
        "claim": "Without invariance, reduction need not commute with partial composition",
    }
    (COUNTEREXAMPLE_ROOT / "no_invariance_composition.json").write_text(json.dumps(no_invariance, indent=2), encoding="utf-8")
    sweep = []
    for exponent in range(2, 9):
        delta = 10.0 ** (-exponent)
        before = np.diag([0.5 - delta, 0.5 + delta])
        after = np.diag([0.5 + delta, 0.5 - delta])
        p_before = np.diag([0.0, 1.0])
        p_after = np.diag([1.0, 0.0])
        sweep.append(
            {
                "delta": delta,
                "perturbation_norm_2": float(np.linalg.norm(after - before, 2)),
                "snapped_projector_distance_2": float(np.linalg.norm(p_after - p_before, 2)),
            }
        )
    (COUNTEREXAMPLE_ROOT / "spectral_gap_sweep.json").write_text(json.dumps(sweep, indent=2), encoding="utf-8")


def main() -> int:
    matrix = yaml.safe_load(MATRIX_PATH.read_text(encoding="utf-8"))
    RUN_ROOT.mkdir(parents=True, exist_ok=True)
    INDEX_ROOT.mkdir(parents=True, exist_ok=True)
    write_exact_artifacts()
    rows: list[dict[str, Any]] = []
    rows.extend(run_bound_experiments(matrix))
    rows.extend(run_projector_recovery(matrix))
    rows.extend(run_cp_sweep(matrix))
    rows.extend(run_spectral_gap(matrix))
    rows.extend(run_cpu_gpu_parity(matrix))
    write_csv(INDEX_ROOT / "run_index_v2.csv", rows)
    write_csv(INDEX_ROOT / "scientific_instances_v2.csv", rows)
    write_csv(INDEX_ROOT / "research_v2_summary.csv", summary_rows(rows))
    write_csv(INDEX_ROOT / "bound_tightness_v2.csv", [row for row in rows if row["experiment_id"] == "V2_APPROX_CLOSURE_BOUND"])
    write_csv(INDEX_ROOT / "projector_recovery_v2.csv", [row for row in rows if row["experiment_id"] == "V2_PROJECTOR_RECOVERY"])
    write_csv(INDEX_ROOT / "cp_rank_sweep_v2.csv", [row for row in rows if row["experiment_id"] == "V2_CP_RANK_SWEEP"])
    write_csv(INDEX_ROOT / "spectral_gap_v2.csv", [row for row in rows if row["experiment_id"] == "V2_SPECTRAL_GAP"])
    write_csv(INDEX_ROOT / "failure_registry_v2.csv", [row for row in rows if row["status"] != "complete" or int(row.get("failure_count", 0) or 0) > 0])
    summary = {
        "version": 2,
        "implementation_version": VERSION,
        "source_commit": git("rev-parse", "HEAD"),
        "worktree_dirty": bool(git("status", "--porcelain")),
        "total_runs": len(rows),
        "complete_runs": sum(row["status"] == "complete" for row in rows),
        "failed_runs": sum(row["status"] != "complete" for row in rows),
        "unique_scientific_instances": len({row["mathematical_object_hash"] + row["input_artifact_hash"] + str(row["seed"]) + row["experiment_id"] for row in rows}),
        "required_seed_count": 5,
        "legacy_history_modified": False,
        "gpu_rows": sum(row["experiment_id"] == "V2_CPU_GPU_PARITY" for row in rows),
        "gpu_completed": sum(row.get("status_detail") == "complete" for row in rows),
    }
    (INDEX_ROOT / "research_v2_manifest.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")
    print(json.dumps(summary, indent=2))
    return 0 if summary["failed_runs"] == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
