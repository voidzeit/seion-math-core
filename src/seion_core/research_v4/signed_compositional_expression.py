"""Generic signed compositional expressions over P6B/P7B polynomials.

P7C is intentionally an instantiation layer.  It does not implement separate
Jacobiator or Filippov algebra engines: every expression is a finite signed
collection of source polynomials and is certified by the P7B aggregator.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable

from .higher_order_source_polynomial import SourcePolynomial
from .signed_source_polynomial import (
    SignedPolynomialTerm,
    SignedSourcePolynomialCertificate,
    certify_signed_source_polynomial,
)


@dataclass(frozen=True, slots=True)
class CompositionalTerm:
    """One labelled compositional term with its P6B source polynomial."""

    term_id: str
    coefficient: complex
    source_polynomial: SourcePolynomial

    def as_signed_term(self) -> SignedPolynomialTerm:
        return SignedPolynomialTerm(self.term_id, self.coefficient, self.source_polynomial)


@dataclass(frozen=True, slots=True)
class SignedCompositionalExpression:
    """A generic finite expression ``sum_j c_j T_j``."""

    expression_id: str
    expression_kind: str
    terms: tuple[CompositionalTerm, ...]

    def __post_init__(self) -> None:
        if not self.expression_id:
            raise ValueError("expression id must be nonempty")
        if not self.expression_kind:
            raise ValueError("expression kind must be nonempty")
        if not self.terms:
            raise ValueError("expression must contain at least one term")
        term_ids = [term.term_id for term in self.terms]
        if len(set(term_ids)) != len(term_ids):
            raise ValueError("expression term ids must be unique")

    def certify(
        self,
        source_amplitudes: dict[str, complex | float],
        *,
        truncation_order: int | None = None,
    ) -> "SignedCompositionalExpressionCertificate":
        certificate = certify_signed_source_polynomial(
            tuple(term.as_signed_term() for term in self.terms),
            source_amplitudes,
            truncation_order=truncation_order,
        )
        return SignedCompositionalExpressionCertificate(
            expression_id=self.expression_id,
            expression_kind=self.expression_kind,
            certificate=certificate,
        )


@dataclass(frozen=True, slots=True)
class SignedCompositionalExpressionCertificate:
    """P7C-labelled view of the generic P7B certificate."""

    expression_id: str
    expression_kind: str
    certificate: SignedSourcePolynomialCertificate

    @property
    def actual_norm(self) -> float:
        return self.certificate.actual_norm

    @property
    def signed_bound(self) -> float:
        return self.certificate.exact_polynomial_bound

    @property
    def treewise_bound(self) -> float:
        return self.certificate.treewise_bound

    @property
    def remainder_bound(self) -> float:
        return self.certificate.remainder_bound

    @property
    def total_certified_bound(self) -> float:
        return self.certificate.total_certified_bound


def _expression(
    expression_id: str,
    expression_kind: str,
    terms: Iterable[CompositionalTerm],
) -> SignedCompositionalExpression:
    return SignedCompositionalExpression(expression_id, expression_kind, tuple(terms))


def make_associator_expression(
    left: SourcePolynomial,
    right: SourcePolynomial,
) -> SignedCompositionalExpression:
    """Return the signed associator form ``T_left - T_right``."""

    return _expression(
        "associator",
        "ASSOCIATOR_CERTIFICATE",
        (CompositionalTerm("left", 1.0, left), CompositionalTerm("right", -1.0, right)),
    )


def make_jacobiator_expression(
    xy_z: SourcePolynomial,
    yz_x: SourcePolynomial,
    zx_y: SourcePolynomial,
) -> SignedCompositionalExpression:
    """Return the standard three-term Jacobiator *defect* expression.

    The convention is ``[x,[y,z]] + [y,[z,x]] + [z,[x,y]]``.  The function
    certifies the calculated defect and makes no assumption that it vanishes.
    """

    return _expression(
        "jacobiator",
        "JACOBIATOR_CERTIFICATE",
        (
            CompositionalTerm("x_yz", 1.0, xy_z),
            CompositionalTerm("y_zx", 1.0, yz_x),
            CompositionalTerm("z_xy", 1.0, zx_y),
        ),
    )


def make_filippov_defect_expression(
    fundamental_term: SourcePolynomial,
    insertion_terms: Iterable[SourcePolynomial],
) -> SignedCompositionalExpression:
    """Return ``T0 - sum_i T_i`` as a Filippov/FI defect expression.

    The arity and bracket convention are represented by the caller's term
    construction.  This factory only fixes the signed defect convention and
    never labels the identity as satisfied.
    """

    terms = [CompositionalTerm("fundamental", 1.0, fundamental_term)]
    terms.extend(
        CompositionalTerm(f"insertion_{index}", -1.0, polynomial)
        for index, polynomial in enumerate(insertion_terms)
    )
    return _expression("filippov_defect", "FILIPPOV_DEFECT_CERTIFICATE", terms)


def certify_signed_compositional_expression(
    expression: SignedCompositionalExpression,
    source_amplitudes: dict[str, complex | float],
    *,
    truncation_order: int | None = None,
) -> SignedCompositionalExpressionCertificate:
    """Certify any generic signed expression using the P7B engine."""

    return expression.certify(source_amplitudes, truncation_order=truncation_order)
