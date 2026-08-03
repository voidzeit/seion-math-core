"""Gate 13.2 (``campaigns/gate13/``): ``BatchedPathReasoner`` — the same
message-passing computation as ``reasoner.PathReasoner``, but with every
per-sample Python loop replaced by CSR expansion (``frontier_ops.py``) +
vectorized segment top-k (``segment_topk.py``) + scatter-reduce
aggregation. No ``for b in range(batch)``, no per-query dict.

Submodule names (``mu``, ``U``, ``V``, ``W``, ``projector``, ``ln``,
``unreached_state``) intentionally match ``PathReasoner`` exactly, so a
trained legacy reasoner's weights transfer via a plain
``load_state_dict()`` — this is what the parity test
(``tests/kgr/test_reasoner_batched_parity.py``) uses to prove the two
implementations compute the same thing, not just structurally similar
things.

Scope for this campaign (see ``campaigns/gate13/preregistration.md`` §4):
only ``selector_mode in {"full_neighborhood", "budgeted_bfs"}`` are
implemented here. ``"learned_topk"`` and
``"oracle_or_gold_path_debug_mode"`` remain on the legacy
``PathReasoner`` only — vectorizing the learned selector's per-edge MLP
score is a natural follow-up once this base is validated, not a blocker
for closing the scaling bottleneck this file exists to fix. Wiring this
reasoner into ``SeionKGRv26``/``train.py`` as the default is ALSO left as
an explicit follow-up (see the deviations log) — this file and its tests
prove the mechanism works and scales; switching the production training
path to use it is a separate, separately-validated step.
"""
from __future__ import annotations

from typing import Optional

import torch
import torch.nn as nn

from .frontier_ops import CSRAdjacency, FrontierBatch, expand_frontier
from .kernels import CPTernaryLaw, StiefelProjector
from .segment_topk import segment_topk

SUPPORTED_SELECTOR_MODES = ("full_neighborhood", "budgeted_bfs")


