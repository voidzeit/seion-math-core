"""Full filtered-test validation for selected frozen TTN rank assignments.

This post-training validator deliberately avoids the exhaustive grid.  It
loads a completed frozen checkpoint, evaluates the official test split with
the existing filtered evaluator, and reports score-gap probes plus global
certificate values for selected allocations.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import torch

from . import reproducibility as repro
from .data import load_knowledge_graph
from .evaluate import evaluate
from .run_ttn_fb15k237 import _candidate_ids
from .ttn_branching import BranchingTTNK3, branch_leaf_norm_bounds


def parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--checkpoint", type=Path, required=True)
    p.add_argument("--train", default="data/FB15K-237/train.txt")
    p.add_argument("--valid", default="data/FB15K-237/valid.txt")
    p.add_argument("--test", default="data/FB15K-237/test.txt")
    p.add_argument("--out", type=Path, required=True)
    p.add_argument("--candidate-sample", type=int, default=256)
    p.add_argument("--entity-block", type=int, default=4096)
    p.add_argument("--batch-size", type=int, default=128)
    p.add_argument("--ranks", default="1:16,4:24,8:24,16:32,32:32")
    p.add_argument("--cpu", action="store_true")
    p.add_argument("--seed", type=int, default=42)
    return p


def _device(args: argparse.Namespace) -> torch.device:
    return torch.device("cpu" if args.cpu or not torch.cuda.is_available() else "cuda")


def _queries(kg) -> list[tuple[int, int, int]]:
    return [tuple(int(value) for value in row) for row in kg.test]


def main() -> None:
    args = parser().parse_args()
    device = _device(args)
    repro.set_seed(args.seed)
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
    model.set_mode("full")
    test_queries = _queries(kg)
    candidate_ids = _candidate_ids(kg.num_entities, args.candidate_sample, args.seed + 91)
    bounds = branch_leaf_norm_bounds(model)
    baseline = evaluate(
        model,
        kg,
        "test",
        device,
        batch_size=args.batch_size,
        entity_block=args.entity_block,
        subset=1.0,
        seed=args.seed,
        queries=test_queries,
        return_ranks=True,
    )
    baseline_ranks = torch.cat((baseline["tail_ranks"], baseline["head_ranks"]))
    baseline_metrics = {key: value for key, value in baseline.items() if key not in {"tail_ranks", "head_ranks"}}
    rank_pairs = []
    for item in args.ranks.split(","):
        first, second = item.split(":")
        rank_pairs.append((int(first), int(second)))

    records = []
    for rank1, rank2 in rank_pairs:
        model.set_ranks(rank1, rank2)
        certificate = model.certificate(bounds, rank1, rank2, rank_aware=True)
        gap = _full_test_score_gap(
            model, test_queries, candidate_ids, device, rank1, rank2, args.batch_size
        )
        model.set_mode("projected")
        projected = evaluate(
            model,
            kg,
            "test",
            device,
            batch_size=args.batch_size,
            entity_block=args.entity_block,
            subset=1.0,
            seed=args.seed,
            queries=test_queries,
            return_ranks=True,
        )
        projected_ranks = torch.cat((projected["tail_ranks"], projected["head_ranks"]))
        projected_metrics = {key: value for key, value in projected.items() if key not in {"tail_ranks", "head_ranks"}}
        records.append({
            "rank1": rank1,
            "rank2": rank2,
            "certificate_root_bound": float(certificate["root_bound"]),
            "full_test_score_gap_probe": gap,
            "certificate_holds_on_probe": bool(
                gap["max_abs_score_gap"] <= float(certificate["root_bound"]) + 1e-5
            ),
            "full_filtered_test": baseline_metrics["combined"],
            "projected_filtered_test": projected_metrics["combined"],
            "rank_equal_fraction": float((baseline_ranks == projected_ranks).float().mean().item()),
            "delta_MRR": float(projected_metrics["combined"]["MRR"] - baseline_metrics["combined"]["MRR"]),
            "delta_Hits@10": float(
                projected_metrics["combined"]["Hits@10"] - baseline_metrics["combined"]["Hits@10"]
            ),
            "resource_proxy": model.resource_proxy(
                rank1, rank2, candidate_count=kg.num_entities
            ),
        })

    output = {
        "status": "FULL_FILTERED_TEST_POSTTRAIN_VALIDATION",
        "device": str(device),
        "checkpoint": str(args.checkpoint),
        "dataset": {
            "name": "FB15K-237",
            "test_queries": len(test_queries),
            "num_entities": kg.num_entities,
            "official_split_paths": {
                "train": str(Path(args.train)),
                "valid": str(Path(args.valid)),
                "test": str(Path(args.test)),
            },
        },
        "protocol": {
            "weights_frozen": True,
            "projectors_from_train_only": True,
            "filtered_evaluator": True,
            "score_gap_candidates": args.candidate_sample,
            "rank_pairs": rank_pairs,
        },
        "leaf_norm_bounds": bounds,
        "baseline": baseline_metrics,
        "records": records,
        "limitations": [
            "Score-gap probe samples fixed candidate entities; the global certificate is the domain-level object.",
            "This validator reports full filtered MRR/Hits but does not claim full-test CCR without a separate rank-margin pass.",
            "One frozen seed and selected allocations; no multi-seed superiority claim.",
        ],
    }
    args.out.parent.mkdir(parents=True, exist_ok=True)
    repro.save_json(output, args.out)
    print(json.dumps({"out": str(args.out), "records": len(records), "device": str(device)}, sort_keys=True))


@torch.inference_mode()
def _full_test_score_gap(
    model: BranchingTTNK3,
    queries: list[tuple[int, int, int]],
    candidate_ids: torch.Tensor,
    device: torch.device,
    rank1: int,
    rank2: int,
    batch_size: int,
) -> dict[str, float]:
    model.set_ranks(rank1, rank2)
    gaps: list[torch.Tensor] = []
    candidates = candidate_ids.to(device=device)
    for offset in range(0, len(queries), batch_size):
        chunk = queries[offset : offset + batch_size]
        h = torch.tensor([item[0] for item in chunk], device=device)
        r = torch.tensor([item[1] for item in chunk], device=device)
        t = torch.tensor([item[2] for item in chunk], device=device)
        model.set_mode("full")
        full = torch.cat([
            model.score_positive(h, r, t).unsqueeze(1),
            model.score_tail_candidates(h, r, candidates),
        ], dim=1)
        model.set_mode("projected")
        projected = torch.cat([
            model.score_positive(h, r, t).unsqueeze(1),
            model.score_tail_candidates(h, r, candidates),
        ], dim=1)
        gaps.append((full - projected).abs().reshape(-1).cpu())
    values = torch.cat(gaps)
    return {
        "max_abs_score_gap": float(values.max().item()),
        "mean_abs_score_gap": float(values.mean().item()),
        "query_count": len(queries),
        "candidate_count": int(candidate_ids.numel()),
    }


if __name__ == "__main__":
    main()
