"""Post-training branching-TTN benchmark on FB15K-237.

This is an exploratory vertical slice, not a production KGE campaign.  It
trains a full-rank ``BranchingTTNK3`` model, freezes it, fits branch SVD
projectors, and compares uniform, local-SVD, certificate, and validation
oracle rank allocations.  The existing filtered evaluator is reused once for
the full-rank MRR/Hits baseline; projected ranking, score gaps, certificates,
and resources are reported separately.
"""

from __future__ import annotations

import argparse
import json
import math
import sys
import time
from pathlib import Path
from typing import Iterable

import numpy as np
import torch
import torch.nn.functional as F

from . import reproducibility as repro
from .data import KnowledgeGraph, load_knowledge_graph, sample_negatives, train_only_filter_view
from .gpu_negative_sampler import GpuNegativeSampler
from .evaluate import evaluate, ranks_to_metrics
from .ttn_branching import (
    BranchingTTNK3,
    branch_leaf_norm_bounds,
    query_leaf_norm_bounds,
)


APPLICATION_RESULT_DIR = Path(__file__).resolve().parents[1] / "applications" / "adaptive_tensor_network" / "results"
DEFAULT_OUT = Path("runs/TTN_FB15K237_BRANCHING_K3_POSTTRAIN_2026-08-09")


def parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--train", default="data/FB15K-237/train.txt")
    p.add_argument("--valid", default="data/FB15K-237/valid.txt")
    p.add_argument("--test", default="data/FB15K-237/test.txt")
    p.add_argument("--out-dir", type=Path, default=DEFAULT_OUT)
    p.add_argument("--dim", type=int, default=32)
    p.add_argument("--branch-dim", type=int, default=32)
    p.add_argument("--epochs", type=int, default=3)
    p.add_argument("--batch-size", type=int, default=4096)
    p.add_argument("--neg-k", type=int, default=32)
    p.add_argument("--lr", type=float, default=1e-3)
    p.add_argument("--weight-decay", type=float, default=1e-6)
    p.add_argument("--loss-temperature", type=float, default=1000.0)
    p.add_argument("--embedding-max-norm", type=float, default=1.0)
    p.add_argument("--core-max-fro", type=float, default=1.0)
    p.add_argument("--root-max-fro", type=float, default=1.0)
    p.add_argument("--tolerances", default="0.1,0.01,0.001,0.0001,0.00001")
    p.add_argument("--calibration-triples", type=int, default=8192)
    p.add_argument("--eval-queries", type=int, default=128)
    p.add_argument("--candidate-sample", type=int, default=256)
    p.add_argument("--seed", type=int, default=42)
    p.add_argument("--negative-filter", choices=("train_valid_test", "train_only"),
                   default="train_valid_test",
                   help="which known-positive tables mask TRAINING negatives (B-0014). "
                        "'train_valid_test' reproduces earlier runs but leaks held-out "
                        "membership into training; 'train_only' is the non-leaking choice. "
                        "Evaluation always keeps the full filters.")
    p.add_argument("--gpu-negative-sampler", action="store_true",
                   help="draw filtered negatives on the device instead of the per-row "
                        "Python/NumPy loop; distributionally equivalent, not bit-exact")
    p.add_argument("--cpu", action="store_true")
    p.add_argument("--allow-existing", action="store_true")
    p.add_argument("--skip-application-result", action="store_true")
    p.add_argument("--rank-grid", action="store_true", help="also evaluate the declared rank-pair grid")
    p.add_argument("--budgets", default="2,4,8,16,32,48,64")
    return p


def _device(args: argparse.Namespace) -> torch.device:
    return torch.device("cpu" if args.cpu or not torch.cuda.is_available() else "cuda")


def _query_subset(kg: KnowledgeGraph, split: str, count: int) -> list[tuple[int, int, int]]:
    values = kg.valid if split == "valid" else kg.test
    if not values:
        return []
    size = min(len(values), max(1, int(count)))
    rng = np.random.default_rng(12345 if split == "valid" else 67890)
    indices = rng.choice(len(values), size=size, replace=False)
    return [values[int(index)] for index in indices]


