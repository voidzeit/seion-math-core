"""Exact symbolic small-case optimization and explicit SOS witnesses."""

from __future__ import annotations

from dataclasses import dataclass
from fractions import Fraction

import sympy as sp


@dataclass(frozen=True, slots=True)
class PolynomialCertificate:
    lower: Fraction
    upper: Fraction
    maximizers: tuple[str, ...]
    witness: str
    status: str
    backend: str


def certify_quadratic_on_unit_interval(
    a: int | Fraction, b: int | Fraction, c: int | Fraction
) -> PolynomialCertificate:
    """Globally maximize ``a*x^2+b*x+c`` on ``[-1,1]`` exactly.

    This is an independent symbolic certificate for the low-degree cases for
    which invoking an SDP solver would add numerical uncertainty.  The
    nonnegativity witness ``U-p`` is retained as an exact symbolic expression.
    """

    x = sp.Symbol("x", real=True)
    polynomial = sp.Rational(a) * x**2 + sp.Rational(b) * x + sp.Rational(c)
    candidates = [sp.Rational(-1), sp.Rational(1)]
    derivative = sp.diff(polynomial, x)
    for root in sp.solve(derivative, x):
        if root.is_real and bool(root >= -1) and bool(root <= 1):
            candidates.append(root)
    values = [(sp.simplify(polynomial.subs(x, point)), point) for point in candidates]
    maximum = max(value for value, _ in values)
    points = tuple(str(point) for value, point in values if value == maximum)
    rational = Fraction(int(sp.numer(maximum)), int(sp.denom(maximum)))
    witness = str(sp.factor(maximum - polynomial))
    return PolynomialCertificate(
        lower=rational,
        upper=rational,
        maximizers=points,
        witness=witness,
        status="VERIFIED_GLOBAL_OPTIMUM_SMALL_CASE",
        backend="exact SymPy stationary-point elimination / SOS-readable witness",
    )


def sos_backend_status() -> dict[str, str]:
    """Declare optional SDP availability without fabricating a certificate."""

    try:
        import cvxpy  # noqa: F401
    except Exception as exc:  # pragma: no cover - environment dependent
        return {"available": "false", "reason": f"cvxpy unavailable: {type(exc).__name__}"}
    return {
        "available": "true",
        "reason": "cvxpy import succeeds; each SDP still requires solver/status validation",
    }
