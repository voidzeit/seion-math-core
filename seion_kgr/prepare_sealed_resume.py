"""Prepare a fail-closed provenance manifest for a sealed SRATM resume.

This utility reads only the sealed run checkpoint, TRAIN, and VALID.  It never
opens, stats, or hashes TEST.  A resume is marked ready only when the persisted
checkpoint protocol and the run metadata agree with the current source
provenance.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
import sys
from pathlib import Path
from typing import Any

import torch


REQUIRED_CHECKPOINT_KEYS = {"model", "teacher", "optimizer", "epoch", "step", "rng", "sealed_protocol", "test_split_opened"}


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def git(*args: str) -> str:
    return subprocess.run(["git", *args], capture_output=True, text=True, check=False).stdout.strip()


def finite_state(value: Any) -> bool:
    if isinstance(value, torch.Tensor):
        return bool(torch.isfinite(value).all().item()) if value.is_floating_point() else True
    if isinstance(value, dict):
        return all(finite_state(item) for item in value.values())
    if isinstance(value, (list, tuple)):
        return all(finite_state(item) for item in value)
    return True


def parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--run-dir", type=Path, required=True)
    p.add_argument("--train", type=Path, required=True)
    p.add_argument("--valid", type=Path, required=True)
    p.add_argument("--trainer-source", type=Path, default=Path("seion_kgr/train_sratm_sealed.py"))
    return p


def main() -> int:
    args = parser().parse_args()
    run_dir = args.run_dir
    checkpoint = run_dir / "checkpoint_last.pt"
    prior_manifest = json.loads((run_dir / "manifest.json").read_text(encoding="utf-8"))
    prior_config = json.loads((run_dir / "config.json").read_text(encoding="utf-8"))
    checkpoint_state = torch.load(checkpoint, map_location="cpu", weights_only=False)
    embedded = dict(checkpoint_state.get("sealed_protocol") or {})

    current_git = git("rev-parse", "HEAD")
    original_git = prior_manifest.get("git_head")
    trainer_source_hash = sha256(args.trainer_source)
    train_hash = sha256(args.train)
    valid_hash = sha256(args.valid)
    required = sorted(REQUIRED_CHECKPOINT_KEYS)
    missing = [key for key in required if key not in checkpoint_state]
    mismatches = {}
    for key in sorted(set(embedded) | set(prior_config)):
        if key in {"resume", "out_dir"}:
            continue
        if embedded.get(key) != prior_config.get(key):
            mismatches[key] = {"checkpoint": embedded.get(key), "config": prior_config.get(key)}

    reasons: list[str] = []
    if missing:
        reasons.append("CHECKPOINT_REQUIRED_STATE_MISSING")
    if checkpoint_state.get("test_split_opened") is not False:
        reasons.append("CHECKPOINT_SEALED_FLAG_INVALID")
    if not finite_state(checkpoint_state.get("model")) or not finite_state(checkpoint_state.get("teacher")):
        reasons.append("CHECKPOINT_NONFINITE_STATE")
    if original_git != current_git:
        reasons.append("RUN_GIT_SHA_DIFFERS_FROM_CURRENT_CHECKOUT")
    if "seion_kgr/train_sratm_sealed.py" not in git("ls-tree", "-r", "--name-only", original_git).splitlines():
        reasons.append("ORIGINAL_GIT_SHA_DID_NOT_CONTAIN_SEALED_TRAINER")
    if mismatches:
        reasons.append("PERSISTED_CONFIG_CONFLICTS_WITH_CHECKPOINT_PROTOCOL")

    result = {
        "campaign": "SRATM_SEALED_TEACHER_CLOSURE_V1",
        "status": "RESUME_PROVENANCE_FAILURE" if reasons else "RESUME_PROVENANCE_VERIFIED",
        "resume_ready": not reasons,
        "decision": "DO_NOT_RESUME" if reasons else "RESUME_ALLOWED",
        "reasons": reasons,
        "run": {
            "path": str(run_dir),
            "prior_manifest_git_sha": original_git,
            "current_git_sha": current_git,
            "checkpoint": str(checkpoint),
            "checkpoint_sha256": sha256(checkpoint),
            "checkpoint_step": checkpoint_state.get("step"),
            "checkpoint_epoch": checkpoint_state.get("epoch"),
            "checkpoint_required_keys": required,
            "checkpoint_missing_keys": missing,
            "optimizer_state_present": "optimizer" in checkpoint_state,
            "scheduler_state": "NOT_CONFIGURED_IN_RUNNER",
            "ema_state_present": "teacher" in checkpoint_state,
            "rng_state_present": "rng" in checkpoint_state,
            "checkpoint_state_finite": finite_state(checkpoint_state),
        },
        "protocol": {
            "checkpoint_embedded": embedded,
            "persisted_config": prior_config,
            "config_mismatches": mismatches,
            "loader": "TRAIN_PLUS_VALID_ONLY",
            "filter_policy": "TRAIN_PLUS_VALID_ONLY",
            "test_split_opened": False,
            "test_split_read": False,
            "test_split_hashed": False,
            "forbidden_test_accesses": 0,
        },
        "datasets": {
            "train_path": str(args.train),
            "valid_path": str(args.valid),
            "train_sha256": train_hash,
            "valid_sha256": valid_hash,
            "test": "NOT_READ_NOT_HASHED_NOT_OPENED",
        },
        "source_provenance": {
            "trainer_source": str(args.trainer_source),
            "trainer_source_sha256_current": trainer_source_hash,
            "original_git_contains_trainer": "seion_kgr/train_sratm_sealed.py" in git("ls-tree", "-r", "--name-only", original_git).splitlines(),
        },
        "scientific_status": "NOT_ESTABLISHED_RESUME_PROVENANCE",
        "historical_metric_status": "HISTORICAL_UNRECONCILED",
        "test_policy": "TEST_UNTOUCHED",
    }
    output = run_dir / "resume_manifest.json"
    output.write_text(json.dumps(result, indent=2, default=str) + "\n", encoding="utf-8")
    print(json.dumps(result, indent=2, default=str))
    return 0 if not reasons else 2


if __name__ == "__main__":
    sys.exit(main())
