"""Hardware microbenchmark for a frozen TTN checkpoint."""

from __future__ import annotations

import argparse
import json
import time
from pathlib import Path

import torch

from . import reproducibility as repro
from .data import load_knowledge_graph
from .ttn_branching import BranchingTTNK3


def parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--checkpoint", type=Path, required=True)
    p.add_argument("--train", default="data/FB15K-237/train.txt")
    p.add_argument("--valid", default="data/FB15K-237/valid.txt")
    p.add_argument("--test", default="data/FB15K-237/test.txt")
    p.add_argument("--out", type=Path, required=True)
    p.add_argument("--queries", type=int, default=512)
    p.add_argument("--batch-size", type=int, default=64)
    p.add_argument("--repeats", type=int, default=3)
    p.add_argument("--ranks", default="1:4,4:24,8:24,16:32,32:32")
    p.add_argument("--cpu", action="store_true")
    return p


def _device(args: argparse.Namespace) -> torch.device:
    return torch.device("cpu" if args.cpu or not torch.cuda.is_available() else "cuda")


@torch.inference_mode()
def _measure(model, kg, queries, device, mode, rank1, rank2, batch_size, repeats):
    model.set_ranks(rank1, rank2)
    model.set_mode(mode)
    h = torch.tensor([row[0] for row in queries], device=device)
    r = torch.tensor([row[1] for row in queries], device=device)
    candidates = torch.arange(kg.num_entities, device=device)

    def one_pass():
        checksum = torch.zeros((), device=device)
        for offset in range(0, len(queries), batch_size):
            scores = model.score_tail_candidates(
                h[offset : offset + batch_size],
                r[offset : offset + batch_size],
                candidates,
            )
            checksum = checksum + scores.sum()
        return checksum

    one_pass()
    if device.type == "cuda":
        torch.cuda.synchronize(device)
        torch.cuda.reset_peak_memory_stats(device)
    elapsed = []
    checksum = None
    for _ in range(repeats):
        if device.type == "cuda":
            torch.cuda.synchronize(device)
        start = time.perf_counter()
        checksum = one_pass()
        if device.type == "cuda":
            torch.cuda.synchronize(device)
        elapsed.append(time.perf_counter() - start)
    peak_allocated = int(torch.cuda.max_memory_allocated(device)) if device.type == "cuda" else None
    peak_reserved = int(torch.cuda.max_memory_reserved(device)) if device.type == "cuda" else None
    mean_seconds = sum(elapsed) / len(elapsed)
    return {
        "mode": mode,
        "rank1": rank1,
        "rank2": rank2,
        "queries": len(queries),
        "entities_scored_per_query": kg.num_entities,
        "batch_size": batch_size,
        "repeats": repeats,
        "mean_seconds": mean_seconds,
        "queries_per_second": len(queries) / mean_seconds,
        "peak_allocated_bytes": peak_allocated,
        "peak_reserved_bytes": peak_reserved,
        "checksum": float(checksum.item()),
        "resource_proxy": model.resource_proxy(rank1, rank2, candidate_count=kg.num_entities),
    }


def main() -> None:
    args = parser().parse_args()
    if args.queries <= 0 or args.batch_size <= 0 or args.repeats <= 0:
        raise ValueError("queries, batch-size, and repeats must be positive")
    device = _device(args)
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
    queries = [tuple(int(value) for value in row) for row in kg.test[: args.queries]]
    ranks = [(int(a), int(b)) for a, b in (item.split(":") for item in args.ranks.split(","))]
    records = [_measure(model, kg, queries, device, "full", model.branch_dim, model.branch_dim, args.batch_size, args.repeats)]
    records += [_measure(model, kg, queries, device, "projected", a, b, args.batch_size, args.repeats) for a, b in ranks]
    output = {
        "status": "TTN_HARDWARE_MICROBENCHMARK",
        "device": str(device),
        "checkpoint": str(args.checkpoint),
        "dataset": "FB15K-237",
        "queries": len(queries),
        "records": records,
        "limitations": [
            "Microbenchmark uses fixed test-query order and measures scorer throughput, not end-to-end filtered ranking.",
            "One hardware device and one frozen seed; results are not universal hardware claims.",
        ],
    }
    args.out.parent.mkdir(parents=True, exist_ok=True)
    repro.save_json(output, args.out)
    print(json.dumps({"out": str(args.out), "records": len(records), "device": str(device)}, sort_keys=True))


if __name__ == "__main__":
    main()
