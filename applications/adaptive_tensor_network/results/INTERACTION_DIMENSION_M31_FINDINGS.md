# M31 — the low rank is real only in the structured regime, and the modes are not stable

**EXPLORATORY, NOT CONFIRMATORY.**

Raw: `interaction_dimension_raw.json` (420 configs). Analysis:
`interaction_dimension_analysis.json`, by
`../experiments/analyze_interaction_dimension.py`.

Design: M30's measurement, ambient dimension swept `D ∈ {4, 6, 8, 12, 16, 24,
32}`, internal nodes held at 15 (m = 14 allocatable), chain and balanced
families, both regimes, 5 seeds. Budgets are set as fractions of `m·D`
(0.25 / 0.40 / 0.55) rather than absolute, so the compression regime is
comparable across dimensions — at a fixed absolute budget, D = 32 would be
barely truncated and the sweep would measure that instead of the interaction.

## M31A: the gate splits by regime

| D | regime | R1 | R2 | R4 | R8 | r_eff | r_eff/D | r_eff/m |
|---|---|---|---|---|---|---|---|---|
| 4 | iid | 0.474 | 0.830 | 0.962 | 0.996 | 4.57 | 1.141 | 0.326 |
| 8 | iid | 0.390 | 0.683 | 0.885 | 0.985 | 6.76 | 0.845 | 0.483 |
| 16 | iid | 0.327 | 0.576 | 0.806 | 0.969 | 8.19 | 0.512 | 0.585 |
| 32 | iid | 0.294 | 0.525 | **0.767** | 0.954 | **9.05** | 0.283 | **0.647** |
| 4 | het | 0.509 | 0.894 | 0.979 | 0.998 | 3.82 | 0.955 | 0.273 |
| 8 | het | 0.460 | 0.829 | 0.960 | 0.997 | 4.61 | 0.576 | 0.329 |
| 16 | het | 0.458 | 0.826 | 0.953 | 0.998 | 4.55 | 0.284 | 0.325 |
| 32 | het | 0.531 | 0.881 | **0.981** | 0.999 | **3.76** | 0.117 | **0.269** |

**Heterogeneous — the strong result.** Ambient dimension grows 8× (4 → 32)
while `r_eff` is flat: 3.82 → 3.76, never leaving 3.8–4.8. `R4` is flat at
0.95–0.98. `r_eff/D` falls 0.955 → 0.117 and `r_eff/m` stays ~0.27–0.34. There
is a genuine latent interaction dimension of about four, independent of the
ambient space it lives in.

**i.i.d. — the low rank was substantially a small-D artifact.** `r_eff` doubles
(4.57 → 9.05), `r_eff/m` rises 0.326 → 0.647, and `R4` decays 0.962 → 0.767.
Growth is sublinear in D, so some structure remains, but the rank tracks the
ambient space rather than saturating.

M30 pooled these. At its single operating point D = 6 both regimes looked
low-rank (R4 = 0.894 iid, 0.967 het) and the difference was invisible. **The
low-rank finding belongs to the structured regime, not to the problem as
such.**

## Signed inertia: RETRACTED — the measurement was a design tautology

This section originally reported that `I` is strongly indefinite (negative
energy fraction 0.454–0.511, n₊ ≈ n₋ ≈ 7, leading patterns always sign-mixed)
and concluded that the quadratic surrogate `½ΔᵀIΔ` is inherently non-convex.

**That conclusion does not follow, and the measurement carries no information.**
`I` is built from off-diagonal second differences only, so its diagonal is zero
by construction, so `tr(I) = 0`, so its eigenvalues sum to zero. Any nonzero
symmetric matrix with zero trace is necessarily indefinite, with balanced
positive and negative counts and roughly half its spectral energy negative.
The reported inertia was forced by the design of the measurement, not observed
in the problem. The numbers above are exactly what a zero-diagonal matrix must
produce.

Convexity is a property of the **full discrete Hessian**

    H = I + diag(H_vv),   H_vv = E(r + 2e_v) − 2E(r + e_v) + E(r),

whose diagonal is the second difference in a single coordinate and was never
measured in this pass. A sufficiently positive diagonal can dominate the
off-diagonal coupling and leave `H` positive definite even though `I` is
indefinite. Only `H` decides.

`H_vv` is measured, and the two inertias compared, in
`DISCRETE_HESSIAN_FINDINGS.md`. Until then no claim about the convexity of the
surrogate is supported by this campaign, and the mechanistic link drawn here
between negative eigenvalues and M27's non-monotonicity is withdrawn.

## M31B: the modes are NOT stable

`S_q(A,B) = ‖Q_Aᵀ Q_B‖²_F / q`, null value `q/m = 0.286`:

| D | regime | across budgets | across seeds | null |
|---|---|---|---|---|
| 4 | iid | 0.494 | 0.305 | 0.286 |
| 8 | iid | 0.265 | 0.262 | 0.286 |
| 16 | iid | 0.296 | 0.285 | 0.286 |
| 32 | iid | 0.282 | 0.281 | 0.286 |
| 4 | het | 0.601 | 0.294 | 0.286 |
| 16 | het | 0.485 | 0.292 | 0.286 |
| 32 | het | 0.561 | 0.282 | 0.286 |

**Across seeds the overlap is at the null value everywhere** (0.246–0.305): the
subspace is a property of the instance, not of the architecture. **Across
budgets in the i.i.d. regime it is also at null** — changing the base state
regenerates the modes entirely. Only heterogeneous-across-budgets rises above
chance, to 0.39–0.60, and that is still far from the ≈1 that would license
calibrating a basis once.

This is Case A: the interaction can be compressed *after* being measured, but
`Q` cannot be estimated once and reused. Any allocator built on it must
re-estimate `I` at each base state, which is the expensive branch.

## M31C: only two features touch the subspace

`R²_Q(x) = ‖QQᵀx‖²/‖x‖²`. The random control lands at 0.281–0.298 across every
row, matching the analytic null `q/m = 0.286` — the measurement is calibrated.

| D | regime | constant | depth | local_error | path_weight | rank | \|utility\| | random |
|---|---|---|---|---|---|---|---|---|
| 8 | iid | 0.290 | 0.294 | 0.292 | 0.291 | 0.290 | **0.534** | 0.294 |
| 32 | iid | 0.300 | 0.298 | 0.300 | 0.298 | 0.300 | **0.380** | 0.281 |
| 8 | het | 0.271 | 0.267 | **0.440** | 0.239 | 0.271 | **0.785** | 0.286 |
| 16 | het | 0.304 | 0.337 | **0.530** | 0.291 | 0.304 | **0.744** | 0.288 |
| 24 | het | 0.269 | 0.263 | **0.615** | 0.244 | 0.269 | **0.796** | 0.292 |
| 32 | het | 0.302 | 0.317 | **0.695** | 0.249 | 0.302 | **0.858** | 0.291 |

- `constant`, `depth`, `path_weight`: **at null in every row.** Node depth and
  the pathwise transport weight carry no more of the interaction subspace than
  a random vector does. This closes the topological-geometry question opened by
  M30 from the other side.
- `rank` is degenerate here — the base allocation is uniform, so the rank
  vector is (nearly) the constant vector, and its column duplicates `constant`
  exactly. It tests nothing and is retained only to make that visible.
- `local_error` carries real signal in the heterogeneous regime and **grows
  with D**: 0.398 → 0.695 from D = 4 to 32. At null in i.i.d.
- **`|U_v|` is the strongest by far**: 0.74–0.86 in heterogeneous at every D,
  0.38–0.80 in i.i.d. The leading interaction subspace is substantially aligned
  with the marginal-utility vector.

That last point is the one piece of good news for a coupled allocator: the
directions carrying the interaction are largely the directions that matter for
the gradient, so a `q`-dimensional reduction captures both terms at once rather
than needing separate bases. Note that `U` and `I` come from overlapping
perturbation experiments — distinct measurements, but not independent ones.

## Status of the allocation programme

| gate | verdict |
|---|---|
| low rank survives branching (M30) | **passed** |
| low rank survives growing D | **passed in the structured regime only**; fails in i.i.d. |
| I is well-conditioned for optimization | **not established** — the inertia reported here was a tautology of the zero diagonal; see `DISCRETE_HESSIAN_FINDINGS.md` |
| modes stable enough to calibrate once | **failed** — at null across seeds, at null across budgets in i.i.d. |
| modes explained by tree geometry | **failed** (M30, and confirmed here: depth and path weight at null) |
| modes aligned with something usable | **`|U_v|`, strongly; `local_error` in the structured regime** |

M32 — whether the quadratic surrogate predicts held-out multi-node
perturbations — remains the right next test, but it should now be run in the
heterogeneous regime and with `I` re-estimated per state. Held-out
perturbations must have `‖Δ‖₀ ≥ 3`: singles and pairs were consumed to build
`U` and `I`, so anything smaller is training data.

## Scope

The heterogeneous regime is synthetic by construction: per-node power-law
spectra with exponents drawn from [0.3, 2.0]. That real trained layers exhibit
comparable spectral dispersion is plausible but **untested here**, so "genuine
latent dimension" is established for a structured synthetic family, not for
real networks. Binary trees, 15 internal nodes, `uniform` base allocation,
Δrank = +1, 5 seeds, `q = 4` throughout.
