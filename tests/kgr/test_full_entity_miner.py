from __future__ import annotations

import numpy as np
import torch

from seion_kgr.data import tiny_kg
from seion_kgr.sota.full_entity_miner import mine_full_entity_hard_negatives


class _ToyScorer:
    def score_tail_candidates(self, h_ids, relation_ids, candidates):
        # Candidate 2 is the strongest valid negative; the gold/known-positive
        # candidate 1 must be filtered.
        scores = candidates.float().unsqueeze(0).expand(h_ids.shape[0], -1).clone()
        scores[0, candidates == 2] = 100.0
        return scores


def test_full_entity_miner_filters_known_positives_and_keeps_topk():
    kg = tiny_kg()
    h = torch.tensor([0])
    r = torch.tensor([0])
    gold = torch.tensor([1])
    ids, scores = mine_full_entity_hard_negatives(_ToyScorer(), h, r, gold, kg, candidate_block=2, hard_k=2)
    assert ids.shape == (1, 2)
    assert 1 not in ids[0].tolist()
    assert 2 in ids[0].tolist()
    assert torch.isfinite(scores).all()


def test_full_entity_miner_filters_reciprocal_known_positives():
    kg = tiny_kg()
    # Original triples include (0, 0, 1) and (1, 0, 2), therefore the
    # reciprocal query (1, 2, ?) must filter tails 0 and any supplied gold.
    h = torch.tensor([1])
    r = torch.tensor([kg.num_relations_original])
    gold = torch.tensor([0])
    ids, _ = mine_full_entity_hard_negatives(
        _ToyScorer(), h, r, gold, kg, candidate_block=3, hard_k=3
    )
    assert 0 not in ids[0].tolist()
