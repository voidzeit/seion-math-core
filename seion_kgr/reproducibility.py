"""Run manifests, hashing, RNG state — pattern reused from ``seion_train_v25.py``.

Contract §XV / `papers/software_v4`. Every trainer run gets a
``runs/<run_id>/`` directory with hashed inputs/outputs and an
append-only metrics log.
"""
from __future__ import annotations

import datetime as dt
import hashlib
import json
import os
import platform
import random
import subprocess
import sys
from pathlib import Path
from typing import Any, Dict, Mapping, Optional, Sequence

import numpy as np
import torch


def utc_now() -> str:
    return dt.datetime.now(dt.timezone.utc).isoformat()


def ensure_dir(path: str | Path) -> Path:
    p = Path(path)
    p.mkdir(parents=True, exist_ok=True)
    return p


def atomic_write_text(path: str | Path, text: str) -> None:
    path = Path(path)
    ensure_dir(path.parent)
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(text, encoding="utf-8")
    os.replace(tmp, path)


def save_json(obj: Any, path: str | Path) -> None:
    atomic_write_text(path, json.dumps(obj, indent=2, ensure_ascii=False, allow_nan=False, default=str))


def append_jsonl(obj: Mapping[str, Any], path: str | Path) -> None:
    path = Path(path)
    ensure_dir(path.parent)
    with path.open("a", encoding="utf-8") as f:
        f.write(json.dumps(dict(obj), ensure_ascii=False, allow_nan=False, default=str) + "\n")


def sha256_file(path: str | Path, chunk_size: int = 1 << 20) -> str:
    p = Path(path)
    h = hashlib.sha256()
    with p.open("rb") as f:
        while True:
            block = f.read(chunk_size)
            if not block:
                break
            h.update(block)
    return h.hexdigest()


def sha256_bytes(blob: bytes) -> str:
    return hashlib.sha256(blob).hexdigest()


def file_manifest(path: str | Path) -> Dict[str, Any]:
    p = Path(path).resolve()
    return {
        "path": str(p),
        "exists": p.is_file(),
        "size_bytes": p.stat().st_size if p.is_file() else None,
        "sha256": sha256_file(p) if p.is_file() else None,
    }


def run_command(cmd: Sequence[str], cwd: Optional[str | Path] = None, timeout: float = 5.0) -> str:
    try:
        r = subprocess.run(
            list(cmd), cwd=str(cwd) if cwd is not None else None,
            capture_output=True, text=True, timeout=timeout, check=False,
        )
        return (r.stdout or r.stderr or "").strip()[:20000]
    except Exception as exc:  # pragma: no cover - environment dependent
        return f"unavailable: {type(exc).__name__}: {exc}"


def git_manifest(cwd: str | Path) -> Dict[str, Any]:
    root = run_command(["git", "rev-parse", "--show-toplevel"], cwd=cwd)
    if not root or root.startswith("unavailable") or "fatal:" in root.lower():
        return {"available": False, "root": None, "commit": None, "dirty": None}
    commit = run_command(["git", "rev-parse", "HEAD"], cwd=root)
    status = run_command(["git", "status", "--porcelain"], cwd=root)
    return {
        "available": True, "root": root, "commit": commit,
        "dirty": bool(status.strip()), "status_porcelain": status,
    }


def environment_manifest() -> Dict[str, Any]:
    return {
        "created_utc": utc_now(),
        "python": sys.version,
        "platform": platform.platform(),
        "numpy": np.__version__,
        "torch": torch.__version__,
        "torch_cuda": torch.version.cuda,
    }


def hardware_manifest() -> Dict[str, Any]:
    out: Dict[str, Any] = {"cuda_available": bool(torch.cuda.is_available()), "cpu_count": os.cpu_count()}
    if torch.cuda.is_available():
        out["cuda_devices"] = [
            {"index": i, "name": torch.cuda.get_device_name(i)} for i in range(torch.cuda.device_count())
        ]
    return out


def set_seed(seed: int) -> None:
    random.seed(seed)
    np.random.seed(seed)
    torch.manual_seed(seed)
    if torch.cuda.is_available():
        torch.cuda.manual_seed_all(seed)


RUN_CONTROL_FIELDS = (
    "seed", "out_dir", "resume", "self_test", "cpu",
    "epochs", "eval_every", "eval_batch", "eval_subset", "eval_max_queries", "entity_block_eval",
)


def config_identity_hash(resolved_config: Mapping[str, Any], exclude: Sequence[str] = RUN_CONTROL_FIELDS) -> str:
    """Mandate §I.5: configuration identity is not execution identity. A
    resume/retry/CPU-vs-GPU duplicate, or a run continued for more
    epochs, must hash to the SAME `configuration_id` — only the
    architecture/data/optimization hyperparameters that actually change
    what is being learned count as "configuration"; run-control knobs
    (seed, device, epoch budget, eval cadence/subset) do not. Each
    actual invocation still gets its own `execution_id`."""
    filtered = {k: v for k, v in sorted(resolved_config.items()) if k not in exclude}
    blob = json.dumps(filtered, sort_keys=True, default=str).encode("utf-8")
    return hashlib.sha256(blob).hexdigest()[:16]


def new_execution_id() -> str:
    import uuid

    return uuid.uuid4().hex[:16]


