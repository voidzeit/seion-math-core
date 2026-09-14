# Canonical PMT core

This directory documents the finite-dimensional Projected Multilinear Tree
(PMT) contract implemented by `seion_core.pmt`.

## Mathematical object

An ordered rooted tree has finite-dimensional real or complex Hilbert spaces at
every vertex.  A node law is a dense typed multilinear map

\[
\mu_v:H_{c_1(v)}\times\cdots\times H_{c_{m_v}(v)}\to H_v,
\qquad m_v\ge2,
\]

stored in output-first coordinates.  Every internal output has an orthogonal
projector `P_v`; leaves use the identity convention.  For ambient leaf vectors
`z_l`, the two evaluations are

\[
F_v=\mu_v(F_{c_1(v)},\ldots,F_{c_{m_v}(v)}),
\qquad
R_v=P_v\mu_v(R_{c_1(v)},\ldots,R_{c_{m_v}(v)}).
\]

The primary error is

\[
E_T^P=\|P_rF_r-R_r\|.
\]

`seion_core.pmt.evaluate_pmt` also returns the ambient error
`||F_r-R_r||`, the normal component `||Q_r F_r||`, and the exact
Pythagorean residual.  It accepts ambient leaf vectors; this is intentionally
different from the legacy `research_v3` evaluator, which accepts reduced leaf
coordinates for its historical run protocol.

## Defect and norm contracts

The local admissibility quantity is the projected-input closure defect

\[
\rho_v^{\rm proj}
=\|Q_v\mu_v(\widehat P_{c_1(v)}\cdot,\ldots,
                  \widehat P_{c_{m_v}(v)}\cdot)\|_{\rm op}.
\]

`projected_closure_bracket` reports an attained lower value and a Frobenius
upper certificate for this norm.  The upper endpoint is safe; a finite
alternating maximization lower endpoint is not a global optimum proof.  The
same distinction is retained by `admissibility_bracket` for the full law norm.

## Exact theorem contracts

The closed-form functions in `seion_core.pmt.bounds` encode the declared
finite-dimensional theorem scope:

* `projected_root_bound(k, M, rho, L)` returns
  `(k-1) rho M^(k-1) L`, with zero for `k <= 1`.
* `w3(eta)` returns the exact independent-law `k=3` value
  `sqrt(4-3 eta^2)` below `sqrt(2/3)` and
  `2/(sqrt(3) eta)` above it.
* `w3_sos_residual(xi, zeta)` exposes the nonnegative sum-of-squares identity
  behind the `4/3` extremal step.
* `chain_w3_extremizer` and `branching_w3_extremizer` build the analytic
  two-dimensional rank-one witnesses.  Their status is an analytic
  construction, not a numerical search result.

## The `k >= 4` boundary

`seion_core.pmt.k4_frontier()` deliberately returns `exact_constant: None`.
The universal projected upper coefficient is known to be `k-1`, and the
finite-tree small-`eta` asymptotic result is registered separately, but the
fixed-`eta` independent-law constant for `k>=4` remains an open problem.  A
future optimizer may attach a record under `observation_status:
NUMERICAL_OBSERVATION`; the API has no path that upgrades that record to an
exact constant.

The research design and topology checklist live in
`research/math_closure/k4_exploration/PMT_K4_FRONTIER.md`.
