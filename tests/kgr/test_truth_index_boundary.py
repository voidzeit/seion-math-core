"""The two truth tables must not be interchangeable.

B-0014 was a single object used for two incompatible purposes. These tests pin
that the replacement cannot repeat it: no conversion path, no shared accessor
name, and explicit rejection at each gate.
"""

from __future__ import annotations

import numpy as np
import pytest

from seion_kgr.truth_index import (
    EvaluationFilterIndex,
    TrainTruthIndex,
    require_evaluation_filter,
    require_train_truth,
)

TRAIN = [(0, 0, 1), (0, 0, 2), (3, 1, 4)]
VALID = [(0, 0, 7)]
TEST = [(0, 0, 9)]


def test_train_index_carries_no_heldout_membership():
    idx = TrainTruthIndex.from_train(TRAIN)
    tails = idx.train_tails(0, 0).tolist()
    assert tails == [1, 2]
    assert 7 not in tails and 9 not in tails, "VALID/TEST must be invisible to training"
    assert idx.provenance == "TRAIN_ONLY"


def test_evaluation_index_carries_every_split():
    idx = EvaluationFilterIndex.from_splits(TRAIN, VALID, TEST)
    assert idx.filtered_tails(0, 0).tolist() == [1, 2, 7, 9]
    assert idx.provenance == "TRAIN_PLUS_VALID_PLUS_TEST"


def test_sealed_evaluation_index_stops_at_valid():
    idx = EvaluationFilterIndex.from_train_and_valid(TRAIN, VALID)
    assert idx.filtered_tails(0, 0).tolist() == [1, 2, 7]
    assert idx.provenance == "TRAIN_PLUS_VALID"


def test_training_gate_rejects_an_evaluation_filter():
    bad = EvaluationFilterIndex.from_splits(TRAIN, VALID, TEST)
    with pytest.raises(TypeError, match="B-0014"):
        require_train_truth(bad)


def test_evaluation_gate_rejects_a_train_index():
    with pytest.raises(TypeError):
        require_evaluation_filter(TrainTruthIndex.from_train(TRAIN))


def test_gates_accept_their_own_kind():
    assert isinstance(require_train_truth(TrainTruthIndex.from_train(TRAIN)), TrainTruthIndex)
    ev = EvaluationFilterIndex.from_splits(TRAIN, VALID, TEST)
    assert isinstance(require_evaluation_filter(ev), EvaluationFilterIndex)


def test_accessor_names_do_not_overlap():
    """A training path written against train_tails cannot silently accept the other."""
    train_api = {"train_tails", "train_heads"}
    eval_api = {"filtered_tails", "filtered_heads"}
    assert train_api <= set(dir(TrainTruthIndex))
    assert not (train_api & set(dir(EvaluationFilterIndex))), "accessor names must not overlap"
    assert eval_api <= set(dir(EvaluationFilterIndex))
    assert not (eval_api & set(dir(TrainTruthIndex)))


def test_there_is_no_conversion_path_between_them():
    train = TrainTruthIndex.from_train(TRAIN)
    ev = EvaluationFilterIndex.from_splits(TRAIN, VALID, TEST)
    for src, dst in ((train, EvaluationFilterIndex), (ev, TrainTruthIndex)):
        constructors = [n for n in dir(dst) if n.startswith("from_")]
        for name in constructors:
            with pytest.raises(Exception):
                getattr(dst, name)(src)


def test_missing_keys_return_empty_not_none():
    idx = TrainTruthIndex.from_train(TRAIN)
    out = idx.train_tails(999, 999)
    assert isinstance(out, np.ndarray) and out.size == 0
