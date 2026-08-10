"""Paired benchmark for output-space compression of a frozen branching TTN."""

from __future__ import annotations

import argparse
import json
import statistics
from pathlib import Path
from typing import Any, Sequence

import torch
import numpy as np

from . import reproducibility as repro
from .benchmark_ttn_hardware_v3 import (
    _cuda_or_wall_pass,
    _log_ratio_ci95,
    _percentile,
    _synchronize,
)
from .data import KnowledgeGraph, load_knowledge_graph
from .ttn_branching import BranchingTTNK3, branch_leaf_norm_bounds


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
    p.add_argument("--output-ranks", default="4,8,16,24,32")
    p.add_argument("--probe-queries", type=int, default=128)
    p.add_argument("--candidate-sample", type=int, default=256)
    p.add_argument("--tolerances", default="0.1,0.01,0.001,0.0001")
    p.add_argument("--cpu", action="store_true")
    return p


def _device(args: argparse.Namespace) -> torch.device:
    return torch.device("cpu" if args.cpu or not torch.cuda.is_available() else "cuda")


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


@torch.inference_mode()
def _measure_paired(
    model: BranchingTTNK3,
    kg: KnowledgeGraph,
    queries: Sequence[tuple[int, int, int]],
    output_ranks: Sequence[int],
    device: torch.device,
    batch_size: int,
    candidate_block: int,
    warmups: int,
    repeats: int,
) -> list[dict[str, Any]]:
    conditions = list(dict.fromkeys([model.dim, *output_ranks]))
    h_ids = torch.tensor([row[0] for row in queries], device=device, dtype=torch.long)
    r_ids = torch.tensor([row[1] for row in queries], device=device, dtype=torch.long)
    candidate_blocks = [
        torch.arange(start, min(start + candidate_block, kg.num_entities), device=device, dtype=torch.long)
        for start in range(0, kg.num_entities, candidate_block)
    ]
    prepared: list[tuple[int, Any]] = []

    for output_rank in conditions:
        model.set_mode("projected")
        model.set_ranks(model.branch_dim, model.branch_dim)
        model.set_output_rank(output_rank)
        model.prepare_output_executor()

        def one_pass(h=h_ids, r=r_ids, blocks=candidate_blocks) -> torch.Tensor:
            checksum = torch.zeros((), device=device)
            for offset in range(0, len(queries), batch_size):
                h_batch = h[offset : offset + batch_size]
                r_batch = r[offset : offset + batch_size]
                for candidates in blocks:
                    checksum = checksum + model.score_tail_candidates(h_batch, r_batch, candidates).sum()
            return checksum

        one_pass()  # cache transformed root and candidate table offline
        prepared.append((output_rank, one_pass))

    for _ in range(warmups):
        for _, one_pass in prepared:
            one_pass()
    _synchronize(device)
    if device.type == "cuda":
        torch.cuda.reset_peak_memory_stats(device)

    samples: list[list[float]] = [[] for _ in prepared]
    checksums: list[float | None] = [None for _ in prepared]
    for repetition in range(repeats):
        order = range(len(prepared)) if repetition % 2 == 0 else range(len(prepared) - 1, -1, -1)
        for index in order:
            output_rank, one_pass = prepared[index]
            model.set_output_rank(output_rank)
            _synchronize(device)
            elapsed, checksum = _cuda_or_wall_pass(one_pass, device)
            samples[index].append(elapsed)
            checksums[index] = float(checksum.item())

    peak_allocated = int(torch.cuda.max_memory_allocated(device)) if device.type == "cuda" else None
    peak_reserved = int(torch.cuda.max_memory_reserved(device)) if device.type == "cuda" else None
    records = []
    for (output_rank, _), values, checksum in zip(prepared, samples, checksums):
        model.set_output_rank(output_rank)
        mean_ms = statistics.fmean(values)
        records.append({
            "output_rank": int(output_rank),
            "internal_rank1": model.branch_dim,
            "internal_rank2": model.branch_dim,
            "executor_mode": "projected",
            "queries": len(queries),
            "batch_size": batch_size,
            "candidate_block": candidate_block,
            "warmups": warmups,
            "repeats": repeats,
            "mean_ms": mean_ms,
            "p50_ms": _percentile(values, 0.50),
            "p95_ms": _percentile(values, 0.95),
            "samples_ms": values,
            "queries_per_second": len(queries) / (mean_ms / 1000.0),
            "peak_allocated_bytes": peak_allocated,
            "peak_reserved_bytes": peak_reserved,
            "checksum": checksum,
            "resource_proxy": model.resource_proxy(
                model.branch_dim, model.branch_dim,
                output_rank=output_rank,
                candidate_count=kg.num_entities,
            ),
            "output_certificate": model.output_certificate(
                branch_leaf_norm_bounds(model), model.branch_dim, model.branch_dim
            ),
        })
    return records


@torch.inference_mode()
def _probe_score_errors(
    model: BranchingTTNK3,
    kg: KnowledgeGraph,
    queries: Sequence[tuple[int, int, int]],
    output_ranks: Sequence[int],
    candidate_sample: int,
    device: torch.device,
) -> dict[int, dict[str, float]]:
    h = torch.tensor([row[0] for row in queries], device=device, dtype=torch.long)
    r = torch.tensor([row[1] for row in queries], device=device, dtype=torch.long)
    t = torch.tensor([row[2] for row in queries], device=device, dtype=torch.long)
    candidates = torch.arange(min(candidate_sample, kg.num_entities), device=device, dtype=torch.long)
    model.set_mode("projected")
    model.set_ranks(model.branch_dim, model.branch_dim)
    model.set_output_rank(model.dim)
    full = torch.cat([
        model.score_positive(h, r, t),
        model.score_tail_candidates(h, r, candidates).reshape(-1),
    ])
    errors: dict[int, dict[str, float]] = {}
    for output_rank in output_ranks:
        model.set_output_rank(output_rank)
        current = torch.cat([
            model.score_positive(h, r, t),
            model.score_tail_candidates(h, r, candidates).reshape(-1),
        ])
        gap = (full - current).abs()
        errors[int(output_rank)] = {
            "max_abs_score_gap": float(gap.max().item()),
            "mean_abs_score_gap": float(gap.mean().item()),
            "query_count": int(len(queries)),
            "candidate_count": int(candidates.numel()),
        }
    return errors


