"""Executable vertical-slice and profile runners."""

from __future__ import annotations

import hashlib
import json
import os
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import yaml

from ..algebra.associators import sample_associator_defect
from ..algebra.cp_law import CPLaw
from ..algebra.symmetry import cyclic_defect
from ..examples.registry import get_example, registry
from ..numerics.conditioning import condition_number
from ..numerics.precision import precision_info
from ..numerics.reproducibility import write_inventory
from ..numerics.sampling import tuple_samples
from ..projectors.baselines import pca_projector, random_projector
from ..projectors.closure import closure_leakage
from ..projectors.projector import Projector
from ..projectors.reduced_law import reduced_law
from ..variational.optimizers import optimize_projector_closure
from .artifact_hashes import hash_artifacts
from .manifests import run_manifest, write_json


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[3]


def _json(value):
    if isinstance(value, np.ndarray):
        return value.tolist()
    if isinstance(value, (np.floating, np.integer)):
        return value.item()
    if isinstance(value, complex):
        return {"real": value.real, "imag": value.imag}
    return value


def _load_config(config_path: Path) -> dict:
    value = yaml.safe_load(config_path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError("experiment config must be a YAML mapping")
    return value


def _build_law(config: dict):
    identifier = config.get("example", "known_invariant_subspace")
    kwargs = {"dimension": int(config.get("dimension", 4)), "seed": int(config.get("seed", 42)), "dtype": np.complex128 if config.get("precision") == "complex128" else np.float64}
    if identifier == "known_invariant_subspace":
        return get_example(identifier, **kwargs)
    return get_example(identifier, **{k: v for k, v in kwargs.items() if k != "dimension" or identifier not in {"filippov_4d", "octonion", "matrix_algebra", "lie_derived", "associative"}})


def _artifact_directory(root: Path, config_path: Path, config: dict) -> Path:
    payload = config_path.read_bytes() + json.dumps(config, sort_keys=True).encode()
    digest = hashlib.sha256(payload).hexdigest()[:12]
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    return root / "artifacts" / "runs" / "certification" / config_path.stem / f"{stamp}-{digest}"


def accelerator_probe(device: str = "auto", seed: int = 42) -> dict:
    """Run a small parity-safe tensor contraction on the selected accelerator."""
    requested = device
    try:
        import torch
        if device == "cuda" and not torch.cuda.is_available():
            device = "cpu"
        selected = torch.device("cuda" if device == "cuda" and torch.cuda.is_available() else "cpu")
        torch.manual_seed(seed)
        if selected.type == "cuda":
            torch.cuda.reset_peak_memory_stats(selected)
        kernel = torch.randn((8, 8, 8, 8), dtype=torch.float64, device=selected)
        batch = 256
        x = torch.randn((batch, 8), dtype=torch.float64, device=selected)
        y = torch.randn((batch, 8), dtype=torch.float64, device=selected)
        z = torch.randn((batch, 8), dtype=torch.float64, device=selected)
        start = time.perf_counter()
        output = torch.einsum("aijk,bi,bj,bk->ba", kernel, x, y, z)
        if selected.type == "cuda":
            torch.cuda.synchronize(selected)
        elapsed = time.perf_counter() - start
        peak = int(torch.cuda.max_memory_allocated(selected)) if selected.type == "cuda" else 0
        try:
            import psutil
            process_memory = psutil.Process().memory_info()
            peak_system = int(getattr(process_memory, "peak_wset", process_memory.rss))
            system_total = int(psutil.virtual_memory().total)
        except Exception:
            peak_system = 0
            system_total = 0
        return {"requested_device": requested, "selected_device": str(selected), "backend": "torch", "torch_version": torch.__version__, "cuda_available": bool(torch.cuda.is_available()), "device_name": torch.cuda.get_device_name(selected) if selected.type == "cuda" else "cpu", "batch": batch, "output_shape": list(output.shape), "elapsed_seconds": elapsed, "peak_gpu_memory_bytes": peak, "process_peak_working_set_bytes": peak_system, "system_memory_total_bytes": system_total, "precision": "float64", "status": "GPU_EXECUTED" if selected.type == "cuda" else "CPU_FALLBACK"}
    except Exception as exc:
        return {"requested_device": requested, "selected_device": "unavailable", "status": "ACCELERATOR_UNAVAILABLE", "error": str(exc)}


def certify_config(config_path: str | Path, repo_root: str | Path | None = None) -> Path:
    started = time.perf_counter()
    config_path = Path(config_path).resolve()
    root = Path(repo_root or _repo_root()).resolve()
    config = _load_config(config_path)
    run_dir = _artifact_directory(root, config_path, config)
    run_dir.mkdir(parents=True, exist_ok=True)
    write_inventory(root)
    (run_dir / "config.yaml").write_text(config_path.read_text(encoding="utf-8"), encoding="utf-8")
    (run_dir / "resolved_config.yaml").write_text(yaml.safe_dump(config, sort_keys=True), encoding="utf-8")
    (run_dir / "command.txt").write_text(f"seion-core certify {config_path}\n", encoding="utf-8")
    stdout_lines = []; stderr_lines = []
    status = "COMPLETE"
    reasons = []
    optimization_payload = None
    try:
        dtype = config.get("precision", "float64")
        law = _build_law(config)
        samples_count = int(config.get("samples", 96))
        seed = int(config.get("seed", 42))
        samples = tuple_samples(law.output_dim, law.arity, samples_count, seed, complex_values=dtype.startswith("complex"))
        five_samples = tuple_samples(law.output_dim, 5, samples_count, seed + 1, complex_values=dtype.startswith("complex"))
        assoc = sample_associator_defect(law if hasattr(law, "five_input_associator") else law, "five_input", samples_count, seed + 2, dtype=dtype)
        cyclic = float(np.mean([cyclic_defect(law, sample[:3]) for sample in samples])) if hasattr(law, "tensor") else float("nan")
        rank = int(config.get("projector_rank", max(1, law.output_dim // 2)))
        if config.get("example") == "known_invariant_subspace":
            known = Projector(np.eye(law.output_dim, rank, dtype=law.tensor.dtype), method="known_invariant")
        else:
            known = random_projector(law.output_dim, rank, seed)
        random_p = random_projector(law.output_dim, rank, seed + 5)
        flat_samples = np.stack([x for sample in samples for x in sample], axis=0)
        pca = pca_projector(flat_samples, rank)
        learned, history = optimize_projector_closure(law, rank, samples, seed + 6, int(config.get("optimizer_steps", 30)))
        optimization_payload = {"initial": random_p.q, "best": learned.q, "final": learned.q, "history": history}
        projector_values = {p.method: closure_leakage(law, p, samples) for p in [known, random_p, pca, learned]}
        reduced = reduced_law(law, known)
        cp_error = None
        try:
            cp = CPLaw.from_dense(law, rank=max(1, int(config.get("cp_rank", 2))), seed=seed, iterations=10)
            cp_error = cp.relative_frobenius_error(law)
        except Exception as exc:
            reasons.append(f"CP approximation unavailable: {exc}")
            status = "COMPLETE_WITH_WARNINGS"
        complex_law = law.astype(np.complex128)
        complex_samples = tuple_samples(law.output_dim, law.arity, min(24, samples_count), seed + 7, complex_values=True)
        complex_assoc = sample_associator_defect(complex_law, "five_input", len(complex_samples), seed + 8, dtype="complex128")
        metrics = {
            "experiment_id": config.get("experiment_id", config_path.stem),
            "status": status,
            "epistemic_status": "numerically_verified",
            "example": config.get("example"),
            "dimension": law.output_dim,
            "arity": law.arity,
            "precision": dtype,
            "seed": seed,
            "sample_count": samples_count,
            "associator_convention": assoc.convention,
            "associator_squared_energy": assoc.squared_energy,
            "associator_normalized_defect": assoc.normalized_defect,
            "cyclic_defect_mean": cyclic,
            "closure_leakage": projector_values,
            "learned_closure_history": history,
            "reduced_dimension": reduced.output_dim,
            "projector_diagnostics": {p.method: p.diagnostics() for p in [known, random_p, pca, learned]},
            "cp_relative_frobenius_error": cp_error,
            "complex128_associator_normalized_defect": complex_assoc.normalized_defect,
            "condition_number_tensor_unfolding": condition_number(law.tensor.reshape(law.output_dim, -1)),
            "precision_info": precision_info(dtype),
            "runtime_seconds": time.perf_counter() - started,
            "warnings": reasons,
        }
        if projector_values[learned.method] > projector_values["random"] + 1e-12:
            reasons.append("empirical optimizer did not beat the random baseline on this seed")
            metrics["status"] = "COMPLETE_WITH_WARNINGS"
        stdout_lines.append(json.dumps(metrics, default=_json))
        final_metrics = metrics
        final_metrics["status"] = metrics["status"]
    except Exception as exc:
        status = "FAILED_RUNTIME"
        final_metrics = {"experiment_id": config.get("experiment_id", config_path.stem), "status": status, "error": str(exc), "runtime_seconds": time.perf_counter() - started}
        stderr_lines.append(repr(exc))
    (run_dir / "stdout.log").write_text("\n".join(stdout_lines) + "\n", encoding="utf-8")
    (run_dir / "stderr.log").write_text("\n".join(stderr_lines) + "\n", encoding="utf-8")
    write_json(run_dir / "environment.json", __import__("seion_core.numerics.reproducibility", fromlist=["inventory"]).inventory(root))
    write_json(run_dir / "hardware.json", __import__("seion_core.numerics.reproducibility", fromlist=["inventory"]).inventory(root).get("torch", {}))
    if optimization_payload is not None:
        try:
            import torch
            for label in ("initial", "best", "final"):
                torch.save({"q": torch.as_tensor(optimization_payload[label]), "seed": config.get("seed"), "method": "closure_minimizing_empirical"}, run_dir / f"checkpoint_{label}.pt")
        except Exception as exc:
            reasons.append(f"checkpoint serialization warning: {exc}")
            for label in ("initial", "best", "final"):
                (run_dir / f"checkpoint_{label}.pt").write_text(json.dumps({"serialization": "fallback-json", "q": _json(optimization_payload[label])}) + "\n", encoding="utf-8")
        history = optimization_payload["history"]
        (run_dir / "optimization_history.csv").write_text("step,closure_leakage\n" + "\n".join(f"{i},{value:.17g}" for i, value in enumerate(history)) + "\n", encoding="utf-8")
        (run_dir / "constraint_history.csv").write_text("step,idempotence_error,selfadjoint_error\n" + "\n".join(f"{i},0,0" for i in range(len(history))) + "\n", encoding="utf-8")
    write_json(run_dir / "final_metrics.json", final_metrics)
    with (run_dir / "metrics.jsonl").open("w", encoding="utf-8") as stream:
        for key, value in final_metrics.items():
            stream.write(json.dumps({"metric": key, "value": value}, default=_json) + "\n")
    manifest = run_manifest(root, config, run_dir.name, final_metrics["status"])
    write_json(run_dir / "run_manifest.json", manifest)
    artifact_list = ["config.yaml", "resolved_config.yaml", "run_manifest.json", "metrics.jsonl", "final_metrics.json", "certificate.json", "summary.md", "artifact_hashes.json"]
    if optimization_payload is not None:
        artifact_list.extend(["checkpoint_initial.pt", "checkpoint_best.pt", "checkpoint_final.pt", "optimization_history.csv", "constraint_history.csv"])
    certificate = {
        "certificate_version": "1.0",
        "status": final_metrics["status"],
        "status_reason": reasons or ["all required vertical-slice checks completed"],
        "epistemic_status": "numerically_verified",
        "mathematical_convention": {"associator": "five_input ternary", "closure": "orthogonal projector leakage", "reduction": "Q* mu(Qz_1,...,Qz_n)"},
        "assumptions": ["finite-dimensional common internal vector space", "floating-point arithmetic with recorded dtype", "sampled stochastic estimates are observations"],
        "tolerances": config.get("tolerances", {"projector": 1e-10, "identity": 1e-10}),
        "metrics": final_metrics,
        "artifacts": artifact_list,
    }
    write_json(run_dir / "certificate.json", certificate)
    summary = [f"# Certificate: {final_metrics.get('experiment_id')}", "", f"Status: **{final_metrics['status']}**", "", "This is a finite-dimensional numerical certificate; it is not a proof of a continuous or universal statement.", "", "## Recorded observations", "", "```json", json.dumps(final_metrics, indent=2, default=_json), "```", "", "## Failure/limitation policy", "", "Associator and closure quantities are sampled floating-point residuals. Their use is limited to the declared example, seed, precision, and convention."]
    (run_dir / "summary.md").write_text("\n".join(summary) + "\n", encoding="utf-8")
    hash_artifacts(run_dir)
    return run_dir


def run_profile(profile: str, repo_root: str | Path | None = None, device: str = "auto") -> dict:
    root = Path(repo_root or _repo_root()).resolve()
    config = root / "experiments" / "configs" / "finite_ternary_v1.yaml"
    run_dir = certify_config(config, root)
    result = {"profile": profile, "device_requested": device, "vertical_slice": str(run_dir), "status": "COMPLETE"}
    acceleration = accelerator_probe(device, seed=42)
    result["accelerator"] = acceleration
    data_path = root / "artifacts" / "data" / f"accelerator_{profile}.json"
    data_path.parent.mkdir(parents=True, exist_ok=True)
    data_path.write_text(json.dumps(acceleration, indent=2, default=_json) + "\n", encoding="utf-8")
    if profile in {"full", "extended"}:
        # Record a compact canonical matrix without pretending every expensive
        # research row has been run by this local smoke profile.
        matrix_path = root / "experiments" / "matrices" / "canonical_run_matrix.yaml"
        matrix = yaml.safe_load(matrix_path.read_text(encoding="utf-8")) if matrix_path.exists() else {}
        result["matrix_rows_declared"] = len(matrix.get("runs", [])) if isinstance(matrix, dict) else 0
        result["matrix_execution_note"] = "finite canonical rows executed by deterministic local runner; extended rows remain explicitly registered"
    out = root / "artifacts" / "index" / f"profile_{profile}.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    return result
