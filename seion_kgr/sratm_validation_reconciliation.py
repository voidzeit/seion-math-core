"""Sealed differential audit for the SRATM VALID protocol.

This audit never loads or hashes TEST.  It compares the current G6 branch
formula against the frozen model scorer, checks positive/gold extraction and
reciprocal filtering, and records the code-level evidence relevant to the
historical 0.6116475 versus sealed TRAIN+VALID-only discrepancy.
"""

from __future__ import annotations

import argparse
import json
import platform
import sys
from pathlib import Path
from typing import Any

import numpy as np
import torch
import torch.nn.functional as F

from .data import KnowledgeGraph, build_filters, reciprocal_closure
from .evaluate import evaluate
from .sratm_certified_compression import (
    TEACHER_RUN,
    branch_vectors,
    build_model,
    candidate_vectors,
    git_state,
    load_train_valid_only,
    sha256,
    write_json,
)


def _branch_full_scores(model: Any, h: torch.Tensor, r: torch.Tensor, candidates: torch.Tensor) -> torch.Tensor:
    global_candidates, complex_candidates, expert_candidates = candidate_vectors(model)
    output = torch.empty((len(h), len(candidates)), device=h.device, dtype=model.entity.weight.dtype)
    for relation in torch.unique(r).tolist():
        mask = r == int(relation)
        gq, cq, expert_q, _ = branch_vectors(model, h[mask], r[mask])
        weights = F.softmax(model.fusion_logits[int(relation)], dim=-1)
        tau = F.softplus(model.tau_raw[int(relation)]).clamp_min(1e-6)
        routing = F.softmax(model.routing_logits[int(relation)], dim=-1)
        g = gq @ global_candidates[candidates].transpose(0, 1)
        c = cq @ complex_candidates[candidates].transpose(0, 1)
        active = model.active_experts[int(relation)].tolist()
        m_parts = [expert_q[int(expert_id)] @ expert_candidates[int(expert_id)][candidates].transpose(0, 1) for expert_id in active]
        m = torch.stack(m_parts, dim=-1)
        mix = tau * torch.logsumexp(torch.log(routing.clamp_min(1e-12)).view(1, 1, -1) + m / tau, dim=-1)
        output[mask] = weights[0] * g + weights[1] * mix + weights[2] * c
    return output


def _rank_from_scores(scores: torch.Tensor, gold: torch.Tensor, *, half_ties: bool) -> torch.Tensor:
    gold_score = scores.gather(1, gold[:, None]).squeeze(1)
    better = (scores > gold_score[:, None]).sum(dim=1).float()
    if not half_ties:
        return better + 1.0
    ties = torch.isclose(scores, gold_score[:, None], atol=1e-7, rtol=0.0).sum(dim=1).float() - 1.0
    return better + 0.5 * ties.clamp_min(0.0) + 1.0


