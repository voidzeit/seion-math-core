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


def build_run_contract(out_dir: str | Path, command: Sequence[str], dataset_paths: Mapping[str, str]) -> Dict[str, Any]:
    out = ensure_dir(out_dir)
    datasets = {name: file_manifest(path) for name, path in dataset_paths.items() if path}
    git = git_manifest(Path(__file__).resolve().parent)
    environment = environment_manifest()
    hardware = hardware_manifest()
    save_json(environment, out / "environment.json")
    save_json(hardware, out / "hardware.json")
    save_json(datasets, out / "dataset_manifest.json")
    save_json(git, out / "git_manifest.json")
    atomic_write_text(out / "command.txt", " ".join(command) + "\n")
    manifest = {
        "schema": "seion-kgr-run-v26.0",
        "created_utc": utc_now(),
        "status": "RUNNING",
        "command": " ".join(command),
        "datasets": datasets,
        "git": git,
        "scientific_warnings": [
            "A numerical regularizer is not a theorem.",
            "certified_bound and empirical_error_predictor are separate objects; never conflate them.",
            "A smoke-scale run (few epochs, one seed) is not a confirmatory campaign (Gate 12).",
        ],
    }
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
            "args": dict(args),
            "rng_state": dict(rng_state),
        },
        tmp,
    )
    os.replace(tmp, path)


def load_checkpoint(path: str | Path) -> Dict[str, Any]:
    return torch.load(path, map_location="cpu", weights_only=False)


def rng_state_snapshot(seed: int, numpy_rng: Optional[np.random.Generator] = None) -> Dict[str, Any]:
    return {
        "torch": torch.get_rng_state(),
        "numpy": numpy_rng.bit_generator.state if numpy_rng is not None else None,
        "seed": seed,
    }


def mark_completed(out_dir: str | Path, final_metrics: Mapping[str, Any]) -> None:
    out = Path(out_dir)
    save_json(dict(final_metrics), out / "final_metrics.json")
    manifest_path = out / "run_manifest.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    manifest["status"] = "COMPLETED"
    manifest["completed_utc"] = utc_now()
    save_json(manifest, manifest_path)
