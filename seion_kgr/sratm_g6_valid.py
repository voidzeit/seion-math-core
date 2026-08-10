"""G6 all-entity VALID evaluation for frozen SRATM, without opening TEST.

The evaluator streams validation queries and all entities in candidate blocks.
It computes filtered ranks using TRAIN+VALID-only positives, while score-bound
checks cover every candidate score in the same pass.  Results are explicitly
labelled as pre-test validation evidence; no TEST file is loaded or hashed.
"""

from __future__ import annotations

import argparse
import json
import math
import platform
import sys
import time
from pathlib import Path
from typing import Any, Iterable, Mapping

import numpy as np
import torch
import torch.nn.functional as F

from .data import reciprocal_closure
from .sratm_certified_compression import (
    TEACHER_RUN,
    branch_vectors,
    build_model,
    candidate_vectors,
    deterministic_sample,
    fit_audits,
    load_train_valid_only,
    relation_branch_ids,
    ranks_for_policy,
    git_state,
    write_json,
    sha256,
)


def _filter_block(
    scores: torch.Tensor,
    bounds: torch.Tensor,
    rows: np.ndarray,
    kg: Any,
    start: int,
    gold_scores: torch.Tensor,
) -> tuple[torch.Tensor, torch.Tensor]:
    filtered_scores = scores.clone()
    filtered_bounds = bounds.clone()
    end = start + scores.shape[1]
    for index, row in enumerate(rows):
        h, relation, gold = (int(row[0]), int(row[1]), int(row[2]))
        if relation < kg.num_relations_original:
            positives = kg.tails_of_hr.get((h, relation))
        else:
            positives = kg.heads_of_rt.get((relation - kg.num_relations_original, h))
        if positives is not None and len(positives):
            local = positives[(positives >= start) & (positives < end)] - start
            if len(local):
                local_tensor = torch.as_tensor(local, device=scores.device, dtype=torch.long)
                filtered_scores[index, local_tensor] = -torch.inf
                filtered_bounds[index, local_tensor] = -torch.inf
        if start <= gold < end:
            local_gold = gold - start
            filtered_scores[index, local_gold] = gold_scores[index]
            filtered_bounds[index, local_gold] = bounds[index, local_gold]
    return filtered_scores, filtered_bounds


def _merge_top(
    old_scores: torch.Tensor,
    old_ids: torch.Tensor,
    old_bounds: torch.Tensor,
    new_scores: torch.Tensor,
    new_ids: torch.Tensor,
    new_bounds: torch.Tensor,
    k: int,
) -> tuple[torch.Tensor, torch.Tensor, torch.Tensor]:
    values = torch.cat((old_scores, new_scores), dim=1)
    ids = torch.cat((old_ids, new_ids), dim=1)
    bounds = torch.cat((old_bounds, new_bounds), dim=1)
    selected, indices = torch.topk(values, k, dim=1)
    return selected, ids.gather(1, indices), bounds.gather(1, indices)


def _merge_bound_top(
    old_values: torch.Tensor,
    old_ids: torch.Tensor,
    new_values: torch.Tensor,
    new_ids: torch.Tensor,
    k: int,
) -> tuple[torch.Tensor, torch.Tensor]:
    values = torch.cat((old_values, new_values), dim=1)
    ids = torch.cat((old_ids, new_ids), dim=1)
    selected, indices = torch.topk(values, k, dim=1)
    return selected, ids.gather(1, indices)


def _rank_projected_branch(audit: Any, relation: int, query: torch.Tensor, rank: int, device: torch.device):
    basis = audit.projectors[relation].basis[:, :rank].to(device=device, dtype=query.dtype)
    q_white = audit.whitening.whiten_queries(query)
    q_projected = q_white @ basis
    q_residual = (q_white.square().sum(dim=-1) - q_projected.square().sum(dim=-1)).clamp_min(0).sqrt()
    e_white = audit.candidate_white(device, query.dtype)
    e_projected = e_white @ basis
    e_residual = (e_white.square().sum(dim=-1) - e_projected.square().sum(dim=-1)).clamp_min(0).sqrt()
    return q_projected, q_residual, e_projected, e_residual


