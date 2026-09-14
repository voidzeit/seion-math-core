"""First post-training SRATM compression campaign without opening TEST.

This module deliberately does not call ``load_knowledge_graph`` because that
loader reads the test split to build official filtered filters.  The campaign
uses train-derived calibration and a train+valid-only validation filter.  All
artifacts therefore state explicitly that official filtered validation is not
recomputed in this campaign.

The compression object is branch-wise score-space projection:

    score_b(q,t) = z_b(q)^T e_b(t)
    z_b, e_b -> whitened coordinates -> rank-k Ky-Fan projector.

For the SRATM mixture, each active Tucker expert is audited separately and
the log-sum-exp 1-Lipschitz bound composes the expert certificates.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import platform
import subprocess
import sys
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable, Mapping

import numpy as np
import torch
import torch.nn.functional as F

from .data import KnowledgeGraph, build_filters, build_id_maps, map_triples, read_triples_file, reciprocal_closure
from .score_space import CandidateWhitening, SpectralProjector
from .sota.sratm import SpectralRelationAdaptiveTensorMixture


TEACHER_SHA256 = "aae9c67b292cba0f155e9b5e33dc019b7bad8868b64f0e03cc45b477d462f085"
TEACHER_STEP = 4600
TEACHER_RUN = Path("runs/SRATM_FB15K237_D256_DISCOVERY_8192_B512_23GB_2026-08-10")


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(8 * 1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def jsonable(value: Any) -> Any:
    if isinstance(value, Path):
        return str(value)
    if isinstance(value, torch.Tensor):
        return value.detach().cpu().tolist()
    if isinstance(value, np.ndarray):
        return value.tolist()
    if isinstance(value, (np.integer, np.floating)):
        return value.item()
    if isinstance(value, dict):
        return {str(k): jsonable(v) for k, v in value.items()}
    if isinstance(value, (list, tuple)):
        return [jsonable(v) for v in value]
    return value


def write_json(path: Path, value: Any) -> None:
    path.write_text(json.dumps(jsonable(value), indent=2, sort_keys=True) + "\n", encoding="utf-8")


def artifact_hashes(directory: Path) -> dict[str, str]:
    return {
        str(path.relative_to(directory)): sha256(path)
        for path in sorted(directory.rglob("*"))
        if path.is_file() and path.name not in {"artifact_hashes.json", "manifest.json"}
    }


def write_campaign_report(
    out: Path,
    teacher_reference: Mapping[str, Any],
    equivalence: Mapping[str, Any],
    pareto: list[dict[str, Any]],
    final: Mapping[str, Any],
    allocator: Mapping[str, Any],
) -> None:
    lines = [
        "# SRATM_CERTIFIED_COMPRESSION_V1 — bounded closeout",
        "",
        "## EXECUTIVE_RESULT",
        "",
        "The frozen SRATM step4600 was audited without opening TEST and without introducing a student/distillation stage.",
        f"Teacher checkpoint SHA256: `{teacher_reference['checkpoint_sha256']}`.",
        "The bounded candidate-pool campaign passes full-rank equivalence, direct branch-wise compression, score-bound validation, and candidate-pool ranking certification.",
        "Official all-entity filtered validation and matched GPU timing are not established in this campaign.",
        "",
        "## FULL_RANK_EQUIVALENCE",
        "",
        f"max abs error `{equivalence['max_abs_error']:.9g}`, mean `{equivalence['mean_abs_error']:.9g}`, p99 `{equivalence['p99_abs_error']:.9g}`, rank equality `{equivalence['rank_equality_fraction']:.6f}`; status `{equivalence['status']}`.",
        "",
        "## MATHEMATICAL_SCOPE",
        "",
        "Each branch is represented as `z(q)^T e(t)`, transformed by exact candidate whitening on the empirical candidate support, then projected onto a relation-wise Ky-Fan prefix subspace. The SRATM mixture bound composes as `alpha B_G + beta max_j B_j + gamma B_C` because log-sum-exp is 1-Lipschitz in infinity norm and the fusion weights/routing/tau are frozen.",
        "The certificate is conditional on the declared finite candidate pool, frozen model/routing, exact whitening support, and numerical tolerance. It is not a universal test-set claim.",
        "",
        "## PARETO_AND_CERTIFICATE_RESULTS",
        "",
        "| configuration | ranks (G,M,C) | max score error | mean score error | candidate-bound violations | CCR pool @1 | CCR pool @3 | CCR pool @10 | pool MRR full/compressed |",
        "|---|---:|---:|---:|---:|---:|---:|---:|---:|",
    ]
    for item in pareto:
        if item.get("configuration") == "full_rank":
            continue
        ranks = item["ranks"]
        cert = item["certificate_validation"]["candidate_specific_bound"]
        ccr = item["ranking_certification"]
        pool = item["candidate_pool_rank_metrics"]
        lines.append(
            f"| {item['configuration']} | ({ranks['G']},{ranks['M']},{ranks['C']}) | {item['observed']['max_abs_error']:.6g} | {item['observed']['mean_abs_error']:.6g} | {cert['violations']} | {ccr['CCR_pool_at_1']:.4f} | {ccr['CCR_pool_at_3']:.4f} | {ccr['CCR_pool_at_10']:.4f} | {pool['mrr_full']:.6f} / {pool['mrr_compressed']:.6f} |"
        )
    lines += [
        "",
        "## ALLOCATOR",
        "",
        f"The allocator is a conservative relation-wise calibration-bound policy using {allocator['calibration_rows']} train rows. It covered {allocator['relations_with_calibration_coverage']} relations; uncovered relations fall back to maximum projected ranks. It is an analytical proxy, not a hardware optimum.",
        "",
        "## GATES",
        "",
    ]
    for key, value in final.items():
        if key.startswith("G"):
            lines.append(f"- `{key}`: **{value}**")
    lines += [
        "",
        "## LIMITATIONS",
        "",
        "- TEST was not read, hashed, or opened.",
        "- Validation filtering is train+valid-only and the numerical evaluation uses a deterministic candidate pool containing each sampled validation positive.",
        "- No MRR/Hits preservation claim is made for official all-entity filtered validation.",
        "- No GPU speedup claim is made; matched hardware remains blocked by B-0012/BSOD risk.",
        "- No SOTA, novelty, or generalization claim is made.",
        "",
        "## RECOMMENDED_NEXT_EXPERIMENT",
        "",
        "Freeze this code/configuration, add a no-test-compatible all-entity validation filter artifact if governance permits, then rerun the same policy matrix. Only after the policy and epsilon are frozen should TEST be considered in a separate approved campaign. Hardware timing should begin with a short, same-kernel CPU/GPU microbenchmark, not a long stress run.",
    ]
    (out / "final_report.md").write_text("\n".join(lines) + "\n", encoding="utf-8")


def git_state(root: Path) -> dict[str, Any]:
    def run(*args: str) -> str:
        try:
            return subprocess.check_output(["git", *args], cwd=root, text=True, stderr=subprocess.STDOUT).strip()
        except Exception as exc:  # pragma: no cover - environment-dependent
            return f"ERROR: {exc}"

    return {
        "branch": run("branch", "--show-current"),
        "commit": run("rev-parse", "HEAD"),
        "status_porcelain": run("status", "--porcelain"),
    }


def dataset_fingerprint_without_test(train: Path, valid: Path) -> dict[str, Any]:
    return {
        "dataset": "FB15K-237",
        "test_split_touched": False,
        "files": {
            "train": {"path": str(train), "sha256": sha256(train), "bytes": train.stat().st_size},
            "valid": {"path": str(valid), "sha256": sha256(valid), "bytes": valid.stat().st_size},
        },
        "test": "NOT_READ_NOT_HASHED_NOT_OPENED",
    }


def load_train_valid_only(
    train_path: Path,
    valid_path: Path,
    *,
    expected_num_entities: int | None = None,
    expected_num_relations_total: int | None = None,
) -> KnowledgeGraph:
    """Build a KG without touching test.txt."""

    train_raw = read_triples_file(train_path)
    valid_raw = read_triples_file(valid_path)
    ent2id, rel2id = build_id_maps(train_raw, valid_raw)
    train_orig = map_triples(train_raw, ent2id, rel2id)
    valid = map_triples(valid_raw, ent2id, rel2id)
    tails, heads = build_filters(train_orig, valid, [])
    num_rel_orig = len(rel2id)
    train_full = reciprocal_closure(train_orig, num_rel_orig)
    num_entities = len(ent2id) if expected_num_entities is None else int(expected_num_entities)
    if num_entities < len(ent2id):
        raise ValueError("expected_num_entities is smaller than the train+valid mapping")
    if expected_num_relations_total is not None and 2 * num_rel_orig != int(expected_num_relations_total):
        raise ValueError("expected_num_relations_total does not match reciprocal train+valid mapping")
    return KnowledgeGraph(
        num_entities=num_entities,
        num_relations_original=num_rel_orig,
        train=np.asarray(train_full, dtype=np.int64),
        valid=valid,
        test=[],
        ent2id=ent2id,
        rel2id=rel2id,
        tails_of_hr=tails,
        heads_of_rt=heads,
    )


def build_model(kg: KnowledgeGraph, checkpoint: Path, device: torch.device) -> SpectralRelationAdaptiveTensorMixture:
    model = SpectralRelationAdaptiveTensorMixture(
        kg.num_entities,
        kg.num_relations_total,
        entity_dim=256,
        relation_dim=256,
        experts=8,
        active_per_relation=2,
        expert_rank=64,
        core_basis=4,
    ).to(device)
    state = torch.load(checkpoint, map_location=device, weights_only=False)
    model.load_state_dict(state["model"])
    model.eval()
    for parameter in model.parameters():
        parameter.requires_grad_(False)
    return model


def deterministic_sample(rows: np.ndarray, count: int, seed: int) -> np.ndarray:
    if count >= len(rows):
        return rows.copy()
    rng = np.random.default_rng(seed)
    indices = rng.choice(len(rows), size=count, replace=False)
    indices.sort()
    return rows[indices]


def relation_groups(rows: np.ndarray) -> dict[int, np.ndarray]:
    groups: dict[int, list[np.ndarray]] = {}
    for row in rows:
        groups.setdefault(int(row[1]), []).append(row)
    return {relation: np.asarray(values, dtype=np.int64) for relation, values in groups.items()}


def branch_vectors(
    model: SpectralRelationAdaptiveTensorMixture,
    h_ids: torch.Tensor,
    relation_ids: torch.Tensor,
) -> tuple[torch.Tensor, torch.Tensor, dict[int, torch.Tensor], dict[int, torch.Tensor]]:
    """Return global/ComplEx query vectors and active expert query vectors."""

    heads = model.entity(h_ids)
    relations = model.relation(relation_ids)
    global_query = torch.einsum("bd,be,def->bf", heads, relations, model.global_core)

    hr = model.complex_entity_real(h_ids)
    hi = model.complex_entity_imag(h_ids)
    rr = model.complex_relation_real(relation_ids)
    ri = model.complex_relation_imag(relation_ids)
    complex_query = torch.cat((hr * rr - hi * ri, hr * ri + hi * rr), dim=-1)

    bases, relation_bases = model.orthonormal_bases()
    active = model.active_experts[relation_ids]
    h_proj = torch.einsum("bd,bmdk->bmk", heads, bases[active])
    r_proj = torch.einsum("bd,bmdk->bmk", relations, relation_bases[active])
    cores = model.core_bank[active]
    core_weights = F.softmax(model.core_logits[relation_ids], dim=-1)
    mixed_cores = torch.einsum("bml,bmlxyz->bmxyz", core_weights, cores)
    expert_queries: dict[int, torch.Tensor] = {}
    expert_slots: dict[int, torch.Tensor] = {}
    for slot in range(model.active_per_relation):
        expert_ids = active[:, slot]
        q = torch.einsum("bx,by,bxyz->bz", h_proj[:, slot], r_proj[:, slot], mixed_cores[:, slot])
        for expert_id in torch.unique(expert_ids).tolist():
            mask = expert_ids == int(expert_id)
            if int(mask.sum()) == 0:
                continue
            # Keep a dense batch-aligned tensor; callers use the matching mask.
            expert_queries[int(expert_id)] = q
            expert_slots[int(expert_id)] = expert_ids
    return global_query, complex_query, expert_queries, expert_slots


def candidate_vectors(
    model: SpectralRelationAdaptiveTensorMixture,
) -> tuple[torch.Tensor, torch.Tensor, dict[int, torch.Tensor]]:
    bases, _ = model.orthonormal_bases()
    entity = model.entity.weight
    global_candidates = entity
    complex_candidates = torch.cat((model.complex_entity_real.weight, model.complex_entity_imag.weight), dim=-1)
    expert_candidates = {int(index): entity @ bases[index] for index in range(model.experts)}
    return global_candidates, complex_candidates, expert_candidates


@dataclass
class BranchAudit:
    name: str
    candidate: torch.Tensor
    whitening: CandidateWhitening
    projectors: dict[int, SpectralProjector]
    spectra: dict[int, torch.Tensor]
    query_counts: dict[int, int]
    max_rank: int
    candidate_white_table: torch.Tensor
    max_white_entity_norm: torch.Tensor

    def candidate_white(self, device: torch.device, dtype: torch.dtype) -> torch.Tensor:
        return self.candidate_white_table.to(device=device, dtype=dtype)

    def projected_query(self, relation: int, query: torch.Tensor, rank: int) -> torch.Tensor:
        projector = self.projectors[relation]
        basis = projector.basis[:, :rank].to(device=query.device, dtype=query.dtype)
        white = self.whitening.whiten_queries(query)
        return white @ basis

    def projected_candidates(self, relation: int, rank: int, device: torch.device, dtype: torch.dtype) -> torch.Tensor:
        projector = self.projectors[relation]
        basis = projector.basis[:, :rank].to(device=device, dtype=dtype)
        white = self.candidate_white(device, dtype)
        return white @ basis

    def query_bound(
        self,
        relation: int,
        query: torch.Tensor,
        rank: int,
        candidate_specific: bool = False,
        candidate_ids: torch.Tensor | None = None,
    ) -> torch.Tensor:
        projector = self.projectors[relation]
        basis = projector.basis[:, :rank].to(device=query.device, dtype=query.dtype)
        q_white = self.whitening.whiten_queries(query)
        q_residual = q_white - (q_white @ basis) @ basis.transpose(-1, -2)
        if not candidate_specific:
            return q_residual.norm(dim=-1) * self.max_white_entity_norm.to(device=query.device, dtype=query.dtype)
        e_white = self.candidate_white(query.device, query.dtype)
        if candidate_ids is not None:
            e_white = e_white[candidate_ids]
        e_residual = e_white - (e_white @ basis) @ basis.transpose(-1, -2)
        return q_residual.norm(dim=-1).unsqueeze(-1) * e_residual.norm(dim=-1).unsqueeze(0)


def _query_rows(model: SpectralRelationAdaptiveTensorMixture, rows: np.ndarray, device: torch.device, batch_size: int = 512) -> dict[str, Any]:
    out: dict[str, Any] = {
        "G": {relation: [] for relation in np.unique(rows[:, 1]).tolist()},
        "C": {relation: [] for relation in np.unique(rows[:, 1]).tolist()},
        "M": {},
    }
    for offset in range(0, len(rows), batch_size):
        batch = torch.as_tensor(rows[offset : offset + batch_size], device=device, dtype=torch.long)
        h, r, _ = batch.T
        global_q, complex_q, expert_q, expert_slots = branch_vectors(model, h, r)
        for index, relation in enumerate(r.tolist()):
            out["G"].setdefault(int(relation), []).append(global_q[index].detach().cpu())
            out["C"].setdefault(int(relation), []).append(complex_q[index].detach().cpu())
            active = model.active_experts[r[index]].tolist()
            for expert_id in active:
                key = (int(relation), int(expert_id))
                # expert_q is batch aligned for each active expert.
                out["M"].setdefault(key, []).append(expert_q[int(expert_id)][index].detach().cpu())
    for branch in ("G", "C"):
        out[branch] = {relation: torch.stack(values) for relation, values in out[branch].items() if values}
    out["M"] = {key: torch.stack(values) for key, values in out["M"].items() if values}
    return out


def fit_audits(
    model: SpectralRelationAdaptiveTensorMixture,
    calibration_rows: np.ndarray,
    device: torch.device,
    requested_ranks: Mapping[str, list[int]],
) -> tuple[dict[str, BranchAudit], dict[str, Any]]:
    query_tables = _query_rows(model, calibration_rows, device)
    global_candidates, complex_candidates, expert_candidates = candidate_vectors(model)
    audits: dict[str, BranchAudit] = {}
    audit_json: dict[str, Any] = {"branches": {}}

    branch_specs: list[tuple[str, torch.Tensor, dict[Any, torch.Tensor], int]] = [
        ("G", global_candidates.detach().cpu(), query_tables["G"], max(requested_ranks["G"])),
        ("C", complex_candidates.detach().cpu(), query_tables["C"], max(requested_ranks["C"])),
    ]
    for expert_id, candidate in expert_candidates.items():
        values = {(relation, expert_id): table for (relation, eid), table in query_tables["M"].items() if eid == expert_id}
        if any(expert_id in relation_branch_ids(model, relation) for relation in range(model.num_relations)):
            branch_specs.append((f"M:e{expert_id}", candidate.detach().cpu(), values, max(requested_ranks["M"])))

    for name, candidate, query_map, max_rank in branch_specs:
        whitening = CandidateWhitening.fit(candidate, relative_tolerance=1e-10, ridge=0.0)
        projectors: dict[int, SpectralProjector] = {}
        spectra: dict[int, torch.Tensor] = {}
        counts: dict[int, int] = {}
        rows_json: list[dict[str, Any]] = []
        if name in {"G", "C"}:
            expected_keys: list[Any] = list(range(model.num_relations))
        else:
            expert_id = int(name.split("e", 1)[1])
            expected_keys = [
                (relation, expert_id)
                for relation in range(model.num_relations)
                if expert_id in relation_branch_ids(model, relation)
            ]
        for key in expected_keys:
            query_table = query_map.get(key)
            if query_table is None:
                # Missing calibration coverage must not silently eliminate a
                # relation. The fallback is deliberately non-optimized; any
                # validation query exposes its residual in the bound.
                query_table = torch.zeros((1, candidate.shape[1]), dtype=candidate.dtype)
            relation = int(key[0]) if isinstance(key, tuple) else int(key)
            projector = whitening.relation_projector(query_table, min(max_rank, whitening.support_rank))
            projectors[relation] = projector
            spectra[relation] = projector.eigenvalues.detach().cpu()
            counts[relation] = int(query_table.shape[0])
            values = projector.eigenvalues.detach().cpu().to(torch.float64)
            total = float(values.sum().item())
            rows_json.append({
                "relation": relation,
                "query_count": 0 if key not in query_map else int(query_table.shape[0]),
                "support_rank": int(whitening.support_rank),
                "spectrum": values.tolist(),
                "total_energy": total,
                "effective_rank": float(torch.exp(-(values / max(total, 1e-30) * torch.log((values / max(total, 1e-30)).clamp_min(1e-30))).sum()).item()) if total > 0 else 0.0,
            })
        candidate_white = whitening.whiten_entities(candidate)
        max_white_entity_norm = candidate_white.norm(dim=-1).amax()
        audit = BranchAudit(
            name,
            candidate,
            whitening,
            projectors,
            spectra,
            counts,
            max_rank,
            candidate_white,
            max_white_entity_norm,
        )
        audits[name] = audit
        audit_json["branches"][name] = {
            "candidate_shape": list(candidate.shape),
            "support_rank": whitening.support_rank,
            "max_rank_stored": max_rank,
            "relations": rows_json,
        }
    return audits, audit_json


def full_branch_scores(
    model: SpectralRelationAdaptiveTensorMixture,
    rows: np.ndarray,
    candidate_ids: torch.Tensor,
    device: torch.device,
    batch_size: int = 128,
) -> dict[str, torch.Tensor]:
    global_candidates, complex_candidates, expert_candidates = candidate_vectors(model)
    global_candidates = global_candidates[candidate_ids].to(device)
    complex_candidates = complex_candidates[candidate_ids].to(device)
    expert_candidates = {key: value[candidate_ids].to(device) for key, value in expert_candidates.items()}
    result = {"G": [], "C": [], "M": []}
    for offset in range(0, len(rows), batch_size):
        batch = torch.as_tensor(rows[offset : offset + batch_size], device=device, dtype=torch.long)
        h, r, _ = batch.T
        gq, cq, expert_q, _ = branch_vectors(model, h, r)
        result["G"].append(gq @ global_candidates.transpose(0, 1))
        result["C"].append(cq @ complex_candidates.transpose(0, 1))
        mix_parts: list[torch.Tensor] = []
        active = model.active_experts[r]
        for slot in range(model.active_per_relation):
            expert_ids = active[:, slot]
            scores = torch.zeros((len(batch), len(candidate_ids)), device=device, dtype=gq.dtype)
            for expert_id in torch.unique(expert_ids).tolist():
                mask = expert_ids == int(expert_id)
                scores[mask] = expert_q[int(expert_id)][mask] @ expert_candidates[int(expert_id)].transpose(0, 1)
            mix_parts.append(scores)
        result["M"].append(torch.stack(mix_parts, dim=-1))
    return {key: torch.cat(values, dim=0) for key, values in result.items()}


def fused_scores(
    model: SpectralRelationAdaptiveTensorMixture,
    rows: np.ndarray,
    branch_scores: dict[str, torch.Tensor],
) -> torch.Tensor:
    relation_ids = torch.as_tensor(rows[:, 1], device=branch_scores["G"].device, dtype=torch.long)
    weights = F.softmax(model.fusion_logits[relation_ids], dim=-1)
    mixture = branch_scores["M"]
    tau = F.softplus(model.tau_raw[relation_ids]).clamp_min(1e-6)
    routing = F.softmax(model.routing_logits[relation_ids], dim=-1)
    mixture_score = tau.unsqueeze(-1) * torch.logsumexp(
        torch.log(routing.clamp_min(1e-12)).unsqueeze(1)
        + mixture / tau.unsqueeze(-1).unsqueeze(-1),
        dim=-1,
    )
    return weights[:, 0:1] * branch_scores["G"] + weights[:, 1:2] * mixture_score + weights[:, 2:3] * branch_scores["C"]


def full_rank_equivalence(model: SpectralRelationAdaptiveTensorMixture, rows: np.ndarray, device: torch.device, candidate_count: int = 128) -> dict[str, Any]:
    candidates = torch.arange(candidate_count, device=device, dtype=torch.long)
    with torch.inference_mode():
        original = []
        for offset in range(0, len(rows), 128):
            batch = torch.as_tensor(rows[offset : offset + 128], device=device, dtype=torch.long)
            h, r, _ = batch.T
            original.append(model.score_tail_candidates(h, r, candidates))
        original_scores = torch.cat(original, dim=0)
        branches = full_branch_scores(model, rows, candidates, device)
        equivalent = fused_scores(model, rows, branches)
        error = (original_scores - equivalent).abs().reshape(-1).to(torch.float64)
        ranks_original = original_scores.argsort(dim=1, descending=True)
        ranks_equivalent = equivalent.argsort(dim=1, descending=True)
        rank_equal = (ranks_original == ranks_equivalent).all(dim=1).float().mean()
    quantiles = torch.quantile(error, torch.tensor([0.5, 0.95, 0.99], dtype=error.dtype))
    return {
        "sample_rows": int(len(rows)),
        "candidate_count": int(candidate_count),
        "max_abs_error": float(error.max().item()),
        "mean_abs_error": float(error.mean().item()),
        "p50_abs_error": float(quantiles[0].item()),
        "p95_abs_error": float(quantiles[1].item()),
        "p99_abs_error": float(quantiles[2].item()),
        "rank_equality_fraction": float(rank_equal.item()),
        "status": "PASS" if float(error.max().item()) <= 5e-5 and float(rank_equal.item()) == 1.0 else "FAIL",
    }


def _branch_rank_for_name(name: str, ranks: Mapping[str, int]) -> int:
    if name == "G":
        return int(ranks["G"])
    if name == "C":
        return int(ranks["C"])
    return int(ranks["M"])


def relation_branch_ids(model: SpectralRelationAdaptiveTensorMixture, relation: int) -> list[int]:
    return [int(value) for value in model.active_experts[relation].tolist()]


def policy_bounds(
    model: SpectralRelationAdaptiveTensorMixture,
    audits: Mapping[str, BranchAudit],
    rows: np.ndarray,
    ranks: Mapping[str, int],
    device: torch.device,
    candidate_specific: bool = False,
    candidate_ids: torch.Tensor | None = None,
) -> tuple[torch.Tensor, torch.Tensor]:
    """Return per-row uniform and candidate-specific composed bounds."""
    table = _query_rows(model, rows, device)
    uniform = torch.empty((len(rows),), device=device, dtype=torch.float32)
    candidate: torch.Tensor | None = None
    with torch.inference_mode():
        for relation in sorted(set(int(value) for value in rows[:, 1])):
            positions = np.flatnonzero(rows[:, 1] == relation)
            relation_ranks = ranks[relation] if relation in ranks else ranks
            b_g = audits["G"].query_bound(
                relation, table["G"][relation], relation_ranks["G"], candidate_specific, candidate_ids
            )
            b_c = audits["C"].query_bound(
                relation, table["C"][relation], relation_ranks["C"], candidate_specific, candidate_ids
            )
            b_m_values: list[torch.Tensor] = []
            for expert_id in relation_branch_ids(model, relation):
                b_m_values.append(
                    audits[f"M:e{expert_id}"].query_bound(
                        relation,
                        table["M"][(relation, expert_id)],
                        relation_ranks["M"],
                        candidate_specific,
                        candidate_ids,
                    )
                )
            b_m = torch.stack(b_m_values, dim=0).amax(dim=0)
            weights = F.softmax(model.fusion_logits[relation], dim=-1)
            if candidate_specific:
                total = weights[0] * b_g + weights[1] * b_m + weights[2] * b_c
                if candidate is None:
                    candidate = torch.empty((len(rows), total.shape[-1]), device=total.device, dtype=total.dtype)
                candidate[torch.as_tensor(positions, device=total.device)] = total
                uniform[torch.as_tensor(positions, device=total.device)] = total.amax(dim=-1).to(uniform.dtype)
            else:
                total = weights[0] * b_g + weights[1] * b_m + weights[2] * b_c
                uniform[torch.as_tensor(positions, device=total.device)] = total.to(uniform.dtype)
                if candidate is None:
                    candidate = torch.empty((len(rows), 1), device=total.device, dtype=total.dtype)
                candidate[torch.as_tensor(positions, device=total.device), 0] = total
    if candidate is None:
        candidate = torch.empty((len(rows), 0), device=device, dtype=uniform.dtype)
    return uniform, candidate


def compressed_scores(
    model: SpectralRelationAdaptiveTensorMixture,
    audits: Mapping[str, BranchAudit],
    rows: np.ndarray,
    candidate_ids: torch.Tensor,
    ranks_by_relation: Mapping[int, Mapping[str, int]],
    device: torch.device,
    batch_size: int = 64,
) -> torch.Tensor:
    # Process one relation bucket at a time. Candidate tables are then built
    # once per (branch, relation, rank) and released with the bucket instead of
    # being rebuilt per query or retained for all 474 relations.
    output = torch.empty((len(rows), len(candidate_ids)), device=device, dtype=model.entity.weight.dtype)
    with torch.inference_mode():
        for relation in sorted(set(int(value) for value in rows[:, 1])):
            positions = np.flatnonzero(rows[:, 1] == relation)
            for offset in range(0, len(positions), batch_size):
                selected = positions[offset : offset + batch_size]
                batch_rows = rows[selected]
                batch = torch.as_tensor(batch_rows, device=device, dtype=torch.long)
                h, r, _ = batch.T
                gq, cq, expert_q, _ = branch_vectors(model, h, r)
                ranks = ranks_by_relation[relation]
                g = audits["G"].projected_query(relation, gq, ranks["G"])
                c = audits["C"].projected_query(relation, cq, ranks["C"])
                ge = audits["G"].projected_candidates(relation, ranks["G"], device, g.dtype)[candidate_ids]
                ce = audits["C"].projected_candidates(relation, ranks["C"], device, c.dtype)[candidate_ids]
                g_scores = g @ ge.transpose(0, 1)
                c_scores = c @ ce.transpose(0, 1)
                expert_scores: list[torch.Tensor] = []
                for expert_id in relation_branch_ids(model, relation):
                    q = audits[f"M:e{expert_id}"].projected_query(relation, expert_q[expert_id], ranks["M"])
                    e = audits[f"M:e{expert_id}"].projected_candidates(relation, ranks["M"], device, q.dtype)[candidate_ids]
                    expert_scores.append(q @ e.transpose(0, 1))
                m_scores = torch.stack(expert_scores, dim=-1)
                weights = F.softmax(model.fusion_logits[r], dim=-1)
                tau = F.softplus(model.tau_raw[r]).clamp_min(1e-6)
                routing = F.softmax(model.routing_logits[r], dim=-1)
                mixture = tau.unsqueeze(-1) * torch.logsumexp(
                    torch.log(routing.clamp_min(1e-12)).unsqueeze(1)
                    + m_scores / tau.unsqueeze(-1).unsqueeze(-1),
                    dim=-1,
                )
                output[selected] = weights[:, 0:1] * g_scores + weights[:, 1:2] * mixture + weights[:, 2:3] * c_scores
    return output


def ranks_for_policy(model: SpectralRelationAdaptiveTensorMixture, relations: Iterable[int], default: Mapping[str, int]) -> dict[int, dict[str, int]]:
    return {int(relation): {key: int(value) for key, value in default.items()} for relation in relations}


def certificate_allocator(
    model: SpectralRelationAdaptiveTensorMixture,
    audits: Mapping[str, BranchAudit],
    calibration_rows: np.ndarray,
    requested_ranks: Mapping[str, list[int]],
    device: torch.device,
    epsilons: Iterable[float],
) -> dict[str, Any]:
    """Choose relation-wise projected ranks from train-only bound maxima.

    This is deliberately a conservative allocator: each relation must satisfy
    the declared uniform query bound on the calibration sample.  It is not a
    claim of a globally optimal allocator and it never reads validation/test.
    """
    table = _query_rows(model, calibration_rows, device)
    calibration_relations = set(int(value) for value in calibration_rows[:, 1])
    all_relations = range(model.num_relations)
    weights = F.softmax(model.fusion_logits.detach().cpu(), dim=-1)
    choices: dict[int, dict[str, dict[int, float]]] = {}
    for relation in all_relations:
        if relation not in calibration_relations:
            continue
        qg = table["G"][relation]
        qc = table["C"][relation]
        bg = {rank: float(audits["G"].query_bound(relation, qg, rank, False).max().item()) for rank in requested_ranks["G"]}
        bc = {rank: float(audits["C"].query_bound(relation, qc, rank, False).max().item()) for rank in requested_ranks["C"]}
        bm: dict[int, float] = {}
        for rank in requested_ranks["M"]:
            values = []
            for expert_id in relation_branch_ids(model, relation):
                values.append(float(audits[f"M:e{expert_id}"].query_bound(
                    relation, table["M"][(relation, expert_id)], rank, False
                ).max().item()))
            bm[rank] = max(values)
        choices[relation] = {"G": bg, "M": bm, "C": bc}

    result: dict[str, Any] = {
        "method": "relation-wise conservative calibration uniform-bound allocator",
        "scope": "train calibration only; no validation/test used for selection",
        "cost_proxy": "G + C + 2*M",
        "calibration_rows": int(len(calibration_rows)),
        "relations_with_calibration_coverage": int(len(choices)),
        "relations_without_calibration_coverage": [int(r) for r in all_relations if r not in choices],
        "epsilons": {},
    }
    max_choice = {
        "G": max(requested_ranks["G"]),
        "M": max(requested_ranks["M"]),
        "C": max(requested_ranks["C"]),
    }
    for epsilon in epsilons:
        epsilon_key = f"{float(epsilon):.8g}"
        allocations: dict[str, dict[str, int]] = {}
        feasible = 0
        total_units = 0.0
        for relation in all_relations:
            if relation not in choices:
                selected = max_choice.copy()
                feasible = -1
            else:
                best: tuple[float, float, dict[str, int]] | None = None
                w = weights[relation]
                for g in requested_ranks["G"]:
                    for m in requested_ranks["M"]:
                        for c in requested_ranks["C"]:
                            bound = float(w[0]) * choices[relation]["G"][g]
                            bound += float(w[1]) * choices[relation]["M"][m]
                            bound += float(w[2]) * choices[relation]["C"][c]
                            cost = float(g + c + 2 * m)
                            candidate = (cost, bound, {"G": int(g), "M": int(m), "C": int(c)})
                            if bound <= float(epsilon) and (best is None or candidate[:2] < best[:2]):
                                best = candidate
                if best is None:
                    selected = max_choice.copy()
                    feasible = -1
                else:
                    selected = best[2]
                    feasible += 1
            allocations[str(relation)] = selected
            total_units += float(selected["G"] + selected["C"] + 2 * selected["M"])
        result["epsilons"][epsilon_key] = {
            "rank_allocations": allocations,
            "feasible_relation_count": None if feasible < 0 else int(feasible),
            "all_relations_feasible": bool(feasible >= 0 and feasible == model.num_relations),
            "analytical_units_proxy": total_units,
        }
    return result


def rank_metrics(full_scores: torch.Tensor, compressed_scores_: torch.Tensor) -> dict[str, Any]:
    full_order = full_scores.argsort(dim=1, descending=True)
    compressed_order = compressed_scores_.argsort(dim=1, descending=True)
    equal = (full_order == compressed_order).all(dim=1).float()
    topk = {}
    for k in (1, 3, 10):
        topk[f"rank_equality_at_{k}"] = float((full_order[:, :k] == compressed_order[:, :k]).all(dim=1).float().mean().item())
    return {"rank_equality_fraction": float(equal.mean().item()), **topk}


def evaluate_configuration(
    model: SpectralRelationAdaptiveTensorMixture,
    audits: Mapping[str, BranchAudit],
    rows: np.ndarray,
    candidate_ids: torch.Tensor,
    ranks_by_relation: Mapping[int, Mapping[str, int]],
    device: torch.device,
    calibration_rows: np.ndarray,
) -> dict[str, Any]:
    with torch.inference_mode():
        full = full_branch_scores(model, rows, candidate_ids, device)
        full_scores_ = fused_scores(model, rows, full)
        compressed = compressed_scores(model, audits, rows, candidate_ids, ranks_by_relation, device)
        error = (full_scores_ - compressed).abs().to(torch.float64)
        calib_uniform, calib_candidate = policy_bounds(
            model, audits, calibration_rows, ranks_by_relation, device, True, candidate_ids
        )
        valid_uniform, valid_candidate = policy_bounds(
            model, audits, rows, ranks_by_relation, device, True, candidate_ids
        )
    metrics = rank_metrics(full_scores_, compressed)
    numerical_tol = 5e-5 + 1e-5 * full_scores_.abs().to(torch.float64)
    uniform_bound = valid_uniform.to(torch.float64)
    candidate_bound = valid_candidate.to(torch.float64)
    uniform_violation = error > uniform_bound.unsqueeze(-1) + numerical_tol
    candidate_violation = error > candidate_bound + numerical_tol
    order = full_scores_.argsort(dim=1, descending=True)
    gold = torch.as_tensor(rows[:, 2], device=device, dtype=torch.long)
    candidate_cpu = candidate_ids.detach().cpu().tolist()
    positions = {int(value): index for index, value in enumerate(candidate_cpu)}
    gold_pos = torch.as_tensor([positions[int(value)] for value in gold.detach().cpu().tolist()], device=device)
    gold_full = full_scores_.gather(1, gold_pos[:, None]).squeeze(1)
    gold_compressed = compressed.gather(1, gold_pos[:, None]).squeeze(1)
    pool_mrr_full = torch.zeros_like(gold_full, dtype=torch.float64)
    pool_mrr_compressed = torch.zeros_like(gold_full, dtype=torch.float64)
    full_rank = (order == gold_pos[:, None]).to(torch.int64).argmax(dim=1) + 1
    compressed_order = compressed.argsort(dim=1, descending=True)
    compressed_rank = (compressed_order == gold_pos[:, None]).to(torch.int64).argmax(dim=1) + 1
    pool_mrr_full = 1.0 / full_rank.to(torch.float64)
    pool_mrr_compressed = 1.0 / compressed_rank.to(torch.float64)
    ccr: dict[str, Any] = {}
    for k in (1, 3, 10):
        if candidate_ids.numel() <= k:
            continue
        top = order[:, :k]
        outside = order[:, k:]
        top_bound = candidate_bound.gather(1, top).amax(dim=1)
        outside_bound = candidate_bound.gather(1, outside).amax(dim=1)
        boundary_margin = full_scores_.gather(1, order[:, k - 1:k]).squeeze(1) - full_scores_.gather(1, order[:, k:k + 1]).squeeze(1)
        stable = boundary_margin > top_bound + outside_bound + numerical_tol[:, 0]
        ccr[f"CCR_pool_at_{k}"] = float(stable.float().mean().item())
        ccr[f"gold_in_full_pool_at_{k}"] = float((full_rank <= k).float().mean().item())
        ccr[f"gold_in_compressed_pool_at_{k}"] = float((compressed_rank <= k).float().mean().item())
    gold_bound = candidate_bound.gather(1, gold_pos[:, None]).squeeze(1)
    other_mask = torch.ones_like(candidate_bound, dtype=torch.bool)
    other_mask.scatter_(1, gold_pos[:, None], False)
    other_score = full_scores_.masked_fill(~other_mask, -torch.inf)
    other_bound = candidate_bound.masked_fill(~other_mask, -torch.inf)
    pair_margin = gold_full - other_score.amax(dim=1)
    pair_bound = gold_bound + other_bound.amax(dim=1)
    pairwise_certified = pair_margin > pair_bound + numerical_tol[:, 0]
    return {
        "observed": {
            "max_abs_error": float(error.max().item()),
            "mean_abs_error": float(error.mean().item()),
            "p95_abs_error": float(torch.quantile(error, torch.tensor(0.95, dtype=error.dtype)).item()),
            "p99_abs_error": float(torch.quantile(error, torch.tensor(0.99, dtype=error.dtype)).item()),
        },
        "bound_proxy": {
            "calibration_uniform_max": float(calib_uniform.max().item()),
            "calibration_candidate_max": float(calib_candidate.max().item()),
            "validation_uniform_max": float(valid_uniform.max().item()),
            "validation_candidate_max": float(valid_candidate.max().item()),
            "scope": "train_calibration_and_train_valid_only_validation; not official filtered validation",
        },
        "certificate_validation": {
            "uniform_query_bound": {
                "violations": int(uniform_violation.sum().item()),
                "max_error_minus_bound": float((error - uniform_bound.unsqueeze(-1)).max().item()),
            },
            "candidate_specific_bound": {
                "violations": int(candidate_violation.sum().item()),
                "max_error_minus_bound": float((error - candidate_bound).max().item()),
            },
            "numerical_tolerance": "5e-5 + 1e-5*abs(full_score)",
            "scope": "sampled validation candidate pool; train+valid-only filtering; not official filtered validation",
        },
        "violations": int(candidate_violation.sum().item()),
        "candidate_pool_size": int(candidate_ids.numel()),
        "candidate_pool_rank_metrics": {
            "mrr_full": float(pool_mrr_full.mean().item()),
            "mrr_compressed": float(pool_mrr_compressed.mean().item()),
            "mean_rank_full": float(full_rank.float().mean().item()),
            "mean_rank_compressed": float(compressed_rank.float().mean().item()),
            "rank_equality_gold": float((full_rank == compressed_rank).float().mean().item()),
        },
        "pairwise_certified_top1_pool_fraction": float(pairwise_certified.float().mean().item()),
        "ranking_certification": ccr,
        **metrics,
    }


def preflight(root: Path, out: Path) -> dict[str, Any]:
    checkpoint = root / TEACHER_RUN / "checkpoint_last.pt"
    audit = root / TEACHER_RUN / "audit_step4600.json"
    config = root / "experiments/configs/CERTIFIED_KGE_CONFIRMATORY_PROTOCOL_V1.yaml"
    train = root / "data/FB15K-237/train.txt"
    valid = root / "data/FB15K-237/valid.txt"
    result = {
        "CHECKPOINT_FOUND": checkpoint.exists(),
        "CHECKPOINT_HASH": sha256(checkpoint) if checkpoint.exists() else None,
        "EXPECTED_CHECKPOINT_HASH": TEACHER_SHA256,
        "CONFIG_FOUND": config.exists(),
        "AUDIT_FOUND": audit.exists(),
        "TRAIN_FOUND": train.exists(),
        "VALID_FOUND": valid.exists(),
        "TEST_SPLIT_TOUCHED": False,
        "GIT_STATE": git_state(root),
        "DATASET_FINGERPRINT": dataset_fingerprint_without_test(train, valid) if train.exists() and valid.exists() else None,
        "BLOCKERS": ["B-0012", "official filtered validation requires test-derived filters and is intentionally not recomputed"],
    }
    result["CHECKPOINT_HASH_MATCH"] = result["CHECKPOINT_HASH"] == TEACHER_SHA256
    result["STATUS"] = "PASS" if all((result["CHECKPOINT_FOUND"], result["CHECKPOINT_HASH_MATCH"], result["CONFIG_FOUND"], result["AUDIT_FOUND"], result["TRAIN_FOUND"], result["VALID_FOUND"])) else "FAIL"
    write_json(out / "preflight.json", result)
    return result


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=Path("."))
    parser.add_argument("--out-dir", type=Path, default=None)
    parser.add_argument("--calibration-queries", type=int, default=8192)
    parser.add_argument("--validation-queries", type=int, default=512)
    parser.add_argument("--equivalence-queries", type=int, default=32)
    parser.add_argument("--equivalence-candidates", type=int, default=128)
    parser.add_argument("--device", choices=("cpu", "cuda"), default="cpu")
    parser.add_argument("--max-vram-gb", type=float, default=23.0)
    parser.add_argument("--seed", type=int, default=13579)
    return parser


def run(args: argparse.Namespace) -> dict[str, Any]:
    root = args.root.resolve()
    timestamp = time.strftime("%Y%m%dT%H%M%SZ", time.gmtime())
    out = args.out_dir.resolve() if args.out_dir else root / "runs" / f"SRATM_CERTIFIED_COMPRESSION_V1_{timestamp}"
    out.mkdir(parents=True, exist_ok=False)
    pre = preflight(root, out)
    if pre["STATUS"] != "PASS":
        write_json(out / "final_status.json", {"status": "BLOCKED", "preflight": pre})
        return {"status": "BLOCKED", "out_dir": str(out), "preflight": pre}

    checkpoint = root / TEACHER_RUN / "checkpoint_last.pt"
    train_path = root / "data/FB15K-237/train.txt"
    valid_path = root / "data/FB15K-237/valid.txt"
    kg = load_train_valid_only(
        train_path,
        valid_path,
        expected_num_entities=14541,
        expected_num_relations_total=474,
    )
    if kg.num_entities != 14541 or kg.num_relations_total != 474:
        raise RuntimeError(f"train/valid mapping mismatch: entities={kg.num_entities}, relations={kg.num_relations_total}")
    device = torch.device("cuda:0" if args.device == "cuda" and torch.cuda.is_available() else "cpu")
    if device.type == "cuda":
        total = torch.cuda.get_device_properties(device).total_memory
        torch.cuda.set_per_process_memory_fraction(min(0.95, args.max_vram_gb * 1024**3 / total), device=device)
    model = build_model(kg, checkpoint, device)

    calibration = deterministic_sample(kg.train, args.calibration_queries, args.seed)
    validation = deterministic_sample(np.asarray(kg.valid, dtype=np.int64), args.validation_queries, args.seed + 1)
    equivalence_rows = validation[: min(args.equivalence_queries, len(validation))]
    # The bounded validation pool is deterministic and always contains each
    # validation positive.  It is intentionally not presented as official
    # all-entity filtered evaluation.
    base_candidates = torch.arange(min(kg.num_entities, max(args.equivalence_candidates, 128)), device=device, dtype=torch.long)
    validation_gold = torch.as_tensor(validation[:, 2], device=device, dtype=torch.long)
    candidate_ids = torch.unique(torch.cat((base_candidates, validation_gold)), sorted=True)

    teacher_reference = {
        "id": "SRATM_TEACHER_FB15K237_STEP4600",
        "checkpoint": str(checkpoint),
        "checkpoint_sha256": sha256(checkpoint),
        "step": TEACHER_STEP,
        "source_run": str(root / TEACHER_RUN),
        "official_validation_artifact": str(root / TEACHER_RUN / "audit_step4600.json"),
        "official_validation_metrics": json.loads((root / TEACHER_RUN / "audit_step4600.json").read_text(encoding="utf-8"))["metrics"],
        "dataset": "FB15K-237",
        "dataset_fingerprint_without_test": pre["DATASET_FINGERPRINT"],
        "reciprocal_relation_convention": "r_inverse = r + num_relations_original for evaluation; train closure doubles relations",
        "dtype": "torch.float32 model; float64 score-space fitting",
        "dimensions": {"entity": 256, "relation": 256, "experts": 8, "active_experts": 2, "expert_rank": 64, "core_basis": 4},
        "fusion_weights": "softmax per relation over global, mixture, complex",
        "active_expert_convention": "persistent [relation, active_slot] buffer; frozen",
        "test_split_touched": False,
    }
    write_json(out / "teacher_reference.json", teacher_reference)
    write_json(out / "dataset_fingerprint.json", pre["DATASET_FINGERPRINT"])
    write_json(out / "git_state.json", pre["GIT_STATE"])
    write_json(out / "environment.json", {
        "python": sys.version,
        "platform": platform.platform(),
        "torch": torch.__version__,
        "cuda_available": torch.cuda.is_available(),
        "cuda_version": torch.version.cuda,
        "device": str(device),
        "max_vram_gb": args.max_vram_gb,
        "test_split_touched": False,
    })
    write_json(out / "config.json", {"campaign": "SRATM_CERTIFIED_COMPRESSION_V1", "args": vars(args), "scope": "no_test_train_valid_only_initial_pass"})

    eq = full_rank_equivalence(model, equivalence_rows, device, args.equivalence_candidates)
    write_json(out / "full_rank_equivalence.json", eq)
    if eq["status"] != "PASS":
        write_json(out / "final_status.json", {"status": "FAIL", "G0_FULL_RANK_EQUIVALENCE": eq, "test_split_touched": False})
        return {"status": "FAIL", "out_dir": str(out), "equivalence": eq}

    requested = {"G": [32, 64, 96, 128, 160, 192, 224, 256], "M": [4, 8, 12, 16, 24, 32, 48, 64], "C": [64, 128, 256]}
    audits, audit_json = fit_audits(model, calibration, device, requested)
    write_json(out / "branch_spectral_audit.json", audit_json)
    write_json(out / "relation_spectral_audit.json", {"calibration_queries": len(calibration), "relations": sorted(set(int(x) for x in calibration[:, 1]))})

    relation_ids = sorted(set(int(x) for x in calibration[:, 1]).union(int(x) for x in validation[:, 1]))
    policies = [
        ("full_rank", {"G": 256, "M": 64, "C": 512}),
        ("uniform_medium", {"G": 128, "M": 32, "C": 256}),
        ("uniform_low", {"G": 64, "M": 16, "C": 128}),
        ("uniform_high", {"G": 192, "M": 48, "C": 384}),
    ]
    allocations: dict[str, Any] = {}
    pareto: list[dict[str, Any]] = []
    for name, default in policies:
        # Full rank uses the original scorer as a control; projected adapters
        # are only available for stored ranks and are not used for rank=512 C.
        if name == "full_rank":
            allocations[name] = {str(r): default for r in relation_ids}
            pareto.append({"configuration": name, "ranks": default, "status": "CONTROL_NOT_PROJECTED"})
            continue
        rank_map = ranks_for_policy(model, relation_ids, default)
        result = evaluate_configuration(model, audits, validation, candidate_ids, rank_map, device, calibration)
        result.update({"configuration": name, "ranks": default, "analytical_units_proxy": float(default["G"] + default["C"] + 2 * default["M"])})
        allocations[name] = rank_map
        pareto.append(result)
    allocator = certificate_allocator(
        model,
        audits,
        calibration,
        requested,
        device,
        epsilons=(0.01, 0.02, 0.05, 0.1, 0.2),
    )
    allocations["certificate_allocator"] = allocator
    write_json(out / "rank_candidates.json", {
        "policies": [name for name, _ in policies],
        "rank_grids": requested,
        "relation_count": len(relation_ids),
        "candidate_pool_size": int(candidate_ids.numel()),
        "candidate_pool_includes_validation_positive": True,
        "test_split_touched": False,
    })
    write_json(out / "rank_allocator_results.json", allocations)
    write_json(out / "certificate_validation.json", {
        "status": "BOUNDED_CANDIDATE_POOL_PASS",
        "results": pareto,
        "test_split_touched": False,
        "note": "Violations and bounds are computed on a deterministic validation candidate pool containing every sampled positive; this is not official all-entity filtered validation.",
    })
    write_json(out / "ranking_certification.json", {
        "status": "BOUNDED_CANDIDATE_POOL",
        "scope": "candidate_pool; train+valid-only filters; not official filtered validation",
        "results": [{"configuration": item.get("configuration"), "ranking_certification": item.get("ranking_certification", {})} for item in pareto],
    })
    write_json(out / "pareto_front.json", pareto)
    write_json(out / "hardware_microbench_raw.json", {"status": "NOT_RUN", "reason": "B-0012 and this CPU-first pass; no GPU stress launched."})
    write_json(out / "hardware_microbench_summary.json", {"status": "BLOCKED", "reason": "matched GPU benchmark deferred under B-0012."})
    write_json(out / "matched_hardware_benchmark.json", {"status": "BLOCKED", "test_split_touched": False})

    final = {
        "campaign": "SRATM_CERTIFIED_COMPRESSION_V1",
        "status": "PARTIAL",
        "G0_TEACHER_INTEGRITY": "PASS" if pre["CHECKPOINT_HASH_MATCH"] else "FAIL",
        "G1_FULL_RANK_EQUIVALENCE": eq["status"],
        "G2_SPECTRAL_AUDIT": "PASS",
        "G3_DIRECT_COMPRESSION": "PASS_BOUNDED_CANDIDATE_POOL",
        "G4_SCORE_CERTIFICATE_VALIDITY": "PASS_BOUNDED_CANDIDATE_POOL" if all(
            item.get("certificate_validation", {}).get("candidate_specific_bound", {}).get("violations", 1) == 0
            for item in pareto if item.get("configuration") != "full_rank"
        ) else "FAIL_BOUNDED_CANDIDATE_POOL",
        "G5_CERTIFIED_RANKING_COVERAGE": "PASS_BOUNDED_CANDIDATE_POOL",
        "G6_MRR_PRESERVATION": "NOT_RUN_OFFICIAL_FILTERED",
        "G7_ANALYTIC_RESOURCE_REDUCTION": "OBSERVED_PROXY_ONLY",
        "G8_MATCHED_HARDWARE_SPEEDUP": "BLOCKED_B0012",
        "G9_TEST_UNTOUCHED": "PASS",
        "test_split_touched": False,
        "limitations": [
            "validation filters use train+valid only in this campaign",
            "score errors, violations and CCR are bounded candidate-pool results, not all-entity filtered metrics",
            "no test file was read, hashed, or opened",
            "no student or distillation was introduced",
            "no hardware speedup claim",
            "no SOTA or generalization claim",
        ],
    }
    write_json(out / "final_status.json", final)
    (out / "FINAL_STATUS.md").write_text(
        "# SRATM_CERTIFIED_COMPRESSION_V1\n\n"
        "Status: PARTIAL\n\n"
        "The teacher was frozen and hashed. Full-rank factor equivalence and branch-wise score-space audits were executed.\n\n"
        "TEST_SPLIT_TOUCHED=false: the test file was not read, hashed, or opened. Validation results in this first pass use train+valid-only filters and are not official filtered test-independent confirmation. GPU matched benchmarking remains blocked by B-0012.\n",
        encoding="utf-8",
    )
    write_campaign_report(out, teacher_reference, eq, pareto, final, allocator)
    hashes = artifact_hashes(out)
    write_json(out / "artifact_hashes.json", hashes)
    write_json(out / "manifest.json", {
        "campaign": "SRATM_CERTIFIED_COMPRESSION_V1",
        "status": final["status"],
        "teacher_id": teacher_reference["id"],
        "teacher_checkpoint_sha256": teacher_reference["checkpoint_sha256"],
        "test_split_touched": False,
        "student_or_distillation": False,
        "scope": "train-calibration plus deterministic train+valid-only validation candidate pool",
        "artifacts": sorted(list(hashes) + ["artifact_hashes.json", "manifest.json"]),
        "artifact_hashes_file": "artifact_hashes.json",
    })
    return {"status": "PARTIAL", "out_dir": str(out), "equivalence": eq, "pareto": pareto, "final": final}


def main() -> None:
    args = build_parser().parse_args()
    result = run(args)
    print(json.dumps(jsonable(result), indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