class BatchedPathReasoner(nn.Module):
    def __init__(
        self,
        dim: int,
        rank: int,
        num_layers: int = 2,
        max_neighbors: int = 32,
        proj_rank: int = 0,
        selector_mode: str = "budgeted_bfs",
    ):
        super().__init__()
        if selector_mode not in SUPPORTED_SELECTOR_MODES:
            raise ValueError(
                f"BatchedPathReasoner supports {SUPPORTED_SELECTOR_MODES}, got {selector_mode!r} "
                "(learned_topk/oracle_or_gold_path_debug_mode are not yet vectorized — see module docstring)"
            )
        self.dim = dim
        self.num_layers = num_layers
        self.max_neighbors = max_neighbors
        self.selector_mode = selector_mode
        self.mu = CPTernaryLaw(dim_x=dim, dim_a=dim, dim_q=dim, dim_out=dim, rank=rank)
        self.U = nn.Linear(dim, dim, bias=False)
        self.V = nn.Linear(dim, dim, bias=False)
        self.W = nn.Linear(dim, dim, bias=False)
        for layer in (self.U, self.V, self.W):
            nn.init.xavier_uniform_(layer.weight, gain=0.1)
        self.projector = StiefelProjector(dim, proj_rank)
        self.ln = nn.LayerNorm(dim)
        self.unreached_state = nn.Parameter(torch.zeros(dim))

    def message(self, x_u: torch.Tensor, a_edge: torch.Tensor, q_query: torch.Tensor) -> torch.Tensor:
        m_tilde = self.mu(x_u, a_edge, q_query) + self.U(x_u) + self.V(a_edge) + self.W(q_query)
        return self.projector.apply(m_tilde) if self.projector.enabled else m_tilde

    def _select_step_edges(
        self,
        frontier: FrontierBatch,
        csr: CSRAdjacency,
        head_ids: torch.Tensor, relation_ids: torch.Tensor, tail_ids: torch.Tensor, r_inv_ids: torch.Tensor,
        training: bool,
        generator: Optional[torch.Generator],
    ):
        """Expansion + queried-edge exclusion + selector budget, factored
        out of ``_step`` so Gate 13.4's certified-bound recurrence
        (``certified_path.py``) can compute bounds over EXACTLY the same
        trace the real forward pass takes — never a separately
        re-implemented (and possibly silently divergent) copy of this
        selection logic. Returns ``(cq, fr, src, rel, tgt)``, all possibly
        empty (``numel()==0``)."""
        if frontier.query_id.numel() == 0:
            empty = torch.zeros(0, dtype=torch.long, device=frontier.state.device)
            return empty, empty, empty, empty, empty
        cq, fr, src, rel, tgt = expand_frontier(csr, frontier)
        if cq.numel() == 0:
            return cq, fr, src, rel, tgt

        # Leakage prevention (Gate 6, matches reasoner.py exactly): the
        # queried edge and, during training, its reciprocal, are excluded
        # BEFORE any budget/selector ever sees the candidate.
        exclude = (src == head_ids[cq]) & (rel == relation_ids[cq]) & (tgt == tail_ids[cq])
        if training:
            exclude = exclude | ((src == tail_ids[cq]) & (rel == r_inv_ids[cq]) & (tgt == head_ids[cq]))
        keep = ~exclude
        cq, fr, src, rel, tgt = cq[keep], fr[keep], src[keep], rel[keep], tgt[keep]
        if cq.numel() == 0:
            return cq, fr, src, rel, tgt

        if self.selector_mode == "budgeted_bfs":
            counts = torch.bincount(fr, minlength=frontier.query_id.numel())
            scores = torch.rand(cq.numel(), generator=generator, device=cq.device)
            budget_keep = segment_topk(scores, counts, self.max_neighbors)
            cq, fr, src, rel, tgt = cq[budget_keep], fr[budget_keep], src[budget_keep], rel[budget_keep], tgt[budget_keep]
        # "full_neighborhood": no further filtering.
        return cq, fr, src, rel, tgt

    def _step(
        self,
        frontier: FrontierBatch,
        csr: CSRAdjacency,
        relation_embed: torch.Tensor,
        query_vecs: torch.Tensor,  # [B, dim], indexed by query_id
        head_ids: torch.Tensor, relation_ids: torch.Tensor, tail_ids: torch.Tensor, r_inv_ids: torch.Tensor,
        training: bool,
        generator: Optional[torch.Generator],
    ) -> FrontierBatch:
        cq, fr, src, rel, tgt = self._select_step_edges(
            frontier, csr, head_ids, relation_ids, tail_ids, r_inv_ids, training, generator,
        )
        if cq.numel() == 0:
            return FrontierBatch(
                query_id=cq, node=tgt, state=torch.zeros(0, self.dim, device=frontier.state.device),
            )

        source_state = frontier.state[fr]
        edge_embed = relation_embed[rel]
        query_vec = query_vecs[cq]
        msgs = self.message(source_state, edge_embed, query_vec)  # [C, dim]

        key = cq * csr.num_nodes + tgt
        unique_key, inverse = torch.unique(key, return_inverse=True)
        num_groups = unique_key.numel()
        summed = torch.zeros(num_groups, self.dim, device=msgs.device, dtype=msgs.dtype).index_add_(0, inverse, msgs)
        group_counts = torch.zeros(num_groups, device=msgs.device, dtype=msgs.dtype).index_add_(
            0, inverse, torch.ones(inverse.numel(), device=msgs.device, dtype=msgs.dtype),
        )
        next_state = self.ln(torch.tanh(summed / group_counts.clamp_min(1).unsqueeze(-1)))
        next_query_id = torch.div(unique_key, csr.num_nodes, rounding_mode="floor")
        next_node = unique_key % csr.num_nodes
        return FrontierBatch(query_id=next_query_id, node=next_node, state=next_state)

    def run_batch_frontiers(
        self,
        csr: CSRAdjacency,
        relation_embed: torch.Tensor,
        head_ids: torch.Tensor,
        relation_ids: torch.Tensor,
        tail_ids: torch.Tensor,
        query_vecs: torch.Tensor,
        seed: int,
        training: bool,
    ) -> FrontierBatch:
        """Tensor-only counterpart of ``PathReasoner.run_batch_frontiers``.
        No Python loop over the batch — only a fixed, batch-size-independent
        Python loop over ``num_layers`` (2-3 in practice), each iteration a
        handful of whole-batch tensor ops."""
        batch = int(head_ids.numel())
        num_rel = relation_embed.shape[0] // 2
        r_inv_ids = torch.where(relation_ids < num_rel, relation_ids + num_rel, relation_ids - num_rel)
        # A CUDA generator cannot seed a CPU tensor and vice versa (PyTorch
        # raises), so the generator's device must match head_ids' device —
        # this is why it is constructed here, not at module-import time.
        generator = (
            torch.Generator(device=head_ids.device).manual_seed(int(seed))
            if self.selector_mode == "budgeted_bfs" else None
        )

        frontier = FrontierBatch(
            query_id=torch.arange(batch, device=head_ids.device), node=head_ids.clone(), state=query_vecs,
        )
        for _layer in range(self.num_layers):
            frontier = self._step(
                frontier, csr, relation_embed, query_vecs, head_ids, relation_ids, tail_ids, r_inv_ids, training, generator,
            )
            if frontier.query_id.numel() == 0:
                break
        return frontier

    @staticmethod
    def state_for_node_batch(
        frontier: FrontierBatch, query_ids: torch.Tensor, node_ids: torch.Tensor, num_nodes: int, unreached_state: torch.Tensor,
    ) -> torch.Tensor:
        """Vectorized counterpart of ``PathReasoner.state_for_node`` for a
        whole batch at once. Delegates to ``PathReasonerOutput`` (Gate
        13.2b) — the single implementation of this lookup shared with the
        legacy backend, so ``model.py`` never needs backend-specific
        readout code."""
        from .path_reasoner_output import PathReasonerOutput
        return PathReasonerOutput.from_batched_frontier(frontier, num_nodes, unreached_state).state_for(query_ids, node_ids)

    @classmethod
    def states_for_candidates_batch(
        cls, frontier: FrontierBatch, query_ids: torch.Tensor, candidates_ids_2d: torch.Tensor, num_nodes: int, unreached_state: torch.Tensor,
    ) -> torch.Tensor:
        """``candidates_ids_2d``: ``[B, K]``. Returns ``[B, K, dim]``."""
        from .path_reasoner_output import PathReasonerOutput
        return PathReasonerOutput.from_batched_frontier(frontier, num_nodes, unreached_state).states_for_candidates(query_ids, candidates_ids_2d)
