# M29 — the interaction is low-rank, not local

**EXPLORATORY, NOT CONFIRMATORY.** Same label as the campaigns it reuses.

Raw: `pairwise_interaction_raw.json` (400 configs, same base states as M27).
Analysis: `pairwise_interaction_analysis.json`, by
`../experiments/analyze_pairwise_interaction.py`.

Measured, at each M27 base state, for every pair of allocatable nodes:

    I_uv(r) = E(r + e_u + e_v) - E(r + e_u) - E(r + e_v) + E(r)

the finite-difference analogue of `d²E / dr_u dr_v`, symmetric by
construction, and equal to `-(U_v(r + e_u) - U_v(r))`.

## Result 1: the interaction dominates the gradient

| regime | k | m | ‖I‖_F / ‖U‖₂ | r_eff | r_eff/m | R1 | R2 | R4 | pairs@80% | reversals |
|---|---|---|---|---|---|---|---|---|---|---|
| het | 6 | 5 | 0.53 | 2.68 | 0.535 | 0.521 | 0.949 | 0.999 | 0.204 | 0.081 |
| het | 10 | 9 | 1.33 | 3.69 | 0.410 | 0.486 | 0.875 | 0.981 | 0.099 | 0.081 |
| het | 16 | 15 | 2.20 | 4.99 | 0.333 | 0.467 | 0.799 | 0.951 | 0.059 | 0.084 |
| het | 24 | 23 | **3.83** | 5.52 | 0.240 | 0.490 | 0.810 | 0.940 | 0.037 | 0.084 |
| iid | 6 | 5 | 1.51 | 3.19 | 0.638 | 0.518 | 0.896 | 0.995 | 0.298 | 0.144 |
| iid | 10 | 9 | 1.93 | 5.23 | 0.581 | 0.404 | 0.720 | 0.929 | 0.179 | 0.144 |
| iid | 16 | 15 | 3.29 | 6.07 | 0.405 | 0.426 | 0.740 | 0.910 | 0.093 | 0.127 |
| iid | 24 | 23 | **4.63** | 6.81 | 0.296 | 0.450 | 0.770 | 0.904 | 0.050 | 0.136 |

`‖I‖_F / ‖U‖₂` grows monotonically with depth to **3.8–4.6 at k=24**: the
second-order term is roughly four times the size of the first-order term. Any
allocator built on a first-order score is fitting the smaller part of the
objective. This is the quantitative form of M27's negative result.

## Result 2: the interaction is not local ALONG CHAINS — hypothesis 1 rejected here

Mean `|I_uv|` against topological distance `d_T(u,v)`:

| | d=1 | d=2 | d=3 | d=4 | d=5 | d=6 | d=7 | d=8 |
|---|---|---|---|---|---|---|---|---|
| iid k=10 | 9.41e−3 | 7.97e−3 | 8.21e−3 | 6.34e−3 | 5.96e−3 | 6.51e−3 | 5.79e−3 | 7.02e−3 |
| iid k=24 | 4.04e−3 | 2.82e−3 | 2.92e−3 | 2.74e−3 | 2.33e−3 | 2.67e−3 | 2.85e−3 | 2.23e−3 |
| het k=24 | 2.59e−2 | 4.74e−2 | 1.80e−2 | 2.33e−2 | 1.61e−2 | 1.87e−2 | 1.42e−2 | 1.81e−2 |

There is no exponential decay: iid k=24 falls only by a factor 1.8 across eight
hops, and the heterogeneous curve is not even monotone (d=2 exceeds d=1).
Windowed dynamic programming, message passing over the tree, or subtree-local
optimization will not capture this structure.

**Read this as "not local along chains", not "not local in general."** Every
pair in a chain is ancestor/descendant and shares its entire downstream path to
the root, so `d_T` here is a generation gap and the genuinely branched cases —
siblings, and pairs whose transport paths are partly disjoint — are untested.
Whether distance or *shared downstream* is the explanatory variable cannot be
separated in this topology. That is M30.

## Result 3: the interaction IS strongly low-rank — hypothesis 2

