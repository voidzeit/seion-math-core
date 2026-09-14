"""The fast full-entity miner must be bit-exact with the reference miner.

``full_entity_miner_fast`` exists purely to remove per-row CUDA
synchronizations from the hard-negative mining inner loop.  It is only a
legitimate substitution if it returns identical tensors, so these tests compare
the two implementations exactly (not approximately) across randomized scorers,
batch shapes, candidate-block sizes, reciprocal relations, and hard_k values --
including the boundary case ``hard_k > candidate_block``, where the reference
clamps the per-block topk to ``end - start``.
"""

from __future__ import annotations

import numpy as np
import torch

from seion_kgr.data import tiny_kg
from seion_kgr.sota.full_entity_miner import mine_full_entity_hard_negatives
from seion_kgr.sota.full_entity_miner_fast import mine_full_entity_hard_negatives_fast


class _RandomScorer:
    """Deterministic pseudo-random scores that depend on (h, r, candidate)."""

    def __init__(self, seed: int) -> None:
        self.seed = seed

    def score_tail_candidates(self, h_ids, relation_ids, candidates):
        h = h_ids.unsqueeze(1).double()
        r = relation_ids.unsqueeze(1).double()
        c = candidates.unsqueeze(0).double()
        # A smooth but non-monotone mixture, so ties are rare and the topk
        # ordering is genuinely exercised.
        return torch.sin(1.7 * h + 2.3 * r + 0.9 * c + self.seed) + 0.3 * torch.cos(0.5 * c - h)


def _assert_identical(a, b):
    ids_ref, scores_ref = a
    ids_fast, scores_fast = b
    assert torch.equal(ids_ref, ids_fast), "hard-negative ids differ"
    assert torch.equal(scores_ref, scores_fast), "hard-negative scores differ"


def test_fast_miner_matches_reference_on_toy_kg_across_configurations():
    kg = tiny_kg()
    n = kg.num_entities
    rng = np.random.default_rng(20260810)
    checked = 0
    for seed in range(6):
        scorer = _RandomScorer(seed)
        for candidate_block in (1, 2, 3, n, n + 5):
            for hard_k in (1, 2, 3, 5):
                batch = int(rng.integers(1, 5))
                h = torch.from_numpy(rng.integers(0, n, size=batch).astype(np.int64))
                # Cover both original and reciprocal relation ids.
                r = torch.from_numpy(
                    rng.integers(0, 2 * kg.num_relations_original, size=batch).astype(np.int64)
                )
                gold = torch.from_numpy(rng.integers(0, n, size=batch).astype(np.int64))
                _assert_identical(
                    mine_full_entity_hard_negatives(
                        scorer, h, r, gold, kg, candidate_block=candidate_block, hard_k=hard_k
                    ),
                    mine_full_entity_hard_negatives_fast(
                        scorer, h, r, gold, kg, candidate_block=candidate_block, hard_k=hard_k
                    ),
                )
                checked += 1
    assert checked >= 100


def test_fast_miner_masks_gold_and_reciprocal_positives_like_reference():
    kg = tiny_kg()
    # Same two scenarios the reference miner's own tests pin down.
    h = torch.tensor([0])
    r = torch.tensor([0])
    gold = torch.tensor([1])
    ids_fast, _ = mine_full_entity_hard_negatives_fast(
        _RandomScorer(0), h, r, gold, kg, candidate_block=2, hard_k=2
    )
    assert 1 not in ids_fast[0].tolist()

    h = torch.tensor([1])
    r = torch.tensor([kg.num_relations_original])
    gold = torch.tensor([0])
    ids_fast, _ = mine_full_entity_hard_negatives_fast(
        _RandomScorer(1), h, r, gold, kg, candidate_block=3, hard_k=3
    )
    assert 0 not in ids_fast[0].tolist()


def test_fast_miner_rejects_malformed_inputs_like_reference():
    kg = tiny_kg()
    scorer = _RandomScorer(0)
    h = torch.tensor([0, 1])
    r = torch.tensor([0])
    gold = torch.tensor([1, 2])
    for bad in (
        dict(h_ids=h, relation_ids=r, gold_ids=gold),
        dict(h_ids=h.unsqueeze(0), relation_ids=h.unsqueeze(0), gold_ids=gold.unsqueeze(0)),
    ):
        try:
            mine_full_entity_hard_negatives_fast(scorer, kg=kg, **bad)
        except ValueError:
            pass
        else:  # pragma: no cover - guard
            raise AssertionError("expected ValueError for malformed inputs")

    for bad_kwargs in (dict(candidate_block=0), dict(hard_k=0)):
        try:
            mine_full_entity_hard_negatives_fast(
                scorer, torch.tensor([0]), torch.tensor([0]), torch.tensor([1]), kg, **bad_kwargs
            )
        except ValueError:
            pass
        else:  # pragma: no cover - guard
            raise AssertionError("expected ValueError for non-positive sizes")
