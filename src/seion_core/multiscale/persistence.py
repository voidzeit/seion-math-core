from __future__ import annotations

from .alignment import align_bases


def basis_persistence(left, right) -> float:
    _, aligned = align_bases(left, right)
    return float(((left - aligned) ** 2).sum() ** 0.5)