def _train_full(
    model: BranchingTTNK3,
    kg: KnowledgeGraph,
    device: torch.device,
    *,
    epochs: int,
    batch_size: int,
    neg_k: int,
    lr: float,
    weight_decay: float,
    loss_temperature: float,
    embedding_max_norm: float,
    core_max_fro: float,
    root_max_fro: float,
    seed: int,
    gpu_negative_sampler: bool = False,
) -> list[dict[str, float | int]]:
    if epochs <= 0 or batch_size <= 0 or neg_k <= 0 or loss_temperature <= 0:
        raise ValueError("epochs, batch_size, neg_k, and loss_temperature must be positive")
    model.train()
    model.set_mode("full")
    optimizer = torch.optim.AdamW(model.parameters(), lr=lr, weight_decay=weight_decay)
    train_tensor = torch.from_numpy(kg.train.astype(np.int64, copy=False))
    rng = np.random.default_rng(seed)
    # The reference sampler is a per-row Python/NumPy loop and pins a CPU core
    # while the GPU idles; the device-resident one keeps the whole step on the
    # accelerator. Distributionally equivalent, not bit-exact -- see
    # seion_kgr/gpu_negative_sampler.py.
    gpu_sampler = None
    gpu_generator = None
    if gpu_negative_sampler:
        gpu_sampler = GpuNegativeSampler(kg, device)
        gpu_generator = torch.Generator(device=device).manual_seed(seed)
    history: list[dict[str, float | int]] = []
    for epoch in range(1, epochs + 1):
        start = time.perf_counter()
        order = rng.permutation(len(train_tensor))
        losses: list[float] = []
        for offset in range(0, len(order), batch_size):
            indices = order[offset : offset + batch_size]
            batch = train_tensor[indices].to(device=device, non_blocking=True)
            h_ids, r_ids, t_ids = batch.T
            if gpu_sampler is not None:
                negatives = gpu_sampler.sample(h_ids, r_ids, neg_k, gpu_generator)
            else:
                negatives = sample_negatives(
                    h_ids, r_ids, t_ids, kg, neg_k, rng, device
                )
            optimizer.zero_grad(set_to_none=True)
            positive = model.score_positive(h_ids, r_ids, t_ids)
            negative = model.score_tail_candidates(h_ids, r_ids, negatives)
            # Pairwise logistic loss directly separates each positive from
            # its sampled corruptions; the previous independent logistic
            # terms stayed numerically at log(2) with tiny entity vectors.
            loss = F.softplus(
                loss_temperature * (negative - positive.unsqueeze(1))
            ).mean()
            loss.backward()
            torch.nn.utils.clip_grad_norm_(model.parameters(), 1.0)
            optimizer.step()
            model.project_parameter_norms(
                embedding_max_norm=embedding_max_norm,
                core_max_fro=core_max_fro,
                root_max_fro=root_max_fro,
            )
            losses.append(float(loss.detach().item()))
        record = {
            "epoch": epoch,
            "loss": float(np.mean(losses)),
            "steps": len(losses),
            "seconds": time.perf_counter() - start,
        }
        history.append(record)
    model.eval()
    return history


def _candidate_ids(num_entities: int, count: int, seed: int) -> torch.Tensor:
    count = min(num_entities, max(1, count))
    rng = np.random.default_rng(seed)
    return torch.from_numpy(
        rng.choice(num_entities, size=count, replace=False).astype(np.int64)
    )


@torch.inference_mode()
def _sampled_score_gap(
    model: BranchingTTNK3,
    queries: list[tuple[int, int, int]],
    candidate_ids: torch.Tensor,
    device: torch.device,
    rank1: int,
    rank2: int,
    full_cache: tuple[torch.Tensor, torch.Tensor] | None = None,
) -> dict[str, float]:
    model.set_ranks(rank1, rank2)
    h = torch.tensor([item[0] for item in queries], device=device)
    r = torch.tensor([item[1] for item in queries], device=device)
    t = torch.tensor([item[2] for item in queries], device=device)
    candidates = candidate_ids.to(device=device)
    if full_cache is None:
        model.set_mode("full")
        full_pos = model.score_positive(h, r, t)
        full_candidates = model.score_tail_candidates(h, r, candidates)
    else:
        full_pos, full_candidates = full_cache
    model.set_mode("projected")
    projected_pos = model.score_positive(h, r, t)
    projected_candidates = model.score_tail_candidates(h, r, candidates)
    gaps = torch.cat(
        [
            (full_pos - projected_pos).abs(),
            (full_candidates - projected_candidates).abs().reshape(-1),
        ]
    )
    return {
        "max_abs_score_gap": float(gaps.max().item()),
        "mean_abs_score_gap": float(gaps.mean().item()),
    }


@torch.inference_mode()
def _sampled_full_cache(
    model: BranchingTTNK3,
    queries: list[tuple[int, int, int]],
    candidate_ids: torch.Tensor,
    device: torch.device,
) -> tuple[torch.Tensor, torch.Tensor]:
    """Cache full scores once for repeated rank-allocation comparisons."""

    h = torch.tensor([item[0] for item in queries], device=device)
    r = torch.tensor([item[1] for item in queries], device=device)
    t = torch.tensor([item[2] for item in queries], device=device)
    model.set_mode("full")
    return (
        model.score_positive(h, r, t),
        model.score_tail_candidates(h, r, candidate_ids.to(device=device)),
    )


