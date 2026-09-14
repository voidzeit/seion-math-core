"""Improved k=3 upper envelope for chain and branching independent-law trees.

This module implements the CLOSED session's tightened upper bound for the
real (or complex) binary k=3 case, proved directly from the exact local
error algebra -- not conditioned on any unproved scalar-reduction
assumption, and not restricted to rank-one projectors or any specific
witness family.

Derivation summary (chain topology; branching is identical up to relabelling,
see the proof note in ``research/math_closure/k3/upper_envelope.tex``):

Let node1 combine leaves a,b; node2 combine node1's output and leaf c; node3
(root) combine node2's output and leaf d. Write D1=(I-P1)mu1(a,b), R1=P1
mu1(a,b). Bilinearity gives

    P3 F3 - R3 = P3 mu3(mu2(D1, c), d) + P3 mu3((I-P2) mu2(R1, c), d)

Bounding each term with the declared operator-norm cap M and closure-residual
cap rho, and using the Pythagorean split ||R1||^2 + ||D1||^2 = ||mu1(a,b)||^2
<= M^2 ||a||^2 ||b||^2 (valid because P1 is an orthogonal projector) gives,
with q := ||D1|| / (||a|| ||b||) in [0, rho]:

    E_P / L_T <= h(q) := M^2 * q + M * rho * sqrt(M^2 - q^2)

Maximizing h over q in [0, rho] gives the closed-form envelope U_3(eta) below.
This is STRICTLY BETTER than the universal (k-1)=2 bound for every eta>0, and
recovers the universal bound only in the eta->0 limit (matching the already
proved asymptotic-sharpness result).

The bound remains a certified UPPER bound only; it does not close the gap to
the certified LOWER witness curve L_3(eta) from V5-A/V5-B
(``research/projected_trees_v5/extremal/V5B_EXTREMAL_STATUS.md``). Fixed-eta
global sharpness for k=3 remains OPEN.
"""

from __future__ import annotations

from dataclasses import dataclass
from math import sqrt

_ETA_C = sqrt((sqrt(5.0) - 1.0) / 2.0)  # ~0.7861513777574233


@dataclass(frozen=True, slots=True)
class K3UpperEnvelope:
    eta: float
    M: float
    rho: float
    q_star: float
    h_at_q_star: float
    normalized_bound: float
    absolute_bound: float
    regime: str
    universal_bound: float
    improvement_over_universal: float


def h_chain_or_branch(q: float, *, M: float = 1.0, rho: float) -> float:
    """The scalar objective ``M^2*q + M*rho*sqrt(M^2-q^2)`` for ``0<=q<=M``.

    Both the chain and branching k=3 topologies reduce to maximizing exactly
    this function of the single free scalar ``q = ||D1||/(||a|| ||b||)``, the
    normalized magnitude of the closure defect injected at the FIRST internal
    node encountered on the path whose local error is propagated furthest.
    """

    if M <= 0.0 or rho < 0.0 or not 0.0 <= q <= M:
        raise ValueError("require M>0, rho>=0, 0<=q<=M")
    return M * M * q + M * rho * sqrt(max(0.0, M * M - q * q))


def eta_transition_point() -> float:
    """Return eta_c = sqrt((sqrt(5)-1)/2), the exact regime boundary.

    At eta=eta_c both regimes of the piecewise envelope agree and equal the
    golden ratio phi=(1+sqrt(5))/2 -- a closed-form continuity check, not
    assumed, that any correct re-derivation should reproduce exactly.
    """

    return _ETA_C


def k3_upper_envelope(eta: float, *, M: float = 1.0) -> K3UpperEnvelope:
    """Return the tightened k=3 upper bound for chain and branching trees.

    ``U_3(eta) = 1 + sqrt(1-eta^2)``            for ``0 < eta <= eta_c``
    ``U_3(eta) = sqrt(1+eta^2) / eta``           for ``eta_c < eta <= 1``

    with ``eta_c = sqrt((sqrt(5)-1)/2)``. The absolute bound is
    ``U_3(eta) * rho * M^2 * L_T`` (``L_T`` the leaf-norm product, omitted
    here since this module works in the normalized frame ``L_T=1``).
    """

    if not 0.0 < eta <= 1.0 or M <= 0.0:
        raise ValueError("require 0 < eta <= 1 and M > 0")
    rho = eta * M
    if eta <= _ETA_C:
        q_star = rho
        regime = "boundary_q_equals_rho"
    else:
        q_star = M * M / sqrt(M * M + rho * rho)
        regime = "interior_critical_point"
    value = h_chain_or_branch(q_star, M=M, rho=rho)
    normalized = value / (rho * M * M)
    universal = 2.0 * rho * M * M
    return K3UpperEnvelope(
        eta=eta,
        M=M,
        rho=rho,
        q_star=q_star,
        h_at_q_star=value,
        normalized_bound=normalized,
        absolute_bound=value,
        regime=regime,
        universal_bound=universal,
        improvement_over_universal=universal - value,
    )


def verify_continuity_at_transition(*, tol: float = 1e-10) -> bool:
    """Check the two regime formulas agree at eta=eta_c (golden ratio)."""

    left = 1.0 + sqrt(1.0 - _ETA_C * _ETA_C)
    right = sqrt(1.0 + _ETA_C * _ETA_C) / _ETA_C
    phi = (1.0 + sqrt(5.0)) / 2.0
    return abs(left - right) < tol and abs(left - phi) < tol


def verify_asymptotic_limit(*, eta: float = 1e-6, tol: float = 1e-5) -> bool:
    """Check U_3(eta) -> 2 as eta -> 0, matching the already-proved squeeze."""

    return abs(k3_upper_envelope(eta).normalized_bound - 2.0) < tol