This is the actionable finding. At k=24 with 23 allocatable nodes and 253
distinct pairs:

- one mode carries **~45–49%** of the spectral energy (R1),
- two modes carry **77–81%** (R2),
- four modes carry **90–94%** (R4).

And the participation ratio `r_eff` grows far slower than `m`: as `m` goes
5 → 23, `r_eff/m` falls 0.64 → 0.30 (iid) and 0.54 → 0.24 (het). The
interaction among tens of nodes is governed by a handful of latent modes.

The energy is also concentrated in few pairs — 3.7–5.0% of pairs carry 80% of
`Σ I_uv²` at k=24 — but low-rank is the stronger and basis-independent
statement, and sparsity is partly a consequence of it (a concentrated rank-one
outer product looks sparse).

## Result 4: a no-go for the two score classes actually tested

Bumping one node's rank reverses the true utility ordering of two *other*
nodes in **8.1–14.4%** of triples.

For the two scores under test this is not merely a measurement, it is a
representability failure, provable from their definitions:

- `local_truncation_error` ([network.py:184](../src/network.py)) reads
  `ambient_values`, produced by `ambient_forward`, which never consults ranks —
  and indexes `ranks` only at the node itself. So `eps_v = f(v, r_v)`.
- `path_amplification` ([network.py:202](../src/network.py)) takes no ranks at
  all. So `w_v` is rank-independent.

Hence both `eps_v` and `w_v·eps_v` are functions of `r_v` alone, and are
*identically unchanged* under `r → r + e_w` for any `w ≠ v`. Their predicted
ordering of `u` and `v` therefore cannot change under exactly the perturbation
that reverses the true ordering 8–14% of the time.

**Proposition (measured no-go).** Any allocator ranking nodes by a score
depending only on `(v, r_v)` — which includes `local_error_greedy` and
`pathwise_global` as implemented — predicts an ordering invariant under
changes to third nodes' ranks, while the true ordering reverses in 8.1–14.4%
of such triples in this design.

This is a statement about this score class, not about all separable scores: a
score allowed to depend on the full allocation vector is not covered.

## Result 5: coupling is associated with negative utility, partially

`P(U_v < 0)` by quartile of a node's total coupling `Σ_u |I_uv|`, normalized
per config:

| quartile | P(U_v < 0) |
|---|---|
| Q1 weakest | 37.3% |
| Q2 | 38.6% |
| Q3 | 45.2% |
| Q4 strongest | **49.5%** |

Mean normalized coupling is 1.32× higher for negative-utility nodes than for
positive ones. The association is real and in the predicted direction, but it
is not a full explanation: even the weakest-coupling quartile is 37.3%
negative. (The 42.7% overall rate reproduces M27 exactly, as it must — same
base states, independently recomputed.)

## What this licenses

A second-order allocator is now motivated by measurement rather than by
analogy. With `E(r + Δ) ≈ E(r) − Uᵀ Δ + ½ ΔᵀIΔ`, the low-rank structure means
`I ≈ QΛQᵀ` with `Q` of 4–8 columns is a faithful surrogate, so the whole
interaction enters through `z = Qᵀ Δ ∈ R^q` with `q ≈ 4–8`.

**Low-rank makes efficient global optimization plausible; it does not make it
easy.** `I` is not guaranteed positive semidefinite, so the quadratic form need
not be convex, and `Δ` is integer-valued — this remains a quadratic integer
program. What the low-rank structure buys is that the coupling is carried by a
handful of latent coordinates rather than by 253 independent pair terms, which
admits specialized algorithms that were not available before.

What the data rules out: local/windowed methods (Result 2) and any allocator
in the `(v, r_v)` score class (Result 4).

## Scope

Chain topologies only — every pair is ancestor/descendant, so the
"different branches" case is untested and `d_T` is a generation gap. Ambient
dimension 6, synthetic cores, `uniform` base allocation, Δrank = +1, one base
point per budget. `I` is a finite difference at Δ=1, not a derivative. k=3
again yields no records (fewer than three allocatable nodes).
