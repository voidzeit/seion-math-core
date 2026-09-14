"""Explicit data-role contract for the exploratory teacher track."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable


@dataclass(frozen=True)
class SplitContract:
    train_ids: frozenset[str]
    calibration_ids: frozenset[str]
    valid_ids: frozenset[str]
    test_ids: frozenset[str]

    def __post_init__(self) -> None:
        if not self.calibration_ids.issubset(self.train_ids):
            raise ValueError("calibration_ids must be a subset of train_ids")
        if self.train_ids & self.test_ids or self.valid_ids & self.test_ids:
            raise ValueError("train/valid identifiers must be disjoint from test")

    @classmethod
    def from_iterables(cls, train: Iterable[str], calibration: Iterable[str], valid: Iterable[str], test: Iterable[str]) -> "SplitContract":
        return cls(frozenset(train), frozenset(calibration), frozenset(valid), frozenset(test))

    def assert_discovery_ids(self, ids: Iterable[str]) -> None:
        leaked = set(ids) & self.test_ids
        if leaked:
            raise ValueError(f"test identifiers entered discovery: {sorted(leaked)[:3]}")

    def assert_test_only(self, ids: Iterable[str]) -> None:
        if set(ids) - self.test_ids:
            raise ValueError("final test evaluation received identifiers outside test")
