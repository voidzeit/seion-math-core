"""Certified finite-dimensional enclosures for multilinear operator norms.

The module deliberately separates attained lower values from certified upper
enclosures.  No alternating/power iteration result is labelled exact.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Sequence

import mpmath as mp
import numpy as np


@dataclass(frozen=True, slots=True)
class NormEnclosure:
    lower: float
    upper: float
    method: str
    certified: bool
    lower_method: str
    upper_method: str
    fallback_used: bool = False

    def __post_init__(self) -> None:
        if min(self.lower, self.upper) < -1.0e-15 or self.upper + 1.0e-12 < self.lower:
            raise ValueError("invalid norm enclosure")

    @property
    def gap(self) -> float:
        return self.upper - self.lower

    @property
    def relative_gap(self) -> float:
        return self.gap / self.upper if self.upper > 0.0 else 0.0


def _validate_tensor(tensor: np.ndarray) -> np.ndarray:
    data = np.asarray(tensor)
    if data.ndim < 2:
        raise ValueError("a multilinear tensor must have output and at least one input axis")
    if not np.issubdtype(data.dtype, np.number):
        raise TypeError("tensor must have a numeric dtype")
    return data


def _attained_basis_lower(data: np.ndarray) -> float:
    return float(np.max(np.abs(data))) if data.size else 0.0


def _outward(value: float) -> float:
    return float(np.nextafter(float(value), np.inf))


def frobenius_enclosure(tensor: np.ndarray) -> NormEnclosure:
    data = _validate_tensor(tensor)
    upper = _outward(float(np.linalg.norm(data.ravel())))
    return NormEnclosure(
        lower=_attained_basis_lower(data),
        upper=upper,
        method="frobenius",
        certified=True,
        lower_method="basis-vector-attained-entry",
        upper_method="||T||_op <= ||T||_F",
        fallback_used=False,
    )


def flattening_enclosure(tensor: np.ndarray, *, split: int = 1) -> NormEnclosure:
    """Use an induced-norm upper bound on a tensor flattening.

    The flattening spectral norm upper bound is certified through
    ``sqrt(||A||_1 ||A||_inf)``; no power iteration is used.
    """

    data = _validate_tensor(tensor)
    if not 1 <= split < data.ndim:
        raise ValueError("split must separate output/input flattening axes")
    rows = int(np.prod(data.shape[:split]))
    cols = int(np.prod(data.shape[split:]))
    matrix = np.reshape(data, (rows, cols))
    abs_matrix = np.abs(matrix)
    one_norm = float(np.max(np.sum(abs_matrix, axis=0))) if cols else 0.0
    inf_norm = float(np.max(np.sum(abs_matrix, axis=1))) if rows else 0.0
    upper = _outward(float(np.sqrt(one_norm * inf_norm)))
    return NormEnclosure(
        lower=_attained_basis_lower(data),
        upper=upper,
        method=f"flattening_induced(split={split})",
        certified=True,
        lower_method="basis-vector-attained-entry",
        upper_method="||A||_2 <= sqrt(||A||_1 ||A||_inf)",
        fallback_used=False,
    )


def validated_interval_enclosure(tensor: np.ndarray, *, precision_bits: int = 160) -> NormEnclosure:
    """Compute an interval-certified Frobenius upper enclosure."""

    data = _validate_tensor(tensor)
    old_precision = mp.iv.prec
    mp.iv.prec = precision_bits
    try:
        sum_sq = mp.iv.mpf([0, 0])
        for value in data.ravel():
            real = mp.iv.mpf(str(float(np.real(value))))
            imag = mp.iv.mpf(str(float(np.imag(value)))) if np.iscomplexobj(data) else mp.iv.mpf([0, 0])
            sum_sq += real * real + imag * imag
        interval = mp.iv.sqrt(sum_sq)
        upper = float(interval.b)
        return NormEnclosure(
            lower=_attained_basis_lower(data),
            upper=_outward(upper),
            method=f"validated_interval_frobenius({precision_bits}bits)",
            certified=True,
            lower_method="basis-vector-attained-entry",
            upper_method="outward interval evaluation of Frobenius enclosure",
            fallback_used=False,
        )
    finally:
        mp.iv.prec = old_precision


def cp_enclosure(
    weights: Sequence[complex | float],
    factors: Sequence[Sequence[np.ndarray]],
    *,
    attained_lower: float = 0.0,
) -> NormEnclosure:
    """Certify a CP decomposition upper bound.

    Each term is ``weight * outer(factor_1, ..., factor_a)``. The upper bound
    is the sum of rank-one operator norms. The caller may provide an attained
    lower value from direct evaluation; it is never inferred as exact.
    """

    if len(weights) != len(factors) or not weights:
        raise ValueError("weights and factor terms must be nonempty and aligned")
    upper = 0.0
    for weight, term_factors in zip(weights, factors):
        if not term_factors:
            raise ValueError("each CP term must have at least one factor")
        upper += abs(weight) * float(np.prod([np.linalg.norm(np.asarray(factor)) for factor in term_factors]))
    if attained_lower < 0.0 or attained_lower > upper + 1.0e-12:
        raise ValueError("invalid attained lower bound")
    return NormEnclosure(
        lower=float(attained_lower),
        upper=_outward(upper),
        method="cp_structural",
        certified=True,
        lower_method="caller-supplied-attained-value",
        upper_method="sum of rank-one CP operator bounds",
        fallback_used=False,
    )


def exact_rank_one_enclosure(weight: complex | float, factors: Sequence[np.ndarray]) -> NormEnclosure:
    if not factors:
        raise ValueError("rank-one law requires factors")
    value = float(abs(weight) * np.prod([np.linalg.norm(np.asarray(factor)) for factor in factors]))
    return NormEnclosure(
        lower=value,
        upper=value,
        method="exact_rank_one",
        certified=True,
        lower_method="rank-one exact formula",
        upper_method="rank-one exact formula",
        fallback_used=False,
    )


def enclose_multilinear_norm(
    tensor: np.ndarray,
    *,
    method: str = "auto",
    split: int = 1,
    precision_bits: int = 160,
) -> NormEnclosure:
    """Select a certified enclosure method; ``auto`` prefers flattening."""

    if method == "auto":
        method = "flattening" if np.asarray(tensor).ndim >= 2 else "frobenius"
    if method == "frobenius":
        return frobenius_enclosure(tensor)
    if method == "flattening":
        return flattening_enclosure(tensor, split=split)
    if method == "validated_interval":
        return validated_interval_enclosure(tensor, precision_bits=precision_bits)
    raise ValueError("method must be auto, frobenius, flattening, or validated_interval")
