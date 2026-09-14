# M37 — the heterogeneity mechanism is refuted; effective rank measures the rank requirement, not the residual regret

**EXPERIMENTAL** unless marked otherwise. 630 distribution configurations
(D ∈ {8,16,32} × 10 seeds × 21 alpha families) plus 60 placement
configurations. Raw: `m37_raw.json`, `m37_raw_d16.json`, `m37_raw_d32.json`,
`m37_placement_raw.json`. Summaries: `m37_spectral_summary.csv`,
`m37_operational_summary.csv`, `m37_statistics.json`.

## 1. Executive verdict

**What actually causes the low-dimensional interaction observed in M31?**

> The mean spectral decay rate is the dominant identified driver — not
> heterogeneity, whose measured effect runs *opposite* to the hypothesis — but
> it explains only a third to a half of the variance, so the mechanism is at
> best partially identified.

Closest to **OUTCOME D** (no complete systematic mechanism) with a partial
predictor, not OUTCOME A.

**Not OUTCOME E.** §8 shows r_eff does not predict residual regret at a fixed
rank, which on first reading was taken as operational inertness. §11 corrects
that: r_eff predicts the *rank requirement* per instance at Spearman
0.69–0.79. Low-rank approximation remains useful; what fails is the
heterogeneity explanation, not the tool.

## 2. Gate 0 — M31 reproduction: **PASS**

Three published M31 cells reproduced by running M31's own code, to machine
precision:

| cell | r_eff | R4 |
|---|---|---|
| D16_heterogeneous | 4.5461 vs 4.5461 (Δ = 0) | 0.9535 vs 0.9535 (Δ = 0) |
| D8_heterogeneous | 4.6073 vs 4.6073 (Δ = 8.9e−16) | 0.9603 vs 0.9603 |
| D16_iid | 8.1910 vs 8.1910 (Δ = 1.8e−15) | 0.8056 vs 0.8056 |

**Note on r_eff.** M31's code computes the participation ratio
`(Σ|λ|)²/Σλ²`. The M37 brief specifies an entropy form `exp(−Σ p log p)`.
These are different statistics; the frozen M31 definition is used throughout
and the entropy form is reported alongside in the raw records.

## 3. H1 — heterogeneity width: **REFUTED IN TESTED REGIME, and inverted**

The decisive contrast is degenerate (`α_std = 0` exactly) against the M31
baseline `U[0.3, 2.0]`:

| D | degenerate | baseline | verdict |
|---|---|---|---|
| 8 | 5.69 [5.09, 6.30] | 4.37 [3.54, 5.21] | H1 refuted (no increase) |
| 16 | 5.97 [5.30, 6.62] | 4.10 [3.66, 4.50] | **H1 INVERTED** |
| 32 | 6.95 [6.29, 7.62] | 4.38 [3.65, 5.03] | **H1 INVERTED** |

A network with **zero** spectral heterogeneity has *higher* effective
interaction rank than the heterogeneous baseline, significantly so at D = 16
and D = 32. In regression, `alpha_std` carries a **negative** slope at every
dimension (−2.16, −2.68, −4.00), the opposite sign to H1's prediction.

The controlled sub-contrast is cleaner still. Varying the mean at zero width
moves r_eff by 2.4 units (D = 8: α = 0.5 → 7.17, α = 1.0 → 5.09,
α = 1.5 → 4.80), while varying width at fixed mean moves it by ±0.4 with
inconsistent sign (at α₀ = 1.0 it *increases*: 5.03 → 5.34 → 5.37).

## 4. H2 — effective-scale count: **not supported**

Bimodal families impose exactly two spectral scales. Their r_eff ranges over
2.78–6.22 depending on mixture fraction and on which pair of α values is used,
with no tendency toward 2. Effective rank does not count spectral scales.

## 5. H3 — topological placement: **not supported at n = 10**

Gate 2 passed exactly: the alpha multiset is identical across placements
(max deviation 0.000e+00). Seed-matched against random placement:

| placement | r_eff | difference vs random |
|---|---|---|
| random | 4.92 | — |
| high_at_root | 5.55 | +0.630 [−0.292, +1.652] ns |
| low_at_root | 4.71 | −0.204 [−1.412, +1.090] ns |
| alternating | 5.02 | +0.103 [−0.770, +1.040] ns |
| clustered | 5.13 | +0.217 [−0.844, +1.244] ns |
| dispersed | 4.74 | −0.180 [−0.840, +0.485] ns |