@torch.inference_mode()
def _full_ranking_cache(
    model: BranchingTTNK3,
    kg: KnowledgeGraph,
    queries: list[tuple[int, int, int]],
    device: torch.device,
    batch_size: int = 32,
) -> dict[str, torch.Tensor]:
    """Cache full tail/head score matrices for all repeated allocations."""

    candidates = torch.arange(kg.num_entities, device=device)
    cache: dict[str, torch.Tensor] = {}
    for direction, data in (
        ("tail", queries),
        ("head", [(t, r + kg.num_relations_original, h) for h, r, t in queries]),
    ):
        rows: list[torch.Tensor] = []
        for offset in range(0, len(data), batch_size):
            chunk = data[offset : offset + batch_size]
            h = torch.tensor([item[0] for item in chunk], device=device)
            r = torch.tensor([item[1] for item in chunk], device=device)
            rows.append(model.score_tail_candidates(h, r, candidates))
        cache[direction] = torch.cat(rows, dim=0)
    return cache


def _filtered_rank(scores: torch.Tensor, gold: int, forbidden: Iterable[int]) -> tuple[float, float]:
    masked = scores.clone()
    for value in forbidden:
        if int(value) != gold:
            masked[int(value)] = -torch.inf
    gold_score = float(masked[gold].item())
    better = int((masked > masked[gold]).sum().item())
    competitor = masked.clone()
    competitor[gold] = -torch.inf
    margin = gold_score - float(competitor.max().item())
    return float(1 + better), margin


def _topk_boundary_margin(
    scores: torch.Tensor, gold: int, forbidden: Iterable[int], k: int
) -> float:
    masked = scores.clone()
    for value in forbidden:
        if int(value) != gold:
            masked[int(value)] = -torch.inf
    masked[gold] = scores[gold]
    if masked.numel() <= k:
        return float("inf")
    ordered = torch.sort(masked, descending=True).values
    return float((ordered[k - 1] - ordered[k]).item())


@torch.inference_mode()
def _ranking_stability(
    model: BranchingTTNK3,
    kg: KnowledgeGraph,
    queries: list[tuple[int, int, int]],
    device: torch.device,
    rank1: int,
    rank2: int,
    batch_size: int = 32,
    full_score_cache: dict[str, torch.Tensor] | None = None,
) -> dict[str, object]:
    model.set_ranks(rank1, rank2)
    candidates = torch.arange(kg.num_entities, device=device)
    full_ranks: list[float] = []
    projected_ranks: list[float] = []
    margins: list[float] = []
    certificate_bounds: list[float] = []
    certified: list[bool] = []
    certified_boundaries = {k: [] for k in (1, 3, 10)}
    certified_hits = {k: [] for k in (1, 3, 10)}
    false_certificates = 0
    for direction, data in (
        ("tail", queries),
        ("head", [
            (t, r + kg.num_relations_original, h) for h, r, t in queries
        ]),
    ):
        for offset in range(0, len(data), batch_size):
            chunk = data[offset : offset + batch_size]
            h = torch.tensor([item[0] for item in chunk], device=device)
            r = torch.tensor([item[1] for item in chunk], device=device)
            t = torch.tensor([item[2] for item in chunk], device=device)
            if full_score_cache is None:
                model.set_mode("full")
                full_scores = model.score_tail_candidates(h, r, candidates)
            else:
                full_scores = full_score_cache[direction][offset : offset + len(chunk)]
            model.set_mode("projected")
            projected_scores = model.score_tail_candidates(h, r, candidates)
            for row, (h_id, r_id, gold) in enumerate(chunk):
                if direction == "tail":
                    forbidden = kg.tails_of_hr.get((h_id, r_id), np.empty(0, dtype=np.int64))
                    original_r = r_id
                    original_h = h_id
                else:
                    original_r = r_id - kg.num_relations_original
                    original_h = gold
                    forbidden = kg.heads_of_rt.get((original_r, h_id), np.empty(0, dtype=np.int64))
                full_rank, margin = _filtered_rank(full_scores[row], gold, forbidden)
                projected_rank, _ = _filtered_rank(projected_scores[row], gold, forbidden)
                bounds = query_leaf_norm_bounds(model, original_h, original_r)
                bound = float(model.certificate(bounds, rank1, rank2, rank_aware=True)["root_bound"])
                is_certified = bool(margin > 2.0 * bound)
                if is_certified and full_rank != projected_rank:
                    false_certificates += 1
                for k in (1, 3, 10):
                    boundary = _topk_boundary_margin(full_scores[row], gold, forbidden, k)
                    boundary_certified = bool(boundary > 2.0 * bound)
                    certified_boundaries[k].append(boundary_certified)
                    certified_hits[k].append(bool(full_rank <= k and boundary_certified))
                full_ranks.append(full_rank)
                projected_ranks.append(projected_rank)
                margins.append(margin)
                certificate_bounds.append(bound)
                certified.append(is_certified)
    full_tensor = torch.tensor(full_ranks)
    projected_tensor = torch.tensor(projected_ranks)
    full_metrics = ranks_to_metrics(full_tensor)
    projected_metrics = ranks_to_metrics(projected_tensor)
    return {
        "full": full_metrics,
        "projected": projected_metrics,
        "rank_equal_fraction": float(np.mean(np.asarray(full_ranks) == np.asarray(projected_ranks))),
        "certified_rank_stable_fraction": float(np.mean(certified)) if certified else 0.0,
        "CCR@1": float(np.mean(certified_boundaries[1])) if certified else 0.0,
        "CCR@3": float(np.mean(certified_boundaries[3])) if certified else 0.0,
        "CCR@10": float(np.mean(certified_boundaries[10])) if certified else 0.0,
        "certified_Hits@1_fraction": float(np.mean(certified_hits[1])) if certified else 0.0,
        "certified_Hits@3_fraction": float(np.mean(certified_hits[3])) if certified else 0.0,
        "certified_Hits@10_fraction": float(np.mean(certified_hits[10])) if certified else 0.0,
        "false_certificates": false_certificates,
        "minimum_observed_margin": float(min(margins)) if margins else None,
        "maximum_query_certificate": float(max(certificate_bounds)) if certificate_bounds else None,
    }


