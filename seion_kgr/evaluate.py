"""Blocked filtered evaluator. Head-ranking is never a separate code
path: contract §II.3.2's whole point is that ``(?,r,t)`` head-ranking is
exactly ``(t,r^{-1},?)`` tail-ranking, so this file has ONE ranking loop,
called twice with swapped/inverted arguments — unlike v25, which carried
a fully duplicated ``score_head_candidates`` implementation.
"""
from __future__ import annotations

from typing import Any, Dict, List, Mapping, Sequence, Tuple

import torch

from .data import KnowledgeGraph
from .reasoner import Adjacency


def _inverse_relation(r: int, num_rel_orig: int) -> int:
    return r + num_rel_orig if r < num_rel_orig else r - num_rel_orig


def ranks_to_metrics(ranks: torch.Tensor) -> Dict[str, float]:
    ranks = ranks.float()
    return {
        "MRR": float((1.0 / ranks).mean().item()),
        "Hits@1": float((ranks <= 1).float().mean().item()),
        "Hits@3": float((ranks <= 3).float().mean().item()),
        "Hits@10": float((ranks <= 10).float().mean().item()),
        "mean_rank": float(ranks.mean().item()),
        "count": int(ranks.numel()),
    }


def _tail_ranks_for_query_set(
    model,
    kg: KnowledgeGraph,
    queries: Sequence[Tuple[int, int, int]],  # (h, r, t) — always scored as tail-ranking of (h,r,?)
    filter_table: Mapping[Tuple[int, int], "object"],
    device: torch.device,
    batch_size: int,
    entity_block: int,
    adjacency: Adjacency | None,
    seed: int,
) -> torch.Tensor:
    all_ranks: List[torch.Tensor] = []
    eps_tie = 1e-7
    for offset in range(0, len(queries), batch_size):
        chunk = queries[offset : offset + batch_size]
        h_ids = torch.tensor([x[0] for x in chunk], device=device, dtype=torch.long)
        r_ids = torch.tensor([x[1] for x in chunk], device=device, dtype=torch.long)
        t_ids = torch.tensor([x[2] for x in chunk], device=device, dtype=torch.long)

        true_scores = model.score_positive(h_ids, r_ids, t_ids, adjacency, seed, training=False).unsqueeze(1)
        ranks = torch.ones(len(chunk), device=device, dtype=torch.float32)
        keys = [(int(h), int(r)) for h, r, _ in chunk]

        for start in range(0, kg.num_entities, entity_block):
            end = min(start + entity_block, kg.num_entities)
            candidates = torch.arange(start, end, device=device, dtype=torch.long)
            scores = model.score_tail_candidates(
                h_ids, r_ids, candidates, adjacency, seed, training=False, gold_tail_ids=t_ids,
            ).float()

            rows: List[torch.Tensor] = []
            cols: List[torch.Tensor] = []
            for row, key in enumerate(keys):
                values = filter_table.get(key)
                if values is None or values.size == 0:
                    continue
                mask = (values >= start) & (values < end)
                if mask.any():
                    c = torch.from_numpy(values[mask] - start).to(device=device, dtype=torch.long)
                    rows.append(torch.full((c.numel(),), row, device=device, dtype=torch.long))
                    cols.append(c)
            if rows:
                scores[torch.cat(rows), torch.cat(cols)] = -torch.inf

            in_block = (t_ids >= start) & (t_ids < end)
            if in_block.any():
                rows_t = torch.nonzero(in_block, as_tuple=False).squeeze(1)
                cols_t = t_ids[in_block] - start
                scores[rows_t, cols_t] = true_scores[rows_t, 0]

            better = (scores > true_scores).sum(dim=1).float()
            ties = torch.isclose(scores, true_scores, atol=eps_tie, rtol=0.0).sum(dim=1).float() - 1.0
            ranks = ranks + better + 0.5 * ties.clamp_min(0.0)

        all_ranks.append(ranks.cpu())
    return torch.cat(all_ranks) if all_ranks else torch.zeros(0)


@torch.inference_mode()
def evaluate(
    model,
    kg: KnowledgeGraph,
    split: str,
    device: torch.device,
    batch_size: int,
    entity_block: int,
    adjacency: Adjacency | None = None,
    subset: float = 1.0,
    seed: int = 0,
) -> Dict[str, Any]:
    model.eval()
    data_full = kg.valid if split == "valid" else kg.test
    if not (0 < subset <= 1.0):
        raise ValueError("subset must be in (0,1]")
    if subset < 1.0:
        import numpy as np

        rng = np.random.default_rng(12345 if split == "valid" else 67890)
        size = max(1, int(len(data_full) * subset))
        idx = rng.choice(len(data_full), size=size, replace=False)
        data = [data_full[int(i)] for i in idx]
    else:
        data = data_full

    tail_ranks = _tail_ranks_for_query_set(
        model, kg, data, kg.tails_of_hr, device, batch_size, entity_block, adjacency, seed,
    )

    # Head-ranking via the reciprocal trick: (?,r,t) tail-ranks as (t,r^-1,?).
    inv_queries = [(t, _inverse_relation(r, kg.num_relations_original), h) for h, r, t in data]
    head_filter = {(t, _inverse_relation(r, kg.num_relations_original)): kg.heads_of_rt.get((r, t), None) for h, r, t in data}
    # heads_of_rt values are already np arrays keyed by (r,t); reuse directly under the inverse-query key.
    head_ranks = _tail_ranks_for_query_set(
        model, kg, inv_queries, head_filter, device, batch_size, entity_block, adjacency, seed + 1,
    )

    combined = torch.cat((tail_ranks, head_ranks))
    return {
        "split": split,
        "combined": ranks_to_metrics(combined),
        "tail": ranks_to_metrics(tail_ranks),
        "head": ranks_to_metrics(head_ranks),
        "eval_subset": float(subset),
        "entity_block": int(entity_block),
    }
