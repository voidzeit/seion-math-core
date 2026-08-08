"""Monotone registry for certified extremal lower/upper bands."""

from __future__ import annotations

from dataclasses import dataclass, replace


@dataclass(frozen=True, slots=True)
class ExtremalRecord:
    topology: str
    k: int
    eta: float
    field: str
    dimension: int | None
    projector_rank: int | None
    lower_bound: float
    upper_bound: float
    lower_certificate: str
    upper_certificate: str
    proof_status: str
    source_commit: str

    def __post_init__(self) -> None:
        if self.k < 0 or not 0.0 <= self.eta <= 1.0:
            raise ValueError("invalid extremal coordinates")
        if self.lower_bound < 0.0 or self.upper_bound < self.lower_bound:
            raise ValueError("invalid extremal lower/upper band")

    @property
    def gap(self) -> float:
        return self.upper_bound - self.lower_bound

    @property
    def relative_gap(self) -> float:
        return self.gap / self.upper_bound if self.upper_bound > 0.0 else 0.0

    @property
    def status(self) -> str:
        if self.upper_bound <= 0.0:
            return "EXACTLY_ZERO_BY_THEOREM"
        if self.relative_gap <= 1.0e-10:
            return "EXACTLY_DETERMINED_POSITIVE"
        if self.lower_bound > 0.0:
            return "POSITIVE_LOWER_BOUND_WITH_NONZERO_GAP"
        return "NO_POSITIVE_LOWER_BOUND_OBTAINED"


def merge_extremal_records(existing: ExtremalRecord, incoming: ExtremalRecord) -> ExtremalRecord:
    """Merge evidence monotonically for one fixed extremal cell."""

    key = (existing.topology, existing.k, existing.eta, existing.field, existing.dimension, existing.projector_rank)
    incoming_key = (incoming.topology, incoming.k, incoming.eta, incoming.field, incoming.dimension, incoming.projector_rank)
    if key != incoming_key:
        raise ValueError("only records for the same extremal cell can be merged")
    if incoming.upper_bound > existing.upper_bound + 1.0e-12:
        raise ValueError("an upper-bound update may only tighten the existing upper bound")
    lower = max(existing.lower_bound, incoming.lower_bound)
    upper = min(existing.upper_bound, incoming.upper_bound)
    if lower > upper + 1.0e-12:
        raise ValueError("merged lower/upper evidence is inconsistent")
    return replace(
        existing,
        lower_bound=lower,
        upper_bound=upper,
        lower_certificate=f"{existing.lower_certificate}; {incoming.lower_certificate}",
        upper_certificate=f"{existing.upper_certificate}; {incoming.upper_certificate}",
        proof_status=incoming.proof_status,
        source_commit=incoming.source_commit,
    )
