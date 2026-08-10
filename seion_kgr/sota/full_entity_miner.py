"""Full-entity hard-negative mining without materializing ``[B,N,D]``."""

from __future__ import annotations

from typing import Any

import torch

from ..data import KnowledgeGraph


@torch.no_grad()
def mine_full_entity_hard_negatives(
    model: Any,
    h_ids: torch.Tensor,
    relation_ids: torch.Tensor,
    gold_ids: torch.Tensor,
    kg: KnowledgeGraph,
    *,
    candidate_block: int = 2048,
    hard_k: int = 128,
) -> tuple[torch.Tensor, torch.Tensor]:
    """Mine filtered model-hard negatives over all entities in blocks.

    Only ``[B, block]`` scores and the running ``[B, hard_k]`` frontier are
    kept.  This is the online full-entity mining path; it does not construct a
    ``[B,N,D]`` candidate tensor.
    """
    if h_ids.ndim != 1 or relation_ids.shape != h_ids.shape or gold_ids.shape != h_ids.shape:
        raise ValueError("h_ids, relation_ids and gold_ids must all be [B]")
    if candidate_block <= 0 or hard_k <= 0:
        raise ValueError("candidate_block and hard_k must be positive")
    batch = h_ids.numel()
    device = h_ids.device
    best_scores = torch.full((batch, hard_k), -torch.inf, device=device)
    best_ids = torch.full((batch, hard_k), -1, dtype=torch.long, device=device)
    for start in range(0, kg.num_entities, candidate_block):
        end = min(start + candidate_block, kg.num_entities)
        candidates = torch.arange(start, end, device=device, dtype=torch.long)
        scores = model.score_tail_candidates(h_ids, relation_ids, candidates)
        filtered = scores.clone()
        for row in range(batch):
            h_id = int(h_ids[row].item())
            relation_id = int(relation_ids[row].item())
            if relation_id < kg.num_relations_original:
                positives = kg.tails_of_hr.get((h_id, relation_id))
            else:
                # Reciprocal training turns a head query into a tail query:
                # (h, r^-1, t) is equivalent to (t, r, h).  The public
                # filter tables are intentionally keyed only by original
                # relations, so consult heads_of_rt for reciprocal ids.
                original_relation = relation_id - kg.num_relations_original
                positives = kg.heads_of_rt.get((original_relation, h_id))
            if positives is not None and len(positives):
                local = positives[(positives >= start) & (positives < end)] - start
                if len(local):
                    filtered[row, torch.as_tensor(local, device=device, dtype=torch.long)] = -torch.inf
            # The positive path is excluded even if a caller supplies a KG
            # whose filter table is incomplete.
            gold_local = int(gold_ids[row].item())
            if start <= gold_local < end:
                filtered[row, gold_local - start] = -torch.inf
        block_k = min(hard_k, end - start)
        block_scores, block_positions = torch.topk(filtered, block_k, dim=1)
        block_ids = candidates[block_positions]
        merged_scores = torch.cat((best_scores, block_scores), dim=1)
        merged_ids = torch.cat((best_ids, block_ids), dim=1)
        best_scores, positions = torch.topk(merged_scores, hard_k, dim=1)
        best_ids = merged_ids.gather(1, positions)
    return best_ids, best_scores