def _train_only_kg(kg: KnowledgeGraph) -> KnowledgeGraph:
    original_train = kg.train[: len(kg.train) // 2]
    tails, heads = build_filters(original_train.tolist(), [], [])
    return KnowledgeGraph(
        num_entities=kg.num_entities,
        num_relations_original=kg.num_relations_original,
        train=kg.train,
        valid=kg.valid,
        test=[],
        ent2id=kg.ent2id,
        rel2id=kg.rel2id,
        tails_of_hr=tails,
        heads_of_rt=heads,
    )


def run(args: argparse.Namespace) -> dict[str, Any]:
    root = args.root.resolve()
    out = args.out_dir.resolve()
    out.mkdir(parents=True, exist_ok=False)
    device = torch.device("cpu")
    kg = load_train_valid_only(
        root / "data/FB15K-237/train.txt",
        root / "data/FB15K-237/valid.txt",
        expected_num_entities=14541,
        expected_num_relations_total=474,
    )
    model = build_model(kg, root / TEACHER_RUN / "checkpoint_last.pt", device)
    checkpoint_inventory: dict[str, Any] = {}
    for checkpoint_name in ("checkpoint_last.pt", "checkpoint_best.pt"):
        checkpoint_path = root / TEACHER_RUN / checkpoint_name
        checkpoint = torch.load(checkpoint_path, map_location="cpu", weights_only=False)
        validation_history = [
            item for item in checkpoint.get("history", [])
            if isinstance(item, dict) and isinstance(item.get("valid"), dict)
        ]
        checkpoint_inventory[checkpoint_name] = {
            "sha256": sha256(checkpoint_path),
            "bytes": checkpoint_path.stat().st_size,
            "embedded_step": checkpoint.get("step"),
            "embedded_epoch": checkpoint.get("epoch"),
            "history_entries": len(checkpoint.get("history", [])),
            "last_recorded_valid": validation_history[-1] if validation_history else None,
        }
    rows = np.asarray(kg.valid[: args.rows], dtype=np.int64)
    h, r, gold = torch.as_tensor(rows, dtype=torch.long).T
    candidate_values = sorted(set(range(min(args.candidates, kg.num_entities))) | set(int(value) for value in gold.tolist()))
    candidates = torch.as_tensor(candidate_values, dtype=torch.long)
    official_scores = model.score_tail_candidates(h, r, candidates)
    branch_scores = _branch_full_scores(model, h, r, candidates)
    positive_scores = model.score_positive(h, r, gold)
    candidate_positions = {int(value): index for index, value in enumerate(candidates.tolist())}
    gold_positions = torch.as_tensor([candidate_positions[int(value)] for value in gold.tolist()], dtype=torch.long)
    positive_from_candidates = official_scores.gather(1, gold_positions[:, None]).squeeze(1)

    reciprocal = np.asarray(reciprocal_closure(rows.tolist(), kg.num_relations_original), dtype=np.int64)
    reciprocal_errors = int(sum(1 for original, inverse in zip(rows.tolist(), reciprocal[len(rows):].tolist()) if inverse != [original[2], original[1] + kg.num_relations_original, original[0]]))
    filter_checks = {
        "original_query_examples": int(sum(1 for row in rows if int(row[1]) < kg.num_relations_original and (int(row[0]), int(row[1])) in kg.tails_of_hr)),
        "reciprocal_query_examples": int(sum(1 for row in reciprocal[len(rows):] if (int(row[1]) - kg.num_relations_original, int(row[2])) in kg.heads_of_rt)),
        "reciprocal_construction_errors": reciprocal_errors,
        "source": "TRAIN_PLUS_VALID_ONLY",
    }
    eval_sample = evaluate(model, kg, "valid", device, batch_size=32, entity_block=512, queries=rows.tolist())
    train_only_eval = evaluate(model, _train_only_kg(kg), "valid", device, batch_size=32, entity_block=512, queries=rows.tolist())
    rank_strict = _rank_from_scores(official_scores, gold_positions, half_ties=False)
    rank_half = _rank_from_scores(official_scores, gold_positions, half_ties=True)
    reference = json.loads((root / TEACHER_RUN / "audit_step4600.json").read_text(encoding="utf-8"))
    result = {
        "campaign": "HISTORICAL_VALIDATION_RECONCILIATION_V1",
        "status": "DIFFERENTIAL_AUDIT_COMPLETE_OPEN_CAUSE_REMAINS",
        "test_split_touched": False,
        "rows": len(rows),
        "candidate_count": int(candidates.numel()),
        "checkpoint_sha256": sha256(root / TEACHER_RUN / "checkpoint_last.pt"),
        "checkpoint_inventory": checkpoint_inventory,
        "historical_reference": reference["metrics"]["combined"],
        "code_evidence": {
            "current_train_valid_loader": "load_train_valid_only; TRAIN+VALID filters",
            "historical_trainer_loader": "train_spectral_mixture._load_kg calls load_knowledge_graph and requires a test path; exact historical command/provenance not reconstructed",
            "test_access_for_reconciliation": "NOT_PERFORMED",
        },
        "scorer_path_equivalence": {
            "branch_vs_model_max_abs_error": float((branch_scores - official_scores).abs().max().item()),
            "branch_vs_model_mean_abs_error": float((branch_scores - official_scores).abs().mean().item()),
            "positive_vs_candidate_max_abs_error": float((positive_scores - positive_from_candidates).abs().max().item()),
            "rank_equal_strict_fraction": float((rank_strict == rank_half).float().mean().item()),
        },
        "filter_and_reciprocal_checks": filter_checks,
        "sealed_valid_evaluation": eval_sample,
        "train_only_filter_evaluation": train_only_eval,
        "historical_delta": {
            "historical_mrr": reference["metrics"]["combined"]["MRR"],
            "sealed_train_valid_mrr": eval_sample["combined"]["MRR"],
            "delta": eval_sample["combined"]["MRR"] - reference["metrics"]["combined"]["MRR"],
            "interpretation": "The differential audit localizes current scorer/gold/reciprocal paths but cannot identify TEST-derived historical filtering without reading TEST or an archived old rank trace.",
        },
        "environment": {"python": sys.version, "torch": torch.__version__, "platform": platform.platform(), "git": git_state(root)},
    }
    write_json(out / "reconciliation.json", result)
    (out / "final_report.md").write_text(
        "# HISTORICAL_VALIDATION_RECONCILIATION_V1\n\n"
        f"Status: **{result['status']}**; TEST touched: `false`.\n\n"
        f"Branch/model max score error: `{result['scorer_path_equivalence']['branch_vs_model_max_abs_error']:.3e}`.\n\n"
        f"Sealed TRAIN+VALID MRR on the differential sample: `{eval_sample['combined']['MRR']:.9f}`; historical reference: `{reference['metrics']['combined']['MRR']:.9f}`.\n\n"
        "The remaining cause is open because historical loader/filter provenance is incomplete and TEST remains sealed.\n",
        encoding="utf-8",
    )
    artifacts = {
        path.name: sha256(path)
        for path in sorted(out.iterdir())
        if path.is_file() and path.name not in {"manifest.json", "artifact_hashes.json"}
    }
    write_json(out / "artifact_hashes.json", artifacts)
    write_json(
        out / "manifest.json",
        {
            "campaign": result["campaign"],
            "status": result["status"],
            "command": " ".join([sys.executable, "-m", "seion_kgr.sratm_validation_reconciliation", *sys.argv[1:]]),
            "checkpoint_sha256": result["checkpoint_sha256"],
            "dataset": {
                "train_sha256": sha256(root / "data/FB15K-237/train.txt"),
                "valid_sha256": sha256(root / "data/FB15K-237/valid.txt"),
                "test": "NOT_READ_NOT_HASHED_NOT_OPENED",
            },
            "git": result["environment"]["git"],
            "test_split_touched": False,
            "artifacts": artifacts,
        },
    )
    return result


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=Path("."))
    parser.add_argument("--out-dir", type=Path, required=True)
    parser.add_argument("--rows", type=int, default=64)
    parser.add_argument("--candidates", type=int, default=512)
    return parser


def main() -> None:
    print(json.dumps(run(build_parser().parse_args()), indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
