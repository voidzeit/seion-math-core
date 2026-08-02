"""Gate 13.2: vectorized segment (ragged-group) top-k, no per-group Python
loop. Given a flat array of candidate scores and the (contiguous) group
each candidate belongs to, keeps at most ``k`` highest-scoring candidates
per group.

Algorithm: sort by a composite key ``(group_id, -score)`` so that, within
the single global sort, each group's candidates end up contiguous and
score-descending in the same relative group order as the input. The
position of each item within its own group in that sorted order is then
just another ``repeat_interleave_offsets`` computation (reusing the same
primitive ``frontier_ops.py`` uses for CSR expansion) — no group-by-group
Python loop anywhere.
"""
from __future__ import annotations

import torch

from .frontier_ops import repeat_interleave_offsets


def segment_topk(scores: torch.Tensor, counts: torch.Tensor, k: int) -> torch.Tensor:
    """``scores``: ``[C]``. ``counts``: ``[G]``, group sizes, groups appear
    in the same contiguous order as they do in ``scores`` (group 0's items
    first, then group 1's, ...). Returns a boolean ``[C]`` keep-mask, at
    most ``k`` ``True`` entries per group (all ``True`` if a group has
    ``<= k`` candidates)."""
    total = int(scores.numel())
    if total == 0:
        return torch.zeros(0, dtype=torch.bool, device=scores.device)
    group_id, local_offset = repeat_interleave_offsets(counts)

    # Composite sort key: group_id dominates (so groups never interleave),
    # -score breaks ties within a group in descending-score order. Scores
    # are rank-transformed to integers first so no floating-point range
    # assumption is needed for the composite key to be exact.
    score_rank = torch.argsort(torch.argsort(scores))  # 0..total-1, ties broken by index (stable)
    key = group_id.to(torch.int64) * total - score_rank.to(torch.int64)
    sorted_order = torch.argsort(key)  # positions into the ORIGINAL arrays, grouped + score-descending

    # `sorted_order` lists group 0's candidates (best score first), then
    # group 1's, etc. — the exact same group sizes/order as `counts`, so
    # `local_offset` (computed above from `counts` alone) already gives each
    # SORTED position's rank within its group; it does not depend on the
    # scores themselves, only on the group sizes.
    keep_in_sorted_order = local_offset < k

    keep_mask = torch.zeros(total, dtype=torch.bool, device=scores.device)
    keep_mask[sorted_order] = keep_in_sorted_order
    return keep_mask
