"""Gate 13.2 (``campaigns/gate13/``): CSR adjacency + tensor-only frontier
expansion, replacing the per-sample ``for b in range(batch)`` dict-keyed
BFS in ``reasoner.py`` (measured: 8+ minutes without completing one full
WN18RR epoch at ``batch_size=256`` — see ``campaigns/gate12/
preregistration.md`` §11's deviation log). Every operation here is a
tensor op over the whole batch at once; nothing here loops over queries
or frontier nodes in Python.
"""
from __future__ import annotations

from dataclasses import dataclass

import torch

from .reasoner import Adjacency


@dataclass
class CSRAdjacency:
    """``row_ptr[u]:row_ptr[u+1]`` indexes into ``edge_relation``/
    ``edge_target`` for node ``u``'s outgoing edges. ``num_nodes`` is the
    number of rows (``len(row_ptr) - 1``), which may exceed the highest
    node id actually appearing in an edge (isolated nodes have an empty
    range)."""

    row_ptr: torch.Tensor  # [num_nodes + 1], int64
    edge_relation: torch.Tensor  # [E], int64
    edge_target: torch.Tensor  # [E], int64
    num_nodes: int

    @property
    def num_edges(self) -> int:
        return int(self.edge_relation.numel())


def build_csr_adjacency(adjacency: Adjacency, num_nodes: int) -> CSRAdjacency:
    """Converts the legacy dict-of-lists ``Adjacency`` (``reasoner.py``)
    into CSR form. This conversion itself is O(E) Python (run once per KG,
    not per batch/epoch) — the per-batch, per-epoch hot path
    (``expand_frontier`` below) never touches Python-level dicts."""
    rows, rels, tgts = [], [], []
    for u in range(num_nodes):  # already produces row-sorted order, so no separate sort step is needed below
        for r, v in adjacency.out_edges.get(u, []):
            rows.append(u)
            rels.append(r)
            tgts.append(v)
    row_ptr = torch.zeros(num_nodes + 1, dtype=torch.long)
    counts = torch.bincount(torch.tensor(rows, dtype=torch.long), minlength=num_nodes) if rows else torch.zeros(num_nodes, dtype=torch.long)
    row_ptr[1:] = torch.cumsum(counts, dim=0)
    edge_relation = torch.tensor(rels, dtype=torch.long)
    edge_target = torch.tensor(tgts, dtype=torch.long)
    return CSRAdjacency(row_ptr=row_ptr, edge_relation=edge_relation, edge_target=edge_target, num_nodes=num_nodes)


def repeat_interleave_offsets(counts: torch.Tensor) -> tuple[torch.Tensor, torch.Tensor]:
    """The standard "ragged expand" primitive: given group sizes ``counts``
    (``[G]``), returns ``(group_id, local_offset)`` each of shape
    ``[counts.sum()]``, where ``group_id`` repeats index ``g`` ``counts[g]``
    times and ``local_offset`` counts ``0..counts[g]-1`` within each group.
    Used to turn a per-frontier-row degree list into a flat candidate-edge
    index array without a Python loop over rows."""
    total = int(counts.sum().item())
    if total == 0:
        empty = torch.zeros(0, dtype=torch.long, device=counts.device)
        return empty, empty
    group_id = torch.repeat_interleave(torch.arange(counts.numel(), device=counts.device), counts)
    group_start_in_flat = torch.cumsum(counts, dim=0) - counts  # exclusive cumsum
    local_offset = torch.arange(total, device=counts.device) - torch.repeat_interleave(group_start_in_flat, counts)
    return group_id, local_offset


@dataclass
class FrontierBatch:
    """A tensor-only replacement for ``List[Dict[int, torch.Tensor]]``:
    row ``f`` is the state of ``node[f]`` reached while answering query
    ``query_id[f]``. There is at most one row per ``(query_id, node)`` pair
    (duplicates are mean-aggregated during expansion, see
    ``reasoner_batched.py``)."""

    query_id: torch.Tensor  # [F], int64
    node: torch.Tensor  # [F], int64
    state: torch.Tensor  # [F, D]


def expand_frontier(csr: CSRAdjacency, frontier: FrontierBatch) -> tuple[torch.Tensor, torch.Tensor, torch.Tensor, torch.Tensor, torch.Tensor]:
    """One un-budgeted, un-filtered hop: every outgoing edge of every
    frontier row becomes one candidate row. Returns
    ``(candidate_query_id, candidate_frontier_row, source_node, relation,
    target)``, all ``[C]``, where ``candidate_frontier_row`` indexes back
    into ``frontier`` (so the caller can gather ``frontier.state`` for the
    message function)."""
    degrees = csr.row_ptr[frontier.node + 1] - csr.row_ptr[frontier.node]  # [F]
    frontier_row, local_offset = repeat_interleave_offsets(degrees)  # [C]
    edge_idx = csr.row_ptr[frontier.node[frontier_row]] + local_offset  # [C]
    candidate_query_id = frontier.query_id[frontier_row]
    source_node = frontier.node[frontier_row]
    relation = csr.edge_relation[edge_idx]
    target = csr.edge_target[edge_idx]
    return candidate_query_id, frontier_row, source_node, relation, target
