"""Paired hardware benchmark for transformed TTN execution.

The comparison is deliberately between two calls through the same projected
executor: transformed full rank ``(D, D)`` versus transformed compressed
``(r1, r2)``.  The older benchmark compared ambient full execution against
projected execution and is retained as historical evidence, not as the
primary compression comparison.
"""

from __future__ import annotations

import argparse
import json
import math
import statistics
import time
from pathlib import Path
from typing import Any, Sequence

import torch

from . import reproducibility as repro
from .data import KnowledgeGraph, load_knowledge_graph
from .evaluate import evaluate
from .ttn_branching import BranchingTTNK3


def parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--checkpoint", type=Path, required=True)
    p.add_argument("--train", default="data/FB15K-237/train.txt")
    p.add_argument("--valid", default="data/FB15K-237/valid.txt")
    p.add_argument("--test", default="data/FB15K-237/test.txt")
    p.add_argument("--out", type=Path, required=True)
    p.add_argument("--queries", type=int, default=8192)
    p.add_argument("--batch-size", type=int, default=128)
    p.add_argument("--candidate-block", type=int, default=4096)
    p.add_argument("--warmups", type=int, default=100)
    p.add_argument("--repeats", type=int, default=30)
    p.add_argument("--filtered-warmups", type=int, default=2)
    p.add_argument("--filtered-repeats", type=int, default=3)
    p.add_argument("--ranks", default="1:4,1:16,4:24,8:24,16:32,32:32")
    p.add_argument("--skip-scorer", action="store_true")
    p.add_argument("--skip-filtered", action="store_true")
    p.add_argument("--cpu", action="store_true")
    return p


def _device(args: argparse.Namespace) -> torch.device:
    return torch.device("cpu" if args.cpu or not torch.cuda.is_available() else "cuda")


def _synchronize(device: torch.device) -> None:
    if device.type == "cuda":
        torch.cuda.synchronize(device)


def _percentile(values: Sequence[float], percentile: float) -> float:
    if not values:
        raise ValueError("cannot compute a percentile of an empty sequence")
    ordered = sorted(float(value) for value in values)
    if len(ordered) == 1:
        return ordered[0]
    position = (len(ordered) - 1) * percentile
    lower = int(position)
    upper = min(lower + 1, len(ordered) - 1)
    weight = position - lower
    return ordered[lower] * (1.0 - weight) + ordered[upper] * weight


def _log_ratio_ci95(numerator: Sequence[float], denominator: Sequence[float]) -> tuple[float, float]:
    """Approximate a paired 95% CI for a positive timing ratio."""

    if len(numerator) != len(denominator) or len(numerator) < 2:
        raise ValueError("paired timing samples must have equal length >= 2")
    ratios = [float(a) / float(b) for a, b in zip(numerator, denominator)]
    logs = [math.log(ratio) for ratio in ratios]
    mean_log = statistics.fmean(logs)
    standard_error = statistics.stdev(logs) / (len(logs) ** 0.5)
    return (
        math.exp(mean_log - 1.96 * standard_error),
        math.exp(mean_log + 1.96 * standard_error),
    )


def _cuda_or_wall_pass(one_pass, device: torch.device) -> tuple[float, Any]:
    """Run one pass and return milliseconds plus its checksum.

    CUDA events capture device execution; CPU runs use wall-clock timing.
    Inputs and candidate blocks are created outside this function so both
    paired conditions use the same executor and timed workload.
    """

    if device.type == "cuda":
        start = torch.cuda.Event(enable_timing=True)
        end = torch.cuda.Event(enable_timing=True)
        start.record()
        checksum = one_pass()
        end.record()
        end.synchronize()
        return float(start.elapsed_time(end)), checksum

    start_time = time.perf_counter()
    checksum = one_pass()
    return float((time.perf_counter() - start_time) * 1000.0), checksum


