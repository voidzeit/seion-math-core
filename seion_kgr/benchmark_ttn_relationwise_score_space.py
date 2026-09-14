"""Matched-kernel benchmark for relation-wise whitened score projectors.

The model and whitening/projector transforms are frozen. Candidate tables are
materialized offline, then the timed executor measures only online query
projection and candidate GEMMs. The finite-query certificate is explicitly
labelled as such; it is not a universal input-domain certificate.
"""

from __future__ import annotations

import argparse
import json
import statistics
import time
from pathlib import Path
from typing import Mapping

import numpy as np
import torch

from .data import KnowledgeGraph, load_knowledge_graph
from .score_space import CandidateWhitening
from .ttn_branching import BranchingTTNK3


def parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--checkpoint", type=Path, required=True)
    p.add_argument("--audit", type=Path, required=True)
    p.add_argument("--train", default="data/FB15K-237/train.txt")
    p.add_argument("--valid", default="data/FB15K-237/valid.txt")
    p.add_argument("--test", default="data/FB15K-237/test.txt")
    p.add_argument("--out", type=Path, required=True)
    p.add_argument("--tolerance", type=float, default=0.0005)
    p.add_argument("--queries", type=int, default=1024)
    p.add_argument("--calibration-queries", type=int, default=512)
    p.add_argument("--batch-size", type=int, default=64)
    p.add_argument("--candidate-block", type=int, default=4096)
    p.add_argument("--warmups", type=int, default=5)
    p.add_argument("--repeats", type=int, default=10)
    p.add_argument("--max-vram-gb", type=float, default=20.0)
    p.add_argument("--score-only", action="store_true", help="precompute whitened query representations outside timing")
    p.add_argument("--batched-routing", action="store_true", help="batch equal-rank relation routes with bmm")
    p.add_argument("--relation-batch", type=int, default=8, help="relations per bmm route")
    p.add_argument("--cpu", action="store_true")
    return p


def _device(args: argparse.Namespace) -> torch.device:
    if args.cpu or not torch.cuda.is_available():
        return torch.device("cpu")
    total = torch.cuda.get_device_properties(0).total_memory
    fraction = min(0.90, args.max_vram_gb * 1024**3 / total)
    torch.cuda.set_per_process_memory_fraction(fraction, device=0)
    return torch.device("cuda:0")


def _load_model(checkpoint: Path, kg: KnowledgeGraph, device: torch.device) -> BranchingTTNK3:
    state = torch.load(checkpoint, map_location=device)
    model = BranchingTTNK3(kg.num_entities, kg.num_relations_total, int(state["dim"]), int(state["branch_dim"])).to(device)
    model.load_state_dict(state["model_state"])
    model.eval()
    model.set_mode("full")
    return model


def _query_subset(values: np.ndarray, count: int, seed: int) -> np.ndarray:
    values = np.asarray(values, dtype=np.int64)
    if len(values) == 0:
        raise ValueError("query split is empty")
    count = min(len(values), max(1, int(count)))
    rng = np.random.default_rng(seed)
    indices = rng.choice(len(values), size=count, replace=False)
    return values[indices]


def _percentile(values: list[float], q: float) -> float:
    return float(np.percentile(np.asarray(values, dtype=np.float64), q))


def _relation_groups(rows: np.ndarray) -> list[tuple[int, np.ndarray]]:
    """Return stable relation buckets so routing is not rebuilt per batch."""
    groups: list[tuple[int, np.ndarray]] = []
    for relation in np.unique(rows[:, 1]):
        relation_id = int(relation)
        groups.append((relation_id, np.flatnonzero(rows[:, 1] == relation_id)))
    return groups


def _batched_routes(
    relation_groups: list[tuple[int, np.ndarray]],
    ranks: list[int],
    relation_tables: dict[int, torch.Tensor],
    *,
    relation_batch: int = 8,
) -> dict[int, list[tuple[list[int], list[np.ndarray], torch.Tensor]]]:
    """Build offline candidate-table stacks for equal-rank routes."""
    by_rank: dict[int, list[tuple[int, np.ndarray]]] = {}
    for relation, indices in relation_groups:
        by_rank.setdefault(int(ranks[relation]), []).append((relation, indices))
    routes: dict[int, list[tuple[list[int], list[np.ndarray], torch.Tensor]]] = {}
    for rank, entries in by_rank.items():
        for start in range(0, len(entries), relation_batch):
            chunk = entries[start : start + relation_batch]
            relations = [relation for relation, _ in chunk]
            indices = [values for _, values in chunk]
            tables = torch.stack([relation_tables[relation][:, :rank] for relation in relations], dim=0)
            routes.setdefault(rank, []).append((relations, indices, tables))
    return routes


