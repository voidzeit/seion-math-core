"""V5-B extremal analysis for k=3 and repeated-law k=2.

This module separates three logically different objects:

* the exact one-variable optimization hidden in the V5-A witness;
* the resulting certified lower-bound curve for the declared witness family;
* a conditional upper-bound envelope that is valid only after an independent
  proof of the scalar reduction assumptions.

No function in this module upgrades the V5-A construction to global fixed-eta
sharpness.  The global k=3 problem and the repeated-law k=2 problem remain
explicitly open in the registries.
"""

from __future__ import annotations

from dataclasses import dataclass
from math import isclose, sqrt


_SQRT_HALF = 1.0 / sqrt(2.0)


@dataclass(frozen=True, slots=True)
class ScalarK3Optimization:
    """Exact solution of ``max 2*M*q*sqrt(M^2-q^2)`` on ``0 <= q <= rho``."""

    eta: float
    M: float
    rho: float
    q_upper: float
    q_star: float
    objective_at_q_star: float
    normalized_by_rho_M2: float
    universal_bound: float
    gap_to_universal: float
    regime: str


def scalar_k3_objective(q: float, *, M: float = 1.0) -> float:
    """Return ``2*M*q*sqrt(M^2-q^2)`` for ``0 <= q <= M``."""

    if M <= 0.0 or not 0.0 <= q <= M:
        raise ValueError("require M > 0 and 0 <= q <= M")
    return 2.0 * M * q * sqrt(max(0.0, M * M - q * q))


def optimize_scalar_k3_family(eta: float, *, M: float = 1.0) -> ScalarK3Optimization:
    """Solve the scalar V5-A optimization exactly.

    The unconstrained maximizer is ``q=M/sqrt(2)``.  The defect budget gives
    ``q <= rho=eta*M``.  Therefore ``q_star=min(rho,M/sqrt(2))``.  This is an
    exact calculus result for the scalar objective, not a global tree theorem.
    """

    if not 0.0 < eta <= 1.0 or M <= 0.0:
        raise ValueError("require 0 < eta <= 1 and M > 0")
    rho = eta * M
    q_upper = min(rho, M)
    q_star = min(q_upper, M * _SQRT_HALF)
    value = scalar_k3_objective(q_star, M=M)
    universal = 2.0 * rho * M * M
    normalized = value / (rho * M * M)
    regime = "constraint_active" if rho < M * _SQRT_HALF else "interior_extremum"
    return ScalarK3Optimization(
        eta=eta,
        M=M,
        rho=rho,
        q_upper=q_upper,
        q_star=q_star,
        objective_at_q_star=value,
        normalized_by_rho_M2=normalized,
        universal_bound=universal,
        gap_to_universal=universal - value,
        regime=regime,
    )


def v5a_piecewise_lower_bound(eta: float) -> float:
    """Return the normalized V5-A lower curve ``L_3(eta)``."""

    result = optimize_scalar_k3_family(eta)
    return result.normalized_by_rho_M2


def v5a_piecewise_lower_bound_closed_form(eta: float) -> float:
    """Closed form for ``L_3(eta)`` with the declared transition point."""

    if not 0.0 < eta <= 1.0:
        raise ValueError("require 0 < eta <= 1")
    if eta <= _SQRT_HALF:
        return 2.0 * sqrt(1.0 - eta * eta)
    return 1.0 / eta


def asymptotic_k3_limit_witness(*, tolerance: float = 1e-8) -> bool:
    """Check the lower curve against the universal limit near ``eta=0``.

    This is a deterministic finite check supporting the already proved
    squeeze argument; it is not itself the proof of the limit.
    """

    eta = 1e-6
    lower = v5a_piecewise_lower_bound_closed_form(eta)
    return abs(2.0 - lower) < tolerance


@dataclass(frozen=True, slots=True)
class ConditionalK3UpperBound:
    """Bookkeeping object for the proposed scalar-reduction upper bound."""

    eta: float
    M: float
    bound: float
    status: str
    assumptions: tuple[str, ...]


def conditional_scalar_reduction_upper_bound(
    eta: float, *, M: float = 1.0
) -> ConditionalK3UpperBound:
    """Return the candidate envelope under explicit scalar-reduction assumptions.

    The bound is ``2*M*q*sqrt(M^2-q^2)`` with the scalar optimizer ``q_star``.
    It is *conditional*: the repository has not proved that every admissible
    k=3 candidate admits the required two-scalar reduction.  Callers must not
    register this result as a global upper bound.
    """

    result = optimize_scalar_k3_family(eta, M=M)
    return ConditionalK3UpperBound(
        eta=eta,
        M=M,
        bound=result.objective_at_q_star,
        status="CONDITIONAL_ON_UNPROVED_SCALAR_REDUCTION",
        assumptions=(
            "E_proj <= 2*A*B",
            "A^2 + B^2 <= M^2",
            "0 <= A <= rho",
            "same real rank-one binary k=3 class as V5-A",
        ),
    )


@dataclass(frozen=True, slots=True)
class RepeatedLawK2Band:
    """Current certified band for the repeated/shared-law k=2 class."""

    eta: float
    known_lower_bound: float
    universal_upper_bound: float
    gated_planar_exact_value: float
    gated_planar_normalized_value: float
    status: str = "OPEN_FIXED_ETA_SHARPNESS"


def repeated_law_k2_band(eta: float) -> RepeatedLawK2Band:
    """Return ``eta <= C_2,rep^P(eta) <= 1`` and the known eta^2 witness."""

    if not 0.0 < eta <= 1.0:
        raise ValueError("require 0 < eta <= 1")
    return RepeatedLawK2Band(
        eta=eta,
        known_lower_bound=eta,
        universal_upper_bound=1.0,
        gated_planar_exact_value=eta * eta,
        gated_planar_normalized_value=eta,
    )


def verify_scalar_closed_form(eta: float, *, M: float = 1.0) -> bool:
    """Check the optimizer implementation against the piecewise formula."""

    result = optimize_scalar_k3_family(eta, M=M)
    expected = v5a_piecewise_lower_bound_closed_form(eta)
    return isclose(result.normalized_by_rho_M2, expected, rel_tol=1e-12, abs_tol=1e-12)