def build_run_contract(
    out_dir: str | Path,
    command: Sequence[str],
    dataset_paths: Mapping[str, str],
    resolved_config: Optional[Mapping[str, Any]] = None,
    resume_from: Optional[str] = None,
    allow_existing: bool = False,
) -> Dict[str, Any]:
    out = Path(out_dir)
    if out.exists() and any(out.iterdir()) and not allow_existing and resume_from is None:
        raise FileExistsError(
            f"--out_dir {out} already exists and is not empty. Reusing an output directory silently "
            "mixes provenance across configurations (mandate §I.5) — use a fresh --out_dir, or pass "
            "--resume to explicitly continue the SAME configuration."
        )
    ensure_dir(out)
    datasets = {name: file_manifest(path) for name, path in dataset_paths.items() if path}
    git = git_manifest(Path(__file__).resolve().parent)
    environment = environment_manifest()
    hardware = hardware_manifest()
    save_json(environment, out / "environment.json")
    save_json(hardware, out / "hardware.json")
    save_json(datasets, out / "dataset_manifest.json")
    save_json(git, out / "git_manifest.json")
    atomic_write_text(out / "command.txt", " ".join(command) + "\n")

    configuration_id = config_identity_hash(resolved_config) if resolved_config else None
    execution_id = new_execution_id()
    manifest = {
        "schema": "seion-kgr-run-v26.0",
        "created_utc": utc_now(),
        "status": "RUNNING",
        "command": " ".join(command),
        "datasets": datasets,
        "git": git,
        "configuration_id": configuration_id,
        "execution_id": execution_id,
        "parent_execution_id": None,  # filled in by the caller if this run is a --resume continuation
        "resume_from": resume_from,
        "scientific_warnings": [
            "A numerical regularizer is not a theorem.",
            "certified_bound and empirical_error_predictor are separate objects; never conflate them.",
            "A smoke-scale run (few epochs, one seed) is not a confirmatory campaign (Gate 12).",
            "A resume, retry, CPU duplicate, or GPU duplicate is not a new seed (mandate §I.5) — "
            "compare execution_id, not just configuration_id + seed, when counting independent runs.",
        ],
    }
    if resolved_config is not None:
        save_json(dict(resolved_config), out / "resolved_config.json")
    save_json(manifest, out / "run_manifest.json")
    return manifest


def save_checkpoint(
    path: str | Path,
    model_state: Mapping[str, Any],
    optimizer_state: Mapping[str, Any],
    epoch: int,
    global_step: int,
    best_mrr: float,
    args: Mapping[str, Any],
    rng_state: Mapping[str, Any],
    best_epoch: Optional[int] = None,
    evaluations_without_improvement: int = 0,
) -> None:
    path = Path(path)
    ensure_dir(path.parent)
    tmp = path.with_suffix(path.suffix + ".tmp")
    torch.save(
        {
            "model_state": model_state,
            "optimizer_state": optimizer_state,
            "epoch": int(epoch),
            "global_step": int(global_step),
            "best_mrr": float(best_mrr),
            "best_epoch": best_epoch,
            "evaluations_without_improvement": int(evaluations_without_improvement),
            "args": dict(args),
            "rng_state": dict(rng_state),
        },
        tmp,
    )
    os.replace(tmp, path)


def load_checkpoint(path: str | Path) -> Dict[str, Any]:
    return torch.load(path, map_location="cpu", weights_only=False)


def rng_state_snapshot(
    seed: int,
    numpy_rng: Optional[np.random.Generator] = None,
    generators: Optional[Mapping[str, torch.Generator]] = None,
) -> Dict[str, Any]:
    """Capture every stochastic stream owned by the trainer."""
    return {
        "python": random.getstate(),
        "torch": torch.get_rng_state(),
        "torch_cuda": torch.cuda.get_rng_state_all() if torch.cuda.is_available() else None,
        "numpy": numpy_rng.bit_generator.state if numpy_rng is not None else None,
        "generators": {name: generator.get_state() for name, generator in (generators or {}).items()},
        "seed": seed,
    }


def restore_rng_state(
    state: Mapping[str, Any],
    numpy_rng: Optional[np.random.Generator] = None,
    generators: Optional[Mapping[str, torch.Generator]] = None,
) -> None:
    """Restore the state captured by :func:`rng_state_snapshot`."""
    if state.get("python") is not None:
        random.setstate(state["python"])
    if state.get("torch") is not None:
        torch.set_rng_state(state["torch"])
    cuda_state = state.get("torch_cuda")
    if cuda_state is not None and torch.cuda.is_available():
        torch.cuda.set_rng_state_all(cuda_state)
    if numpy_rng is not None and state.get("numpy") is not None:
        numpy_rng.bit_generator.state = state["numpy"]
    saved_generators = state.get("generators") or {}
    for name, generator in (generators or {}).items():
        if name in saved_generators:
            generator.set_state(saved_generators[name])


def mark_completed(out_dir: str | Path, final_metrics: Mapping[str, Any]) -> None:
    out = Path(out_dir)
    save_json(dict(final_metrics), out / "final_metrics.json")
    manifest_path = out / "run_manifest.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    manifest["status"] = "COMPLETED"
    manifest["completed_utc"] = utc_now()
    save_json(manifest, manifest_path)
