"""Training-time hard-negative masking must not leak VALID membership.

``load_train_valid_only`` builds one pair of filter tables from TRAIN+VALID.
Those tables are right for evaluation (standard filtered protocol) but wrong for
masking training negatives: reusing them exempts every VALID gold from ever
receiving negative gradient for its own query, which inflates VALID metrics
without any TEST access being involved.

These tests pin the mechanism and the fix.
"""

from __future__ import annotations

import numpy as np

from seion_kgr.data import KnowledgeGraph, build_filters, reciprocal_closure
from seion_kgr.train_sratm_sealed import _train_only_filter_view


def _kg() -> KnowledgeGraph:
    # TRAIN: (0,0,1). VALID: (0,0,2) -- same query key (0,0), different tail.
    train_orig = [(0, 0, 1)]
    valid = [(0, 0, 2)]
    tails, heads = build_filters(train_orig, valid, [])
    return KnowledgeGraph(
        num_entities=4,
        num_relations_original=1,
        train=np.asarray(reciprocal_closure(train_orig, 1), dtype=np.int64),
        valid=valid,
        test=[],
        ent2id={f"e{i}": i for i in range(4)},
        rel2id={"r0": 0},
        tails_of_hr=tails,
        heads_of_rt=heads,
    )


def test_train_valid_tables_exempt_the_valid_gold_this_is_the_leak():
    kg = _kg()
    # Entity 2 is a VALID-only tail for query (0,0); the shipped tables hide it.
    assert 2 in kg.tails_of_hr[(0, 0)].tolist()


def test_train_only_view_stops_exempting_the_valid_gold():
    view = _train_only_filter_view(_kg())
    masked = view.tails_of_hr[(0, 0)].tolist()
    assert 1 in masked, "the genuine TRAIN positive must still be masked"
    assert 2 not in masked, "the VALID gold must be minable as a negative"


def test_train_only_view_preserves_every_other_field():
    kg = _kg()
    view = _train_only_filter_view(kg)
    assert view.num_entities == kg.num_entities
    assert view.num_relations_original == kg.num_relations_original
    assert np.array_equal(view.train, kg.train)
    assert view.valid == kg.valid
    assert view.test == kg.test
    assert view.ent2id == kg.ent2id and view.rel2id == kg.rel2id
    # The original tables must not be mutated in place.
    assert 2 in kg.tails_of_hr[(0, 0)].tolist()


def test_train_only_view_ignores_reciprocal_rows_when_rebuilding():
    kg = _kg()
    view = _train_only_filter_view(kg)
    # reciprocal_closure added (1,1,0); filters are keyed on original relations
    # only, so no reciprocal relation id may appear as a filter key.
    assert all(r < kg.num_relations_original for _, r in view.tails_of_hr)
    assert all(r < kg.num_relations_original for r, _ in view.heads_of_rt)
    # The reciprocal direction of the TRAIN triple is still represented.
    assert view.heads_of_rt[(0, 1)].tolist() == [0]
