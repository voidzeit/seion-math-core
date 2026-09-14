# M38 — the lookahead result survives at m = 10; the greedy-harm result does not

**EXPERIMENTAL.** M38-0 and M38A complete; M38B (m ≥ 12, no oracle) not run.
Raw: `terminal_oracle_m10_parallel_raw.json`,
`terminal_oracle_m10_parallel_values_seed*.npy`,
`rollout_calibration_m10_raw.json`, `policy_scaling_m10.json`.
Summary: `m38_horizon_scaling.csv`.

## 1. M38-0 — an exact terminal oracle exists at m = 10

| | m = 8 | m = 10 |
|---|---|---|
| terminal profiles | 235,348 | **3,039,400** |
| action sequences | 3.08e10 | 2.99e12 |
| unique optimum | 5 of 5 seeds | **5 of 5 seeds** |
| enumeration-vs-direct verification | 0.000e+00 | **0.000e+00** |
| wall time per seed | 24 s (parallel) | 428 s (parallel) |

Enumeration is licensed by terminal-state sufficiency under (H1) fixed
projector bases and (H2) purely rank-indexed evaluation. The parallel
enumerator splits the depth-first walk on the first two coordinates into
independent prefix subtrees; it reproduced the serial m = 8 optimum exactly
(1.154480) before being used at m = 10.

**m = 10 is the last comfortable size.** Cost scales at 18× per size step,
worse than the 12.9× profile growth because the chain is longer. Extrapolating,
m = 11 costs ~25 min/seed and m = 12 ~80 min/seed. Beyond m = 10 the two-phase
design is forced, exactly as planned.

## 2. M38A — the two M35c claims, retested

`Γ = R_T^rollout / R_T^base`, both regrets against the same exact optimum.
Both estimands reported: ratio-of-means (`G_rm`) and mean-of-paired-ratios
(`G_mr`) with a paired bootstrap CI.

| m | base | h | true regret | G_rm | G_mr | paired CI95 | rank | percentile | evals |
|---|---|---|---|---|---|---|---|---|---|
| 8 | first order | 0 | 0.2298 | 1.000 | 1.000 | — | 24,148 | 10.26% | 55 |
| 8 | first order | 1 | 0.3867 | 1.683 | **1.690** | **[1.052, 2.866]** | 40,073 | 17.03% | 337 |
| 8 | first order | 6 | 0.0218 | 0.095 | **0.122** | **[0.028, 0.245]** | **11** | **0.0046%** | 7,897 |
| 10 | first order | 0 | 0.2942 | 1.000 | 1.000 | — | 374,160 | 12.31% | 67 |
| 10 | first order | 1 | 0.3242 | 1.102 | **1.376** | **[0.997, 2.093]** | 378,261 | 12.45% | 721 |
| 10 | first order | 2 | 0.1447 | 0.492 | 0.863 | [0.309, 1.585] | 7,882 | 0.259% | 7,321 |
| 10 | first order | 3 | 0.1302 | 0.443 | 0.813 | [0.264, 1.552] | 5,533 | 0.182% | 12,601 |
| 10 | first order | 6 | 0.0705 | 0.240 | **0.280** | **[0.051, 0.625]** | **4,269** | **0.140%** | 20,521 |

### Claim 1 — "exhaustive one-step optimization is worse than the base policy"

**Does not survive.** At m = 8, Γ = 1.690 with CI [1.052, 2.866], excluding 1.
At m = 10, Γ = 1.376 with CI **[0.997, 2.093]** — the lower bound sits at
0.997 and the interval includes 1. The point estimate still exceeds 1 and the
miss is narrow, so this is "no longer significant at n = 5", not "refuted". But
the M35c wording — *significantly* worse than the base policy — is not
supported at the second problem size and should not be carried forward without
qualification.

### Claim 2 — "full-horizon lookahead recovers most of the regret"

**Survives, attenuated.** Γ goes 0.122 → 0.280; the CI still excludes 1 at
both sizes. The gap closed drops from 88% to 72%, and in landscape terms the
degradation is sharper: rank 11 of 235,348 (0.0046 percentile) becomes rank
4,269 of 3,039,400 (0.140 percentile), a 30× worse percentile. Cost rises from
7,897 to 20,521 evaluations.

So lookahead still helps, significantly, at a second exact reference — but its
advantage shrinks with problem size while its cost grows.

## 3. Policy benchmark at m = 10, against the exact optimum

| policy | terminal/E₀ | true regret | profile rank | percentile | evals |
|---|---|---|---|---|---|
| uniform | 1.0171 | 0.8597 | 1,720,547 | 56.6% | 6 |
| local_greedy | 0.9635 | 0.7425 | 1,155,732 | 38.0% | 6 |
| **measured_first_order** | **0.8487** | **0.2942** | **374,160** | **12.3%** | 72 |
| full_pairwise | 0.8551 | 0.3242 | 378,262 | 12.4% | 342 |
| lowrank_pairwise_q4 | 0.8579 | 0.3377 | 380,206 | 12.5% | 342 |
| step_greedy | 0.8551 | 0.3242 | 378,261 | 12.4% | 726 |

The m = 8 pattern reproduces: measurement separates from non-measurement by a
wide margin, and among measurement-based policies nothing separates —
first order at 72 evaluations matches or beats full pairwise at 342 and
step-greedy at 726. `full_pairwise` and `step_greedy` again land on
near-identical terminal profiles (ranks 378,262 and 378,261), reproducing the
m = 8 observation that the pairwise surrogate converges to the one-step
optimum.

`uniform` sits at the 56.6th percentile of the admissible landscape and
`local_greedy` at the 38.0th — both effectively indistinguishable from an
arbitrary feasible profile at this size.

## 4. What this changes

- The **headline lookahead result stands** at a second problem size with a
  genuine terminal reference, which is what M38 was built to test.
- The **sharpest single number of M35c — Γ(h=1) significantly above 1 — does
  not replicate.** Anywhere it was quoted as evidence that exact greedy is
  actively harmful, it must be softened to "point estimate above 1 at both
  sizes, significant at m = 8 only".
- The **attenuation is the new fact**: 0.122 → 0.280 in Γ and 0.0046% →
  0.140% in landscape percentile, at 2.6× the cost. Whether lookahead remains
  worth its price at m ≥ 12 is now an open quantitative question rather than a
  settled one.

## 5. Scope and what remains

Five seeds per size, chain topologies, D = 16, heterogeneous synthetic regime,
b = 3, T = 6. Nothing here is proved. M38B — paired terminal comparison at
m = 12 and 16 without an oracle — is not run; when it is, it must report cost
in two currencies, rank budget and forward evaluations, since rollout consumes
roughly 300× the evaluations of the first-order base at m = 10 and a
same-rank-budget comparison would flatter it.
