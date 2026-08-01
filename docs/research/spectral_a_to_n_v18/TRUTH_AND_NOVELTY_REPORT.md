# Truth and novelty report — spectral A-N v18 (2026-07-30)

Scope: `SPECTRAL_LEGACY_TRACK` only (`claims/scope_registry_v4.yaml`). Track
T (projected n-ary tree mathematics) is explicitly deferred and out of
scope for this report — see `.ai/SPECTRAL_TRACK_ROADMAP.md`. Nothing here
is a claim about `CANONICAL_FINITE_CORE` (`src/seion_core`), which has its
own separate, pre-existing governance and status
(`FAIL_CLOSED_BLOCKED_PENDING_HUMAN_REVIEW`, unaffected by this track).

Taxonomy used below, per this campaign's own rule that no novelty claim
may self-approve: `PROVED`, `PROVED_UNDER_ASSUMPTIONS`, `EXACT`,
`CERTIFIED`, `STATISTICALLY_VALIDATED`, `EMPIRICAL`,
`STRUCTURAL_IDENTITY`, `STANDARD`, `POTENTIALLY_NOVEL`,
`NOVELTY_UNESTABLISHED`, `REFUTED`, `OPEN`.

## Per-block final status

| Block | Status | Basis |
|---|---|---|
| A — projector validity | `STRUCTURAL_IDENTITY` | `P=UU*` idempotent/self-adjoint for ANY orthonormal U; construction fact, not learned. |
| B — dynamic commutator explanation | `REFUTED` (deployed-regime claim) | All 15 real historical checkpoints: `coherence_ratio<=0` (worse than zero predictor). Ablation matrix identifies the mechanism: genuine conflict with the associator/GJI objective (~100x degradation when trained jointly vs isolated), not capacity/parameterization/starvation. `Phi` alone (law params, U frozen at random init) drives residual to exactly 0 — the fit is substantially independent of the learned subspace. |
| C — FINITE_BEALS_PROXY | `EMPIRICAL` | Finite nested-commutator norms only; explicitly not a PsiDO/microlocal/continuum claim. Adversarial search beats all hand-picked projector families, as required. |
| D — spectral snapping | `EMPIRICAL` | Rank recovery + distance bound hold within tested perturbation range; gap-closing counterexample confirms the Davis-Kahan-style gap condition is necessary. |
| E — interscale subspace transport | `REFUTED` | 3 independently-trained resolutions, frozen lift, principal angles, 2 required baselines: transported-subspace angles sit near maximal (pi/2) in all 3 pairs; beats both baselines in only 1 of 3 pairs, by a small margin. |
| F — rigidity | `EXACT` (Hessian/GGN distinction + gauge-flat-direction) / `EMPIRICAL` (basin stability) | Exact Hessian vs GGN correctly distinguished and named (not conflated, unlike legacy's "hessian_condition_proxy"). Basin stability across seeds: `REFUTED` for single-objective identifiability — 3 seeds converge to near-orthogonal subspaces (~89 degrees) despite all reaching near-zero loss. |
| G — n-ary closure | `STATISTICALLY_VALIDATED` (large-sample + adversarial, single config) | Not `CERTIFIED` — no interval/SOS worst-case bound derived. |
| H — associator constant | `EMPIRICAL`; sharpness `OPEN` (this pass) | Constant 2 (triangle bound) never violated; adversarial search only reaches ratio 0.45 of the bound for this law family — `NOT_SHARP`, but no analytic tighter constant is proved. |
| I — reduced tensor extraction | `EXACT` (rational small case) / `CERTIFIED`-tier (float64 parity) | Extraction-correctness only, per mission's own scope limit — no compactness/significance claim. |
| J — tensor interscale | `REFUTED` | Methodology (gauge-invariant, 4 distances reported separately) is a genuine improvement, now backed by Block E's real experiment: no persistence signal found. |
| K — HOSVD compactness | `EMPIRICAL` (single seed) | Modestly more compact than a random-tensor null in one mode only; far from "canonical low-dimensional structure." |
| L — gauge canonicalization | `EXACT` (residual-gauge detection) / `EMPIRICAL` (stability) | Residual-gauge group correctly identified and distinguished from instability, verified via a deliberately non-infinitesimal within-eigenspace rotation. |
| M — persistent factorization | `REFUTED` (general claim) / `OPEN` (one anomalous mode) | Real >=3-resolution experiment: rank inconsistent across resolutions; one mode/pair shows a near-exact match not explained by this pass — logged as an open anomaly, not smoothed into either a pass or a uniform fail. |
| N — cyclic law and GJI | `STRUCTURAL_IDENTITY` (symmetrized defect) / `EXACT` (GJI formula, cross-validated to 1e-16) | Raw defect ~4.6, symmetrized ~8e-33 — the ~31-order-of-magnitude gap is the construction-identity finding, reported explicitly rather than left implicit. GJI ratio supremum `OPEN`. |

## Novelty

`NOVELTY_UNESTABLISHED` for every methodological improvement in this
track (typed-gate taxonomy, gauge-invariant comparison replacing vacuous
Procrustes, the B ablation-matrix mechanism diagnosis, the Hessian/GGN
distinction). This campaign did not perform an independent literature
search — the same limitation the 2026-07-29 advisory truth audit
(`docs/research/truth_audit_2026_07_29/`) recorded for the separate v3/v4
core. No claim of `POTENTIALLY_NOVEL` is made without that search; nothing
here should be read as a proved priority claim.

## What was proved (exact, no floating-point tolerance)

- `raw_comm = K@Delta@P - P@Delta@K` identically (Block B, model.py).
- `raw_comm` and `C_theta` both have rank <= 2*rank (Block B).
- The rank-2r SVD truncation of `raw_comm` recovers it to machine precision
  (confirms the rank bound numerically).
- Two independent GJI implementations agree to 2.8e-16 (Block N).
- Principal angles correctly distinguish "same subspace, different basis"
  (0 angle) from "different subspace" (large angle), where free-unitary
  Procrustes on orthonormal bases does not (Block M/L, the corrected
  methodology).
- The Pythagorean identity for ambient/projected/normal associator
  decomposition (Block H) holds to 1e-8 relative error.
- Exact Hessian vs GGN are numerically distinct objects, and the
  gauge-rotation direction has Hessian curvature 0 to 1e-18 (Block F).

## What was refuted

- The coherent-dynamic-curvature explanation (Block B) as deployed: worse
  than the zero predictor in every real historical checkpoint.
- Interscale subspace persistence (Block E) and tensor persistence
  (Block J/M) under a closure-only training objective across 3
  independent resolutions.
- Single-objective basin stability (Block F): near-zero loss from 3 seeds,
  but ~89-degree separated subspaces.

## What remains open

- Block H's sharp associator constant (bound is 2, best found is 0.45x
  that — gap not closed analytically).
- Block N's GJI ratio supremum (adversarial max found 5.98, not shown to
  be bounded).
- Block M's one anomalous aligned mode (12-vs-18, mode 2) — coincidence or
  real partial invariant, not resolved.
- Whether Block E/J/M's negative results persist under the full historical
  multi-objective training loss (this pass used a closure-only objective
  for tractability; Block B's ablation matrix shows objective choice
  materially changes outcomes, so this is a real, not merely formal, gap).
- Track T in its entirety (explicitly deferred by user decision).
