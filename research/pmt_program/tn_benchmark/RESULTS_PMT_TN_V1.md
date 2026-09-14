# PMT-TN Benchmark V1 — results

## Status and scope

* **Status:** `NUMERICAL_OBSERVATION`.
* **Theory under test:** Theorem R v2 (`ADVISORY_PROOF_DRAFT`, tag `theorem-R-v2-review`). Nothing here
  is a proof; soundness results are conditional on the draft, exactly as preregistered.
* **Preregistration:** `PREREGISTRATION_PMT_TN_V1.md` with Amendments 1 and 2. Grid:
  `experiments/configs/PMT_TN_BENCHMARK_V1.json`.
* **Data:** `artifacts/pmt_tn_benchmark/2026-09-13-v1/<campaign>/`. Analysis:
  `analysis/tables.json` and `analysis/figures/`, produced by `analyze.py`; input hashes are in `tables.json`.
* **Hardware:** CPU only (AMD Ryzen 5 3600, 64 GB), float64, PyTorch 2.7.1 CPU for F7/F7R.

### Excluded from analysis (quarantined, see `README_ABORTED_AND_SMOKE.md`)

* `F1-ABORTED-nondeterministic-seeds`
* `*-quick-smoke-nondeterministic-seeds`
* `F2-CRASHED-import-error` (no runs)

Later smoke runs were written outside the artifact tree.

## Campaigns

| campaign | runs | labels | ratio max (`E_obs/B_R`) | median deflation `‖F‖/(M̂^k L)` |
|---|---|---|---|---|
| F1 + F5 (matrix products, adaptive SVD) | 4 224 | all `WITHIN_CERTIFICATE` | 0.142 | 2.9e-7 |
| F2 + F5 (TTN, PCA projectors) | 23 040 | all `WITHIN_CERTIFICATE` | 0.0247 | 1.8e-6 |
| F3 (TFIM MPS, TT-SVD projectors) | 2 880 | all `WITHIN_CERTIFICATE` | 0.389 | 0.061 |
| F4 (Hierarchical Tucker, HT-SVD projectors) | 1 152 | all `WITHIN_CERTIFICATE` | 0.0039 | 0.0032 |
| F6 (positive control, witness) | 400 | all `WITHIN_CERTIFICATE` | 1 + 7e-16 | 1 |
| F7 (adversarial) | 1 536 | all `WITHIN_CERTIFICATE` | 1 − 1.3e-11 | 0.96 |
| F7R (adversarial, leakage-constrained) | 960 | all `WITHIN_CERTIFICATE` | 0.9994 | — |
| F8 (constructed negative controls) | 35 | all `EXPECTED_VIOLATION_NEGATIVE_CONTROL` | analytic | — |

## Hypotheses

### H1 — soundness: **supported**

* 34 192 valid runs over F1–F7R: **0 replay triggers**, **0 counterexample candidates**, 0 invalid projectors.
* The closest approach is F7: ratio `1 − 1.3e-11`, still below the `1 + 1e-10` trigger. These are the
  adversary reaching the sharp constant from below.
* H3 shows the pipeline does detect violations when they exist.

### H2 — positive control: **pass**

* Equal angles (200 trees): `max |ratio − 1| = 6.7e-16`.
* Unequal angles (200 trees): `max ratio = 1 + 2e-16`.

### H3 — negative controls: **pass**

* All 35 F8 runs are labelled `EXPECTED_VIOLATION_NEGATIVE_CONTROL`.
* Ratios match the analytic values (`λ`, `√(1+c²)`, `√d`) to 4.7e-16 relative.
* Every validator flags its defect.

### H4 — contraction order (F1): descriptive

Over 528 groups (fixed data, `n`, `χ`, seed, rank; the cost proxy is identical across bracketings):

| bracketing | groups where it minimises `η̂` | groups where it minimises `E_obs` | median `η̂` | median `E_obs/‖F‖` |
|---|---|---|---|---|
| left | 259 | 270 | 0.117 | 0.46 |
| right | 204 | 216 | 0.113 | 0.47 |
| random (5 trees) | 65 | 42 | 0.122 | 0.84 |
| balanced | 0 | 0 | 0.125 | 0.95 |