def main() -> None:
    args = parser().parse_args()
    if args.queries <= 0 or args.queries > 32768 or args.repeats <= 0 or args.warmups < 0:
        raise ValueError("invalid query or timing arguments")
    device = _device(args)
    kg = load_knowledge_graph(args.train, args.valid, args.test)
    model = _load_model(args.checkpoint, kg, device)
    train_entity_ids = torch.from_numpy(
        np.unique(kg.train[:, [0, 2]].reshape(-1)).astype("int64")
    ).to(device=device)
    model.fit_output_projector(train_entity_ids)
    output_ranks = sorted({int(value) for value in args.output_ranks.split(",")})
    if any(rank < 1 or rank > model.dim for rank in output_ranks):
        raise ValueError("output ranks must lie within [1, dim]")
    queries = [tuple(int(value) for value in row) for row in kg.test[: args.queries]]
    records = _measure_paired(
        model, kg, queries, output_ranks, device, args.batch_size,
        args.candidate_block, args.warmups, args.repeats,
    )
    probe_queries = queries[: min(len(queries), max(1, args.probe_queries))]
    probe = _probe_score_errors(model, kg, probe_queries, output_ranks, args.candidate_sample, device)
    for record in records:
        record["observed_probe"] = probe[int(record["output_rank"])]
    full = records[0]
    pairs = []
    for compressed in records[1:]:
        low, high = _log_ratio_ci95(full["samples_ms"], compressed["samples_ms"])
        pairs.append({
            "output_rank": compressed["output_rank"],
            "speedup_vs_full_output_rank": full["mean_ms"] / compressed["mean_ms"],
            "speedup_ci95": {"low": low, "high": high},
            "resource_proxy_ratio": (
                compressed["resource_proxy"]["projected_candidate_score_units"]
                / full["resource_proxy"]["projected_candidate_score_units"]
            ),
            "output_certificate": compressed["output_certificate"],
            "checksum_abs_gap": abs(full["checksum"] - compressed["checksum"]),
            "observed_probe": compressed["observed_probe"],
        })
    tolerances = [float(value) for value in args.tolerances.split(",")]
    allocation_summary = []
    for tolerance in tolerances:
        feasible_observed = [
            record for record in records
            if record["observed_probe"]["max_abs_score_gap"] <= tolerance
        ]
        feasible_certificate = [
            record for record in records
            if record["output_certificate"]["total_error_bound"] <= tolerance
        ]
        oracle = min(feasible_observed, key=lambda record: record["resource_proxy"]["projected_candidate_score_units"], default=None)
        certified = min(feasible_certificate, key=lambda record: record["resource_proxy"]["projected_candidate_score_units"], default=None)
        full_cost = full["resource_proxy"]["projected_candidate_score_units"]
        allocation_summary.append({
            "tolerance": tolerance,
            "uniform_output_rank": full["output_rank"],
            "uniform_resource_units": full_cost,
            "oracle_output_rank": None if oracle is None else oracle["output_rank"],
            "oracle_resource_units": None if oracle is None else oracle["resource_proxy"]["projected_candidate_score_units"],
            "certificate_output_rank": None if certified is None else certified["output_rank"],
            "certificate_resource_units": None if certified is None else certified["resource_proxy"]["projected_candidate_score_units"],
            "G_oracle": None if oracle is None else full_cost / oracle["resource_proxy"]["projected_candidate_score_units"],
            "Pi_cert": None if oracle is None or certified is None else certified["resource_proxy"]["projected_candidate_score_units"] / oracle["resource_proxy"]["projected_candidate_score_units"],
        })
    output = {
        "status": "TTN_OUTPUT_COMPRESSION_BENCHMARK",
        "device": str(device),
        "dataset": "FB15K-237",
        "checkpoint": str(args.checkpoint),
        "output_basis_fit": "train_entities_only",
        "train_entity_count": int(train_entity_ids.numel()),
        "protocol": {
            "same_executor": True,
            "primary_comparison": "output_rank_dim_vs_output_rank_rout",
            "queries": len(queries),
            "batch_size": args.batch_size,
            "candidate_block": args.candidate_block,
            "warmups": args.warmups,
            "repeats": args.repeats,
            "alternating_paired_order": True,
            "probe_queries": len(probe_queries),
            "candidate_sample": min(args.candidate_sample, kg.num_entities),
            "tolerances": tolerances,
        },
        "records": records,
        "pairs": pairs,
        "allocation_summary": allocation_summary,
        "limitations": [
            "The current checkpoint has dim=32; D=128/256 remains a required follow-up.",
            "Output bases are fitted from train-observed entity rows only.",
            "Speedup is one-device evidence and must survive dataset/topology replication.",
        ],
    }
    args.out.parent.mkdir(parents=True, exist_ok=True)
    repro.save_json(output, args.out)
    print(json.dumps({"out": str(args.out), "device": str(device), "pairs": len(pairs)}, sort_keys=True))


if __name__ == "__main__":
    main()
