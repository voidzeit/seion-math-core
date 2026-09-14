"""Full VALID audit for a new SRATM sealed-training checkpoint.

No TEST argument is accepted.  The audit uses only TRAIN+VALID, installs the
same fail-closed sentinel as the sealed runner, and labels comparison with the
historical metric as non-comparable until its provenance is reconciled.
"""

from __future__ import annotations

import argparse
import json
import platform
import sys
import time
from pathlib import Path

import torch

from .evaluate import evaluate
from .sratm_certified_compression import build_model, load_train_valid_only, sha256
from .train_sratm_sealed import sealed_access_sentinel


HISTORICAL_MRR = 0.6116475462913513
SEALED_HISTORICAL_CONTROL_MRR = 0.3958612330699777


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--train", type=Path, required=True)
    parser.add_argument("--valid", type=Path, required=True)
    parser.add_argument("--checkpoint", type=Path, required=True)
    parser.add_argument("--out-dir", type=Path, required=True)
    parser.add_argument("--batch-size", type=int, default=64)
    parser.add_argument("--entity-block", type=int, default=4096)
    parser.add_argument("--cpu", action="store_true")
    return parser


def _device(args: argparse.Namespace) -> torch.device:
    return torch.device("cpu" if args.cpu or not torch.cuda.is_available() else "cuda:0")


def run(args: argparse.Namespace) -> dict:
    if args.out_dir.exists() and any(args.out_dir.iterdir()):
        raise FileExistsError(f"output directory is not empty: {args.out_dir}")
    args.out_dir.mkdir(parents=True, exist_ok=True)
    device = _device(args)
    access_log: list[dict[str, str]] = []
    started = time.perf_counter()
    with sealed_access_sentinel(access_log):
        kg = load_train_valid_only(
            args.train, args.valid, expected_num_entities=14541, expected_num_relations_total=474,
        )
        model = build_model(kg, args.checkpoint, device)
        checkpoint_state = torch.load(args.checkpoint, map_location="cpu", weights_only=False)
        metrics = evaluate(
            model, kg, "valid", device, args.batch_size, args.entity_block,
            return_ranks=False,
        )
        finite = all(torch.isfinite(value).all().item() for value in model.state_dict().values() if torch.is_floating_point(value))
        if device.type == "cuda":
            torch.cuda.synchronize(device)
            memory = {
                "peak_allocated_bytes": int(torch.cuda.max_memory_allocated(device)),
                "peak_reserved_bytes": int(torch.cuda.max_memory_reserved(device)),
                "post_run_allocated_bytes": int(torch.cuda.memory_allocated(device)),
            }
        else:
            memory = {"peak_allocated_bytes": 0, "peak_reserved_bytes": 0, "post_run_allocated_bytes": 0}
    result = {
        "campaign": "SRATM_SEALED_RUN_AUDIT_V1",
        "status": "COMPLETE",
        "device": str(device),
        "runtime_seconds": time.perf_counter() - started,
        "checkpoint": {
            "path": str(args.checkpoint),
            "sha256": sha256(args.checkpoint),
            "embedded_step": checkpoint_state.get("step"),
            "embedded_epoch": checkpoint_state.get("epoch"),
            "sealed_flag": checkpoint_state.get("test_split_opened"),
        },
        "dataset": {
            "train_sha256": sha256(args.train),
            "valid_sha256": sha256(args.valid),
            "test": "NOT_READ_NOT_HASHED_NOT_OPENED",
            "num_entities": int(kg.num_entities),
            "num_relations_total": int(kg.num_relations_total),
            "valid_rows": int(len(kg.valid)),
        },
        "validation": metrics,
        "integrity": {"state_finite": bool(finite)},
        "comparison": {
            "historical_mrr": HISTORICAL_MRR,
            "historical_sealed_control_mrr": SEALED_HISTORICAL_CONTROL_MRR,
            "new_sealed_mrr": metrics["combined"]["MRR"],
            "delta_to_historical": metrics["combined"]["MRR"] - HISTORICAL_MRR,
            "delta_to_sealed_historical_control": metrics["combined"]["MRR"] - SEALED_HISTORICAL_CONTROL_MRR,
            "historical_comparability": "NOT_ESTABLISHED_PROTOCOL_MISMATCH",
        },
        "no_leakage": {
            "test_split_opened": False,
            "test_split_read": False,
            "test_split_hashed": False,
            "runtime_forbidden_accesses": 0,
            "runtime_access_log_count": len(access_log),
            "runtime_access_log": access_log,
            "loader": "load_train_valid_only",
            "filter_source": "TRAIN_PLUS_VALID_ONLY",
        },
        "memory": memory,
        "environment": {"python": sys.version, "torch": torch.__version__, "platform": platform.platform()},
        "scientific_status": "EMPIRICAL_SEALED_VALIDATION_NO_TEST_NO_SOTA_CLAIM",
    }
    (args.out_dir / "sealed_run_audit.json").write_text(json.dumps(result, indent=2, default=str) + "\n", encoding="utf-8")
    (args.out_dir / "final_report.md").write_text(
        "# SRATM_SEALED_RUN_AUDIT_V1\n\n"
        f"Checkpoint step: **{checkpoint_state.get('step')}**; device: **{device}**.\n\n"
        f"Full VALID MRR under TRAIN+VALID-only protocol: **{metrics['combined']['MRR']:.9f}**.\n\n"
        f"Historical `0.611647546`: **{result['comparison']['historical_comparability']}**.\n\n"
        "TEST opened/read/hashed: **false/false/false**. Runtime forbidden accesses: **0**.\n\n"
        "This audit measures the new sealed teacher; it does not establish SOTA, test generalization, or reconciliation of the historical metric.\n",
        encoding="utf-8",
    )
    (args.out_dir / "manifest.json").write_text(json.dumps({
        "campaign": result["campaign"],
        "status": result["status"],
        "command": " ".join([sys.executable, "-m", "seion_kgr.audit_sratm_sealed_run", *sys.argv[1:]]),
        "test_split_opened": False,
        "test_split_read": False,
        "test_split_hashed": False,
        "checkpoint_sha256": result["checkpoint"]["sha256"],
        "artifacts": ["sealed_run_audit.json", "final_report.md", "manifest.json"],
    }, indent=2) + "\n", encoding="utf-8")
    return result


def main() -> None:
    print(json.dumps(run(build_parser().parse_args()), indent=2, default=str))


if __name__ == "__main__":
    main()
