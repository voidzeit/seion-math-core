"""Immutable v3 run identity and mandatory per-run artifact contract."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import platform
import subprocess
import sys
from typing import Any, Mapping, Sequence

import numpy as np
import yaml

from .typed_tree import Tree, tree_hash, tree_to_dict


MANDATORY_FILES = (
    "config.yaml",
    "resolved_config.yaml",
    "command.txt",
    "stdout.log",
    "stderr.log",
    "environment.json",
    "hardware.json",
    "run_manifest.json",
    "tree.json",
    "tree.svg",
    "type_signature.json",
    "law_tensors.npz",
    "local_constants.json",
    "exact_or_reference_metrics.json",
    "optimization_history.csv",
    "node_contributions.csv",
    "final_metrics.json",
    "certificate.json",
    "summary.md",
    "artifact_hashes.json",
)

EXTREMIZER_FILES = (
    "best_lower_bound.json",
    "certified_upper_bound.json",
    "optimality_gap.json",
    "extremizer_tensor.npz",
    "extremizer_inputs.npz",
    "independent_recheck.json",
)


def canonical_hash(value: Any) -> str:
    payload = json.dumps(value, sort_keys=True, separators=(",", ":"), default=str)
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def current_commit(repo_root: Path) -> str:
    result = subprocess.run(
        ["git", "rev-parse", "HEAD"], cwd=repo_root, text=True, capture_output=True, check=True
    )
    return result.stdout.strip()


@dataclass(frozen=True, slots=True)
class V3RunConfig:
    block: str
    instance_id: str
    method: str
    seed: int | None
    precision: str
    device: str
    parameters: Mapping[str, Any]
    restarts: int = 0
    stage: str = "full"

    @property
    def resolved_hash(self) -> str:
        return canonical_hash(asdict(self))

    @property
    def scientific_instance_hash(self) -> str:
        value = asdict(self)
        value.pop("seed", None)
        value.pop("restarts", None)
        return canonical_hash(value)


def environment_inventory() -> dict[str, Any]:
    packages: dict[str, str] = {}
    for name in ("numpy", "scipy", "sympy", "pandas", "torch", "matplotlib", "mpmath"):
        try:
            module = __import__(name)
            packages[name] = str(getattr(module, "__version__", "unknown"))
        except Exception as exc:  # pragma: no cover - optional package path
            packages[name] = f"unavailable:{type(exc).__name__}"
    return {
        "generated_utc": datetime.now(timezone.utc).isoformat(),
        "python": sys.version,
        "executable": sys.executable,
        "platform": platform.platform(),
        "packages": packages,
        "environment_keys": sorted(
            key for key in os.environ if key.startswith(("CUDA", "PYTHON", "OMP", "MKL"))
        ),
    }


def hardware_inventory() -> dict[str, Any]:
    result: dict[str, Any] = {
        "machine": platform.machine(),
        "processor": platform.processor(),
        "logical_cpu_count": os.cpu_count(),
    }
    try:
        import psutil

        result["ram_bytes"] = int(psutil.virtual_memory().total)
    except Exception:
        result["ram_bytes"] = None
    try:
        import torch

        result["cuda_available"] = bool(torch.cuda.is_available())
        result["cuda_version"] = torch.version.cuda
        if torch.cuda.is_available():
            result["gpus"] = [
                {
                    "index": index,
                    "name": torch.cuda.get_device_name(index),
                    "total_memory_bytes": int(torch.cuda.get_device_properties(index).total_memory),
                    "capability": list(torch.cuda.get_device_capability(index)),
                }
                for index in range(torch.cuda.device_count())
            ]
    except Exception as exc:  # pragma: no cover - optional package path
        result["cuda_available"] = False
        result["cuda_error"] = type(exc).__name__
    return result


def _write_json(path: Path, value: Any) -> None:
    path.write_text(json.dumps(value, indent=2, sort_keys=True, default=str) + "\n", encoding="utf-8")


def _tree_svg(tree: Tree) -> str:
    label = tree_hash(tree)[:16]
    return (
        '<svg xmlns="http://www.w3.org/2000/svg" width="640" height="120" viewBox="0 0 640 120">'
        '<rect width="640" height="120" fill="white"/>'
        '<path d="M40 75 H600" stroke="#355c7d" stroke-width="2"/>'
        '<circle cx="320" cy="55" r="18" fill="#f2cc8f" stroke="#23395d" stroke-width="2"/>'
        f'<text x="320" y="60" text-anchor="middle" font-family="Arial" font-size="12">T</text>'
        f'<text x="320" y="102" text-anchor="middle" font-family="Arial" font-size="13">{label}</text>'
        "</svg>\n"
    )


def write_run_artifacts(
    run_dir: Path,
    *,
    repo_root: Path,
    config: V3RunConfig,
    tree: Tree,
    type_signature: Mapping[str, Any],
    law_tensors: Mapping[str, np.ndarray],
    local_constants: Mapping[str, Any],
    reference_metrics: Mapping[str, Any],
    optimization_history: Sequence[Mapping[str, Any]],
    node_contributions: Sequence[Mapping[str, Any]],
    final_metrics: Mapping[str, Any],
    certificate: Mapping[str, Any],
    command: str,
    stdout: str = "",
    stderr: str = "",
    extremizer: Mapping[str, Any] | None = None,
) -> Path:
    """Write and hash the complete v3 artifact set for one run."""

    run_dir.mkdir(parents=True, exist_ok=True)
    config_data = asdict(config)
    (run_dir / "config.yaml").write_text(yaml.safe_dump(config_data, sort_keys=True), encoding="utf-8")
    (run_dir / "resolved_config.yaml").write_text(
        yaml.safe_dump({**config_data, "resolved_config_hash": config.resolved_hash}, sort_keys=True),
        encoding="utf-8",
    )
    (run_dir / "command.txt").write_text(command.rstrip() + "\n", encoding="utf-8")
    (run_dir / "stdout.log").write_text(stdout, encoding="utf-8")
    (run_dir / "stderr.log").write_text(stderr, encoding="utf-8")
    _write_json(run_dir / "environment.json", environment_inventory())
    _write_json(run_dir / "hardware.json", hardware_inventory())
    input_hash = canonical_hash({"tree": tree_to_dict(tree), "types": type_signature})
    manifest = {
        "schema_version": 3,
        "run_id": run_dir.name,
        "block": config.block,
        "stage": config.stage,
        "status": "COMPLETE",
        "source_commit": current_commit(repo_root),
        "resolved_config_hash": config.resolved_hash,
        "scientific_instance_hash": config.scientific_instance_hash,
        "mathematical_object_hash": tree_hash(tree),
        "input_artifact_hash": input_hash,
        "seed": config.seed,
        "restarts": config.restarts,
        "precision": config.precision,
        "device": config.device,
        "generated_utc": datetime.now(timezone.utc).isoformat(),
    }
    _write_json(run_dir / "run_manifest.json", manifest)
    _write_json(run_dir / "tree.json", tree_to_dict(tree))
    (run_dir / "tree.svg").write_text(_tree_svg(tree), encoding="utf-8")
    _write_json(run_dir / "type_signature.json", type_signature)
    np.savez_compressed(run_dir / "law_tensors.npz", **law_tensors)
    _write_json(run_dir / "local_constants.json", local_constants)
    _write_json(run_dir / "exact_or_reference_metrics.json", reference_metrics)
    _write_csv(run_dir / "optimization_history.csv", optimization_history)
    _write_csv(run_dir / "node_contributions.csv", node_contributions)
    _write_json(run_dir / "final_metrics.json", final_metrics)
    _write_json(run_dir / "certificate.json", certificate)
    summary = (
        f"# V3 run {run_dir.name}\n\n"
        f"- Block: `{config.block}`\n"
        f"- Scientific instance: `{config.scientific_instance_hash}`\n"
        f"- Tree: `{tree_hash(tree)}`\n"
        f"- Status: `COMPLETE`\n"
        f"- Epistemic result: `{certificate.get('status', 'NUMERICAL_OBSERVATION')}`\n"
    )
    (run_dir / "summary.md").write_text(summary, encoding="utf-8")
    if extremizer is not None:
        _write_json(run_dir / "best_lower_bound.json", extremizer.get("best_lower_bound", {}))
        _write_json(run_dir / "certified_upper_bound.json", extremizer.get("certified_upper_bound", {}))
        _write_json(run_dir / "optimality_gap.json", extremizer.get("optimality_gap", {}))
        np.savez_compressed(run_dir / "extremizer_tensor.npz", tensor=extremizer.get("tensor", np.empty(0)))
        np.savez_compressed(run_dir / "extremizer_inputs.npz", inputs=extremizer.get("inputs", np.empty(0)))
        _write_json(run_dir / "independent_recheck.json", extremizer.get("independent_recheck", {}))
    hashes: dict[str, dict[str, Any]] = {}
    for path in sorted(run_dir.iterdir()):
        if path.name == "artifact_hashes.json" or not path.is_file():
            continue
        payload = path.read_bytes()
        hashes[path.name] = {"bytes": len(payload), "sha256": hashlib.sha256(payload).hexdigest()}
    _write_json(run_dir / "artifact_hashes.json", hashes)
    validate_run_artifacts(run_dir, extremizer=extremizer is not None)
    return run_dir


def _write_csv(path: Path, rows: Sequence[Mapping[str, Any]]) -> None:
    import csv

    rows = list(rows)
    fields = sorted({key for row in rows for key in row}) or ["empty"]
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        for row in rows:
            writer.writerow(row)


def validate_run_artifacts(run_dir: Path, *, extremizer: bool = False) -> None:
    expected = set(MANDATORY_FILES) | (set(EXTREMIZER_FILES) if extremizer else set())
    missing = sorted(name for name in expected if not (run_dir / name).is_file())
    if missing:
        raise ValueError(f"run artifact contract is incomplete: {missing}")
    hashes = json.loads((run_dir / "artifact_hashes.json").read_text(encoding="utf-8"))
    for name, record in hashes.items():
        payload = (run_dir / name).read_bytes()
        if hashlib.sha256(payload).hexdigest() != record["sha256"]:
            raise ValueError(f"artifact hash mismatch for {name}")
