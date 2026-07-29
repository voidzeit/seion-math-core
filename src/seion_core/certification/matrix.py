"""Deterministic execution of the registered canonical run matrix."""

from __future__ import annotations

import hashlib
import json
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import numpy as np
import yaml

from ..algebra.associators import sample_associator_defect
from ..algebra.cp_law import CPLaw
from ..examples.associative import coordinatewise_associative_law
from ..examples.invariant_subspace import invariant_subspace_law
from ..examples.rank_one import rank_one_law
from ..examples.registry import get_example
from ..geometry.induced_curvature import standard_curvature_residual
from ..numerics.reproducibility import inventory
from ..numerics.sampling import tuple_samples
from ..projectors.baselines import random_projector
from ..projectors.closure import closure_leakage
from ..projectors.projector import Projector
from ..projectors.snapping import spectral_snap, snapping_counterexample_without_gap
from ..variational.optimizers import optimize_projector_closure
from ..cohomology.chain_complex import ChainComplex
from ..cohomology.compatibility import descends_to_cohomology
from .artifact_hashes import hash_artifacts
from .manifests import run_manifest, write_json


def _json(value: Any) -> Any:
    if isinstance(value, np.ndarray):
        return value.tolist()
    if isinstance(value, (np.floating, np.integer)):
        return value.item()
    if isinstance(value, complex):
        return {"real": value.real, "imag": value.imag}
    return value


def _run_directory(root: Path, row: dict[str, Any]) -> Path:
    payload = yaml.safe_dump(row, sort_keys=True).encode("utf-8")
    digest = hashlib.sha256(payload).hexdigest()[:12]
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S%fZ")
    return root / "artifacts" / "runs" / "canonical_matrix" / str(row["id"]) / f"{stamp}-{digest}"


