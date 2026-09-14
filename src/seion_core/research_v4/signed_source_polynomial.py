"""Nonlinear signed source-polynomial certificates (P7B).

The engine accepts any finite signed expression ``sum_j c_j T_j`` whose terms
have already been evaluated into P6B source polynomials.  It aggregates by
source multi-index before taking norms, so associator, Jacobiator, and
Filippov expressions can share one implementation in later phases.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Mapping

import numpy as np

from .higher_order_source_polynomial import MultiIndex, SourcePolynomial, multiindex_degree


@dataclass(frozen=True, slots=True)
class SignedPolynomialTerm:
    """One signed compositional term represented by a P6B polynomial."""

    term_id: str
    coefficient: complex
    polynomial: SourcePolynomial

    def __post_init__(self) -> None:
        if not self.term_id:
            raise ValueError("signed polynomial term ids must be nonempty")


@dataclass(frozen=True, slots=True)
class SignedSourcePolynomialCertificate:
    """Exact and certified truncated bounds for a signed source expression."""

    dimension: int
    terms: tuple[SignedPolynomialTerm, ...]
    source_amplitudes: Mapping[str, complex | float]
    aggregated_polynomial: SourcePolynomial
    direct_value: np.ndarray
    actual_norm: float
    exact_polynomial_bound: float
    truncated_signed_bound: float
    remainder_bound: float
    total_certified_bound: float
    treewise_bound: float
    improvement_absolute: float
    improvement_ratio: float | None
    truncation_order: int | None
    strict_improvement: bool


def _monomial_weight(index: MultiIndex, amplitudes: Mapping[str, complex | float]) -> float:
    weight = 1.0
    for source_id, count in index:
        if source_id not in amplitudes:
            raise ValueError(f"missing amplitude for source {source_id!r}")
        weight *= abs(amplitudes[source_id]) ** count
    return weight


def _aggregate(terms: tuple[SignedPolynomialTerm, ...], dimension: int) -> SourcePolynomial:
    coefficients: dict[MultiIndex, np.ndarray] = {}
    for term in terms:
        if term.polynomial.dimension != dimension:
            raise ValueError("all signed polynomial terms must have the same output dimension")
        for index, coefficient in term.polynomial.coefficients.items():
            scaled = term.coefficient * coefficient
            if index in coefficients:
                coefficients[index] = coefficients[index] + scaled
            else:
                coefficients[index] = np.array(scaled, copy=True)
    return SourcePolynomial(dimension, coefficients)


def _weighted_bound(polynomial: SourcePolynomial, amplitudes: Mapping[str, complex | float], *, max_order: int | None = None) -> float:
    total = 0.0
    for index, coefficient in polynomial.coefficients.items():
        if max_order is not None and multiindex_degree(index) > max_order:
            continue
        total += float(np.linalg.norm(coefficient)) * _monomial_weight(index, amplitudes)
    return total


def certify_signed_source_polynomial(
    terms: tuple[SignedPolynomialTerm, ...],
    source_amplitudes: Mapping[str, complex | float],
    *,
    truncation_order: int | None = None,
) -> SignedSourcePolynomialCertificate:
    """Aggregate signed P6B polynomials and certify nonlinear cancellation.

    ``exact_polynomial_bound`` takes the norm after signed aggregation for all
    finite multi-indices.  With ``truncation_order=p``, the retained signed
    bound and the norm-weighted omitted signed coefficients form a certified
    decomposition whose sum equals the exact signed bound up to floating-point
    roundoff.  ``treewise_bound`` applies the triangle inequality to each term
    before aggregation, so the signed bound is never larger.
    """

    if not terms:
        raise ValueError("signed source-polynomial expression must contain terms")
    if truncation_order is not None and truncation_order < 0:
        raise ValueError("truncation order must be nonnegative")
    dimension = terms[0].polynomial.dimension
    amplitudes = dict(source_amplitudes)
    aggregated = _aggregate(terms, dimension)

    direct_value = np.zeros(dimension, dtype=np.result_type(*[term.polynomial.evaluate(amplitudes) for term in terms], float))
    for term in terms:
        direct_value = direct_value + term.coefficient * term.polynomial.evaluate(amplitudes)

    exact_bound = _weighted_bound(aggregated, amplitudes)
    if truncation_order is None:
        truncated_bound = exact_bound
        remainder_bound = 0.0
    else:
        truncated_bound = _weighted_bound(aggregated, amplitudes, max_order=truncation_order)
        remainder_bound = exact_bound - truncated_bound
        if remainder_bound < 0.0 and abs(remainder_bound) <= 1.0e-12 * max(1.0, exact_bound):
            remainder_bound = 0.0
    total_certified_bound = truncated_bound + remainder_bound

    treewise_bound = 0.0
    for term in terms:
        treewise_bound += abs(term.coefficient) * _weighted_bound(term.polynomial, amplitudes)

    tolerance = 1.0e-10 * max(1.0, abs(treewise_bound))
    actual_norm = float(np.linalg.norm(direct_value))
    if actual_norm > exact_bound + tolerance:
        raise AssertionError("direct signed expression exceeds exact polynomial certificate")
    if exact_bound > treewise_bound + tolerance:
        raise AssertionError("signed source-polynomial bound exceeds treewise triangle bound")

    improvement_absolute = max(0.0, treewise_bound - exact_bound)
    improvement_ratio = exact_bound / treewise_bound if treewise_bound > tolerance else None
    return SignedSourcePolynomialCertificate(
        dimension=dimension,
        terms=terms,
        source_amplitudes=amplitudes,
        aggregated_polynomial=aggregated,
        direct_value=direct_value,
        actual_norm=actual_norm,
        exact_polynomial_bound=exact_bound,
        truncated_signed_bound=truncated_bound,
        remainder_bound=remainder_bound,
        total_certified_bound=total_certified_bound,
        treewise_bound=treewise_bound,
        improvement_absolute=improvement_absolute,
        improvement_ratio=improvement_ratio,
        truncation_order=truncation_order,
        strict_improvement=exact_bound < treewise_bound - tolerance,
    )