@torch.inference_mode()
def _measure_scorer(
    model: BranchingTTNK3,
    kg: KnowledgeGraph,
    queries: Sequence[tuple[int, int, int]],
    device: torch.device,
    rank1: int,
    rank2: int,
    batch_size: int,
    candidate_block: int,
    warmups: int,
    repeats: int,
    role: str,
) -> dict[str, Any]:
    if candidate_block <= 0 or batch_size <= 0 or warmups < 0 or repeats <= 0:
        raise ValueError("candidate-block, batch-size, warmups and repeats are invalid")

    # Both full and compressed conditions use this exact projected path.
    model.set_mode("projected")
    model.set_ranks(rank1, rank2)
    h_ids = torch.tensor([row[0] for row in queries], device=device, dtype=torch.long)
    r_ids = torch.tensor([row[1] for row in queries], device=device, dtype=torch.long)
    candidate_blocks = [
        torch.arange(start, min(start + candidate_block, kg.num_entities), device=device, dtype=torch.long)
        for start in range(0, kg.num_entities, candidate_block)
    ]

    def one_pass() -> torch.Tensor:
        checksum = torch.zeros((), device=device)
        for offset in range(0, len(queries), batch_size):
            h_batch = h_ids[offset : offset + batch_size]
            r_batch = r_ids[offset : offset + batch_size]
            for candidates in candidate_blocks:
                checksum = checksum + model.score_tail_candidates(h_batch, r_batch, candidates).sum()
        return checksum

    for _ in range(warmups):
        one_pass()
    _synchronize(device)
    if device.type == "cuda":
        torch.cuda.reset_peak_memory_stats(device)

    elapsed_ms: list[float] = []
    checksum = None
    for _ in range(repeats):
        _synchronize(device)
        elapsed, checksum = _cuda_or_wall_pass(one_pass, device)
        elapsed_ms.append(elapsed)

    mean_ms = statistics.fmean(elapsed_ms)
    peak_allocated = int(torch.cuda.max_memory_allocated(device)) if device.type == "cuda" else None
    peak_reserved = int(torch.cuda.max_memory_reserved(device)) if device.type == "cuda" else None
    return {
        "role": role,
        "executor_mode": "projected",
        "rank1": int(rank1),
        "rank2": int(rank2),
        "queries": len(queries),
        "entities_scored_per_query": kg.num_entities,
        "batch_size": batch_size,
        "candidate_block": candidate_block,
        "warmups": warmups,
        "repeats": repeats,
        "mean_ms": mean_ms,
        "p50_ms": _percentile(elapsed_ms, 0.50),
        "p95_ms": _percentile(elapsed_ms, 0.95),
        "samples_ms": elapsed_ms,
        "queries_per_second": len(queries) / (mean_ms / 1000.0),
        "peak_allocated_bytes": peak_allocated,
        "peak_reserved_bytes": peak_reserved,
        "checksum": float(checksum.item()),
        "resource_proxy": model.resource_proxy(rank1, rank2, candidate_count=kg.num_entities),
    }


@torch.inference_mode()
def _measure_scorer_paired(
    model: BranchingTTNK3,
    kg: KnowledgeGraph,
    queries: Sequence[tuple[int, int, int]],
    device: torch.device,
    ranks: Sequence[tuple[int, int]],
    batch_size: int,
    candidate_block: int,
    warmups: int,
    repeats: int,
) -> list[dict[str, Any]]:
    """Measure all scorer conditions in alternating order.

    Alternating the order on every repetition suppresses drift from GPU clock
    state and thermal conditions.  Each condition has its own cached
    transformed cores, so rank switching is outside the timed pass.
    """

    if repeats <= 0 or warmups < 0:
        raise ValueError("warmups and repeats are invalid")
    conditions = [(model.branch_dim, model.branch_dim, "transformed_full")]
    conditions.extend((rank1, rank2, "transformed_compressed") for rank1, rank2 in ranks)
    prepared: list[tuple[dict[str, Any], Any]] = []

    h_ids = torch.tensor([row[0] for row in queries], device=device, dtype=torch.long)
    r_ids = torch.tensor([row[1] for row in queries], device=device, dtype=torch.long)
    candidate_blocks = [
        torch.arange(start, min(start + candidate_block, kg.num_entities), device=device, dtype=torch.long)
        for start in range(0, kg.num_entities, candidate_block)
    ]

    for rank1, rank2, role in conditions:
        model.set_mode("projected")
        model.set_ranks(rank1, rank2)

        def one_pass(h=h_ids, r=r_ids, blocks=candidate_blocks) -> torch.Tensor:
            checksum = torch.zeros((), device=device)
            for offset in range(0, len(queries), batch_size):
                h_batch = h[offset : offset + batch_size]
                r_batch = r[offset : offset + batch_size]
                for candidates in blocks:
                    checksum = checksum + model.score_tail_candidates(h_batch, r_batch, candidates).sum()
            return checksum

        # Builds the transformed cores before timed samples.
        one_pass()
        prepared.append(({
            "role": role,
            "executor_mode": "projected",
            "rank1": int(rank1),
            "rank2": int(rank2),
            "queries": len(queries),
            "entities_scored_per_query": kg.num_entities,
            "batch_size": batch_size,
            "candidate_block": candidate_block,
            "warmups": warmups,
            "repeats": repeats,
            "resource_proxy": model.resource_proxy(rank1, rank2, candidate_count=kg.num_entities),
        }, one_pass))

    for _ in range(warmups):
        for _, one_pass in prepared:
            one_pass()
    _synchronize(device)
    if device.type == "cuda":
        torch.cuda.reset_peak_memory_stats(device)

    elapsed_by_condition: list[list[float]] = [[] for _ in prepared]
    checksums: list[float | None] = [None for _ in prepared]
    for repetition in range(repeats):
        order = range(len(prepared)) if repetition % 2 == 0 else range(len(prepared) - 1, -1, -1)
        for index in order:
            metadata, one_pass = prepared[index]
            model.set_ranks(metadata["rank1"], metadata["rank2"])
            _synchronize(device)
            elapsed, checksum = _cuda_or_wall_pass(one_pass, device)
            elapsed_by_condition[index].append(elapsed)
            checksums[index] = float(checksum.item())

    peak_allocated = int(torch.cuda.max_memory_allocated(device)) if device.type == "cuda" else None
    peak_reserved = int(torch.cuda.max_memory_reserved(device)) if device.type == "cuda" else None
    records: list[dict[str, Any]] = []
    for (metadata, _), elapsed_ms, checksum in zip(prepared, elapsed_by_condition, checksums):
        mean_ms = statistics.fmean(elapsed_ms)
        record = dict(metadata)
        record.update({
            "mean_ms": mean_ms,
            "p50_ms": _percentile(elapsed_ms, 0.50),
            "p95_ms": _percentile(elapsed_ms, 0.95),
            "samples_ms": elapsed_ms,
            "queries_per_second": len(queries) / (mean_ms / 1000.0),
            "peak_allocated_bytes": peak_allocated,
            "peak_reserved_bytes": peak_reserved,
            "checksum": checksum,
        })
        records.append(record)
    return records


