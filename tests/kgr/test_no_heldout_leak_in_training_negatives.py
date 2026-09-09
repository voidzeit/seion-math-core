"""Standing detector for B-0014: held-out membership must not shape training.

The defect is not a forbidden file access -- no sentinel can see it. It is the
reuse of evaluation filter tables to generate *training* negatives, which makes
every held-out gold unsamplable and therefore immune to negative gradient.

The control here is statistical and route-agnostic: draw negatives for training
queries that carry held-out-only golds, and assert those golds show up at
roughly the rate chance predicts. A leaking route yields exactly zero.

Measured on real FB15K-237 (`.ai/LEAKAGE_FINDING_MINING_FILTER_2026-08-10.md`):
0/1,048,576 draws with the shipped tables versus 154 observed against 155.0
expected once the TRAIN-only view is used.
"""

from __future__ import annotations

import numpy as np
import torch

from seion_kgr.data import (
    KnowledgeGraph,
    build_filters,
    reciprocal_closure,
    sample_negatives,
    train_only_filter_view,
)

NUM_ENTITIES = 400
NEG_K = 64


def _kg() -> KnowledgeGraph:
    """One relation; entity 0 queries every tail in TRAIN, tails 300+ held out."""
    train_orig = [(0, 0, t) for t in range(1, 200)]
    valid = [(0, 0, t) for t in range(300, 340)]
    test = [(0, 0, t) for t in range(340, 380)]
    tails, heads = build_filters(train_orig, valid, test)
    return KnowledgeGraph(
        num_entities=NUM_ENTITIES,
        num_relations_original=1,
        train=np.asarray(reciprocal_closure(train_orig, 1), dtype=np.int64),
        valid=valid,
        test=test,
        ent2id={f"e{i}": i for i in range(NUM_ENTITIES)},
        rel2id={"r0": 0},
        tails_of_hr=tails,
        heads_of_rt=heads,
    )


def _chance_expectation(rows: int) -> float:
    """How often a correct trainer would sample a held-out gold.

    The reference is always the TRAIN-only view: chance must be measured
    against the pool a non-leaking trainer draws from. Computing it from the
    leaking kg's own tables would give zero -- every held-out gold is masked
    there -- and the test would vacuously "pass".
    """
    reference = train_only_filter_view(_kg())
    heldout = {t for _, _, t in list(reference.valid) + list(reference.test)}
    forbidden = set(reference.tails_of_hr.get((0, 0), np.empty(0, dtype=np.int64)).tolist())
    pool = NUM_ENTITIES - len(forbidden)
    return rows * NEG_K * len(heldout - forbidden) / pool


def _heldout_hits(kg: KnowledgeGraph, rows: int = 256) -> int:
    heldout = {t for _, _, t in list(kg.valid) + list(kg.test)}
    h = torch.zeros(rows, dtype=torch.long)
    r = torch.zeros(rows, dtype=torch.long)
    t = torch.ones(rows, dtype=torch.long)
    negs = sample_negatives(h, r, t, kg, NEG_K, np.random.default_rng(7), torch.device("cpu"))
    return int(sum(len(heldout.intersection(row.tolist())) for row in negs))


def test_shipped_tables_make_heldout_golds_unsamplable_this_is_the_defect():
    expected = _chance_expectation(256)
    assert expected > 50, "fixture must give chance a real opportunity"
    assert _heldout_hits(_kg()) == 0, (
        "regression guard: this documents the leaking behaviour of the shipped "
        "filter tables, so the fixture stays meaningful"
    )


def test_train_only_view_restores_chance_rate_sampling():
    hits = _heldout_hits(train_only_filter_view(_kg()))
    expected = _chance_expectation(256)
    assert hits > 0, "held-out golds must be samplable as negatives"
    # Generous band: this is a leak detector, not a uniformity test.
    assert 0.5 * expected < hits < 1.5 * expected, (
        f"held-out golds sampled {hits} times, chance expects {expected:.1f}"
    )


def test_train_positives_are_still_excluded_after_the_fix():
    view = train_only_filter_view(_kg())
    train_tails = {t for _, _, t in [(0, 0, x) for x in range(1, 200)]}
    h = torch.zeros(128, dtype=torch.long)
    r = torch.zeros(128, dtype=torch.long)
    t = torch.ones(128, dtype=torch.long)
    negs = sample_negatives(h, r, t, view, NEG_K, np.random.default_rng(11), torch.device("cpu"))
    leaked = train_tails.intersection(negs.flatten().tolist())
    assert not leaked, f"genuine TRAIN positives must stay excluded, saw {sorted(leaked)[:5]}"
