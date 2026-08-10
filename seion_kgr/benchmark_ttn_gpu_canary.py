"""Short post-crash CUDA canary for a frozen TTN checkpoint.

This intentionally does not train, allocate the full candidate matrix, or
run filtered evaluation. It is a reversible stability gate before long GPU
jobs. The process memory cap is deliberately below the project ceiling.
"""

from __future__ import annotations

import argparse
import json
import time
from pathlib import Path

import torch

from .data import load_knowledge_graph
from .ttn_branching import BranchingTTNK3


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--checkpoint", type=Path, required=True)
    parser.add_argument("--train", default="data/FB15K-237/train.txt")
    parser.add_argument("--valid", default="data/FB15K-237/valid.txt")
    parser.add_argument("--test", default="data/FB15K-237/test.txt")
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--iterations", type=int, default=32)
    parser.add_argument("--batch-size", type=int, default=32)
    parser.add_argument("--candidate-count", type=int, default=256)
    parser.add_argument("--max-vram-gb", type=float, default=4.0)
    parser.add_argument("--cpu", action="store_true")
    args = parser.parse_args()
    if args.iterations <= 0 or args.batch_size <= 0 or args.candidate_count <= 0:
        raise ValueError("iterations, batch-size, and candidate-count must be positive")

    if args.cpu or not torch.cuda.is_available():
        device = torch.device("cpu")
    else:
        device = torch.device("cuda:0")
        total = torch.cuda.get_device_properties(device).total_memory
        fraction = min(0.90, (args.max_vram_gb * 1024**3) / total)
        if fraction <= 0:
            raise ValueError("max-vram-gb must be positive")
        torch.cuda.set_per_process_memory_fraction(fraction, device=device)

    kg = load_knowledge_graph(args.train, args.valid, args.test)
    state = torch.load(args.checkpoint, map_location=device)
    model = BranchingTTNK3(
        kg.num_entities,
        kg.num_relations_total,
        int(state["dim"]),
        int(state["branch_dim"]),
    ).to(device)
    model.load_state_dict(state["model_state"])
    model.eval()
    model.set_mode("projected")
    model.set_ranks(model.branch_dim, model.branch_dim)
    rows = torch.as_tensor(kg.train[: args.batch_size], dtype=torch.long, device=device)
    h_ids, r_ids = rows[:, 0], rows[:, 1]
    candidates = torch.arange(min(args.candidate_count, kg.num_entities), device=device)
    if device.type == "cuda":
        torch.cuda.reset_peak_memory_stats(device)
        torch.cuda.synchronize(device)
    start = time.perf_counter()
    checksum = torch.zeros((), device=device)
    with torch.inference_mode():
        for _ in range(args.iterations):
            scores = model.score_tail_candidates(h_ids, r_ids, candidates)
            if not torch.isfinite(scores).all():
                raise RuntimeError("non-finite score observed during CUDA canary")
            checksum = checksum + scores.sum()
    if device.type == "cuda":
        torch.cuda.synchronize(device)
    elapsed = time.perf_counter() - start
    result = {
        "status": "GPU_CANARY_COMPLETE" if device.type == "cuda" else "CPU_CANARY_COMPLETE",
        "checkpoint": str(args.checkpoint),
        "device": str(device),
        "iterations": args.iterations,
        "batch_size": int(h_ids.numel()),
        "candidate_count": int(candidates.numel()),
        "elapsed_seconds": elapsed,
        "checksum": float(checksum.detach().cpu().item()),
        "max_vram_gb": args.max_vram_gb if device.type == "cuda" else None,
        "peak_allocated_bytes": torch.cuda.max_memory_allocated(device) if device.type == "cuda" else 0,
        "peak_reserved_bytes": torch.cuda.max_memory_reserved(device) if device.type == "cuda" else 0,
        "post_run_allocated_bytes": torch.cuda.memory_allocated(device) if device.type == "cuda" else 0,
    }
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(result, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