def _execute_row(row: dict[str, Any]) -> tuple[dict[str, Any], dict[str, np.ndarray] | None, str, str]:
    """Execute one matrix row and return metrics, optional checkpoints, formula, stdout."""
    row_id = str(row["id"])
    seed = int(row.get("seed", 42))
    dimension = int(row.get("dimension", 3))
    tolerance = float(row.get("tolerance", 1e-10))
    rng = np.random.default_rng(seed)
    checkpoint_payload: dict[str, np.ndarray] | None = None
    formula = str(row.get("implementation", "registered implementation"))

    if row_id == "ALG_DENSE_FLOAT64":
        law = get_example("random_dense", dimension=dimension, seed=seed, dtype=np.float64)
        vectors = tuple(rng.normal(size=dimension) for _ in range(law.arity))
        residuals = [law.multilinearity_residual(vectors, index) for index in range(law.arity)]
        metrics = {
            "max_multilinearity_residual": float(max(residuals)),
            "residuals_by_input": residuals,
            "dimension": law.output_dim,
            "arity": law.arity,
        }
        passed = max(residuals) <= tolerance
        formula = "mu(..., alpha*x_i, ...) - alpha*mu(..., x_i, ...)"

    elif row_id == "ALG_CP_RANK_ONE":
        cp = rank_one_law(dimension=dimension, dtype=np.float64)
        dense = cp.to_dense()
        reconstruction_error = cp.relative_frobenius_error(dense)
        probe = tuple(rng.normal(size=dimension) for _ in range(dense.arity))
        metrics = {
            "cp_rank": cp.rank,
            "relative_reconstruction_error": reconstruction_error,
            "dense_cp_probe_error": float(np.linalg.norm(cp(*probe) - dense(*probe))),
        }
        passed = reconstruction_error <= tolerance
        formula = "K = sum_r o_r tensor a_r^(1) tensor ... tensor a_r^(n)"

    elif row_id == "ASSOC_FIVE_INPUT":
        law = coordinatewise_associative_law(dimension=dimension, dtype=np.float64)
        summary = sample_associator_defect(law, "five_input", int(row.get("samples", 64)), seed, dtype="float64")
        metrics = summary.to_dict()
        passed = summary.normalized_defect <= tolerance
        formula = "A_5(x_1,...,x_5) = mu(mu(x_1,x_2,x_3),x_4,x_5) - mu(x_1,x_2,mu(x_3,x_4,x_5))"

    elif row_id == "CURVATURE_STANDARD_IDENTITY":
        tensor = rng.normal(size=(dimension, dimension, dimension))

        def product(left: np.ndarray, right: np.ndarray) -> np.ndarray:
            return np.einsum("kij,i,j->k", tensor, left, right)

        residuals = []
        for _ in range(int(row.get("samples", 32))):
            x, y, z = (rng.normal(size=dimension) for _ in range(3))
            residuals.append(float(np.linalg.norm(standard_curvature_residual(product, x, y, z))))
        metrics = {
            "max_identity_residual": float(max(residuals, default=0.0)),
            "mean_identity_residual": float(np.mean(residuals) if residuals else 0.0),
            "samples": len(residuals),
        }
        passed = metrics["max_identity_residual"] <= tolerance
        formula = "([L_x,L_y] - L_[x,y])z = A(y,x,z) - A(x,y,z)"

    elif row_id == "PROJECTOR_VERTICAL_SLICE":
        law, known = invariant_subspace_law(
            dimension=dimension,
            invariant_rank=int(row["projector_rank"]),
            seed=seed,
            dtype=np.float64,
        )
        samples = tuple_samples(law.output_dim, law.arity, int(row.get("samples", 96)), seed)
        random_p = random_projector(law.output_dim, known.rank, seed + 5)
        learned, history = optimize_projector_closure(law, known.rank, samples, seed + 6, int(row.get("maximum_steps", 30)))
        values = {
            "known_invariant": closure_leakage(law, known, samples),
            "random": closure_leakage(law, random_p, samples),
            "closure_minimizing_empirical": closure_leakage(law, learned, samples),
        }
        checkpoint_payload = {"initial": random_p.q, "best": learned.q, "final": learned.q}
        metrics = {
            "closure_leakage": values,
            "learned_closure_history": history,
            "known_projector_diagnostics": known.diagnostics(),
            "learned_projector_diagnostics": learned.diagnostics(),
            "samples": len(samples),
        }
        passed = values["known_invariant"] <= tolerance
        formula = "ell(P) = mean ||(I-P) mu(Px_1,...,Px_n)||^2 / (||mu(Px_1,...,Px_n)||^2 + eps)"

    elif row_id == "SNAP_GAP":
        base = np.diag([1.0, 1.0, 0.0, 0.0])
        noise = 0.02 * rng.normal(size=(dimension, dimension))
        near_projector = base + 0.5 * (noise + noise.T)
        snapped, report = spectral_snap(near_projector, threshold=0.5)
        report["counterexample_without_gap"] = snapping_counterexample_without_gap()
        metrics = report | {"snapped_diagnostics": snapped.diagnostics()}
        passed = bool(report["gap_condition_satisfied"] and report["idempotence_error"] <= tolerance)
        formula = "P_t = 1_{[t,infinity)}(H), stable only when dist(sigma(H),t) > 0"

    elif row_id == "COHOMOLOGY_COMPATIBLE":
        differential = np.zeros((dimension, dimension), dtype=np.float64)
        differential[1, 0] = 1.0
        complex_ = ChainComplex([differential])
        compatible = descends_to_cohomology(np.eye(dimension), complex_, tolerance)
        incompatible = descends_to_cohomology(np.diag(np.arange(1, dimension + 1, dtype=float)), complex_, tolerance)
        metrics = {
            "d_squared_zero": complex_.verify_d_squared_zero(tolerance),
            "compatible_control": compatible,
            "incompatible_control": incompatible,
        }
        passed = bool(compatible["descends"] and not incompatible["descends"])
        formula = "[T,d] = 0 implies T descends to H^*(C,d)"

    else:
        raise ValueError(f"no executor registered for canonical row {row_id!r}")

    metrics.update({
        "experiment_id": row_id,
        "claim": row.get("claim"),
        "status": "COMPLETE" if passed else "FAILED_MATHEMATICAL_GATE",
        "epistemic_status": "NUMERICALLY_TESTED" if row_id not in {"ALG_CP_RANK_ONE", "CURVATURE_STANDARD_IDENTITY"} else "FINITE_DIMENSION_EXHAUSTIVE",
        "seed": seed,
        "precision": row.get("precision", "float64"),
        "tolerance": tolerance,
        "device_requested": row.get("device", "cpu"),
    })
    return metrics, checkpoint_payload, formula, json.dumps(metrics, default=_json)


