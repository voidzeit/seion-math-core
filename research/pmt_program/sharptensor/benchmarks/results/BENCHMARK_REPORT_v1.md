# SharpTensor 0.1 — confirmatory benchmark report v1

```
DATE:      2026-09-15
PROTOCOL:  ../prereg_config.json   sha256 84a4e039fd64727ee1a2b809ea913cf8d3a36df5841b458b35321d6e6c5c9b9e (FREEZE.json)
RAW:       benchmarks_v1.json (includes code sha256 per module), ../run_v1.log
HOST:      Windows 10, Python 3.12.5, numpy 2.4.2, CPU only (GPU paused under blocker B-0012)
VERDICT:   TRL4 criterion NOT met (B2 fails S1/S2). All runs sound. B3 and B1a meet S1–S3.
```

## Preregistered success criteria

Evaluated on `plan_certified_search` with the best certificate and `ε = 0.01 · ‖R_root(full rank)‖`.

- **S1 memory:** stored bytes are below the full-rank factored run.
- **S2 compute:** counted FLOPs are below the full-rank factored run.
- **S3 non-vacuous:** the relative bound `E/(‖R_r‖ − E)` is finite and at most 1.
- **TRL4 claim:** S1, S2 and S3 all hold for B1a, B2 and B3. B1b is a negative control.

| id | role | S1 memory | S2 compute | S3 non-vacuous | memory ratio | FLOPs ratio | all runs sound |
|---|---|---|---|---|---|---|---|
| B1a | positive | yes | yes | yes | 1.27 | 1.13 | yes |
| B1b | cancellation control | yes | yes | yes | 1.01 | 1.01 | yes |
| B2 | MPO→MPS | **no** | **no** | yes | 1.00 | 1.00 | yes |
| B3 | HT arithmetic (x + αd, rounding) | yes | yes | yes | **3.20** | **2.01** | yes |

## Planner results at δ = 0.01 (certified search, best certificate)

| id | stored (plan / full) | actual error | best certificate | bound | relative bound | bound / actual |
|---|---|---|---|---|---|---|
| B1a | 194 048 / 245 760 | 3.65e-8 | slotwise | 4.14e-4 | 0.0101 | 1.13e4 |
| B1b | 243 200 / 245 760 | 3.23e-27 | slotwise | 4.50e-25 | 0.0101 | 139 |
| B2 | 81 160 / 81 160 | 5.1e-15 | theorem_r (no truncation) | 0 | 0 | — |
| B3 | 4 960 / 15 880 | 3.79e-3 | slotwise | 9.17e-3 | 0.0085 | **2.42** |

With δ = 0.1, B2 compresses to 79 256 bytes. There the slotwise bound is 0.0905 (relative 0.085) against an actual error of 1.15e-3, a ratio of 79.

## What the three certificates show

Bound / actual error on the uniform rank sweeps and planner runs:

| id | Theorem R `Λ_T·gBox` | compact amplitude `A` | slotwise `S` |
|---|---|---|---|
| B1a | ~1e7 | ~1e4 | ~1e4 |
| B1b | ~1e23 | ~650 | ~140 |
| B2 | ~1e6 | ~3.6e3 | ~80 |
| B3 | ~1e26 | ~1e9 | **~2.4** |

- **Theorem R certificate.** Sound in every run and vacuous in relative terms whenever there is any truncation. `‖R_r‖/Λ_T` is 5e-4 (B1a), 5e-25 (B1b), 2e-6 (B2) and 1e-30 (B3).
  - As predicted, the class-wide sharp scale `Λ_T` is not an instance-level scale.
  - `gBox` itself is never the bottleneck: the certified enclosures reach width ≤ 1e-9.
- **Slotwise certificate** (`PMT.KTree.err_le_sbound`, exact slot operator norms). Best or within rounding of the best in every truncated run (B3 sweep 0.75: amplitude 0 vs slotwise 1.1e-9), and the only one that makes B2 and B3 non-vacuous.
- **Vacuity mechanisms, measured separately:**
  1. **Amplitude deflation / cancellation** (B1b: `‖R_r‖ ≈ 4.5e-23`). The amplitude certificates survive because they use measured `‖R_j‖`.
  2. **Operator-norm slack** (B1b: `M = 1` against a lower estimate of `1/√2`, ratio 1.41, consistent with the Böttcher–Wenzel constant). It is small here.
  3. **Per-step amplification in chains** (B2: slot constants ‖mat(W_k)‖₂ ≈ 1.3–1.5 per site, observed on the exploratory instance). This is what blocks certified compression at δ = 0.01. It is the main open engineering target: better gauges or norm bounds for MPO site tensors, or a chain-specific bound that uses the right environment.
  4. **Gauge amplification** (B3 weighted gauge: `M_v` up to 1e4, `∏ M_v ≈ 1e30`). It destroys the Theorem R and compact certificates. The slotwise certificate with exact slot operator norms avoids it.

## Additional comparison (POST HOC, not preregistered)

For B1 (d = 32), the **dense** uncompressed algorithm stores 122 880 bytes and uses 9.8e5 counted FLOPs. The B1a certified plan uses 194 048 bytes and 6.5e6 FLOPs, so it beats the full-rank *factored* baseline but not the dense one. The factored representation does not pay off at this size, and B1 should not be cited as a memory win against dense computation.

B3's dense tensor (4⁸ doubles = 524 288 bytes) is far larger than any HT representation. The relevant preregistered baseline is HT arithmetic without rounding.

## Soundness

Every run (full rank, the four sweep levels and both planners at both δ, for each benchmark) satisfied `actual ≤ each certificate`. No violations were observed. Assumptions: float64 values treated as exact; exact orthogonal truncation for the Theorem R certificate; slot and operator norms computed in float64.

## Exploratory history (disclosed)

Before freezing, exploratory runs on other seeds led to three changes:

- B2 moved from Gaussian cores to a left-canonical, weakly entangled MPS and an `I + εH` MPO. A bug in which the identity term was missing was found and fixed.
- B3 moved from random orthogonal HT tensors, where flat basis spectra make node-wise truncation meaningless, to a weighted-gauge HSVD of function tensors.
- The slotwise certificate was added after B2/B3 were found vacuous under the amplitude-only certificates.

The confirmatory seeds (101, 102, 103) were not used before the freeze.

## Consequences

1. The formal chain (Theorem R, H3, trajectory bound and slotwise bound) yields sound certificates on real contract-then-truncate computations. On HT arithmetic the certificate is within a factor 2.4 of the true error at 3.2× compression.
2. TRL4 is not claimed. The MPO→MPS chain needs a tighter chain certificate before its criterion holds at δ = 0.01.
3. Next engineering step: an environment-aware slot constant for chains (`K_k` computed with the right environment in canonical form), evaluated under a new preregistration.