@torch.inference_mode()
def _measure_filtered(
    model: BranchingTTNK3,
    kg: KnowledgeGraph,
    queries: Sequence[tuple[int, int, int]],
    device: torch.device,
    rank1: int,
    rank2: int,
    batch_size: int,
    candidate_block: int,
    warmups: int,
    repeats: int,
    role: str,
) -> dict[str, Any]:
    model.set_mode("projected")
    model.set_ranks(rank1, rank2)

    def one_pass() -> dict[str, Any]:
        return evaluate(
            model,
            kg,
            "test",
            device,
            batch_size=batch_size,
            entity_block=candidate_block,
            queries=queries,
        )

    for _ in range(warmups):
        one_pass()
    _synchronize(device)
    if device.type == "cuda":
        torch.cuda.reset_peak_memory_stats(device)

    elapsed_ms: list[float] = []
    metrics = None
    for _ in range(repeats):
        _synchronize(device)
        start = time.perf_counter()
        metrics = one_pass()
        _synchronize(device)
        elapsed_ms.append((time.perf_counter() - start) * 1000.0)

    peak_allocated = int(torch.cuda.max_memory_allocated(device)) if device.type == "cuda" else None
    peak_reserved = int(torch.cuda.max_memory_reserved(device)) if device.type == "cuda" else None
    mean_ms = statistics.fmean(elapsed_ms)
    return {
        "role": role,
        "executor_mode": "projected",
        "rank1": int(rank1),
        "rank2": int(rank2),
        "queries": len(queries),
        "batch_size": batch_size,
        "candidate_block": candidate_block,
        "warmups": warmups,
        "repeats": repeats,
        "mean_ms": mean_ms,
        "p50_ms": _percentile(elapsed_ms, 0.50),
        "p95_ms": _percentile(elapsed_ms, 0.95),
        "queries_per_second": len(queries) / (mean_ms / 1000.0),
        "peak_allocated_bytes": peak_allocated,
        "peak_reserved_bytes": peak_reserved,
        "metrics": metrics,
    }


def _load_model(checkpoint: Path, kg: KnowledgeGraph, device: torch.device) -> BranchingTTNK3:
    state = torch.load(checkpoint, map_location=device)
    model = BranchingTTNK3(
        kg.num_entities,
        kg.num_relations_total,
        int(state["dim"]),
        int(state["branch_dim"]),
    ).to(device)
    model.load_state_dict(state["model_state"])
    model.eval()
    return model