def evaluate_policy_all_entity(
    model: Any,
    audits: Mapping[str, Any],
    kg: Any,
    rows: np.ndarray,
    ranks_by_relation: Mapping[int, Mapping[str, int]],
    device: torch.device,
    candidate_block: int = 1024,
    query_batch: int = 256,
    top_k: int = 10,
) -> dict[str, Any]:
    num_queries = len(rows)
    num_entities = kg.num_entities
    global_candidates, complex_candidates, expert_candidates = candidate_vectors(model)
    global_candidates = global_candidates.to(device)
    complex_candidates = complex_candidates.to(device)
    expert_candidates = {key: value.to(device) for key, value in expert_candidates.items()}
    all_candidates = torch.arange(num_entities, device=device, dtype=torch.long)
    rank_full = torch.zeros(num_queries, device=device, dtype=torch.long)
    rank_compressed = torch.zeros(num_queries, device=device, dtype=torch.long)
    full_top_scores = torch.full((num_queries, top_k + 1), -torch.inf, device=device)
    full_top_ids = torch.full((num_queries, top_k + 1), -1, device=device, dtype=torch.long)
    full_top_bounds = torch.full((num_queries, top_k + 1), -torch.inf, device=device)
    compressed_top_scores = torch.full((num_queries, top_k + 1), -torch.inf, device=device)
    compressed_top_ids = torch.full((num_queries, top_k + 1), -1, device=device, dtype=torch.long)
    bound_top_values = torch.full((num_queries, top_k + 1), -torch.inf, device=device)
    bound_top_ids = torch.full((num_queries, top_k + 1), -1, device=device, dtype=torch.long)
    max_error_query = torch.zeros(num_queries, device=device, dtype=torch.float64)
    max_bound_query = torch.zeros(num_queries, device=device, dtype=torch.float64)
    max_error = 0.0
    max_error_minus_bound = -math.inf
    sum_error = 0.0
    score_count = 0
    violations = 0
    error_sample: list[float] = []
    sample_cap = 1_000_000
    start_time = time.perf_counter()

    with torch.inference_mode():
        for relation in sorted(set(int(value) for value in rows[:, 1])):
            positions = np.flatnonzero(rows[:, 1] == relation)
            policy = ranks_by_relation[relation]
            active_experts = relation_branch_ids(model, relation)
            weights = F.softmax(model.fusion_logits[relation], dim=-1)
            tau = F.softplus(model.tau_raw[relation]).clamp_min(1e-6)
            routing = F.softmax(model.routing_logits[relation], dim=-1)
            g_audit = audits["G"]
            c_audit = audits["C"]
            g_basis = g_audit.projectors[relation].basis[:, :policy["G"]].to(device=device, dtype=model.entity.weight.dtype)
            c_basis = c_audit.projectors[relation].basis[:, :policy["C"]].to(device=device, dtype=model.entity.weight.dtype)
            g_white_entities = g_audit.candidate_white(device, model.entity.weight.dtype)
            c_white_entities = c_audit.candidate_white(device, model.entity.weight.dtype)
            g_projected_entities = g_white_entities @ g_basis
            c_projected_entities = c_white_entities @ c_basis
            g_entity_residual = (g_white_entities.square().sum(-1) - g_projected_entities.square().sum(-1)).clamp_min(0).sqrt()
            c_entity_residual = (c_white_entities.square().sum(-1) - c_projected_entities.square().sum(-1)).clamp_min(0).sqrt()
            expert_projected_entities: dict[int, torch.Tensor] = {}
            expert_entity_residual: dict[int, torch.Tensor] = {}
            for expert_id in active_experts:
                audit = audits[f"M:e{expert_id}"]
                basis = audit.projectors[relation].basis[:, :policy["M"]].to(device=device, dtype=model.entity.weight.dtype)
                e_white = audit.candidate_white(device, model.entity.weight.dtype)
                e_proj = e_white @ basis
                expert_projected_entities[expert_id] = e_proj
                expert_entity_residual[expert_id] = (e_white.square().sum(-1) - e_proj.square().sum(-1)).clamp_min(0).sqrt()

            for offset in range(0, len(positions), query_batch):
                selected = positions[offset : offset + query_batch]
                batch_rows = rows[selected]
                batch = torch.as_tensor(batch_rows, device=device, dtype=torch.long)
                h, r, gold = batch.T
                gq, cq, expert_q, _ = branch_vectors(model, h, r)
                gq_proj, gq_res, _, _ = _rank_projected_branch(g_audit, relation, gq, policy["G"], device)
                cq_proj, cq_res, _, _ = _rank_projected_branch(c_audit, relation, cq, policy["C"], device)
                expert_q_proj: dict[int, torch.Tensor] = {}
                expert_q_res: dict[int, torch.Tensor] = {}
                for expert_id in active_experts:
                    q_proj, q_res, _, _ = _rank_projected_branch(
                        audits[f"M:e{expert_id}"], relation, expert_q[expert_id], policy["M"], device
                    )
                    expert_q_proj[expert_id] = q_proj
                    expert_q_res[expert_id] = q_res
                # Compute the true scores before streaming candidate blocks.  The
                # rank accumulator visits blocks that may precede the gold
                # entity; using a zero placeholder there would count all
                # positive scores as outranking the gold and corrupt G6.
                full_gold_g = (gq * global_candidates[gold]).sum(dim=-1)
                full_gold_c = (cq * complex_candidates[gold]).sum(dim=-1)
                comp_gold_g = (gq_proj * g_projected_entities[gold]).sum(dim=-1)
                comp_gold_c = (cq_proj * c_projected_entities[gold]).sum(dim=-1)
                full_gold_m_parts: list[torch.Tensor] = []
                comp_gold_m_parts: list[torch.Tensor] = []
                for expert_id in active_experts:
                    full_gold_m_parts.append((expert_q[expert_id] * expert_candidates[expert_id][gold]).sum(dim=-1))
                    comp_gold_m_parts.append((expert_q_proj[expert_id] * expert_projected_entities[expert_id][gold]).sum(dim=-1))
                full_gold_m = torch.stack(full_gold_m_parts, dim=-1)
                comp_gold_m = torch.stack(comp_gold_m_parts, dim=-1)
                full_gold_mix = tau * torch.logsumexp(
                    torch.log(routing.clamp_min(1e-12)).view(1, -1) + full_gold_m / tau,
                    dim=-1,
                )
                comp_gold_mix = tau * torch.logsumexp(
                    torch.log(routing.clamp_min(1e-12)).view(1, -1) + comp_gold_m / tau,
                    dim=-1,
                )
                gold_full = weights[0] * full_gold_g + weights[1] * full_gold_mix + weights[2] * full_gold_c
                gold_compressed = weights[0] * comp_gold_g + weights[1] * comp_gold_mix + weights[2] * comp_gold_c
                local_full_top_scores = torch.full((len(selected), top_k + 1), -torch.inf, device=device)
                local_full_top_ids = torch.full((len(selected), top_k + 1), -1, device=device, dtype=torch.long)
                local_full_top_bounds = torch.full((len(selected), top_k + 1), -torch.inf, device=device)
                local_comp_top_scores = torch.full((len(selected), top_k + 1), -torch.inf, device=device)
                local_comp_top_ids = torch.full((len(selected), top_k + 1), -1, device=device, dtype=torch.long)
                local_bound_top_values = torch.full((len(selected), top_k + 1), -torch.inf, device=device)
                local_bound_top_ids = torch.full((len(selected), top_k + 1), -1, device=device, dtype=torch.long)
                local_max_error = torch.zeros(len(selected), device=device, dtype=torch.float64)
                local_max_bound = torch.zeros(len(selected), device=device, dtype=torch.float64)
                for candidate_start in range(0, num_entities, candidate_block):
                    candidate_end = min(candidate_start + candidate_block, num_entities)
                    ids = all_candidates[candidate_start:candidate_end]
                    full_g = gq @ global_candidates[candidate_start:candidate_end].transpose(0, 1)
                    full_c = cq @ complex_candidates[candidate_start:candidate_end].transpose(0, 1)
                    comp_g = gq_proj @ g_projected_entities[candidate_start:candidate_end].transpose(0, 1)
                    comp_c = cq_proj @ c_projected_entities[candidate_start:candidate_end].transpose(0, 1)
                    full_m_parts: list[torch.Tensor] = []
                    comp_m_parts: list[torch.Tensor] = []
                    bound_m_parts: list[torch.Tensor] = []
                    for expert_id in active_experts:
                        full_m_parts.append(expert_q[expert_id] @ expert_candidates[expert_id][candidate_start:candidate_end].transpose(0, 1))
                        comp_m_parts.append(expert_q_proj[expert_id] @ expert_projected_entities[expert_id][candidate_start:candidate_end].transpose(0, 1))
                        bound_m_parts.append(expert_q_res[expert_id].unsqueeze(1) * expert_entity_residual[expert_id][candidate_start:candidate_end].unsqueeze(0))
                    full_m = torch.stack(full_m_parts, dim=-1)
                    comp_m = torch.stack(comp_m_parts, dim=-1)
                    bound_m = torch.stack(bound_m_parts, dim=-1).amax(dim=-1)
                    routing_term = torch.log(routing.clamp_min(1e-12)).view(1, 1, -1)
                    full_mix = tau * torch.logsumexp(routing_term + full_m / tau, dim=-1)
                    comp_mix = tau * torch.logsumexp(routing_term + comp_m / tau, dim=-1)
                    full_score = weights[0] * full_g + weights[1] * full_mix + weights[2] * full_c
                    comp_score = weights[0] * comp_g + weights[1] * comp_mix + weights[2] * comp_c
                    bound = (
                        weights[0] * gq_res.unsqueeze(1) * g_entity_residual[candidate_start:candidate_end].unsqueeze(0)
                        + weights[1] * bound_m
                        + weights[2] * cq_res.unsqueeze(1) * c_entity_residual[candidate_start:candidate_end].unsqueeze(0)
                    )
                    error = (full_score - comp_score).abs().to(torch.float64)
                    score_count += int(error.numel())
                    sum_error += float(error.sum().item())
                    max_error = max(max_error, float(error.max().item()))
                    max_error_minus_bound = max(max_error_minus_bound, float((error - bound.to(torch.float64)).max().item()))
                    violations += int((error > bound.to(torch.float64) + 5e-5 + 1e-5 * full_score.abs().to(torch.float64)).sum().item())
                    local_max_error = torch.maximum(local_max_error, error.max(dim=1).values)
                    local_max_bound = torch.maximum(local_max_bound, bound.to(torch.float64).max(dim=1).values)
                    if len(error_sample) < sample_cap:
                        stride = max(1, error.numel() // 2048)
                        error_sample.extend(error.reshape(-1)[::stride].detach().cpu().tolist()[: sample_cap - len(error_sample)])
                    filtered_full, filtered_bound = _filter_block(full_score, bound, batch_rows, kg, candidate_start, gold_full)
                    filtered_comp, _ = _filter_block(comp_score, bound, batch_rows, kg, candidate_start, gold_compressed)
                    rank_full[selected] += (filtered_full > gold_full[:, None]).sum(dim=1)
                    rank_compressed[selected] += (filtered_comp > gold_compressed[:, None]).sum(dim=1)
                    block_k = min(top_k + 1, filtered_full.shape[1])
                    fs, fi = torch.topk(filtered_full, block_k, dim=1)
                    cb = filtered_bound.gather(1, fi)
                    ids_block = ids[fi]
                    local_full_top_scores, local_full_top_ids, local_full_top_bounds = _merge_top(
                        local_full_top_scores, local_full_top_ids, local_full_top_bounds,
                        fs, ids_block, cb, top_k + 1
                    )
                    cs, ci = torch.topk(filtered_comp, block_k, dim=1)
                    local_comp_top_scores, local_comp_top_ids, _ = _merge_top(
                        local_comp_top_scores, local_comp_top_ids, local_full_top_bounds,
                        cs, ids[ci], local_full_top_bounds, top_k + 1
                    )
                    bs, bi = torch.topk(filtered_bound, block_k, dim=1)
                    local_bound_top_values, local_bound_top_ids = _merge_bound_top(
                        local_bound_top_values, local_bound_top_ids, bs, ids[bi], top_k + 1
                    )
                rank_full[selected] += 1
                rank_compressed[selected] += 1
                max_error_query[selected] = torch.maximum(max_error_query[selected], local_max_error)
                max_bound_query[selected] = torch.maximum(max_bound_query[selected], local_max_bound)
                full_top_scores[selected] = local_full_top_scores
                full_top_ids[selected] = local_full_top_ids
                full_top_bounds[selected] = local_full_top_bounds
                compressed_top_scores[selected] = local_comp_top_scores
                compressed_top_ids[selected] = local_comp_top_ids
                bound_top_values[selected] = local_bound_top_values
                bound_top_ids[selected] = local_bound_top_ids

    rank_full = rank_full.clamp_min(1)
    rank_compressed = rank_compressed.clamp_min(1)
    mrr_full = (1.0 / rank_full.to(torch.float64)).mean()
    mrr_compressed = (1.0 / rank_compressed.to(torch.float64)).mean()
    metrics: dict[str, Any] = {
        "queries": num_queries,
        "entities": num_entities,
        "filtered_positive_source": "TRAIN_PLUS_VALID_ONLY",
        "test_split_touched": False,
        "mrr_full": float(mrr_full.item()),
        "mrr_compressed": float(mrr_compressed.item()),
        "delta_mrr": float((mrr_compressed - mrr_full).item()),
        "hits_full": {f"@{k}": float((rank_full <= k).double().mean().item()) for k in (1, 3, 10)},
        "hits_compressed": {f"@{k}": float((rank_compressed <= k).double().mean().item()) for k in (1, 3, 10)},
        "mean_rank_full": float(rank_full.double().mean().item()),
        "mean_rank_compressed": float(rank_compressed.double().mean().item()),
        "rank_equality_fraction": float((rank_full == rank_compressed).double().mean().item()),
        "topk_set_equality": {f"@{k}": float((torch.sort(full_top_ids[:, :k], dim=1).values == torch.sort(compressed_top_ids[:, :k], dim=1).values).all(dim=1).double().mean().item()) for k in (1, 3, 10)},
        "score_error": {
            "max_abs_error": max_error,
            "mean_abs_error": sum_error / max(score_count, 1),
            "p95_abs_error_sampled": float(np.quantile(np.asarray(error_sample, dtype=np.float64), 0.95)) if error_sample else None,
            "p99_abs_error_sampled": float(np.quantile(np.asarray(error_sample, dtype=np.float64), 0.99)) if error_sample else None,
            "sample_size": len(error_sample),
            "pair_count": score_count,
        },
        "certificate_validation": {
            "candidate_specific_violations": violations,
            "max_error_minus_bound": max_error_minus_bound,
            "numerical_tolerance": "5e-5 + 1e-5*abs(full_score)",
            "uniform_query_violations": int((max_error_query > max_bound_query + 5e-5).sum().item()),
        },
        "runtime_seconds": time.perf_counter() - start_time,
    }
    for k in (1, 3, 10):
        boundary = full_top_scores[:, k - 1] - full_top_scores[:, k]
        top_bound = full_top_bounds[:, :k].amax(dim=1)
        outside_mask = ~((bound_top_ids[:, :, None] == full_top_ids[:, None, :k]).any(dim=-1))
        outside_bound = bound_top_values.masked_fill(~outside_mask, -torch.inf).amax(dim=1)
        metrics[f"CCR@{k}"] = float((boundary > top_bound + outside_bound + 5e-5).double().mean().item())
    metrics["pairwise_certified_top1_fraction"] = float(
        ((rank_full == 1) & ((full_top_scores[:, 0] - full_top_scores[:, 1]) > full_top_bounds[:, 0] + full_top_bounds[:, 1] + 5e-5)).double().mean().item()
    )
    return metrics


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=Path("."))
    parser.add_argument("--out-dir", type=Path, required=True)
    parser.add_argument("--calibration-queries", type=int, default=8192)
    parser.add_argument("--candidate-block", type=int, default=1024)
    parser.add_argument("--query-batch", type=int, default=256)
    parser.add_argument(
        "--validation-rows",
        type=int,
        default=0,
        help="Evaluate only the first N reciprocal validation rows for a bounded smoke test; 0 means all rows.",
    )
    parser.add_argument("--device", choices=("cpu", "cuda"), default="cpu")
    parser.add_argument("--policies", default="uniform_medium")
    parser.add_argument("--seed", type=int, default=13579)
    return parser


