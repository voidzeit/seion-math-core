# Discrete Hessian — the correction to M31's inertia claim

**EXPLORATORY, NOT CONFIRMATORY.**

Raw: `discrete_hessian_raw.json` (180 configs). Analysis:
`discrete_hessian_analysis.json`, by `../experiments/analyze_discrete_hessian.py`.

## Why this pass exists

M31 reported the signed inertia of the off-diagonal interaction matrix `I` and
concluded the quadratic surrogate is non-convex. **That inference was invalid.**
`I` is assembled from off-diagonal second differences only, so its diagonal is
zero by construction, `tr(I) = 0`, and its eigenvalues sum to zero. Any nonzero
symmetric zero-trace matrix is necessarily indefinite with balanced counts and
roughly half its spectral energy negative. M31's numbers — negative energy
0.454–0.511, n₊ ≈ n₋ ≈ 7 — are precisely what the design forces, and carry no
information about the problem.

Convexity belongs to the **full discrete Hessian**

    H = I + diag(H_vv),   H_vv = E(r + 2e_v) − 2E(r + e_v) + E(r).

This pass measures `H_vv` on the M31 configurations (nodes need `r_v + 2 ≤ D`
of headroom) and compares the two inertias.

## Result

| D | regime | m | I neg-energy | **H neg-energy** | **H is PSD** | **diag > 0** | diagonal dominance |
|---|---|---|---|---|---|---|---|
| 6 | iid | 14 | 0.487 | 0.516 | **0%** | **47%** | 0.271 |
| 6 | het | 14 | 0.472 | 0.414 | **0%** | **52%** | 0.467 |
| 16 | iid | 14 | 0.502 | 0.565 | **0%** | **50%** | 0.374 |
| 16 | het | 14 | 0.471 | 0.464 | **0%** | **51%** | 1.246 |
| 32 | iid | 14 | 0.511 | 0.512 | **0%** | **46%** | 0.450 |
| 32 | het | 14 | 0.454 | 0.454 | **0%** | **50%** | 2.416 |

`diagonal dominance` is the mean of `|H_vv| / Σ_u |H_uv|`; above 1 the diagonal
outweighs the coupling in that row.

## The conclusion survives, for a different and sharper reason

**The surrogate is non-convex: `H` is positive semidefinite in 0 of 180
configurations.** So M31's headline was right — but its evidence was not, and
the actual obstruction is elsewhere than claimed.

**The obstruction is the diagonal, not the coupling.** The single-coordinate
second difference `H_vv` is positive in only **46–52%** of nodes — a coin flip.
Half the time the root error is locally *concave* in a node's own rank, meaning
the marginal return to rank is increasing rather than diminishing. This is not
a tautology of anything: nothing in the construction forces the sign of
`H_vv`, and it is measured directly.

The decisive case is heterogeneous at D = 32, where the diagonal dominates the
off-diagonal row sums by a factor of **2.42** on average, and `H` is *still*
never PSD. A diagonally dominant matrix with sign-mixed diagonal entries is not
positive definite — it is definite with the sign of its diagonal, direction by
direction. So even where the pairwise coupling has been rendered relatively
small, convexity fails on the diagonal alone.

This also gives M27's non-monotonicity a cleaner companion statement. `E` is
not merely non-monotone in `r_v` (42.7% of first differences negative, M27);
it is non-convex in `r_v` (≈50% of second differences negative, here). Rank
allocation is optimizing a discrete function that is rough in each coordinate
separately, before any interaction is considered.

## Consequences for the allocation programme

**Diminishing returns on the integer rank lattice is extensively violated.**
Since `U_v(r + e_v) − U_v(r) = −H_vv`, a positive diagonal means diminishing
returns and a negative one means *increasing* returns to rank. Both occur about
equally often. The precise casualty is the DR property on `Z_{≥0}^m`, not
submodularity of a binary set function — for a set function each element can be
added only once, and submodularity is governed by the cross terms `I_uv`, which
this pass does not bear on.

**The diagonal does not enter binary bundles at all.** The correct discrete
second-order expansion is

    E(r + Δ) − E(r) ≈ −Σ_v U_v Δ_v + Σ_v H_vv C(Δ_v, 2) + Σ_{u<v} I_uv Δ_u Δ_v

with `C(Δ_v, 2) = Δ_v(Δ_v − 1)/2`. For `Δ_v ∈ {0,1}` that coefficient is zero.
(Sanity check: at `Δ = e_v` the expansion gives exactly `−U_v`, which is the
definition, and at `Δ = 2e_v` it gives `−2U_v + H_vv`, which reproduces the
definition of `H_vv`. Writing the diagonal as `½ΔᵀDΔ` instead would add a
spurious `½H_vv` per selected node to a response that is already exact.) So
the M29–M31 low-rank findings remain exactly the relevant structure for
one-unit-per-node bundles; they are not overturned by this correction.

**The useful shape is diagonal-plus-low-rank, not low-rank.** `H = D + I` with
`D` diagonal and `rank_ε(I) ≈ 4` in the structured regime. `D` is full-rank but
costs only `m` numbers, so storing and applying the full second order is
`O(m) + O(mq)`, not `O(m²)`. The plausible theorem is about
`rank_ε(H − diag H)`, which is what M29–M31 actually measured.

## Scope

D ∈ {6, 16, 32}, chain and balanced families, both regimes, 5 seeds, 15
internal nodes (m = 14 allocatable, further restricted to nodes with two
increments of rank headroom). Δrank = +1 and +2 finite differences at a
`uniform` base allocation; these are differences, not derivatives.
