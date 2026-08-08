"""Necessary-and-sufficient saturation characterization for k=2 chains.

Prior work (``k2_sharpness.py``, ``equality_conditions.py``) exhibits two
saturating constructions (independent laws, and a single repeated law) and
audits them with an informal per-construction checklist. This module states
and mechanically checks the underlying THEOREM those two constructions are
both instances of:

    Theorem (k=2 saturation iff). Let T be a binary chain with internal
    nodes "in" (children: leaves a,b) and "out" (children: node "in" and
    leaf d), laws mu_in, mu_out bilinear with ||mu_in||_op<=M,
    ||mu_out||_op<=M, orthogonal projectors P (at "in") and P_out (at the
    root), and closure-residual norm rho_in := ||(I-P) mu_in||_op <= rho.
    Write D := (I-P) mu_in(a,b). Then

        E_P(T) = ||P_out mu_out(D_in,d)||   where D_in = (I-P) mu_in(a,b)

    and the universal bound gives E_P(T) <= rho*M*||a||*||b||*||d||. Equality
    holds for a specific (mu_in,mu_out,P,P_out,a,b,d) if and only if ALL
    THREE conditions hold simultaneously:

        (EQ1) ||mu_out(D_in,d)|| = M*||D_in||*||d||   [mu_out saturates M
              on the pair (D_in,d)]
        (EQ2) ||D_in|| = rho*||a||*||b||               [the closure map
              (I-P) mu_in saturates rho on the pair (a,b)]
        (EQ3) mu_out(D_in,d) is in Range(P_out)         [the root projector
              causes no further loss on the propagated vector]

    Proof. E_P = ||P_out mu_out(D_in,d)|| <= ||mu_out(D_in,d)||
                <= M*||D_in||*||d|| <= M*rho*||a||*||b||*||d||
    is a chain of three real, non-negative inequalities (projection
    contractivity, operator-norm definition, closure-residual definition).
    For non-negative reals x<=y<=z<=w, x=w forces x=y=z=w (the value cannot
    strictly increase and then return to the same value without every step
    being flat). Hence E_P equals the universal bound iff each of the three
    inequalities above is individually an equality, which are exactly
    EQ1-EQ3 stated in reverse order. QED.

    This holds regardless of whether mu_in and mu_out are the SAME map or
    independently chosen -- weight-sharing is not itself an obstruction; it
    only adds the extra requirement that a single map mu satisfy both EQ1
    (evaluated at (D_in,d)) and EQ2 (evaluated at (a,b)) at once, which the
    repeated-law witness in ``k2_sharpness.py`` demonstrates is satisfiable.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np


@dataclass(frozen=True, slots=True)
class SaturationCertificate:
    eq1_operator_norm_saturation: bool
    eq1_gap: float
    eq2_closure_residual_saturation: bool
    eq2_gap: float
    eq3_projection_alignment: bool
    eq3_gap: float
    all_conditions_hold: bool
    E_P: float
    universal_bound: float
    saturates: bool


def certify_k2_saturation(
    mu_in,
    mu_out,
    P: np.ndarray,
    P_out: np.ndarray,
    a: np.ndarray,
    b: np.ndarray,
    d: np.ndarray,
    *,
    M: float,
    rho: float,
    tol: float = 1e-9,
) -> SaturationCertificate:
    """Mechanically check EQ1-EQ3 for a concrete k=2 chain instance.

    ``mu_in``, ``mu_out`` are callables ``(x, y) -> vector`` implementing
    bilinear maps. This function does not search for a saturating
    configuration; it certifies whether a SUPPLIED configuration saturates
    the universal bound, and if so, verifies that this happens exactly when
    EQ1-EQ3 all hold -- i.e. it checks the theorem's claim on one instance
    at a time (used as a unit-test oracle, not a proof).
    """

    F_in = mu_in(a, b)
    R_in = P @ F_in
    D_in = F_in - R_in

    root_ambient_input = D_in  # F_out - R_out = mu_out(D_in, d), see module docstring
    propagated = mu_out(root_ambient_input, d)
    E_P = float(np.linalg.norm(P_out @ propagated))

    norm_D_in = float(np.linalg.norm(D_in))
    norm_d = float(np.linalg.norm(d))
    norm_a = float(np.linalg.norm(a))
    norm_b = float(np.linalg.norm(b))
    norm_propagated = float(np.linalg.norm(propagated))

    eq1_lhs = norm_propagated
    eq1_rhs = M * norm_D_in * norm_d
    eq1_gap = eq1_rhs - eq1_lhs
    eq1_ok = eq1_gap <= tol

    eq2_lhs = norm_D_in
    eq2_rhs = rho * norm_a * norm_b
    eq2_gap = eq2_rhs - eq2_lhs
    eq2_ok = eq2_gap <= tol

    eq3_gap = norm_propagated - E_P
    eq3_ok = eq3_gap <= tol

    universal_bound = rho * M * norm_a * norm_b * norm_d
    saturates = (universal_bound - E_P) <= tol

    all_conditions_hold = eq1_ok and eq2_ok and eq3_ok

    return SaturationCertificate(
        eq1_operator_norm_saturation=eq1_ok,
        eq1_gap=eq1_gap,
        eq2_closure_residual_saturation=eq2_ok,
        eq2_gap=eq2_gap,
        eq3_projection_alignment=eq3_ok,
        eq3_gap=eq3_gap,
        all_conditions_hold=all_conditions_hold,
        E_P=E_P,
        universal_bound=universal_bound,
        saturates=saturates,
    )