def _rank_map(audit: Mapping[str, object], tolerance: float, field: str) -> tuple[int, list[int]]:
    rows = audit[field]
    selected = min(rows, key=lambda row: abs(float(row["tolerance"]) - tolerance))
    ranks = selected.get("spectral_ranks") if field == "allocation_summary" else selected.get("shared_spectral_ranks")
    if ranks is None:
        raise RuntimeError(f"no feasible {field} allocation at tolerance {tolerance}")
    return int(selected["uniform_rank"]), [int(rank) for rank in ranks]


@torch.inference_mode()
def _certificate_ranks(
    model: BranchingTTNK3,
    whitening: CandidateWhitening,
    relation_bases: torch.Tensor,
    rows: np.ndarray,
    entity_table: torch.Tensor,
    tolerance: float,
    device: torch.device,
) -> list[int]:
    max_entity_norm = whitening.max_whitened_entity_norm(entity_table)
    result: list[int] = []
    for relation in range(int(relation_bases.shape[0])):
        selected = rows[rows[:, 1] == relation]
        if len(selected) == 0:
            result.append(1)
            continue
        batch = torch.as_tensor(selected, dtype=torch.long, device=device)
        q = whitening.whiten_queries(model.query_representation(batch[:, 0], batch[:, 1]))
        basis = relation_bases[relation].to(device=device, dtype=q.dtype)
        coefficients = q @ basis
        residual_squared = (q.pow(2).sum(dim=1, keepdim=True) - torch.cumsum(coefficients.pow(2), dim=1)).clamp_min(0)
        bounds = residual_squared.sqrt() * max_entity_norm.to(device=device, dtype=q.dtype)
        feasible = torch.all(bounds <= tolerance, dim=0)
        ranks = torch.nonzero(feasible, as_tuple=False)
        result.append(int(ranks[0].item() + 1) if ranks.numel() else int(basis.shape[1]))
    return result


@torch.inference_mode()
def _run_pass(
    model: BranchingTTNK3,
    whitening: CandidateWhitening,
    rows: np.ndarray,
    entity_white: torch.Tensor,
    candidate_blocks: list[torch.Tensor],
    *,
    batch_size: int,
    mode: str,
    relation_bases: torch.Tensor,
    ranks: list[int],
    relation_tables: dict[int, torch.Tensor],
    relation_groups: list[tuple[int, np.ndarray]],
    relation_bases_device: torch.Tensor,
    batched_routes: dict[int, list[tuple[list[int], list[np.ndarray], torch.Tensor]]] | None,
    device: torch.device,
    precomputed_queries: torch.Tensor | None = None,
) -> float:
    checksum = torch.zeros((), device=device)
    if mode == "full_dense":
        for start in range(0, len(rows), batch_size):
            selected = slice(start, start + batch_size)
            if precomputed_queries is not None:
                q = precomputed_queries[selected]
            else:
                batch = torch.as_tensor(rows[selected], dtype=torch.long, device=device)
                q = whitening.whiten_queries(model.query_representation(batch[:, 0], batch[:, 1]))
            for candidates in candidate_blocks:
                checksum = checksum + (q @ entity_white[candidates].T).sum()
        return float(checksum.detach().cpu().item())

    if mode == "relationwise" and batched_routes is not None and precomputed_queries is not None:
        for rank, routes in batched_routes.items():
            for relations, index_groups, tables in routes:
                projected: list[torch.Tensor] = []
                max_queries = 0
                for relation, indices in zip(relations, index_groups):
                    q = precomputed_queries[indices]
                    basis = relation_bases_device[relation, :, :rank]
                    projected.append(q @ basis)
                    max_queries = max(max_queries, len(indices))
                q_stack = torch.zeros(
                    (len(projected), max_queries, rank),
                    dtype=precomputed_queries.dtype,
                    device=device,
                )
                for offset, q in enumerate(projected):
                    q_stack[offset, : q.shape[0]] = q
                for candidates in candidate_blocks:
                    table_block = tables[:, candidates, :]
                    checksum = checksum + torch.bmm(q_stack, table_block.transpose(1, 2)).sum()
        return float(checksum.detach().cpu().item())

    for relation, indices in relation_groups:
        if mode == "full_grouped":
            basis = None
            table = entity_white
        else:
            rank = ranks[relation]
            basis = relation_bases_device[relation, :, :rank]
            table = relation_tables[relation][:, :rank]
        for start_group in range(0, len(indices), batch_size):
            selected = indices[start_group : start_group + batch_size]
            if precomputed_queries is not None:
                q = precomputed_queries[selected]
            else:
                grouped = torch.as_tensor(rows[selected], dtype=torch.long, device=device)
                q = whitening.whiten_queries(model.query_representation(grouped[:, 0], grouped[:, 1]))
            if basis is not None:
                q = q @ basis
            for candidates in candidate_blocks:
                checksum = checksum + (q @ table[candidates].T).sum()
    return float(checksum.detach().cpu().item())


