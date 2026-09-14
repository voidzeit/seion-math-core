"""Fase 4 / campaign Phase B2: a genuine learned sparse path selector.

The canonical-commit reasoner (`seion_kgr/reasoner.py`) only ever had a
fixed-random top-k neighbor budget — explicitly documented there as "not
the learned A*Net priority network". This module is that missing piece:
`LearnedPathSelector` scores each candidate outgoing edge of a frontier
node from real features (source state, edge relation, query relation,
destination base embedding, depth, accumulated path priority) and keeps
the top-`budget` by score, with the kept edges' contribution to the
aggregated message weighted by a differentiable keep-probability gate —
so gradients genuinely reach the selector's parameters, not just the
edges it happens to keep.

Four modes, matching the campaign mandate exactly:

- `full_neighborhood`: no subsampling, no budget (debug/tiny graphs only).
- `budgeted_bfs`: the original fixed-random top-k (unchanged behavior,
  default, so nothing built on top of the canonical commit silently
  changes semantics).
- `learned_topk`: score every candidate edge with `LearnedPathSelector`,
  keep the top-`budget` by score with an explicit deterministic tie
  policy, weight kept messages by `sigmoid(score)`.
- `oracle_or_gold_path_debug_mode`: force-keep a given set of "gold"
  edges (only meaningful when the gold path is known, i.e. synthetic
  tests) — never used at real inference time, since the gold path is
  exactly what the reasoner is trying to find.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List, Optional, Sequence, Set, Tuple

import numpy as np
import torch
import torch.nn as nn
import torch.nn.functional as F

MODES = ("full_neighborhood", "budgeted_bfs", "learned_topk", "oracle_or_gold_path_debug_mode")


class LearnedPathSelector(nn.Module):
    """Scores candidate edges ``(source_state, edge_relation, query_relation,
    destination_base_embedding, depth, accumulated_priority)`` for a
    budgeted top-k keep decision. A pure per-edge scoring function (no
    recurrence, no order-dependent aggregation across candidates), so it
    is structurally permutation-invariant in the input edge order.
    """

    def __init__(self, dim: int, max_depth: int = 8):
        super().__init__()
        self.dim = dim
        self.max_depth = max_depth
        self.depth_embed = nn.Embedding(max_depth, dim)
        self.mlp = nn.Sequential(
            nn.Linear(5 * dim + 1, dim), nn.ReLU(), nn.Linear(dim, 1),
        )
        nn.init.xavier_uniform_(self.mlp[0].weight)
        nn.init.xavier_uniform_(self.mlp[2].weight)

    def score(
        self,
        x_u: torch.Tensor,  # [E, dim]
        a_s: torch.Tensor,  # [E, dim]
        q: torch.Tensor,  # [dim] (broadcast) or [E, dim]
        dst_base: torch.Tensor,  # [E, dim]
        depth: int,
        accumulated_priority: torch.Tensor,  # [E]
    ) -> torch.Tensor:
        """Returns raw priority scores, shape ``[E]``. Higher = keep."""
        E = x_u.shape[0]
        if q.ndim == 1:
            q = q.unsqueeze(0).expand(E, -1)
        depth_idx = torch.full((E,), min(depth, self.max_depth - 1), dtype=torch.long, device=x_u.device)
        depth_vec = self.depth_embed(depth_idx)
        feat = torch.cat([x_u, a_s, q, dst_base, depth_vec, accumulated_priority.unsqueeze(-1)], dim=-1)
        return self.mlp(feat).squeeze(-1)


@dataclass
class SelectionResult:
    kept_indices: List[int]  # indices into the input candidate list, sorted by priority desc
    keep_weight: torch.Tensor  # [len(kept_indices)] differentiable gate weight for each kept edge
    scores: Optional[torch.Tensor]  # [E] raw scores for ALL candidates, or None (budgeted_bfs/full_neighborhood)


def select_edges(
    mode: str,
    candidates: Sequence[Tuple[int, int]],  # (relation, dst) pairs
    budget: int,
    *,
    selector: Optional[LearnedPathSelector] = None,
    x_u: Optional[torch.Tensor] = None,
    relation_embed: Optional[torch.Tensor] = None,
    query_vec: Optional[torch.Tensor] = None,
    dst_base_embed: Optional[torch.Tensor] = None,  # [num_entities, dim] table, indexed by dst id
    depth: int = 0,
    accumulated_priority: Optional[torch.Tensor] = None,  # [len(candidates)]
    rng: Optional[np.random.Generator] = None,
    gold_edge_indices: Optional[Set[int]] = None,
) -> SelectionResult:
    """Single entry point used by ``PathReasoner``. ``candidates`` are
    already filtered for queried-edge exclusion by the caller — this
    function never re-derives or overrides that exclusion, so leakage
    prevention cannot be silently bypassed by a selector mode."""
    if mode not in MODES:
        raise ValueError(f"mode must be one of {MODES}, got {mode!r}")
    n = len(candidates)

    if mode == "full_neighborhood" or n <= budget:
        idx = list(range(n))
        return SelectionResult(kept_indices=idx, keep_weight=torch.ones(len(idx)), scores=None)

    if mode == "budgeted_bfs":
        if rng is None:
            raise ValueError("budgeted_bfs requires an rng")
        idx = rng.choice(n, size=budget, replace=False).tolist()
        return SelectionResult(kept_indices=idx, keep_weight=torch.ones(len(idx)), scores=None)

    if mode == "oracle_or_gold_path_debug_mode":
        gold = gold_edge_indices or set()
        gold_present = [i for i in range(n) if i in gold]
        rest = [i for i in range(n) if i not in gold]
        if rng is not None and rest:
            fill = rng.choice(len(rest), size=min(len(rest), max(budget - len(gold_present), 0)), replace=False)
            rest_kept = [rest[i] for i in fill]
        else:
            rest_kept = rest[: max(budget - len(gold_present), 0)]
        idx = (gold_present + rest_kept)[:budget]
        return SelectionResult(kept_indices=idx, keep_weight=torch.ones(len(idx)), scores=None)

    # learned_topk
    if selector is None or x_u is None or relation_embed is None or query_vec is None or dst_base_embed is None:
        raise ValueError("learned_topk requires selector, x_u, relation_embed, query_vec, dst_base_embed")
    x_u_rep = x_u.unsqueeze(0).expand(n, -1)
    a_s = torch.stack([relation_embed[r] for r, _ in candidates], dim=0)
    dst_ids = torch.tensor([d for _, d in candidates], dtype=torch.long)
    dst_base = dst_base_embed[dst_ids]
    if accumulated_priority is None:
        accumulated_priority = torch.zeros(n)
    scores = selector.score(x_u_rep, a_s, query_vec, dst_base, depth, accumulated_priority)

    # Deterministic tie policy: sort by (-score, original_index) so equal
    # scores break ties by candidate order, reproducibly, with no RNG.
    order = sorted(range(n), key=lambda i: (-float(scores[i].detach()), i))
    kept = order[:budget]
    keep_weight = torch.sigmoid(scores[kept])
    return SelectionResult(kept_indices=kept, keep_weight=keep_weight, scores=scores)


def supervised_priority_loss(scores: torch.Tensor, gold_mask: torch.Tensor) -> torch.Tensor:
    """BCE between ``sigmoid(score)`` and a binary gold-edge-membership
    label, for supervised warmup on synthetic graphs where the unique
    gold path is known (contract-external utility — the selector is
    never supervised this way against real benchmark test data, only
    against synthetic fixtures in tests)."""
    return F.binary_cross_entropy_with_logits(scores, gold_mask.float())