def main() -> None:
    args = parser().parse_args()
    if args.queries <= 0 or args.queries > 32768:
        raise ValueError("queries must lie in [1, 32768]")
    if args.filtered_repeats <= 0 or args.filtered_warmups < 0:
        raise ValueError("filtered warmups/repeats are invalid")

    device = _device(args)
    kg = load_knowledge_graph(args.train, args.valid, args.test)
    model = _load_model(args.checkpoint, kg, device)
    query_rows = [tuple(int(value) for value in row) for row in kg.test[: args.queries]]
    ranks = [(int(a), int(b)) for a, b in (item.split(":") for item in args.ranks.split(","))]
    full_rank = model.branch_dim
    scorer_records: list[dict[str, Any]] = []
    scorer_full: dict[str, Any] | None = None
    scorer_compressed: list[dict[str, Any]] = []
    if not args.skip_scorer:
        scorer_records = _measure_scorer_paired(
            model, kg, query_rows, device, ranks, args.batch_size,
            args.candidate_block, args.warmups, args.repeats,
        )
        scorer_full = scorer_records[0]
        scorer_compressed = scorer_records[1:]

    filtered_full = None
    filtered_compressed: list[dict[str, Any]] = []
    if not args.skip_filtered:
        filtered_full = _measure_filtered(
            model, kg, query_rows, device, full_rank, full_rank, args.batch_size,
            args.candidate_block, args.filtered_warmups, args.filtered_repeats,
            "transformed_full",
        )
        filtered_compressed = [
            _measure_filtered(
                model, kg, query_rows, device, rank1, rank2, args.batch_size,
                args.candidate_block, args.filtered_warmups, args.filtered_repeats,
                "transformed_compressed",
            )
            for rank1, rank2 in ranks
        ]

    pairs = []
    for compressed in scorer_compressed:
        assert scorer_full is not None
        ci_low, ci_high = _log_ratio_ci95(
            scorer_full["samples_ms"], compressed["samples_ms"]
        )
        pairs.append({
            "rank1": compressed["rank1"],
            "rank2": compressed["rank2"],
            "scorer_speedup_vs_transformed_full": scorer_full["mean_ms"] / compressed["mean_ms"],
            "scorer_checksum_abs_gap_vs_transformed_full": abs(
                scorer_full["checksum"] - compressed["checksum"]
            ),
            "scorer_speedup_ci95": {"low": ci_low, "high": ci_high},
            "resource_proxy_ratio": (
                compressed["resource_proxy"]["projected_candidate_score_units"]
                / scorer_full["resource_proxy"]["projected_candidate_score_units"]
            ),
        })
    filtered_pairs = []
    if filtered_full is not None:
        for compressed in filtered_compressed:
            filtered_pairs.append({
                "rank1": compressed["rank1"],
                "rank2": compressed["rank2"],
                "filtered_speedup_vs_transformed_full": filtered_full["mean_ms"] / compressed["mean_ms"],
                "MRR_abs_gap": abs(
                    filtered_full["metrics"]["combined"]["MRR"]
                    - compressed["metrics"]["combined"]["MRR"]
                ),
                "Hits@10_abs_gap": abs(
                    filtered_full["metrics"]["combined"]["Hits@10"]
                    - compressed["metrics"]["combined"]["Hits@10"]
                ),
            })

    output = {
        "status": "TTN_PAIRED_HARDWARE_V3",
        "device": str(device),
        "checkpoint": str(args.checkpoint),
        "dataset": "FB15K-237",
        "protocol": {
            "primary_comparison": "transformed_full_(D,D)_vs_transformed_compressed_(r1,r2)",
            "same_executor": True,
            "warmups": args.warmups,
            "repeats": args.repeats,
            "filtered_warmups": args.filtered_warmups,
            "filtered_repeats": args.filtered_repeats,
            "queries": len(query_rows),
            "batch_size": args.batch_size,
            "candidate_block": args.candidate_block,
            "ranks": ranks,
            "cuda_events_for_scorer": device.type == "cuda",
        },
        "scorer_records": scorer_records,
        "scorer_pairs": pairs,
        "filtered_full": filtered_full,
        "filtered_compressed": filtered_compressed,
        "filtered_pairs": filtered_pairs,
        "limitations": [
            "Scorer timings include the shared Python batching loop but exclude offline core transformation.",
            "Filtered timings are end-to-end for the selected query subset, but remain one-device measurements.",
            "A speedup result is hardware-specific and does not establish universal kernel superiority.",
        ],
    }
    args.out.parent.mkdir(parents=True, exist_ok=True)
    repro.save_json(output, args.out)
    print(json.dumps({"out": str(args.out), "device": str(device), "pairs": len(pairs)}, sort_keys=True))


if __name__ == "__main__":
    main()