**No placement differs significantly from random.** This is "not supported",
not "refuted": the intervals are wide at 10 seeds and an effect of ~0.6 cannot
be excluded.

Two corrections to an earlier reading of this phase. First, `clustered` and
`high_at_root` originally produced **byte-identical** arrays — on a chain,
"contiguous blocks by value" and "high α toward the root" are both the sorted
multiset, so `clustered` tested nothing. It now permutes the block order.
Second, an earlier run showed high_at_root significantly above random
(+1.086); after the fix the random baseline itself shifted (4.46 → 4.92,
because the corrected generator consumes the RNG differently) and the contrast
became non-significant. The within-seed spread statistic quoted earlier
(median ~3.0) is a max−min over six conditions with one observation each and is
dominated by noise; the seed-matched differences above are the defensible
numbers.

## 6. H4 — stability in ambient dimension: **mixed**

| family | D=8 | D=16 | D=32 |
|---|---|---|---|
| A0 degenerate α=0.5 | 7.17 | 6.79 | **8.45** |
| A0 degenerate α=1.0 | 5.09 | 6.06 | **6.88** |
| A1 narrow α=0.5 ε=0.05 | 7.05 | 7.09 | **8.44** |
| A3 baseline U[0.3,2.0] | 4.37 | 4.10 | **4.38** |
| A4 wide U[0.2,2.5] | 3.91 | 3.95 | **4.13** |
| A2 bimodal 0.3/2.0 p=0.75 | 3.72 | 3.50 | **2.78** |

The split is systematic: **slow-decay families (low α) grow with D; high-mean
and heterogeneous families are flat.** The M31 baseline is flat to within 7%
across a 4× range of D, and the wide family within 6%. So H4 holds for exactly
the families M31 studied, and fails for the low-α ones — which is consistent
with M31's own observation that the iid regime (no imposed decay, effectively
α ≈ 0) grew from 4.57 to 9.05 over D = 4…32.

## 7. Mechanism: partial

Joint regression of r_eff on (`alpha_mean`, `alpha_std`):

| D | n | joint R² | alpha_mean alone | alpha_std alone |
|---|---|---|---|---|
| 8 | 210 | 0.336 | **0.257** | 0.129 |
| 16 | 210 | 0.335 | **0.224** | 0.164 |
| 32 | 210 | **0.570** | **0.363** | 0.298 |

Both coefficients are negative and significant everywhere;
`alpha_mean` is the stronger single predictor at D = 8 and D = 32. But the
alpha distribution explains only **34–57%** of the variance in r_eff. The
remainder is not attributable to distribution or (per H3) to placement.

## 8. H5 — spectral rank predicts residual regret at fixed q: **REFUTED**

Read this section together with §11, which tests the other half of the
question and reaches the opposite answer.

Correlation between r_eff and the decision regret of a rank-4 surrogate, on
held-out bundles with ‖Δ‖₀ ≥ 3:

| D | Spearman(r_eff, q4 decision regret) | n |
|---|---|---|
| 8 | **+0.096** | 210 |
| 16 | **−0.069** | 210 |
| 32 | **+0.026** | 210 |

**Zero at every ambient dimension.** Configurations whose effective rank
differs by a factor of three deliver indistinguishable decision quality under
the same rank-4 approximation.

Pooled across configurations, a single mode appears to capture most of the
operational value — but see §11: this is a pooling artifact, and per
configuration `q = 1` suffices in 2 of 210 cases.

| D | first_order | q=1 | q=2 | q=4 | full |
|---|---|---|---|---|---|
| 8 | R² 0.667 | 0.836 | 0.892 | 0.925 | 0.940 |
| 16 | 0.860 | 0.938 | 0.964 | 0.982 | 0.989 |
| 32 | 0.920 | **0.970** | 0.984 | 0.994 | 0.999 |

At D = 32, `q = 1` reaches R² 0.970 against the full matrix's 0.999. The
interaction matters for prediction, but its *dimension* is not what governs
how much.

## 9. Which hypotheses survived

| | verdict |
|---|---|
| H1 heterogeneity width drives dimension | **REFUTED IN TESTED REGIME**, inverted sign |
| H2 dimension counts spectral scales | **not supported** |
| H3 topological placement drives dimension | **not supported at n = 10** (OPEN) |
| H4 r_eff stable in D | **mixed** — holds for high-mean/heterogeneous, fails for low-α |
| H5a spectral rank ⇒ residual regret at fixed q | **REFUTED** at all three D, n = 210 each |
| H5b spectral rank ⇒ per-instance rank requirement | **supported**, Spearman 0.69–0.79 (§11) |

