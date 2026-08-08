"""Sound certificate selection by minimum certified upper bound."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Mapping


@dataclass(frozen=True, slots=True)
class CertificateCandidate:
    name: str
    bound: float
    certified: bool
    metadata: Mapping[str, object] | None = None

    def __post_init__(self) -> None:
        if not self.name or self.bound < 0.0:
            raise ValueError("certificate candidate must have a name and nonnegative bound")


@dataclass(frozen=True, slots=True)
class CertificateSelection:
    selected: CertificateCandidate
    considered: tuple[CertificateCandidate, ...]
    rejected_uncertified: tuple[CertificateCandidate, ...]


def select_best_sound_certificate(candidates: tuple[CertificateCandidate, ...]) -> CertificateSelection:
    if not candidates:
        raise ValueError("at least one certificate candidate is required")
    certified = tuple(candidate for candidate in candidates if candidate.certified)
    rejected = tuple(candidate for candidate in candidates if not candidate.certified)
    if not certified:
        raise ValueError("no sound certificate candidate is available")
    selected = min(certified, key=lambda candidate: (candidate.bound, candidate.name))
    return CertificateSelection(selected, certified, rejected)
