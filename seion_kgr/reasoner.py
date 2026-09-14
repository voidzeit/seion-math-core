"""Fase 4: query-conditioned path reasoner with a pluggable edge selector.

Contract §VII (message passing) + the "selector de caminos" requirement
in the source design note ("No debes propagar por todo el grafo en
todas las capas"). This is a genuine, bounded frontier-expansion (BFS)
reasoner: per query, per layer, at most ``max_neighbors`` outgoing edges
per frontier node are kept. That budget is what makes this tractable on
FB15K-237-scale graphs at all — it is not an optional feature, it is
the only reason this file runs in seconds instead of hours.

Campaign Phase B2 update: the selector is no longer only a fixed random
sample. ``selector_mode`` picks between the original fixed-random budget
(``"budgeted_bfs"``, still the default — nothing built on the canonical
commit changes behavior unless it opts in), a genuinely learned priority
network (``"learned_topk"``, see ``selector.py``), an unbudgeted mode for
tiny debug graphs (``"full_neighborhood"``), and a synthetic-fixture-only
oracle mode (``"oracle_or_gold_path_debug_mode"``).

Edge removal (Gate 6, "remover la arista consultada evita leakage"): the
specific queried edge ``(h,r,t)`` and its reciprocal ``(t,r^{-1},h)``
are excluded from the candidate list BEFORE any selector (random or
learned) ever sees it — leakage prevention is not something a selector
mode can bypass, by construction.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List, Optional, Set, Tuple

import numpy as np
import torch
import torch.nn as nn

from .data import KnowledgeGraph
from .kernels import CPTernaryLaw, StiefelProjector
from .selector import LearnedPathSelector, select_edges


@dataclass
class Adjacency:
    """``node -> list of (relation, target)`` outgoing edges, built once per KG."""

    out_edges: Dict[int, List[Tuple[int, int]]]

    @staticmethod
    def build(kg: KnowledgeGraph) -> "Adjacency":
        out: Dict[int, List[Tuple[int, int]]] = {}
        for h, r, t in kg.train.tolist():
            out.setdefault(h, []).append((r, t))
        return Adjacency(out)


class PathReasoner(nn.Module):
    """One shared ``CPTernaryLaw`` message + linear residual branches +
    projector, applied over a budgeted BFS frontier, ``num_layers`` hops
    deep. Produces a readout state per query at the (possibly unreached)
    tail node.
    """

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
        self.dim = dim
        self.num_layers = num_layers
        self.max_neighbors = max_neighbors
        self.selector_mode = selector_mode
        self.mu = CPTernaryLaw(dim_x=dim, dim_a=dim, dim_q=dim, dim_out=dim, rank=rank)
        self.U = nn.Linear(dim, dim, bias=False)
        self.V = nn.Linear(dim, dim, bias=False)
        self.W = nn.Linear(dim, dim, bias=False)
        for layer in (self.U, self.V, self.W):
            nn.init.xavier_uniform_(layer.weight, gain=0.1)  # small residual branches
        self.projector = StiefelProjector(dim, proj_rank)
        self.ln = nn.LayerNorm(dim)
        self.unreached_state = nn.Parameter(torch.zeros(dim))
        self.selector = LearnedPathSelector(dim, max_depth=max(num_layers, 1) + 1) if selector_mode == "learned_topk" else None

    def message(self, x_u: torch.Tensor, a_edge: torch.Tensor, q_query: torch.Tensor) -> torch.Tensor:
        m_tilde = self.mu(x_u, a_edge, q_query) + self.U(x_u) + self.V(a_edge) + self.W(q_query)
        return self.projector.apply(m_tilde) if self.projector.enabled else m_tilde

    def _frontier_step(
        self,
        frontier: Dict[int, torch.Tensor],
        adjacency: Adjacency,
        relation_embed: torch.Tensor,
        query_vec: torch.Tensor,
        exclude_edges: set,
        rng: np.random.Generator,
        depth: int = 0,
        entity_embed: Optional[torch.Tensor] = None,
        priority: Optional[Dict[int, float]] = None,
        gold_edges: Optional[Set[Tuple[int, int, int]]] = None,
    ) -> Tuple[Dict[int, torch.Tensor], Dict[int, float]]:
        incoming: Dict[int, List[torch.Tensor]] = {}
        next_priority: Dict[int, float] = {}
        priority = priority or {}
        for u, x_u in frontier.items():
            edges = adjacency.out_edges.get(u, [])
            if not edges:
                continue
            # Leakage prevention happens BEFORE selection, in every mode —
            # the excluded edge is never even a candidate the selector sees.
            candidates = [(r, v) for (r, v) in edges if (u, r, v) not in exclude_edges]
            if not candidates:
                continue
            acc_priority = torch.full((len(candidates),), float(priority.get(u, 0.0)))
            gold_idx = None
            if gold_edges is not None:
                gold_idx = {i for i, (r, v) in enumerate(candidates) if (u, r, v) in gold_edges}
            result = select_edges(
                self.selector_mode, candidates, self.max_neighbors,
                selector=self.selector, x_u=x_u, relation_embed=relation_embed, query_vec=query_vec,
                dst_base_embed=entity_embed, depth=depth, accumulated_priority=acc_priority,
                rng=rng, gold_edge_indices=gold_idx,
            )
            for pos, ci in enumerate(result.kept_indices):
                r, v = candidates[ci]
                m = self.message(x_u, relation_embed[r], query_vec) * result.keep_weight[pos]
                incoming.setdefault(v, []).append(m)
                if result.scores is not None:
                    next_priority[v] = max(next_priority.get(v, -1e9), float(result.scores[ci].detach()))
        next_frontier: Dict[int, torch.Tensor] = {}
        for v, msgs in incoming.items():
            z = torch.stack(msgs, dim=0).mean(dim=0)
            next_frontier[v] = self.ln(torch.tanh(z))
        return next_frontier, next_priority

    def run_batch_frontiers(
        self,
        adjacency: Adjacency,
        relation_embed: torch.Tensor,
        head_ids: torch.Tensor,
        relation_ids: torch.Tensor,
        tail_ids: torch.Tensor,
        query_vecs: torch.Tensor,
        seed: int,
        training: bool,
        entity_embed: Optional[torch.Tensor] = None,
        gold_edges_per_sample: Optional[List[Set[Tuple[int, int, int]]]] = None,
    ) -> List[Dict[int, torch.Tensor]]:
        """Returns, per batch sample, the final-layer frontier dict
        ``{node: state}``. Running BFS once per query and reading off
        *every* reached node's state (rather than only the gold tail's)
        is what makes candidate scoring tractable later — see
        ``score_candidates_from_frontier`` below.

        ``entity_embed`` (the ``[num_entities, dim]`` table) is required
        when ``selector_mode == "learned_topk"`` (destination base
        features); ignored otherwise. ``gold_edges_per_sample`` is only
        used by ``"oracle_or_gold_path_debug_mode"`` and must never be
        populated from real benchmark evaluation code — it exists for
        synthetic-fixture tests only.
        """
        rng = np.random.default_rng(seed)
        batch = int(head_ids.numel())
        frontiers: List[Dict[int, torch.Tensor]] = []
        for b in range(batch):
            h = int(head_ids[b].item())
            r = int(relation_ids[b].item())
            t = int(tail_ids[b].item())
            exclude = {(h, r, t)}
            if training:
                num_rel = relation_embed.shape[0] // 2
                r_inv = r + num_rel if r < num_rel else r - num_rel
                exclude.add((t, r_inv, h))
            gold = gold_edges_per_sample[b] if gold_edges_per_sample is not None else None
            frontier: Dict[int, torch.Tensor] = {h: query_vecs[b]}
            priority: Dict[int, float] = {h: 0.0}
            for layer in range(self.num_layers):
                frontier, priority = self._frontier_step(
                    frontier, adjacency, relation_embed, query_vecs[b], exclude, rng,
                    depth=layer, entity_embed=entity_embed, priority=priority, gold_edges=gold,
                )
                if not frontier:
                    break
            frontiers.append(frontier)
        return frontiers

    def state_for_node(self, frontier: Dict[int, torch.Tensor], node: int) -> torch.Tensor:
        return frontier.get(node, self.unreached_state)

    def states_for_candidates(self, frontier: Dict[int, torch.Tensor], candidate_ids: torch.Tensor) -> torch.Tensor:
        """``[K, dim]`` stacked state for each candidate id (unreached
        nodes get the learned default state)."""
        return torch.stack([self.state_for_node(frontier, int(c)) for c in candidate_ids.tolist()], dim=0)