## 10. Consequences for M31 / M32 / M34

- **M31's observation stands and reproduces exactly**, but its framing as a
  *heterogeneity* effect is wrong. The families it called "heterogeneous" also
  had higher mean α, and mean α is the stronger driver.
- M31's two regimes are unified: iid is not "unstructured", it is
  **slow-decay** (α ≈ 0), which is why its r_eff grew with D exactly as the
  low-α families here do.
- **M32's predictive result is unaffected** — the interaction does predict
  held-out bundles, and q = 4 does approximate the full matrix. What M37 removes
  is the inference that this is *because* the matrix is intrinsically
  low-dimensional.
- M34's decision-value findings are untouched; they never used r_eff.

## 11. Correction to §8 — r_eff *does* predict the rank requirement

The §8 result stands as stated but was over-read on first pass. Two different
questions were conflated:

- *At a fixed q = 4, does higher r_eff mean worse decisions?* **No** —
  Spearman +0.096 / −0.069 / +0.026. At q = 4 most configurations already sit
  near the regret floor, so the statistic cannot discriminate.
- *How much rank does an instance need?* Define the decision-aware rank
  `q_dec⁹⁵ = min{ q : R²(q) − R²(first order) ≥ 0.95 · (R²(full) − R²(first order)) }`
  computed **per configuration**. Then r_eff predicts it strongly.

| D | q=1 | q=2 | q=4 | q=8 | none | median | ≤4 | Spearman(r_eff, q_dec⁹⁵) |
|---|---|---|---|---|---|---|---|---|
| 8 | 5 | 38 | 82 | 77 | 4 | 4 | 60.7% | **+0.710** |
| 16 | 1 | 38 | 82 | 87 | 2 | 4 | 57.6% | **+0.776** |
| 32 | 2 | 30 | 65 | 105 | 8 | 8 | 46.2% | **+0.749** |

Two consequences, both of which correct earlier statements in this file.

**Low-rank approximation of I remains useful and is not withdrawn.** What is
withdrawn is the claim that effective rank fails to identify where the value
is: it identifies how much rank the instance requires, at ρ ≈ 0.71–0.78.

**The earlier reading that "q = 1 already captures most of the value" was a
pooling artifact.** That came from a pooled R² of 0.970 at D = 32. Per
configuration, q = 1 clears the 95% threshold in 2 of 210 cases. Pooling R²
across configurations before choosing q hides instances where low rank fails
inside instances where it succeeds. Likewise q = 4 is a **median**, not a
universal sufficiency — it clears the threshold in under two thirds of
configurations at D = 8 and under half at D = 32, and the requirement grows
with ambient dimension.

## 12. Consequence for the programme

M36 found that certificate tightness does not predict ranking fidelity. M37
finds that spectral concentration is not caused by heterogeneity, and that the
naive fixed-q reading of its operational value was wrong in both directions.
The transferable lesson is narrower than "elegant quantities are inert": it is
that **a structural quantity must be evaluated against the decision question
actually being asked**, and that pooled goodness-of-fit is the wrong instrument
for choosing a per-instance approximation order.

Investment in *explaining* r_eff — mode interpretation, mechanism hunting — is
not supported: 43–66% of its variance is unattributed and heterogeneity is
refuted as the cause. Investment in *using* low-rank approximation is
supported, with q chosen per instance by a decision-aware criterion rather than
by a spectral threshold.

## 13. What remains OPEN

- The majority of r_eff variance (43–66%) is unexplained by distribution or
  placement.
- H3 at larger seed counts: a ~0.6 placement effect is not excluded.
- Why `q = 1` suffices operationally while the spectrum shows 4–8 significant
  modes.
- Everything is synthetic; no trained network or real HT/TTN was used.

## 14. Reproducibility

24-worker CPU parallelism, BLAS pinned to one thread per worker. GPU was
deliberately not used: the frozen pipeline is numpy float64 and Gate 0
reproduced M31 against it exactly, so moving to CUDA would trade
reproducibility for throughput. Speedup 11× at D = 16 and ~60× at D = 32.

Parallel-versus-serial agreement was **asserted, not assumed**: 42
configurations compared field-by-field including full spectra against the
original serial D = 16 file, maximum deviation **0.000e+00**, plus in-process
checks on both sweeps.