def _time_condition(*, fn, device: torch.device, warmups: int, repeats: int) -> dict[str, object]:
    for _ in range(warmups):
        fn()
    if device.type == "cuda":
        torch.cuda.synchronize(device)
    samples: list[float] = []
    for _ in range(repeats):
        if device.type == "cuda":
            start = torch.cuda.Event(enable_timing=True)
            end = torch.cuda.Event(enable_timing=True)
            start.record()
            checksum = fn()
            end.record()
            end.synchronize()
            elapsed = start.elapsed_time(end) / 1000.0
        else:
            begin = time.perf_counter()
            checksum = fn()
            elapsed = time.perf_counter() - begin
        samples.append(float(elapsed))
    return {
        "times_seconds": samples,
        "p50_seconds": _percentile(samples, 50),
        "p95_seconds": _percentile(samples, 95),
        "checksum": checksum,
    }


def main() -> None:
    args = parser().parse_args()
    if args.tolerance <= 0 or args.queries <= 0 or args.calibration_queries <= 0 or args.relation_batch <= 0:
        raise ValueError("tolerance, query counts, and relation batch must be positive")
    device = _device(args)
    kg = load_knowledge_graph(args.train, args.valid, args.test)
    model = _load_model(args.checkpoint, kg, device)
    audit = json.loads(args.audit.read_text(encoding="utf-8"))
    projector_cache = torch.load(Path(audit["projector_cache"]), map_location="cpu")
    relation_bases = projector_cache["relation_bases"].contiguous()
    relation_bases_device = relation_bases.to(device=device, dtype=model.entity.weight.dtype)
    whitening = CandidateWhitening.fit(model.entity.weight.detach())
    entity_white = whitening.whiten_entities(model.entity.weight.detach())
    uniform_rank, oracle_ranks = _rank_map(audit, args.tolerance, "allocation_summary")
    calibration = _query_subset(kg.valid, args.calibration_queries, seed=13579)
    certificate_ranks = _certificate_ranks(model, whitening, relation_bases, calibration, model.entity.weight.detach(), args.tolerance, device)
    rows = _query_subset(kg.valid, args.queries, seed=24680)
    relation_groups = _relation_groups(rows)
    candidate_blocks = [
        torch.arange(start, min(start + args.candidate_block, kg.num_entities), dtype=torch.long, device=device)
        for start in range(0, kg.num_entities, args.candidate_block)
    ]
    used_relations = sorted(set(int(value) for value in rows[:, 1]))
    relation_tables: dict[int, torch.Tensor] = {}
    cache_bytes = 0
    for relation in used_relations:
        rank = max(1, oracle_ranks[relation], uniform_rank, certificate_ranks[relation])
        table = entity_white.to(device=device, dtype=model.entity.weight.dtype) @ relation_bases[relation, :, :rank].to(device=device, dtype=model.entity.weight.dtype)
        relation_tables[relation] = table
        cache_bytes += table.numel() * table.element_size()
    if cache_bytes > args.max_vram_gb * 1024**3 * 0.80:
        raise RuntimeError(f"relation-table cache estimate {cache_bytes / 1024**3:.2f} GB exceeds staged safety budget")
    conditions = {
        "full_dense": ("full_dense", [model.dim] * relation_bases.shape[0]),
        "full_matched": ("full_grouped", [model.dim] * relation_bases.shape[0]),
        "uniform": ("relationwise", [uniform_rank] * relation_bases.shape[0]),
        "spectral_oracle": ("relationwise", oracle_ranks),
        "finite_query_certificate": ("relationwise", certificate_ranks),
    }
    batched_routes = {
        name: (_batched_routes(relation_groups, ranks, relation_tables, relation_batch=args.relation_batch) if args.batched_routing and mode == "relationwise" else None)
        for name, (mode, ranks) in conditions.items()
    }
    precomputed_queries = None
    if args.score_only:
        query_ids = torch.as_tensor(rows, dtype=torch.long, device=device)
        precomputed_queries = whitening.whiten_queries(model.query_representation(query_ids[:, 0], query_ids[:, 1])).detach()
    records: dict[str, object] = {}
    for name, (mode, ranks) in conditions.items():
        result = _time_condition(
            fn=lambda mode=mode, ranks=ranks: _run_pass(
                model, whitening, rows, entity_white, candidate_blocks,
                batch_size=args.batch_size, mode=mode,
                relation_bases=relation_bases, ranks=ranks, relation_tables=relation_tables,
                relation_groups=relation_groups, relation_bases_device=relation_bases_device,
                batched_routes=batched_routes[name], device=device, precomputed_queries=precomputed_queries,
            ),
            device=device,
            warmups=args.warmups,
            repeats=args.repeats,
        )
        records[name] = {**result, "mean_rank_over_queries": float(np.mean([ranks[int(relation)] for relation in rows[:, 1]]))}
    full_p50 = float(records["full_matched"]["p50_seconds"])
    full_times = [float(value) for value in records["full_matched"]["times_seconds"]]
    repeat_speedups = {}
    for name, record in records.items():
        condition_times = [float(value) for value in record["times_seconds"]]
        ratios = [full / condition for full, condition in zip(full_times, condition_times)]
        repeat_speedups[name] = {
            "ratios": ratios,
            "p05": _percentile(ratios, 5),
            "p50": _percentile(ratios, 50),
            "p95": _percentile(ratios, 95),
            "min": float(min(ratios)),
            "max": float(max(ratios)),
        }
    resource = {
        name: float(records[name]["mean_rank_over_queries"])
        for name in records
    }
    output = {
        "status": "RELATIONWISE_SCORE_SPACE_BENCHMARK_COMPLETE",
        "device": str(device),
        "checkpoint": str(args.checkpoint),
        "audit": str(args.audit),
        "tolerance": args.tolerance,
        "query_count": len(rows),
        "calibration_query_count": len(calibration),
        "batch_size": args.batch_size,
        "candidate_block": args.candidate_block,
        "warmups": args.warmups,
        "repeats": args.repeats,
        "score_only": args.score_only,
        "batched_routing": args.batched_routing,
        "relation_batch": args.relation_batch,
        "relation_count_in_queries": len(used_relations),
        "cache_bytes": cache_bytes,
        "certificate_scope": "finite_calibration_queries_and_all_stored_entities",
        "resource": resource,
        "speedup_vs_full_matched_p50": {name: full_p50 / float(record["p50_seconds"]) for name, record in records.items()},
        "repeat_index_speedup_vs_full_matched": repeat_speedups,
        "records": records,
        "rank_vectors": {
            "uniform": [uniform_rank] * relation_bases.shape[0],
            "spectral_oracle": oracle_ranks,
            "finite_query_certificate": certificate_ranks,
        },
        "oracle_gap_on_query_distribution": resource["uniform"] / resource["spectral_oracle"],
        "certificate_gap_on_query_distribution": resource["uniform"] / resource["finite_query_certificate"],
        "Pi_certificate_over_oracle": resource["finite_query_certificate"] / resource["spectral_oracle"],
        "peak_allocated_bytes": int(torch.cuda.max_memory_allocated(device)) if device.type == "cuda" else 0,
        "peak_reserved_bytes": int(torch.cuda.max_memory_reserved(device)) if device.type == "cuda" else 0,
    }
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(output, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"out": str(args.out), "device": str(device), "cache_bytes": cache_bytes}, sort_keys=True))


if __name__ == "__main__":
    main()
