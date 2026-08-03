"""Gate 13.4 acceptance test (``campaigns/gate13/``): exhaustive small-graph
sweep across projector ranks and seeds — the mission brief's "grafo
diminuto, enumerar todas las consultas/candidatos/proyectores/rangos/
semillas... false certificates = 0" requirement.

For every (seed, projector rank) combination, builds a reference
(uncompressed) and compressed `BatchedPathReasoner` pair sharing the SAME
weights (never two independently trained models), scores every candidate
entity for every head node under BOTH models, and certifies using the
compressed model's own margin. A certificate is FALSE if the reference
model (ground truth) would have ranked the gold candidate differently
than what the certificate vouches for — checked directly, not assumed.
"""
from __future__ import annotations

import torch
import torch.nn as nn

from seion_kgr.certification import certify_path_query
from seion_kgr.certified_path import propagate_certified_state_bounds
from seion_kgr.frontier_ops import build_csr_adjacency
from seion_kgr.path_reasoner_output import PathReasonerOutput
from seion_kgr.reasoner import Adjacency
from seion_kgr.reasoner_batched import BatchedPathReasoner


def _small_graph():
    out_edges = {
        0: [(0, 1), (1, 2)], 1: [(0, 3)], 2: [(1, 3)],
        3: [(0, 4), (1, 5)], 4: [(0, 6)], 5: [(1, 6)], 7: [(0, 8)],
    }
    return Adjacency(out_edges), 10


def _build_ref_cmp_pair(dim, rank, proj_rank, num_layers, seed):
    torch.manual_seed(seed)
    ref = BatchedPathReasoner(dim=dim, rank=rank, num_layers=num_layers, max_neighbors=16, proj_rank=0, selector_mode="full_neighborhood")
    cmp = BatchedPathReasoner(dim=dim, rank=rank, num_layers=num_layers, max_neighbors=16, proj_rank=proj_rank, selector_mode="full_neighborhood")
    sd, cmp_sd = ref.state_dict(), cmp.state_dict()
    for k in sd:
        if k in cmp_sd:
            cmp_sd[k] = sd[k]
    cmp.load_state_dict(cmp_sd)
    return ref, cmp


def test_exhaustive_zero_false_certificates_across_ranks_and_seeds():
    adjacency, num_nodes = _small_graph()
    csr = build_csr_adjacency(adjacency, num_nodes)
    dim, rank, num_layers = 8, 4, 1

    total_certified = 0
    total_queries = 0
    false_certificates = 0

    for seed in (0, 1, 2):
        for proj_rank in (1, 2, 3, 5):
            ref, cmp = _build_ref_cmp_pair(dim, rank, proj_rank, num_layers, seed)
            torch.manual_seed(seed + 1000)
            entity = nn.Embedding(num_nodes, dim)
            nn.init.xavier_uniform_(entity.weight)
            relation_embed = torch.randn(4, dim)

            heads = torch.arange(num_nodes)
            rels = torch.zeros(num_nodes, dtype=torch.long)
            query_vecs = relation_embed[rels]

            # dummy tail_ids for exclusion purposes (0 is fine, exhaustive
            # candidate scoring below does not depend on it being "the" gold)
            dummy_tails = torch.zeros(num_nodes, dtype=torch.long)
            frontier_ref = ref.run_batch_frontiers(csr, relation_embed, heads, rels, dummy_tails, query_vecs, seed=seed, training=False)
            frontier_cmp = cmp.run_batch_frontiers(csr, relation_embed, heads, rels, dummy_tails, query_vecs, seed=seed, training=False)
            bounds, _, _ = propagate_certified_state_bounds(cmp, csr, relation_embed, heads, rels, dummy_tails, query_vecs, seed=seed, training=False)

            out_ref = PathReasonerOutput.from_batched_frontier(frontier_ref, num_nodes, ref.unreached_state)
            out_cmp = PathReasonerOutput.from_batched_frontier(frontier_cmp, num_nodes, cmp.unreached_state)

            candidates = torch.arange(num_nodes)
            for qi in range(num_nodes):
                q_ids = torch.full((num_nodes,), qi, dtype=torch.long)
                states_ref = out_ref.state_for(q_ids, candidates)  # [num_nodes, dim]
                states_cmp = out_cmp.state_for(q_ids, candidates)
                cand_emb = entity.weight
                scores_ref_all = (states_ref * cand_emb).sum(dim=-1) / (dim ** 0.5)
                scores_cmp_all = (states_cmp * cand_emb).sum(dim=-1) / (dim ** 0.5)

                # sweep several gamma magnitudes per query — small values are
                # where certification is realistically achievable given how
                # loose the LayerNorm envelope bound is (see test_gate13_
                # certification_bounds.py's docstring)
                for gamma in (1e-6, 1e-5, 1e-4, 1e-3, 1e-2, 0.5):
                    for gold in range(num_nodes):
                        total_queries += 1
                        scored_cmp = gamma * scores_cmp_all.clone()
                        bound = bounds.get((qi, gold))
                        result = certify_path_query(
                            (seed, proj_rank, qi, gamma, gold), scored_cmp, gold, bound, gamma, entity.weight, dim,
                        )
                        if result.certified_rank_stable:
                            total_certified += 1
                            scored_ref = gamma * scores_ref_all.clone()
                            ref_rank = int((scored_ref > scored_ref[gold]).sum().item())
                            cmp_rank = int((scored_cmp > scored_cmp[gold]).sum().item())
                            if ref_rank != cmp_rank:
                                false_certificates += 1

    assert total_queries > 0
    assert false_certificates == 0, f"{false_certificates} false certificate(s) out of {total_certified} certified (of {total_queries} total)"
    # Not requiring total_certified > 0 here (this is the STRICTER/exhaustive
    # zero-false-certificates check across small gamma AND large gamma,
    # including cases expected to be NOT_CERTIFIED); the real-run test
    # separately establishes coverage > 0 with a real trained gate.