* The `η̂`-minimising and error-minimising bracketings coincide in 55% of groups.
* The within-group Spearman correlation between `η̂` and `E_obs` has median 0.53.
* Sequential (chain) bracketings are preferred. `η̂` orders bracketings only partially.
* `B_R` itself is a function of `(k, η̂)` at `M̂ = L = 1`, so "explained by `η̂`" holds by construction for
  the certificate, not for the observed error.

### H5 — sharpness beyond the witness (F7)

**Best rigorous ratio per variant and topology** (best restart of each configuration):

| variant | chain | balanced | star | random |
|---|---|---|---|---|
| `coiso` (preregistered, `M̂ = 1` by flattening) | 1.0000 | 0.898 | 0.866 | 1.0000 |
| `opnorm` (Amendment 2) | 0.9992 | 0.9986 | 0.9964 | 0.9984 |

**Preregistered rule** (Amendment 2): **6 configurations** qualify as "near-sharp non-witness":
* `opnorm` balanced, `k = 5` (r = 1) and `k = 7` (r = 1, 2);
* `opnorm` random, `k = 4` (r = 1), `k = 5` (r = 2) and `k = 7` (r = 2).

Their rigorous ratios are 0.972–0.985, with `χ = 3`, `d_span = 3` and `M_gap_rel = 0.0028`.

**Post-hoc diagnostic** (not preregistered; computed from the frozen instances):
* In all 6, the third singular value of the node value spans is only `1.3e-3` to `2.2e-3` of the first. This
  is just above the preregistered tolerance `1e-3`, at a single node or two.
* The optimum is therefore a 2-dimensional witness-type mechanism with a small third component. We do
  **not** claim a genuinely 3-dimensional sharp mechanism: H5 is met formally, but not in substance.

**Further observations** (exploratory):

1. **Topology-independent sharpness under the operator-norm budget.** With `M̂` equal to the operator norm
   (`opnorm`), the adversary reaches `E_obs/B_R ≥ 0.98` (rigorous) or `≥ 0.992` (estimate) on chain, balanced
   and random trees for every `k ∈ {3, 4, 5, 7}`. The optimum `η̂` sits at `η_c(k)` (0.816, 0.655, 0.543,
   0.403). This matches the topology-independence claim of Theorem R.

2. **Flattening budgets make sharpness topology-dependent.** With coisometric laws and the flattening
   budget `M̂ = 1` (`coiso`):
   * chains reach ratio 1 for every `k` (a coisometric realisation of the witness exists when each node has
     one child and one leaf);
   * branching nodes stay well below 1, independent of `χ` and `r`:
     * balanced: 0.866, 0.898, 0.836, 0.765 for `k = 3, 4, 5, 7`;
     * star: 0.866, 0.778, 0.724, 0.662.

   A plausible reading: the rotation needed to combine two internal children (`ℝ² ≅ ℂ` multiplication)
   has flattening norm `√2` times its operator norm. This is a statement about the budget, not a violation
   of Theorem R.

3. **Stars with arity ≥ 3 (`opnorm`).** Only the flattening bound is rigorous for arity ≥ 3, so the
   rigorous ratio collapses to 0.006–0.29 (`M_gap_rel` 0.40–1.11). The estimates are 0.99 (`k = 4`),
   0.96–0.98 (`k = 5`) and 0.87–0.89 (`k = 7`, under-optimised) — "estimate only".

### H6 — regime (F7R): **flattening supported; strict monotonicity fails in 2 of 6 curves**

| curve | `η_c(k)` | max `E_obs` for `η_t ≥ η_c` | `G_k(η_c)` | flat within 2% | non-decreasing (tolerance 1e-3) |
|---|---|---|---|---|---|
| chain k = 3 | 0.816 | 1.1547 | 1.1547 | yes | yes |
| chain k = 5 | 0.543 | 1.3807 | 1.3809 | yes | yes |
| chain k = 7 | 0.403 | 1.5092 | 1.5096 | yes | yes |
| balanced k = 3 | 0.816 | 1.1509 | 1.1547 | yes | **no** (worst drop 0.12%) |
| balanced k = 5 | 0.543 | 1.3771 | 1.3809 | yes | yes |
| balanced k = 7 | 0.403 | 1.5065 | 1.5096 | yes | **no** (worst drop 0.57%) |

