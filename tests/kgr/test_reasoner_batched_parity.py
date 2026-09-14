"""Gate 13.2 acceptance test (``campaigns/gate13/``): PASS_PATH_SCALING,
parity half.

``BatchedPathReasoner`` (CSR + vectorized frontier expansion,
``reasoner_batched.py``) must reproduce ``PathReasoner`` (the legacy
per-sample dict-BFS, ``reasoner.py``) bit-for-bit (within float tolerance)
on identical small graphs, identical weights (transferred via
``load_state_dict``, since both modules use the same submodule names by
construction), and ``selector_mode="full_neighborhood"`` (no randomness in
edge selection, so any divergence is a real implementation bug, not
sampling noise).
"""
from __future__ import annotations

import torch

from seion_kgr.frontier_ops import build_csr_adjacency
from seion_kgr.reasoner import Adjacency, PathReasoner
from seion_kgr.reasoner_batched import BatchedPathReasoner

TOLERANCE = 1e-4  # campaigns/gate13/preregistration.md §2 NONINFERIORITY_MARGIN


def _small_graph_adjacency(num_relations_original: int = 2):
    """10 nodes, several multi-hop chains, a node with two incoming edges
    from different sources in the same layer (to exercise the mean
    aggregation over incoming messages), and one node with no outgoing
    edges (a query whose frontier dies before ``num_layers`` — exercises
    the "empty frontier" path in both implementations)."""
    out_edges = {
        0: [(0, 1), (1, 2)],
        1: [(0, 3)],
        2: [(1, 3)],  # node 3 has two incoming edges (from 1 via r0, from 2 via r1) in the same layer
        3: [(0, 4), (1, 5)],
        4: [(0, 6)],
        5: [(1, 6)],  # node 6 also has two incoming edges, one layer later
        7: [(0, 8)],
        # node 9: no outgoing edges at all
    }
    return Adjacency(out_edges), 10


def _build_pair(seed: int, num_layers: int, proj_rank: int, dim: int = 8, rank: int = 4, max_neighbors: int = 16):
    torch.manual_seed(seed)
    legacy = PathReasoner(
        dim=dim, rank=rank, num_layers=num_layers, max_neighbors=max_neighbors,
        proj_rank=proj_rank, selector_mode="full_neighborhood",
    )
    batched = BatchedPathReasoner(
        dim=dim, rank=rank, num_layers=num_layers, max_neighbors=max_neighbors,
        proj_rank=proj_rank, selector_mode="full_neighborhood",
    )
    batched.load_state_dict(legacy.state_dict())
    return legacy, batched


def _run_parity_case(num_layers: int, proj_rank: int, training: bool):
    adjacency, num_nodes = _small_graph_adjacency()
    csr = build_csr_adjacency(adjacency, num_nodes)
    dim = 8
    legacy, batched = _build_pair(seed=0, num_layers=num_layers, proj_rank=proj_rank, dim=dim)

    num_relations_total = 4  # 2 original + 2 reciprocal
    torch.manual_seed(1)
    relation_embed = torch.randn(num_relations_total, dim)
    head_ids = torch.tensor([0, 1, 2, 7, 9])  # node 9 has no outgoing edges at all
    relation_ids = torch.tensor([0, 1, 0, 0, 0])
    tail_ids = torch.tensor([1, 3, 3, 8, 9])  # queried edge for the leakage-exclusion check
    query_vecs = relation_embed[relation_ids]

    legacy_frontiers = legacy.run_batch_frontiers(
        adjacency, relation_embed, head_ids, relation_ids, tail_ids, query_vecs, seed=0, training=training,
    )
    batched_frontier = batched.run_batch_frontiers(
        csr, relation_embed, head_ids, relation_ids, tail_ids, query_vecs, seed=0, training=training,
    )

    # Compare every node reached by the legacy reasoner (for every query),
    # PLUS a handful of never-reached nodes (to confirm both fall back to
    # the identical unreached_state), via the vectorized batch lookup.
    query_ids, node_ids, expected = [], [], []
    for b, frontier_dict in enumerate(legacy_frontiers):
        for node in range(num_nodes):
            query_ids.append(b)
            node_ids.append(node)
            expected.append(legacy.state_for_node(frontier_dict, node))
    query_ids_t = torch.tensor(query_ids)
    node_ids_t = torch.tensor(node_ids)
    expected_t = torch.stack(expected, dim=0)

    got_t = BatchedPathReasoner.state_for_node_batch(batched_frontier, query_ids_t, node_ids_t, num_nodes, batched.unreached_state)

    max_err = (got_t - expected_t).abs().max().item()
    assert max_err < TOLERANCE, f"num_layers={num_layers} proj_rank={proj_rank} training={training}: max abs error {max_err}"


def test_parity_two_layers_no_projector_training():
    _run_parity_case(num_layers=2, proj_rank=0, training=True)


def test_parity_two_layers_no_projector_eval():
    _run_parity_case(num_layers=2, proj_rank=0, training=False)


def test_parity_three_layers_with_projector():
    _run_parity_case(num_layers=3, proj_rank=3, training=True)


def test_parity_single_layer():
    _run_parity_case(num_layers=1, proj_rank=0, training=True)


def test_states_for_candidates_batch_matches_legacy_per_sample_lookup():
    adjacency, num_nodes = _small_graph_adjacency()
    csr = build_csr_adjacency(adjacency, num_nodes)
    dim = 8
    legacy, batched = _build_pair(seed=2, num_layers=2, proj_rank=0, dim=dim)

    num_relations_total = 4
    torch.manual_seed(3)
    relation_embed = torch.randn(num_relations_total, dim)
    head_ids = torch.tensor([0, 1, 2])
    relation_ids = torch.tensor([0, 1, 0])
    tail_ids = torch.tensor([1, 3, 3])
    query_vecs = relation_embed[relation_ids]

    legacy_frontiers = legacy.run_batch_frontiers(
        adjacency, relation_embed, head_ids, relation_ids, tail_ids, query_vecs, seed=0, training=True,
    )
    batched_frontier = batched.run_batch_frontiers(
        csr, relation_embed, head_ids, relation_ids, tail_ids, query_vecs, seed=0, training=True,
    )

    candidates = torch.arange(num_nodes).unsqueeze(0).expand(3, -1)  # [B=3, K=num_nodes]
    expected = torch.stack(
        [legacy.states_for_candidates(f, candidates[b]) for b, f in enumerate(legacy_frontiers)], dim=0,
    )
    got = BatchedPathReasoner.states_for_candidates_batch(
        batched_frontier, torch.arange(3), candidates, num_nodes, batched.unreached_state,
    )
    max_err = (got - expected).abs().max().item()
    assert max_err < TOLERANCE, f"states_for_candidates_batch max abs error {max_err}"