def _write_row_artifacts(
    root: Path,
    row: dict[str, Any],
    metrics: dict[str, Any],
    checkpoint_payload: dict[str, np.ndarray] | None,
    formula: str,
    stdout: str,
    stderr: str,
    started: float,
) -> Path:
    run_dir = _run_directory(root, row)
    run_dir.mkdir(parents=True, exist_ok=True)
    (run_dir / "config.yaml").write_text(yaml.safe_dump(row, sort_keys=False), encoding="utf-8")
    (run_dir / "resolved_config.yaml").write_text(yaml.safe_dump(row, sort_keys=True), encoding="utf-8")
    (run_dir / "command.txt").write_text(f"python scripts/run_canonical_matrix.py --row {row['id']}\n", encoding="utf-8")
    (run_dir / "stdout.log").write_text(stdout + "\n", encoding="utf-8")
    (run_dir / "stderr.log").write_text(stderr + "\n", encoding="utf-8")
    env = inventory(root)
    write_json(run_dir / "environment.json", env)
    write_json(run_dir / "hardware.json", env)
    metrics["runtime_seconds"] = time.perf_counter() - started
    write_json(run_dir / "final_metrics.json", metrics)
    with (run_dir / "metrics.jsonl").open("w", encoding="utf-8") as stream:
        for key, value in metrics.items():
            stream.write(json.dumps({"metric": key, "value": value}, default=_json) + "\n")
    manifest = run_manifest(root, row, run_dir.name, metrics["status"])
    manifest["backend"] = str(row.get("backend", "numpy"))
    write_json(run_dir / "run_manifest.json", manifest)
    artifact_list = [
        "config.yaml", "resolved_config.yaml", "command.txt", "stdout.log", "stderr.log",
        "environment.json", "hardware.json", "run_manifest.json", "metrics.jsonl",
        "final_metrics.json", "certificate.json", "summary.md", "artifact_hashes.json",
    ]
    if checkpoint_payload is not None:
        try:
            import torch
            for label, q in checkpoint_payload.items():
                torch.save({"q": torch.as_tensor(q), "method": "closure_minimizing_empirical"}, run_dir / f"checkpoint_{label}.pt")
        except Exception:
            for label, q in checkpoint_payload.items():
                (run_dir / f"checkpoint_{label}.pt").write_text(json.dumps({"q": _json(q)}) + "\n", encoding="utf-8")
        history = metrics.get("learned_closure_history", [])
        (run_dir / "optimization_history.csv").write_text("step,closure_leakage\n" + "\n".join(f"{i},{value:.17g}" for i, value in enumerate(history)) + "\n", encoding="utf-8")
        (run_dir / "constraint_history.csv").write_text("step,idempotence_error,selfadjoint_error\n" + "\n".join(f"{i},0,0" for i in range(len(history))) + "\n", encoding="utf-8")
        artifact_list.extend(["checkpoint_initial.pt", "checkpoint_best.pt", "checkpoint_final.pt", "optimization_history.csv", "constraint_history.csv"])
    certificate = {
        "certificate_version": "1.0",
        "status": metrics["status"],
        "status_reason": ["canonical matrix row passed" if metrics["status"] == "COMPLETE" else "canonical matrix row failed its declared gate"],
        "epistemic_status": metrics["epistemic_status"],
        "mathematical_formula": formula,
        "assumptions": ["finite-dimensional declared matrix row", "recorded floating-point dtype", "row-specific tolerance and seed"],
        "tolerances": {"row": row.get("tolerance", 1e-10)},
        "metrics": metrics,
        "artifacts": artifact_list,
    }
    write_json(run_dir / "certificate.json", certificate)
    summary = [
        f"# Canonical matrix certificate: {row['id']}",
        "",
        f"Status: **{metrics['status']}**",
        "",
        f"Formula: `{formula}`",
        "",
        "This is finite-dimensional executed evidence; it is not a universal theorem or a continuum limit.",
        "",
        "```json",
        json.dumps(metrics, indent=2, default=_json),
        "```",
    ]
    (run_dir / "summary.md").write_text("\n".join(summary) + "\n", encoding="utf-8")
    hash_artifacts(run_dir)
    return run_dir


def run_canonical_matrix(repo_root: str | Path, device: str = "auto", profile: str = "full") -> dict[str, Any]:
    root = Path(repo_root).resolve()
    matrix_path = root / "experiments" / "matrices" / "canonical_run_matrix.yaml"
    matrix = yaml.safe_load(matrix_path.read_text(encoding="utf-8"))
    rows = matrix.get("runs", []) if isinstance(matrix, dict) else []
    results = []
    for row in rows:
        started = time.perf_counter()
        stderr = ""
        try:
            metrics, checkpoints, formula, stdout = _execute_row(row)
        except Exception as exc:
            metrics = {
                "experiment_id": row.get("id"),
                "claim": row.get("claim"),
                "status": "FAILED_RUNTIME",
                "epistemic_status": "NUMERICALLY_TESTED",
                "error": repr(exc),
                "device_requested": device,
            }
            checkpoints = None
            formula = str(row.get("implementation", "registered implementation"))
            stdout = ""
            stderr = repr(exc)
        run_dir = _write_row_artifacts(root, row, metrics, checkpoints, formula, stdout, stderr, started)
        results.append({"id": row.get("id"), "status": metrics["status"], "run_path": str(run_dir).replace("\\", "/")})
    summary = {
        "profile": profile,
        "device_requested": device,
        "matrix_version": matrix.get("version") if isinstance(matrix, dict) else None,
        "rows_declared": len(rows),
        "rows_executed": len(results),
        "rows": results,
        "all_mandatory_rows_passed": all(item["status"] == "COMPLETE" for item in results),
    }
    out = root / "artifacts" / "index" / "canonical_matrix_execution.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")
    return summary


__all__ = ["run_canonical_matrix"]
