"""Throughput-optimized full-entity hard-negative mining.

This module is a bit-exactness-preserving rewrite of
``full_entity_miner.mine_full_entity_hard_negatives``.  The original walks the
batch with a Python ``for row in range(batch)`` loop *inside* the candidate-block
loop, and calls ``.item()`` on device tensors inside that loop.  Each such call
forces a CUDA synchronization, so a step costs ``ceil(num_entities /
candidate_block) * batch`` synchronizations.  At batch 512 and candidate block
2048 on FB15K-237 that is 4,096 syncs per step, which dominates wall clock.

The rewrite performs exactly one device-to-host transfer per call (of the three
index tensors), resolves the filter dictionaries in pure Python/NumPy on the
host, and applies the mask for a whole block with a single vectorized
``index_put_``.  The scores, the mask, the per-block ``topk`` and the running
frontier merge are otherwise identical operation-for-operation, so the returned
tensors are bit-exact with the original implementation.

Semantics deliberately preserved, including the subtle parts:

* reciprocal relations consult ``heads_of_rt`` keyed by the *original* relation;
* the gold entity is masked even when the filter table is incomplete;
* ``block_k = min(hard_k, end - start)`` bounds the per-block ``topk``;
* the frontier merge is ``cat`` then ``topk`` then ``gather``, in that order.

Equivalence is enforced by ``tests/kgr/test_full_entity_miner_fast_equivalence.py``.
"""

from __future__ import annotations

from typing import Any

import numpy as np
import torch

from ..data import KnowledgeGraph


def mine_full_entity_hard_negatives_fast(
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

    Bit-exact drop-in replacement for
    :func:`full_entity_miner.mine_full_entity_hard_negatives` with one host
    synchronization per call instead of ``num_blocks * batch``.
    """
    if h_ids.ndim != 1 or relation_ids.shape != h_ids.shape or gold_ids.shape != h_ids.shape:
        raise ValueError("h_ids, relation_ids and gold_ids must all be [B]")
    if candidate_block <= 0 or hard_k <= 0:
        raise ValueError("candidate_block and hard_k must be positive")

    batch = h_ids.numel()
    device = h_ids.device

    # Exactly one device -> host transfer for the whole call.
    h_host = h_ids.detach().to("cpu", copy=False).numpy()
    r_host = relation_ids.detach().to("cpu", copy=False).numpy()
    gold_host = gold_ids.detach().to("cpu", copy=False).numpy()

    num_original = kg.num_relations_original

    # Resolve every row's filtered-positive set once, on the host.  Rows are
    # kept as separate arrays so the per-block restriction stays exact.
    per_row_positives: list[np.ndarray | None] = []
    for row in range(batch):
        relation_id = int(r_host[row])
        if relation_id < num_original:
            positives = kg.tails_of_hr.get((int(h_host[row]), relation_id))
        else:
            # Reciprocal training turns a head query into a tail query:
            # (h, r^-1, t) is equivalent to (t, r, h).  The public filter
            # tables are intentionally keyed only by original relations, so
            # consult heads_of_rt for reciprocal ids.
            positives = kg.heads_of_rt.get((relation_id - num_original, int(h_host[row])))
        if positives is None or len(positives) == 0:
            per_row_positives.append(None)
        else:
            per_row_positives.append(np.asarray(positives, dtype=np.int64))

    best_scores = torch.full((batch, hard_k), -torch.inf, device=device)
    best_ids = torch.full((batch, hard_k), -1, dtype=torch.long, device=device)

    for start in range(0, kg.num_entities, candidate_block):
        end = min(start + candidate_block, kg.num_entities)
        candidates = torch.arange(start, end, device=device, dtype=torch.long)
        scores = model.score_tail_candidates(h_ids, relation_ids, candidates)
        filtered = scores.clone()

        # Build the (row, column) mask for this block on the host, then apply
        # it in a single vectorized scatter instead of one write per row.
        mask_rows: list[np.ndarray] = []
        mask_cols: list[np.ndarray] = []
        for row in range(batch):
            positives = per_row_positives[row]
            if positives is not None:
                local = positives[(positives >= start) & (positives < end)] - start
                if local.size:
                    mask_rows.append(np.full(local.size, row, dtype=np.int64))
                    mask_cols.append(local)
            # The positive path is excluded even if a caller supplies a KG
            # whose filter table is incomplete.
            gold_local = int(gold_host[row])
            if start <= gold_local < end:
                mask_rows.append(np.array([row], dtype=np.int64))
                mask_cols.append(np.array([gold_local - start], dtype=np.int64))

        if mask_rows:
            rows_idx = torch.from_numpy(np.concatenate(mask_rows)).to(device=device, non_blocking=True)
            cols_idx = torch.from_numpy(np.concatenate(mask_cols)).to(device=device, non_blocking=True)
            filtered.index_put_(
                (rows_idx, cols_idx),
                torch.tensor(-torch.inf, device=device, dtype=filtered.dtype),
            )

        block_k = min(hard_k, end - start)
        block_scores, block_positions = torch.topk(filtered, block_k, dim=1)
        block_ids = candidates[block_positions]
        merged_scores = torch.cat((best_scores, block_scores), dim=1)
        merged_ids = torch.cat((best_ids, block_ids), dim=1)
        best_scores, positions = torch.topk(merged_scores, hard_k, dim=1)
        best_ids = merged_ids.gather(1, positions)

    return best_ids, best_scores