* Once `η_t > η_c(k)`, the unconstrained adversary chooses `η̂ ≈ η_c(k)`: the absolute error saturates at
  `G_k(η_c)`, identically for chain and balanced trees (figure 6).
* The monotonicity failures are below 0.6% and come from optimiser noise across independent runs.
* At `η_t ≤ 0.2` with `k ≥ 5`, the optimiser stays below the bound (ratio 0.50–0.97). This is an
  optimisation limitation, not evidence of slack in `G_k`.

### H7 — usefulness: **fails (preregistered as a possible outcome)**

At the largest preregistered rank, the certificate is informative (`B_R/‖F‖ < 1`) in **0%** of runs for F2,
F3 and F4:

| campaign | median `B_R/‖F‖` | median `E_obs/‖F‖` |
|---|---|---|
| F2 | 6.6e5 | 0.83 |
| F3 | 25 | 2e-7 |
| F4 | 474 | 0.0066 |

* The full-subspace certificate `B_R_full` fares no better (0%).
* The cause is norm deflation: `‖F‖ ≪ M̂^k L` (see the campaigns table). The certificate is sound
  and, adversarially, sharp, but vacuous in absolute terms for these physical and approximation networks.

### H8 — gain over the naive bound: descriptive

Median `B_R/B_naive` per campaign:

| F1 | F2 | F3 | F4 | F6 | F7 | F7R |
|---|---|---|---|---|---|---|
| 0.97 | 0.40 | 0.24 | 0.36 | 0.84 | 0.64 | 0.72 |

By `kη̂` (F1): 1.00 for `[0, 0.5)`, 0.90 for `[1, 2)`, 0.69 for `[2, 4)`, 0.36 for `[4, 8)`, 0.20 for `≥ 8`.
The sharp constant tightens the naive `(k−1)η` bound by up to about 5× in the deep or high-leakage regime.

## Summary against the four anticipated outcomes

The benchmark lands on **sound and sharp, but vacuous on realistic networks**:

* **Soundness:** no violation in 34 192 valid runs; the controls behave exactly.
* **Sharpness:** adversarial networks reach the sharp constant on every topology under the operator-norm
  budget, with the predicted saturation at `η_c(k)`.
* **Usefulness:** in F2–F4 the absolute certificate never beats `‖F‖`, because of deflation.

Natural next steps (not started):
1. a relative or deflation-aware certificate (`E/‖F‖`);
2. heterogeneous per-node budgets `M_v`;
3. an operator-norm upper bound for arity ≥ 3 (e.g. SOS), to make the star results rigorous;
4. a targeted search for genuinely 3-dimensional near-sharp mechanisms with a stricter span tolerance.

## Figures (`analysis/figures/`)

1. `fig1_k_eta_ratio.png` — the `(k, η̂)` plane coloured by ratio.
2. `fig2_F1_bracketing.png` — F1 per bracketing.
3. `fig3_gain.png` — gain against `kη̂`.
4. `fig4_deflation.png` — deflation histograms.
5. `fig5_F1_cost.png` — cost against certificate.
6. `fig6_F7R_regime.png` — regime curves with `G_k` (dashed) and `η_c(k)` (dotted).

## Deviations and incidents

* **Amendment 1:** nondeterministic seeds, fixed before any analysed run.
* **Amendment 2:** F7 design decisions taken before the full F7 run, including the added `opnorm` variant.
* **F2 first launch:** crashed at import and produced no runs.
* **F2 manifest commit:** it records `f003a06`, the HEAD when the run finished. It was launched at
  `3424abc`, which has identical F2 code.
* **H5 diagnostic:** the singular-value check of the flagged configurations is post hoc and labelled as such.