def run(args: argparse.Namespace) -> dict[str, Any]:
    root = args.root.resolve()
    out = args.out_dir.resolve()
    out.mkdir(parents=True, exist_ok=False)
    kg = load_train_valid_only(root / "data/FB15K-237/train.txt", root / "data/FB15K-237/valid.txt", expected_num_entities=14541, expected_num_relations_total=474)
    device = torch.device("cuda:0" if args.device == "cuda" and torch.cuda.is_available() else "cpu")
    model = build_model(kg, root / TEACHER_RUN / "checkpoint_last.pt", device)
    calibration = deterministic_sample(kg.train, args.calibration_queries, args.seed)
    validation_rows = np.asarray(reciprocal_closure(kg.valid, kg.num_relations_original), dtype=np.int64)
    if args.validation_rows:
        if args.validation_rows < 1 or args.validation_rows > len(validation_rows):
            raise ValueError(f"--validation-rows must be in [1, {len(validation_rows)}] or 0")
        validation_rows = validation_rows[: args.validation_rows]
    requested = {"G": [32, 64, 96, 128, 160, 192, 224, 256], "M": [4, 8, 12, 16, 24, 32, 48, 64], "C": [64, 128, 256]}
    audits, _ = fit_audits(model, calibration, device, requested)
    reference_path = root / TEACHER_RUN / "audit_step4600.json"
    reference = json.loads(reference_path.read_text(encoding="utf-8"))
    reference_metrics = reference.get("metrics", {}).get("combined", {})
    relation_ids = sorted(set(int(value) for value in validation_rows[:, 1]))
    policy_defaults = {
        "uniform_low": {"G": 64, "M": 16, "C": 128},
        "uniform_medium": {"G": 128, "M": 32, "C": 256},
        "uniform_high": {"G": 192, "M": 48, "C": 256},
    }
    results: dict[str, Any] = {}
    for name in [value.strip() for value in args.policies.split(",") if value.strip()]:
        if name not in policy_defaults:
            raise ValueError(f"unknown policy {name}")
        ranks = ranks_for_policy(model, relation_ids, policy_defaults[name])
        results[name] = evaluate_policy_all_entity(model, audits, kg, validation_rows, ranks, device, args.candidate_block, args.query_batch)
        results[name]["ranks"] = policy_defaults[name]
    full_rank_control = {
        "protocol": "TRAIN_PLUS_VALID_ONLY_FILTERS",
        "historical_teacher_reference_protocol": "NOT_RECONSTRUCTED_WITHOUT_TEST",
        "mrr_full_g6": float(next(iter(results.values()))["mrr_full"]) if results else None,
        "mrr_historical_teacher_reference": reference_metrics.get("MRR"),
        "delta_mrr_vs_historical_reference": (
            float(next(iter(results.values()))["mrr_full"]) - float(reference_metrics["MRR"])
            if results and reference_metrics.get("MRR") is not None else None
        ),
        "reference_artifact": str(reference_path),
        "interpretation": "The historical reference cannot be reproduced under the sealed TRAIN+VALID-only protocol without opening TEST; this is a protocol discrepancy, not evidence that the scorer is wrong.",
    }
    certificate_pass = all(
        item["certificate_validation"]["candidate_specific_violations"] == 0 for item in results.values()
    )
    reference_match = (
        full_rank_control["delta_mrr_vs_historical_reference"] is not None
        and abs(full_rank_control["delta_mrr_vs_historical_reference"]) <= 1e-3
    )
    output = {
        "campaign": "SRATM_CERTIFIED_COMPRESSION_V1_G6_ALL_ENTITY_VALID",
        "status": (
            "PASS_G6_PRE_TEST_VALIDATION"
            if certificate_pass and reference_match
            else "BLOCKED_REFERENCE_PROTOCOL_MISMATCH"
            if certificate_pass
            else "FAIL_CERTIFICATE_VALIDATION"
        ),
        "certificate_validity_gate": "PASS" if certificate_pass else "FAIL",
        "g6_preservation_gate": "PASS" if reference_match else "BLOCKED_REFERENCE_PROTOCOL_MISMATCH",
        "full_rank_control": full_rank_control,
        "test_split_touched": False,
        "validation_rows": len(validation_rows),
        "validation_rows_requested": args.validation_rows,
        "calibration_queries": len(calibration),
        "validation_convention": "original valid rows plus reciprocal head queries",
        "filtered_positive_source": "TRAIN_PLUS_VALID_ONLY",
        "candidate_block": args.candidate_block,
        "query_batch": args.query_batch,
        "device": str(device),
        "results": results,
        "limitations": [
            "TEST was not read, hashed, or opened.",
            "This is pre-test validation with TRAIN+VALID-only filters, not final benchmark TEST confirmation.",
            "Hardware timing is not included; B-0012 remains active.",
        ],
    }
    write_json(out / "g6_all_entity_valid.json", output)
    write_json(out / "final_status.json", output)
    (out / "final_report.md").write_text(
        "# SRATM_CERTIFIED_COMPRESSION_V1 — G6 all-entity VALID\n\n"
        f"Status: **{output['status']}**\n\n"
        f"Queries: `{len(validation_rows)}`; entities: `{kg.num_entities}`; filters: `TRAIN+VALID`; TEST touched: `false`.\n\n"
        f"Historical teacher reference MRR: `{reference_metrics.get('MRR')}`; sealed-protocol full-rank MRR: `{full_rank_control['mrr_full_g6']}`; delta: `{full_rank_control['delta_mrr_vs_historical_reference']}`.\n\n"
        "The historical reference filter provenance was not reconstructed because TEST remains sealed; G6 preservation is therefore blocked until the pre-test evaluation protocol is reconciled.\n\n"
        + "\n".join(
            f"- `{name}`: MRR full `{value['mrr_full']:.9f}`, compressed `{value['mrr_compressed']:.9f}`, delta `{value['delta_mrr']:.9f}`, violations `{value['certificate_validation']['candidate_specific_violations']}`, CCR@10 `{value['CCR@10']:.6f}`"
            for name, value in results.items()
        )
        + "\n\nNo TEST or GPU stress run was performed.\n",
        encoding="utf-8",
    )
    artifacts = {
        path.name: sha256(path)
        for path in sorted(out.iterdir())
        if path.is_file() and path.name not in {"artifact_hashes.json", "manifest.json"}
    }
    write_json(out / "artifact_hashes.json", artifacts)
    write_json(
        out / "manifest.json",
        {
            "campaign": output["campaign"],
            "status": output["status"],
            "command": " ".join([sys.executable, "-m", "seion_kgr.sratm_g6_valid", *sys.argv[1:]]),
            "git_state": git_state(root),
            "checkpoint": {
                "path": str(root / TEACHER_RUN / "checkpoint_last.pt"),
                "sha256": sha256(root / TEACHER_RUN / "checkpoint_last.pt"),
            },
            "dataset": {
                "name": "FB15K-237",
                "train_sha256": sha256(root / "data/FB15K-237/train.txt"),
                "valid_sha256": sha256(root / "data/FB15K-237/valid.txt"),
                "test": "NOT_READ_NOT_HASHED_NOT_OPENED",
            },
            "hardware": {"device": str(device), "platform": platform.platform()},
            "dtype": str(model.entity.weight.dtype),
            "test_split_touched": False,
            "artifacts": artifacts,
            "limitations": output["limitations"],
        },
    )
    return output


def main() -> None:
    result = run(build_parser().parse_args())
    print(json.dumps(result, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
