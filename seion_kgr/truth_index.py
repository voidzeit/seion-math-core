"""Two deliberately incompatible truth tables.

Blocker B-0014 happened because one object served two purposes: the known-positive
tables built by ``build_filters`` are correct for *evaluation* (the filtered
protocol must not penalise a model for ranking another true triple highly) and
catastrophic for *training* (masking a held-out gold exempts it from ever
receiving negative gradient). Nothing in the type system objected, and no
file-access sentinel could see it.

This module makes the distinction structural rather than nominal:

* :class:`TrainTruthIndex` is built from TRAIN triples only and is the *only*
  object a loss is allowed to consult;
* :class:`EvaluationFilterIndex` is built from all splits and is the *only*
  object a filtered evaluator is allowed to consult.

Neither is constructible from the other, and neither exposes the other's
accessor. Passing the wrong one raises rather than silently degrading, so the
B-0014 mistake becomes a type error instead of a matter of discipline.
"""

from __future__ import annotations

from typing import Iterable, Mapping, Sequence

import numpy as np

TripleI = tuple[int, int, int]


class _TruthTable:
    """Shared storage. Not public: the two subclasses must stay incompatible."""

    __slots__ = ("_tails", "_heads", "_provenance")

    def __init__(self, tails: Mapping, heads: Mapping, provenance: str) -> None:
        self._tails = tails
        self._heads = heads
        self._provenance = provenance

    @property
    def provenance(self) -> str:
        return self._provenance

    def __repr__(self) -> str:  # pragma: no cover - diagnostic only
        return f"{type(self).__name__}(provenance={self._provenance!r}, keys={len(self._tails)})"

    @staticmethod
    def _build(groups: Sequence[Sequence[TripleI]]):
        tails: dict[tuple[int, int], set] = {}
        heads: dict[tuple[int, int], set] = {}
        for group in groups:
            for h, r, t in group:
                tails.setdefault((int(h), int(r)), set()).add(int(t))
                heads.setdefault((int(r), int(t)), set()).add(int(h))
        to_np = lambda d: {k: np.asarray(sorted(v), dtype=np.int64) for k, v in d.items()}
        return to_np(tails), to_np(heads)


class TrainTruthIndex(_TruthTable):
    """Multi-positive targets derived from TRAIN alone.

    This is the only truth table a training objective may consult. It carries no
    VALID or TEST membership, so a held-out gold is an ordinary candidate and
    receives gradient like any other entity.
    """

    @classmethod
    def from_train(cls, train_triples: Iterable[TripleI]) -> "TrainTruthIndex":
        tails, heads = cls._build([list(train_triples)])
        return cls(tails, heads, provenance="TRAIN_ONLY")

    def train_tails(self, head: int, relation: int) -> np.ndarray:
        return self._tails.get((int(head), int(relation)), _EMPTY)

    def train_heads(self, relation: int, tail: int) -> np.ndarray:
        return self._heads.get((int(relation), int(tail)), _EMPTY)


class EvaluationFilterIndex(_TruthTable):
    """Known positives across every split, for filtered ranking only.

    Consulting this during training is exactly the B-0014 defect. It therefore
    exposes accessors under different names from :class:`TrainTruthIndex`, so a
    training routine written against the training API fails loudly if handed one
    of these by mistake.
    """

    @classmethod
    def from_splits(
        cls,
        train_triples: Iterable[TripleI],
        valid_triples: Iterable[TripleI],
        test_triples: Iterable[TripleI],
    ) -> "EvaluationFilterIndex":
        tails, heads = cls._build([list(train_triples), list(valid_triples), list(test_triples)])
        return cls(tails, heads, provenance="TRAIN_PLUS_VALID_PLUS_TEST")

    @classmethod
    def from_train_and_valid(
        cls, train_triples: Iterable[TripleI], valid_triples: Iterable[TripleI]
    ) -> "EvaluationFilterIndex":
        """Sealed variant: the conservative filter used when TEST stays closed."""
        tails, heads = cls._build([list(train_triples), list(valid_triples)])
        return cls(tails, heads, provenance="TRAIN_PLUS_VALID")

    def filtered_tails(self, head: int, relation: int) -> np.ndarray:
        return self._tails.get((int(head), int(relation)), _EMPTY)

    def filtered_heads(self, relation: int, tail: int) -> np.ndarray:
        return self._heads.get((int(relation), int(tail)), _EMPTY)


_EMPTY = np.empty(0, dtype=np.int64)


def require_train_truth(index: object) -> TrainTruthIndex:
    """Gate for training code paths. Rejects evaluation tables explicitly."""
    if isinstance(index, EvaluationFilterIndex):
        raise TypeError(
            "B-0014: an EvaluationFilterIndex reached a training path. Evaluation "
            f"filters (provenance={index.provenance!r}) carry held-out membership and "
            "must never shape the training objective. Build a TrainTruthIndex instead."
        )
    if not isinstance(index, TrainTruthIndex):
        raise TypeError(f"expected TrainTruthIndex, got {type(index).__name__}")
    return index


def require_evaluation_filter(index: object) -> EvaluationFilterIndex:
    """Gate for evaluation code paths. Rejects train-only tables explicitly."""
    if isinstance(index, TrainTruthIndex):
        raise TypeError(
            "a TrainTruthIndex reached a filtered evaluator; filtered ranking needs "
            "known positives from every split or the metric is not the standard one"
        )
    if not isinstance(index, EvaluationFilterIndex):
        raise TypeError(f"expected EvaluationFilterIndex, got {type(index).__name__}")
    return index
