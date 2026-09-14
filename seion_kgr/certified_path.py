"""Gate 13.4.5 (``campaigns/gate13/``): multi-hop certified state-error
bound recurrence, propagated over the REAL CSR/frontier structure
``BatchedPathReasoner`` uses — the actual per-node incoming-message count
and edge set from a real graph traversal, not a worst-case-degree
approximation.

Uses ``BatchedPathReasoner._select_step_edges`` (Gate 13.4's own
refactor of ``reasoner_batched.py``, factored out specifically so this
module and the real forward pass can never silently diverge in which
edges get selected) with the SAME RNG seed, so the bound is computed over
EXACTLY the trace the real forward pass takes.

Recurrence (mission brief §13.4.5, using this module's own bound names):
``B_{v,hop+1} <= L_env * [rho_message + (1/n_v) * sum_{u->v} L_message,x * B_{u,hop}]``
— ``rho_message`` (the closure bound) is per-(mu,U,V,W,projector) and does
not vary hop-to-hop (the SAME weights/projector are reused at every hop,
see ``reasoner_batched.py``'s message-sharing docstring), so it is
computed once and reused; ``L_message,x`` is the query-conditioned
sensitivity bound (tighter than the global one) using the REAL relation/
query embeddings active at that hop.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple

import torch

from .certified_bounds import CertifiedBound, MessageClosureBound, message_closure_bound, message_sensitivity_bound_query_conditioned, envelope_lipschitz_bound
from .frontier_ops import CSRAdjacency, FrontierBatch
from .reasoner_batched import BatchedPathReasoner


@dataclass
class NodeHopBound:
    query_id: int
    hop: int
    node_id: int
    num_incoming_messages: int
    incoming_bound_mean: float
    local_closure_bound: float
    outgoing_bound: float

    def to_dict(self) -> Dict[str, object]:
        return {
            "query_id": self.query_id, "hop": self.hop, "node_id": self.node_id,
            "num_incoming_messages": self.num_incoming_messages,
            "incoming_bound_mean": self.incoming_bound_mean,
            "local_closure_bound": self.local_closure_bound,
            "outgoing_bound": self.outgoing_bound,
        }


def propagate_certified_state_bounds(
    reasoner: BatchedPathReasoner,
    csr: CSRAdjacency,
    relation_embed: torch.Tensor,
    head_ids: torch.Tensor,
    relation_ids: torch.Tensor,
    tail_ids: torch.Tensor,
    query_vecs: torch.Tensor,
    seed: int,
    training: bool,
) -> Tuple[Dict[Tuple[int, int], float], List[NodeHopBound], MessageClosureBound]:
    """Returns ``({(query_id, node_id): B_v at the FINAL reached hop},
    full per-hop ledger, the full MessageClosureBound used — ``.total``
    for the combined value, ``.mu``/``.residual_U``/``.residual_V``/
    ``.residual_W`` for the individual per-component terms)``. ``B_h = 0``
    exactly at hop 0 for every query — the initial frontier state is the
    query relation embedding itself, untouched by any projection."""
    batch = int(head_ids.numel())
    device = head_ids.device
    num_rel = relation_embed.shape[0] // 2
    r_inv_ids = torch.where(relation_ids < num_rel, relation_ids + num_rel, relation_ids - num_rel)
    generator: Optional[torch.Generator] = (
        torch.Generator(device=device).manual_seed(int(seed)) if reasoner.selector_mode == "budgeted_bfs" else None
    )

    closure = message_closure_bound(reasoner.mu, reasoner.U, reasoner.V, reasoner.W, reasoner.projector)
    envelope = envelope_lipschitz_bound(reasoner.ln)

    frontier_query_id = torch.arange(batch, device=device)
    frontier_node = head_ids.clone()
    frontier_bound = torch.zeros(batch, device=device)
    ledger: List[NodeHopBound] = []

    for hop in range(reasoner.num_layers):
        pseudo_frontier = FrontierBatch(query_id=frontier_query_id, node=frontier_node, state=frontier_bound.unsqueeze(-1))
        cq, fr, src, rel, tgt = reasoner._select_step_edges(
            pseudo_frontier, csr, head_ids, relation_ids, tail_ids, r_inv_ids, training, generator,
        )
        if cq.numel() == 0:
            frontier_query_id, frontier_node, frontier_bound = cq, tgt, torch.zeros(0, device=device)
            break

        incoming_bound = frontier_bound[fr]  # B_u for each candidate edge's source, [C]
        edge_embed = relation_embed[rel]
        query_vec = query_vecs[cq]
        L_edge = message_sensitivity_bound_query_conditioned(reasoner.mu, reasoner.U, edge_embed, query_vec).value
        local_message_bound = closure.total.value + L_edge * incoming_bound  # [C]

        key = cq * csr.num_nodes + tgt
        unique_key, inverse = torch.unique(key, return_inverse=True)
        num_groups = unique_key.numel()
        summed_bound = torch.zeros(num_groups, device=device).index_add_(0, inverse, local_message_bound)
        group_counts = torch.zeros(num_groups, device=device).index_add_(0, inverse, torch.ones(inverse.numel(), device=device))
        mean_incoming_bound = summed_bound / group_counts.clamp_min(1)
        outgoing_bound = envelope.value * mean_incoming_bound

        next_query_id = torch.div(unique_key, csr.num_nodes, rounding_mode="floor")
        next_node = unique_key % csr.num_nodes
        for i in range(num_groups):
            ledger.append(NodeHopBound(
                query_id=int(next_query_id[i].item()), hop=hop, node_id=int(next_node[i].item()),
                num_incoming_messages=int(group_counts[i].item()),
                incoming_bound_mean=float(mean_incoming_bound[i].item()),
                local_closure_bound=closure.total.value,
                outgoing_bound=float(outgoing_bound[i].item()),
            ))
        frontier_query_id, frontier_node, frontier_bound = next_query_id, next_node, outgoing_bound

    # Wrapped as CertifiedBound (not a bare float): every consumer of this
    # dict (certify_path_query) requires an actual CertifiedBound instance
    # and checks `.valid()` itself — a proxy/empirical value can never be
    # silently substituted here, it would fail an isinstance check instead.
    final = {
        (int(q.item()), int(n.item())): CertifiedBound(
            value=float(b.item()), formula="B_v (multi-hop recurrence, gate13.4-v1)", assumptions=closure.total.assumptions,
        )
        for q, n, b in zip(frontier_query_id, frontier_node, frontier_bound)
    }
    return final, ledger, closure
