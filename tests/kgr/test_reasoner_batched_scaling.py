"""Gate 13.2 acceptance test (``campaigns/gate13/``): PASS_PATH_SCALING,
scaling half.

The legacy ``PathReasoner.run_batch_frontiers`` (``reasoner.py``) has a
measured failure mode: a live timing probe on full WN18RR at
``batch_size=256`` ran 8+ minutes without completing a single epoch
(``campaigns/gate12/preregistration.md`` §11's deviation log) — its
per-sample Python ``for b in range(batch)`` dict-BFS does not scale.

This test drives ``BatchedPathReasoner`` (CSR + vectorized frontier
expansion) over every training batch of REAL, hash-verified WN18RR data
for one full epoch's worth of ``run_batch_frontiers`` calls (the
identified bottleneck operation itself — this test does not additionally
run backward/optimizer steps, since those are unaffected by this gate)
and asserts completion within a generous, explicit wall-clock ceiling.
"""
from __future__ import annotations

import time
from pathlib import Path

import pytest
import torch

from seion_kgr.data import load_knowledge_graph
from seion_kgr.frontier_ops import build_csr_adjacency
from seion_kgr.reasoner import Adjacency
from seion_kgr.reasoner_batched import BatchedPathReasoner

DATA_DIR = Path(__file__).resolve().parents[2] / "data" / "WN18RR"
WALL_CLOCK_CEILING_SEC = 180.0  # generous vs. the legacy reasoner's 8+ minutes for the SAME workload

pytestmark = pytest.mark.slow


@pytest.mark.skipif(not DATA_DIR.is_dir(), reason="data/WN18RR not present in this checkout")
def test_batched_reasoner_completes_a_full_wn18rr_epoch_within_budget():
    kg = load_knowledge_graph(str(DATA_DIR / "train.txt"), str(DATA_DIR / "valid.txt"), str(DATA_DIR / "test.txt"))
    adjacency = Adjacency.build(kg)
    csr = build_csr_adjacency(adjacency, num_nodes=kg.num_entities)

    dim, rank, num_layers, max_neighbors, batch_size = 64, 32, 2, 32, 256
    torch.manual_seed(0)
    reasoner = BatchedPathReasoner(
        dim=dim, rank=rank, num_layers=num_layers, max_neighbors=max_neighbors, proj_rank=0,
        selector_mode="budgeted_bfs",  # the real train.py default, not the parity test's full_neighborhood
    )
    relation_embed = torch.randn(kg.num_relations_total, dim)

    train = torch.from_numpy(kg.train)  # [N, 3], reciprocal-closed, exactly what train.py iterates over
    num_batches = (train.shape[0] + batch_size - 1) // batch_size

    start = time.time()
    for i in range(num_batches):
        batch = train[i * batch_size : (i + 1) * batch_size]
        h_ids, r_ids, t_ids = batch[:, 0], batch[:, 1], batch[:, 2]
        query_vecs = relation_embed[r_ids]
        frontier = reasoner.run_batch_frontiers(csr, relation_embed, h_ids, r_ids, t_ids, query_vecs, seed=i, training=True)
        assert torch.isfinite(frontier.state).all() if frontier.state.numel() else True
    wall_sec = time.time() - start

    print(f"\n[Gate 13.2] {num_batches} batches (batch_size={batch_size}) over {train.shape[0]} triples "
          f"({kg.num_entities} entities, {csr.num_edges} directed edges) in {wall_sec:.1f}s")
    assert wall_sec < WALL_CLOCK_CEILING_SEC, (
        f"full-epoch reasoner traversal took {wall_sec:.1f}s, exceeding the {WALL_CLOCK_CEILING_SEC}s ceiling "
        "(legacy reasoner did not complete this workload in 8+ minutes, per Gate 12's deviation log)"
    )
