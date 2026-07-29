from __future__ import annotations

import itertools

import numpy as np

from ..algebra.ternary_law import TernaryLaw


def _levi_civita(index: tuple[int, ...]) -> int:
    if len(set(index)) != len(index):
        return 0
    inversions = sum(index[i] > index[j] for i in range(len(index)) for j in range(i + 1, len(index)))
    return -1 if inversions % 2 else 1


def filippov_4d_law(dtype=np.float64) -> TernaryLaw:
    tensor = np.zeros((4, 4, 4, 4), dtype=dtype)
    for a, b, c, d in itertools.product(range(4), repeat=4):
        tensor[a, b, c, d] = _levi_civita((a, b, c, d))
    return TernaryLaw(tensor, "filippov_4d_volume_form")

