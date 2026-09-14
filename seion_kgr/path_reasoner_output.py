"""Gate 13.2b (``campaigns/gate13/``): a single, backend-agnostic
frontier-readout representation, so ``model.py`` never has to know whether
a ``(query_id, node_id) -> state`` lookup came from the legacy per-sample
dict-BFS (``reasoner.PathReasoner``) or the vectorized CSR reasoner
(``reasoner_batched.BatchedPathReasoner``) — it always reads off a
``PathReasonerOutput``.

Scope note: the mission brief's fuller schema (``offsets``,
``selector_scores``, ``selector_margins``, ``reached_gold``) is NOT
implemented here. Those fields would only be load-bearing once the
learned-selector instrumentation and Gate 13.3 attribution work land; until
then they would be unused plumbing. Only the fields both backends can
actually populate today — the ones that make score/gradient parity
checkable — are implemented. This is a deliberate scope cut, not an
oversight (see ``campaigns/gate13/preregistration.md`` §11).
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List

import torch


@dataclass
class PathReasonerOutput:
    query_ids: torch.Tensor  # [F], int64
    node_ids: torch.Tensor  # [F], int64
    states: torch.Tensor  # [F, D]
    num_nodes: int
    unreached_state: torch.Tensor  # [D]

    def state_for(self, query_ids: torch.Tensor, node_ids: torch.Tensor) -> torch.Tensor:
        """Vectorized ``(query_id, node_id) -> state`` lookup (defaulting to
        ``unreached_state``) via sort + ``searchsorted`` — no per-query
        Python loop, and no dependence on which backend produced this
        output."""
        if self.query_ids.numel() == 0:
            return self.unreached_state.unsqueeze(0).expand(query_ids.numel(), -1).clone()
        key = self.query_ids * self.num_nodes + self.node_ids
        order = torch.argsort(key)
        sorted_keys, sorted_states = key[order], self.states[order]

        query_key = query_ids * self.num_nodes + node_ids
        idx = torch.searchsorted(sorted_keys, query_key)
        idx_clamped = idx.clamp(max=sorted_keys.numel() - 1)
        found = (idx < sorted_keys.numel()) & (sorted_keys[idx_clamped] == query_key)
        gathered = sorted_states[idx_clamped]
        default = self.unreached_state.unsqueeze(0).expand_as(gathered)
        return torch.where(found.unsqueeze(-1), gathered, default)

    def states_for_candidates(self, query_ids: torch.Tensor, candidates_ids_2d: torch.Tensor) -> torch.Tensor:
        """``candidates_ids_2d``: ``[B, K]``. Returns ``[B, K, D]``."""
        b, k = candidates_ids_2d.shape
        flat_query_ids = query_ids.unsqueeze(1).expand(b, k).reshape(-1)
        flat_candidates = candidates_ids_2d.reshape(-1)
        flat_states = self.state_for(flat_query_ids, flat_candidates)
        return flat_states.view(b, k, -1)

    def reached_mask(self, query_ids: torch.Tensor, node_ids: torch.Tensor) -> torch.Tensor:
        """``[N]`` bool — was ``(query_ids[i], node_ids[i])`` actually
        reached (as opposed to falling back to ``unreached_state``)? Useful
        for a ``gold_reach_rate`` diagnostic without materializing states."""
        if self.query_ids.numel() == 0:
            return torch.zeros(query_ids.numel(), dtype=torch.bool)
        key = self.query_ids * self.num_nodes + self.node_ids
        order = torch.argsort(key)
        sorted_keys = key[order]
        query_key = query_ids * self.num_nodes + node_ids
        idx = torch.searchsorted(sorted_keys, query_key)
        idx_clamped = idx.clamp(max=sorted_keys.numel() - 1)
        return (idx < sorted_keys.numel()) & (sorted_keys[idx_clamped] == query_key)

    @staticmethod
    def from_legacy_frontiers(
        frontiers: List[Dict[int, torch.Tensor]], num_nodes: int, unreached_state: torch.Tensor,
    ) -> "PathReasonerOutput":
        """Flattens the legacy per-sample dict frontiers into the common
        flat representation. This flattening loop is O(batch) bookkeeping
        (each query's frontier is typically a handful of reached nodes) —
        it is NOT the expensive part the legacy backend is slow at (the
        per-query BFS traversal itself, which still runs in
        ``PathReasoner.run_batch_frontiers`` exactly as before; this
        adapter only unifies the OUTPUT shape for ``model.py``)."""
        query_ids, node_ids, states = [], [], []
        for b, frontier in enumerate(frontiers):
            for node, state in frontier.items():
                query_ids.append(b)
                node_ids.append(node)
                states.append(state)
        dim = unreached_state.shape[0]
        states_t = torch.stack(states, dim=0) if states else torch.zeros(0, dim, device=unreached_state.device)
        return PathReasonerOutput(
            query_ids=torch.tensor(query_ids, dtype=torch.long),
            node_ids=torch.tensor(node_ids, dtype=torch.long),
            states=states_t,
            num_nodes=num_nodes,
            unreached_state=unreached_state,
        )

    @staticmethod
    def from_batched_frontier(frontier, num_nodes: int, unreached_state: torch.Tensor) -> "PathReasonerOutput":
        """``frontier``: a ``frontier_ops.FrontierBatch`` — already in the
        common flat shape, so this is just a type-level wrap."""
        return PathReasonerOutput(
            query_ids=frontier.query_id, node_ids=frontier.node, states=frontier.state,
            num_nodes=num_nodes, unreached_state=unreached_state,
        )
