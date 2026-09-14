# M32 — the surrogate predicts binary bundles well and multi-unit bundles badly

**EXPLORATORY, NOT CONFIRMATORY.**

Raw: `surrogate_prediction_raw.json` (25,600 held-out bundles). Analysis:
`surrogate_prediction_analysis.json`, by
`../experiments/analyze_surrogate_prediction.py`. `R²` is computed per
configuration and then averaged, never pooled across configurations.

Held-out means `‖Δ‖₀ ≥ 3`; singles and pairs were consumed to estimate `U`,
`H_vv` and `I`. Bundle sizes 3, 4, 6, 8; 40 bundles per size per configuration.

The expansion under test is

    E(r+Δ) − E(r) ≈ −Σ_v U_v Δ_v + Σ_v H_vv C(Δ_v,2) + Σ_{u<v} I_uv Δ_u Δ_v

with `C(n,2) = n(n−1)/2`, which returns exactly `−U_v` at `Δ = e_v` and exactly
`−2U_v + H_vv` at `Δ = 2e_v`. The low-rank pairwise term subtracts the spurious
diagonal that truncation introduces:
`½[Δᵀ(QΛQᵀ)Δ − Σ_v (QΛQᵀ)_vv Δ_v²]`, which equals
`Σ_{u<v} (QΛQᵀ)_uv Δ_u Δ_v` exactly and stays `O(mq)`.

## M32A — binary bundles (`Δ_v ∈ {0,1}`, diagonal inert): PASSES

| D | regime | model | R² | ρ | sign | regret |
|---|---|---|---|---|---|---|
| 6 | het | linear | 0.544 | 0.798 | 0.864 | 0.146 |
| 6 | het | pairwise | **0.772** | 0.910 | 0.952 | 0.062 |
| 6 | het | pairwise low-rank | **0.766** | 0.903 | 0.931 | 0.079 |
| 16 | het | linear | 0.767 | 0.936 | 0.951 | 0.039 |
| 16 | het | pairwise | **0.970** | 0.989 | 0.991 | **0.002** |
| 16 | het | pairwise low-rank | **0.962** | 0.985 | 0.980 | **0.002** |
| 16 | iid | linear | 0.519 | 0.757 | 0.848 | 0.119 |
| 16 | iid | pairwise | 0.852 | 0.941 | 0.945 | 0.065 |
| 16 | iid | pairwise low-rank | 0.784 | 0.902 | 0.917 | 0.062 |

Both criteria are met in the structured regime:

- **quadratic ≫ linear.** R² 0.767 → 0.970 at D = 16, 0.544 → 0.772 at D = 6.
  Regret falls 20× (0.039 → 0.002).
- **low-rank ≈ full.** 0.962 against 0.970 — `q = 4` costs 0.8% of R² and
  nothing measurable in regret. In i.i.d. the gap is larger (0.784 against
  0.852, 8%), exactly as M31 predicts: that regime is not genuinely low-rank.

At D = 16 heterogeneous the low-rank surrogate ranks bundles at ρ = 0.985 and
selects a bundle within 0.2% of the best available. **M29–M31 are no longer
only spectral: the low-rank interaction has predictive value on held-out
multi-node perturbations.**

## M32B — multi-unit bundles (`Δ_v ∈ {0,1,2}`, diagonal active): the pairwise term fails

| D | regime | model | R² | ρ | sign | regret |
|---|---|---|---|---|---|---|
| 16 | het | linear | **−0.140** | 0.734 | 0.852 | 0.158 |
| 16 | het | diagonal | **+0.745** | 0.913 | 0.939 | 0.073 |
| 16 | het | diag + pairwise | **+0.197** | 0.877 | 0.931 | 0.085 |
| 16 | het | diag + low-rank | +0.196 | 0.876 | 0.926 | 0.127 |
| 16 | iid | linear | 0.006 | 0.510 | 0.736 | 0.242 |
| 16 | iid | diagonal | **+0.460** | 0.729 | 0.832 | 0.153 |
| 16 | iid | diag + pairwise | +0.274 | 0.693 | 0.821 | 0.293 |
| 6 | het | linear | −0.118 | 0.563 | 0.764 | 0.302 |
| 6 | het | diagonal | **+0.414** | 0.705 | 0.825 | 0.210 |
| 6 | het | diag + pairwise | +0.103 | 0.753 | 0.861 | 0.184 |

Three findings, in order of importance:

**1. The linear model has negative R² for multi-unit bundles** (−0.118 to
−0.140 heterogeneous, 0.006 i.i.d.): it is worse than predicting the mean. A
first-order allocator is not merely weak here, it is actively misleading.

**2. The diagonal is the dominant nonlinearity for multi-unit steps.** Adding
`Σ_v H_vv C(Δ_v,2)` takes R² from −0.140 to **+0.745** at D = 16. This is the
term that was missing, and it is per-coordinate curvature, not coupling.

**3. Adding the pairwise term then *destroys* the magnitude fit** — 0.745 →
0.197 — while barely moving the ranking (ρ 0.913 → 0.877, regret 0.073 →
0.085). The interaction coefficients were estimated at `Δ_u = Δ_v = 1` and do
not extrapolate to `Δ_v = 2`, where the neglected third-order terms scale up
faster than the second-order correction. The second-order expansion is
accurate in a neighbourhood it does not reach.

## What this licenses, and what it forbids

**The supported algorithm is incremental binary rounds.** Add at most one unit
per node per round, score with `−UᵀΔ + low-rank pairwise`, then re-estimate at
the new base state. On held-out bundles that surrogate achieves R² = 0.962,
ρ = 0.985 and regret 0.002 in the structured regime.

**Multi-unit steps from a single expansion are not supported.** Either
re-estimate at the new base point, or move to third order — `I_uvw` and the
higher discrete ANOVA terms — before trusting magnitudes. Note the ranking
degrades far less than the magnitude, so a selection-only use of the
multi-unit surrogate is less damaged than a predictive one.

**Regime matters, as M31 said it would.** Every conclusion above is stronger in
the heterogeneous regime; in i.i.d. the low-rank compression costs 8% of R²
rather than 0.8%.

## Scope

D ∈ {6, 16}, chain and balanced families, 5 seeds, two budget fractions,
`uniform` base allocation, `q = 4`. Bundles are sampled uniformly from
eligible nodes rather than adversarially. `U`, `H_vv` and `I` are re-estimated
at every base state, as M31 requires — no calibrated basis is reused.