def _uniform_ranks(model: BranchingTTNK3, budget: int) -> tuple[int, int]:
    total = min(2 * model.branch_dim, max(2, budget))
    r1 = min(model.branch_dim, (total + 1) // 2)
    r2 = min(model.branch_dim, total - r1)
    return max(1, r1), max(1, r2)


def _all_rank_pairs(model: BranchingTTNK3, budget: int) -> Iterable[tuple[int, int]]:
    for rank1 in range(1, model.branch_dim + 1):
        for rank2 in range(1, model.branch_dim + 1):
            if rank1 + rank2 <= budget:
                yield rank1, rank2


def _svd_energy_ranks(model: BranchingTTNK3, budget: int) -> tuple[int, int]:
    values = []
    for rank1, rank2 in _all_rank_pairs(model, budget):
        tail1 = torch.sum(model.singular_values1[rank1:] ** 2).sqrt()
        tail2 = torch.sum(model.singular_values2[rank2:] ** 2).sqrt()
        values.append((float((tail1 + tail2).item()), rank1, rank2))
    if not values:
        raise ValueError(f"budget {budget} is too small")
    _, rank1, rank2 = min(values)
    return rank1, rank2


def _local_residual_greedy_ranks(model: BranchingTTNK3, budget: int) -> tuple[int, int]:
    """Allocate rank by the largest next local SVD-tail reduction."""

    rank1 = rank2 = 1
    budget = min(2 * model.branch_dim, max(2, int(budget)))
    while rank1 + rank2 < budget:
        candidates: list[tuple[float, int]] = []
        if rank1 < model.branch_dim:
            drop = model.singular_values1[rank1 - 1].pow(2)
            candidates.append((float(drop.item()), 1))
        if rank2 < model.branch_dim:
            drop = model.singular_values2[rank2 - 1].pow(2)
            candidates.append((float(drop.item()), 2))
        if not candidates:
            break
        _, branch = max(candidates)
        if branch == 1:
            rank1 += 1
        else:
            rank2 += 1
    return rank1, rank2


def _oracle_ranks(
    model: BranchingTTNK3,
    validation_queries: list[tuple[int, int, int]],
    candidates: torch.Tensor,
    device: torch.device,
    budget: int,
    full_cache: tuple[torch.Tensor, torch.Tensor] | None = None,
) -> tuple[int, int]:
    values = []
    for rank1, rank2 in _all_rank_pairs(model, budget):
        gap = _sampled_score_gap(
            model, validation_queries, candidates, device, rank1, rank2, full_cache
        )
        values.append((gap["mean_abs_score_gap"], gap["max_abs_score_gap"], rank1, rank2))
    if not values:
        raise ValueError(f"budget {budget} is too small")
    _, _, rank1, rank2 = min(values)
    return rank1, rank2


def _method_ranks(
    method: str,
    model: BranchingTTNK3,
    bounds: dict[str, float],
    validation_queries: list[tuple[int, int, int]],
    candidates: torch.Tensor,
    device: torch.device,
    budget: int,
    validation_full_cache: tuple[torch.Tensor, torch.Tensor] | None = None,
) -> tuple[int, int]:
    if method == "uniform":
        return _uniform_ranks(model, budget)
    if method == "svd_energy":
        return _svd_energy_ranks(model, budget)
    if method == "local_residual_greedy":
        return _local_residual_greedy_ranks(model, budget)
    if method in {"certified", "certified_rank_aware"}:
        ranks, _ = model.optimal_certificate_ranks(
            bounds, budget, rank_aware=method == "certified_rank_aware"
        )
        return int(ranks["branch1"]), int(ranks["branch2"])
    if method == "oracle_validation":
        return _oracle_ranks(
            model, validation_queries, candidates, device, budget, validation_full_cache
        )
    raise ValueError(f"unknown method {method!r}")


def _evaluate_allocation(
    model: BranchingTTNK3,
    kg: KnowledgeGraph,
    bounds: dict[str, float],
    validation_queries: list[tuple[int, int, int]],
    train_queries: list[tuple[int, int, int]],
    test_queries: list[tuple[int, int, int]],
    candidate_ids: torch.Tensor,
    device: torch.device,
    method: str,
    budget: int,
    rank1: int,
    rank2: int,
    validation_full_cache: tuple[torch.Tensor, torch.Tensor],
    train_full_cache: tuple[torch.Tensor, torch.Tensor],
    test_full_cache: tuple[torch.Tensor, torch.Tensor],
    full_ranking_cache: dict[str, torch.Tensor],
    baseline_eval: dict[str, object],
) -> dict[str, object]:
    model.set_ranks(rank1, rank2)
    validation_gap = _sampled_score_gap(
        model, validation_queries, candidate_ids, device, rank1, rank2,
        validation_full_cache,
    )
    train_gap = _sampled_score_gap(
        model, train_queries, candidate_ids, device, rank1, rank2, train_full_cache
    )
    test_gap = _sampled_score_gap(
        model, test_queries, candidate_ids, device, rank1, rank2, test_full_cache
    )
    certificate = model.certificate(bounds, rank1, rank2, rank_aware=True)
    stability = _ranking_stability(
        model, kg, test_queries, device, rank1, rank2,
        full_score_cache=full_ranking_cache,
    )
    resources = model.resource_proxy(rank1, rank2, candidate_count=kg.num_entities)
    return {
        "method": method,
        "budget": budget,
        "rank1": rank1,
        "rank2": rank2,
        "certificate_root_bound": float(certificate["root_bound"]),
        "validation_max_abs_score_gap": validation_gap["max_abs_score_gap"],
        "validation_mean_abs_score_gap": validation_gap["mean_abs_score_gap"],
        "test_max_abs_score_gap": test_gap["max_abs_score_gap"],
        "test_mean_abs_score_gap": test_gap["mean_abs_score_gap"],
        "certificate_holds_on_sample": test_gap["max_abs_score_gap"] <= float(certificate["root_bound"]) + 1e-5,
        "train_max_abs_score_gap": train_gap["max_abs_score_gap"],
        "valid_max_abs_score_gap": validation_gap["max_abs_score_gap"],
        "rank_equal_fraction": stability["rank_equal_fraction"],
        "certified_rank_stable_fraction": stability["certified_rank_stable_fraction"],
        "CCR@1": stability["CCR@1"],
        "CCR@3": stability["CCR@3"],
        "CCR@10": stability["CCR@10"],
        "certified_Hits@1_fraction": stability["certified_Hits@1_fraction"],
        "certified_Hits@3_fraction": stability["certified_Hits@3_fraction"],
        "certified_Hits@10_fraction": stability["certified_Hits@10_fraction"],
        "false_certificates": stability["false_certificates"],
        "test_full_MRR": baseline_eval["combined"]["MRR"],
        "test_full_Hits@1": baseline_eval["combined"]["Hits@1"],
        "test_full_Hits@10": baseline_eval["combined"]["Hits@10"],
        "test_projected_MRR": stability["projected"]["MRR"],
        "test_projected_Hits@1": stability["projected"]["Hits@1"],
        "test_projected_Hits@10": stability["projected"]["Hits@10"],
        **resources,
    }


def _tolerance_allocation_summary(
    records: list[dict[str, object]], tolerances: list[float]
) -> dict[str, object]:
    """Select certificate, uniform, and retrospective oracle allocations."""

    grid = [row for row in records if row["method"] == "rank_grid"]
    allocation_source = "rank_grid"
    if not grid:
        # Multi-seed robustness probes may evaluate only registered policies
        # to control cost; keep their tolerance summary explicit rather than
        # silently returning empty selections.
        grid = [row for row in records if row["method"] != "full_rank"]
        allocation_source = "selected_policies_fallback"
    uniform = [row for row in records if row["method"] == "uniform"]
    resource_key = "projected_candidate_score_units"

    def select(rows: list[dict[str, object]], key: str, tolerance: float) -> dict[str, object] | None:
        feasible = [row for row in rows if float(row[key]) <= tolerance]
        if not feasible:
            return None
        row = min(feasible, key=lambda item: int(item[resource_key]))
        return {
            "ranks": [int(row["rank1"]), int(row["rank2"])],
            "resource_units": int(row[resource_key]),
            "certificate_bound": float(row["certificate_root_bound"]),
            "observed_test_error": float(row["test_max_abs_score_gap"]),
            "rank_equal_fraction": float(row["rank_equal_fraction"]),
            "CCR@1": float(row["CCR@1"]),
            "CCR@3": float(row["CCR@3"]),
            "CCR@10": float(row["CCR@10"]),
        }

    selections: list[dict[str, object]] = []
    for tolerance in tolerances:
        certificate = select(grid, "certificate_root_bound", tolerance)
        oracle = select(grid, "test_max_abs_score_gap", tolerance)
        uniform_row = select(uniform, "certificate_root_bound", tolerance)
        price = None
        if certificate is not None and oracle is not None and oracle["resource_units"]:
            price = float(certificate["resource_units"]) / float(oracle["resource_units"])
        selections.append({
            "tolerance": float(tolerance),
            "certificate_driven": certificate,
            "uniform_certificate_feasible": uniform_row,
            "oracle_retrospective": oracle,
            "Pi_cert_vs_oracle": price,
        })
    return {
        "resource_key": resource_key,
        "allocation_source": allocation_source,
        "tolerances": selections,
        "oracle_definition": "minimum analytical resource among rank_grid rows satisfying observed test score error",
        "certificate_definition": "minimum analytical resource among rank_grid rows satisfying global certificate bound",
    }


def _markdown(output: dict[str, object]) -> str:
    lines = [
        "# FB15K-237 branching TTN post-training probe — 2026-08-09",
        "",
        "Status: exploratory, post-training, and not a production KGE claim. A"
        " full-rank branching TTN was trained first; SVD projectors were then"
        " fitted with frozen weights. No projected model was fine-tuned.",
        "",
        "| Method | Budget | Ranks | Cert. bound | Test score gap | Rank equal | Cert. stable | Full MRR | Projected MRR | Projected contraction units |",
        "|---|---:|---|---:|---:|---:|---:|---:|---:|---:|",
    ]
    for rec in output["records"]:
        lines.append(
            f"| {rec['method']} | {rec['budget']} | "
            f"({rec['rank1']},{rec['rank2']}) | {rec['certificate_root_bound']:.4g} | "
            f"{rec['test_max_abs_score_gap']:.4g} | {rec['rank_equal_fraction']:.3f} | "
            f"{rec['certified_rank_stable_fraction']:.3f} | "
            f"{rec['test_full_MRR']:.4f} | {rec['test_projected_MRR']:.4f} | "
            f"{rec['projected_score_contraction_units']} |"
        )
    lines += [
        "",
        "The certificate is a bounded-domain score bound derived from stored"
        " embedding norms and Frobenius operator enclosures. It is distinct"
        " from observed test score gaps and from MRR/Hits.",
        "",
        "Limitations: one dataset, one seed, one TTN architecture, short"
        " exploratory training, sampled ranking queries, conservative"
        " enclosures, and analytical resource proxies rather than hardware"
        " timing. The result does not establish universal allocator or"
        " industrial superiority.",
    ]
    return "\n".join(lines) + "\n"


def run(args: argparse.Namespace) -> dict[str, object]:
    if args.dim % 2 or args.branch_dim <= 0:
        raise ValueError("dim must be even and branch-dim positive")
    budgets = [int(value) for value in args.budgets.split(",") if value.strip()]
    tolerances = [float(value) for value in args.tolerances.split(",") if value.strip()]
    device = _device(args)
    if device.type == "cuda":
        torch.cuda.reset_peak_memory_stats(device)
    repro.set_seed(args.seed)
    kg = load_knowledge_graph(args.train, args.valid, args.test)
    # B-0014: kg's filter tables contain VALID and TEST. Correct for evaluation,
    # leaking if reused to generate training negatives. Evaluation below keeps
    # `kg`; only the training call gets the TRAIN-only view.
    training_kg = train_only_filter_view(kg) if args.negative_filter == "train_only" else kg
    model = BranchingTTNK3(
        kg.num_entities, kg.num_relations_total, args.dim, args.branch_dim
    ).to(device)
    history = _train_full(
        model, training_kg, device, epochs=args.epochs, batch_size=args.batch_size,
        neg_k=args.neg_k, lr=args.lr, weight_decay=args.weight_decay, seed=args.seed,
        loss_temperature=args.loss_temperature,
        embedding_max_norm=args.embedding_max_norm,
        core_max_fro=args.core_max_fro,
        root_max_fro=args.root_max_fro,
        gpu_negative_sampler=args.gpu_negative_sampler,
    )
    calibration = torch.from_numpy(
        np.asarray(kg.train[: min(args.calibration_triples, len(kg.train)), 0:3], dtype=np.int64)
    ).to(device)
    model.fit_projectors(calibration[:, 0], calibration[:, 1])
    model.eval()
    model.set_mode("full")

    # Persist the frozen state before any potentially expensive evaluation so
    # an interrupted run still leaves an auditable continuation artifact.
    args.out_dir.mkdir(parents=True, exist_ok=True)
    checkpoint_path = args.out_dir / "full_ttn.pt"
    torch.save(
        {
            "model_state": {key: value.detach().cpu() for key, value in model.state_dict().items()},
            "dim": args.dim,
            "branch_dim": args.branch_dim,
            "seed": args.seed,
            "training_history": history,
            "projectors_fit_from": "train_only",
            "calibration_triples": min(args.calibration_triples, len(kg.train)),
        },
        checkpoint_path,
    )

    validation_queries = _query_subset(kg, "valid", args.eval_queries)
    test_queries = _query_subset(kg, "test", args.eval_queries)
    train_queries = [tuple(int(value) for value in row) for row in kg.train[: args.eval_queries]]
    candidate_ids = _candidate_ids(kg.num_entities, args.candidate_sample, args.seed + 91)
    bounds = branch_leaf_norm_bounds(model)
    train_full_cache = _sampled_full_cache(model, train_queries, candidate_ids, device)
    validation_full_cache = _sampled_full_cache(model, validation_queries, candidate_ids, device)
    test_full_cache = _sampled_full_cache(model, test_queries, candidate_ids, device)
    full_ranking_cache = _full_ranking_cache(model, kg, test_queries, device)
    methods = (
        "uniform",
        "svd_energy",
        "local_residual_greedy",
        "certified",
        "certified_rank_aware",
        "oracle_validation",
    )
    model.set_mode("full")
    baseline_eval = evaluate(
        model, kg, "test", device, batch_size=32, entity_block=4096,
        subset=1.0, seed=args.seed, queries=test_queries,
    )
    records: list[dict[str, object]] = []
    for budget in budgets:
        for method in methods:
            rank1, rank2 = _method_ranks(
                method, model, bounds, validation_queries, candidate_ids, device, budget,
                validation_full_cache,
            )
            records.append(_evaluate_allocation(
                model, kg, bounds, validation_queries, train_queries, test_queries,
                candidate_ids, device, method, budget, rank1, rank2,
                validation_full_cache, train_full_cache, test_full_cache,
                full_ranking_cache, baseline_eval,
            ))

    if args.rank_grid:
        grid_values = (1, 2, 4, 8, 16, 24, 32)
        grid_pairs = [
            (rank1, rank2)
            for rank1 in grid_values if rank1 <= model.branch_dim
            for rank2 in grid_values if rank2 <= model.branch_dim
        ]
        for rank1, rank2 in grid_pairs:
            records.append(_evaluate_allocation(
                model, kg, bounds, validation_queries, train_queries, test_queries,
                candidate_ids, device, "rank_grid", rank1 + rank2, rank1, rank2,
                validation_full_cache, train_full_cache, test_full_cache,
                full_ranking_cache, baseline_eval,
            ))

    certificate_values = np.asarray([float(item["certificate_root_bound"]) for item in records])
    test_errors = np.asarray([float(item["test_max_abs_score_gap"]) for item in records])
    if len(records) > 1 and np.std(certificate_values) > 0 and np.std(test_errors) > 0:
        pearson = float(np.corrcoef(certificate_values, test_errors)[0, 1])
        cert_order = np.argsort(np.argsort(certificate_values))
        error_order = np.argsort(np.argsort(test_errors))
        spearman = float(np.corrcoef(cert_order, error_order)[0, 1])
    else:
        pearson = None
        spearman = None
    if device.type == "cuda":
        cuda_memory = {
            "peak_allocated_bytes": int(torch.cuda.max_memory_allocated(device)),
            "peak_reserved_bytes": int(torch.cuda.max_memory_reserved(device)),
        }
    else:
        cuda_memory = {
            "peak_allocated_bytes": None,
            "peak_reserved_bytes": None,
        }
    return {
        "status": "EXPLORATORY_POSTTRAIN_TTN_FB15K237_PROTOCOL_ALIGNED",
        "dataset": {
            "train": str(Path(args.train)),
            "valid": str(Path(args.valid)),
            "test": str(Path(args.test)),
            "num_entities": kg.num_entities,
            "num_relations_original": kg.num_relations_original,
            "train_triples_with_reciprocals": int(len(kg.train)),
        },
        "design": {
            "architecture": "branching_TTN_k3",
            "dim": args.dim,
            "branch_dim": args.branch_dim,
            "truncable_nodes": ["branch1", "branch2"],
            "root_projected": False,
            "training": "full_rank_then_freeze_then_SVD_project",
            "seed": args.seed,
            "device": str(device),
            "epochs": args.epochs,
            "batch_size": args.batch_size,
            "negative_k": args.neg_k,
            "loss_temperature": args.loss_temperature,
            "embedding_max_norm": args.embedding_max_norm,
            "core_max_fro": args.core_max_fro,
            "root_max_fro": args.root_max_fro,
            "calibration_triples": min(args.calibration_triples, len(kg.train)),
            "evaluation_queries_per_split": args.eval_queries,
            "candidate_sample_for_score_gap": args.candidate_sample,
            "budgets": budgets,
            "methods": methods,
            "rank_grid": args.rank_grid,
            "tolerances": tolerances,
            "cuda_memory": cuda_memory,
        },
        "training_history": history,
        "full_checkpoint": str(checkpoint_path),
        "leaf_norm_bounds": bounds,
        "records": records,
        "summary": {
            "certificate_test_violation_rate": float(np.mean([
                not bool(item["certificate_holds_on_sample"]) for item in records
            ])) if records else 0.0,
            "certificate_test_hold_fraction": float(np.mean([
                bool(item["certificate_holds_on_sample"]) for item in records
            ])) if records else 0.0,
            "certificate_error_pearson": pearson,
            "certificate_error_spearman": spearman,
            "false_certificate_count": int(sum(int(item["false_certificates"]) for item in records)),
        },
        "allocation_summary": _tolerance_allocation_summary(records, tolerances),
        "limitations": [
            "One FB15K-237 seed and one branching TTN architecture.",
            "Training and ranking evaluation are exploratory and sampled by query count.",
            "Frobenius enclosures are valid but conservative; resource values are analytical proxies.",
            "No post-projection fine-tuning, multi-seed campaign, or hardware Pareto claim.",
        ],
    }


def main() -> None:
    args = parser().parse_args()
    config = vars(args).copy()
    config["out_dir"] = str(args.out_dir)
    contract = repro.build_run_contract(
        args.out_dir,
        [sys.executable, "-m", "seion_kgr.run_ttn_fb15k237"],
        {"train": args.train, "valid": args.valid, "test": args.test},
        resolved_config=config,
        allow_existing=args.allow_existing,
    )
    try:
        output = run(args)
        args.out_dir.mkdir(parents=True, exist_ok=True)
        repro.save_json(output, args.out_dir / "ttn_results.json")
        manifest = json.loads((args.out_dir / "run_manifest.json").read_text(encoding="utf-8"))
        manifest["status"] = "COMPLETE"
        manifest["result"] = "TTN_BRANCHING_POSTTRAIN_COMPLETE"
        repro.save_json(manifest, args.out_dir / "run_manifest.json")
        if not args.skip_application_result:
            report_path = APPLICATION_RESULT_DIR / "TTN_FB15K237_BRANCHING_K3_POSTTRAIN_2026-08-09.md"
            json_path = APPLICATION_RESULT_DIR / "TTN_FB15K237_BRANCHING_K3_POSTTRAIN_2026-08-09.json"
            repro.save_json(output, json_path)
            report_path.write_text(_markdown(output), encoding="utf-8")
        print(json.dumps({"out_dir": str(args.out_dir), "records": len(output["records"]), "device": output["design"]["device"]}, sort_keys=True))
    except Exception:
        manifest = json.loads((args.out_dir / "run_manifest.json").read_text(encoding="utf-8"))
        manifest["status"] = "FAILED_RUNTIME"
        repro.save_json(manifest, args.out_dir / "run_manifest.json")
        raise


if __name__ == "__main__":
    main()
