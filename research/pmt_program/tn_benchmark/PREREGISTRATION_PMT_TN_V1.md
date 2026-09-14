# PMT-TN Benchmark V1 — preregistration

Frozen before any run of F1–F5 or F7. The commit that adds this file is the preregistration
reference; changes after that commit are recorded in a dated amendment section, never edited in place.
Machine-readable grid: `experiments/configs/PMT_TN_BENCHMARK_V1.json`.

Theory under test: Theorem R, canonical source `research/pmt_program/review/theorem_R_v2/THEOREM_R_v2.md`
(tag `theorem-R-v2-review`), status `ADVISORY_PROOF_DRAFT`. Results of this benchmark are
`NUMERICAL_OBSERVATION`.

---

## 1. Certificate

With uniform law-norm budget `M`, relative leakage `η = ρ/M`, `k` internal nodes and leaf product
`L = ∏‖z_ℓ‖`:

```
B_R     = η · C_k(η) · M^k · L = G_k(η) · M^k · L,   G_k(η) = max_{0≤θ≤arcsin η} |1 − (cos θ e^{iθ})^{k−1}|
B_naive = (k − 1) · η · M^k · L
```

**Correction to the design draft.** The draft used `M^{k−1}`. The correct factor is `M^k`, because
`C = E/(ρ M^{k−1} L)` and `ρ = ηM`. Deflation is `D = ‖F_r‖ / (M^k L)`.

### Uniform `M`

`M̂ := max_v M̂_v`, where `M̂_v` is a certified upper bound on node `v`'s multilinear operator norm.
Provenance is one of:

* `analytic` — proved in the family description;
* `flattening` — the minimum over matrix flattenings of the spectral norm, which is a valid upper bound.

Heterogeneous per-node `M_v` products are **not** used: Theorem R assumes a uniform budget. They
belong to a future extension.

### Leakage

Trajectory leakage:

```
η̂_v = ‖Q_v μ_v(R_children)‖ / (M̂ · ∏ ‖R_c‖ · ∏ ‖z_ℓ‖)      (children R and leaf data of node v)
η̂   = max over non-root internal nodes.
```

Theorem R v2 claims its upper bound in the trajectory-closure class (§1.2), so `B_R` with `η̂` is a
certificate **conditional on the draft being correct**. For fixed-projector families (F2–F4) the
full-subspace upper bound `η̂^full` is also reported:

```
η̂^full_v = ‖Q_v W_v (P_children ⊗ …)‖_flattening / M̂
```

### Root

`P_r = I` in every family, so `E^P = ‖F_r − R_r‖` is the ordinary truncated-contraction error.

## 2. Projector semantics

1. **Adaptive truncation (F1).** The node's projector is chosen by SVD of the reduced intermediate
   `μ_v(R_children)` during the run. The map `X ↦ U_r(X)U_r(X)ᵀX` is **not** a fixed linear
   projector. Each run is therefore certified **conditionally on the frozen projector it produced**:
   the run is one PMT realization with that `P_v`.
2. **Fixed projectors (F2–F4).** Projectors are computed before test evaluation and frozen:
   * F2: PCA on a training batch;
   * F3, F4: TT-SVD / HT-SVD of the exact object.

   The same `P_v` is used for every test input, and `η̂^full` applies.
3. **SVD is not PMT.** TT-SVD and HT-SVD are non-multilinear algorithms; they only **select** the
   projectors. The PMT instance certified is the **subsequent multilinear contraction** with those
   frozen projectors.

Every projector is validated by the orthogonality check (idempotence and self-adjointness on random
inputs, tolerance `1e-9`). A failure marks the run `INVALID_PROJECTOR` and excludes it from H1.

## 3. Families

| id | description | translation | projectors | `M̂` |
|---|---|---|---|---|
| F1 | Product of `n` matrices `A_i ∈ ℝ^{χ×χ}` (unit Frobenius) under a bracketing tree; each intermediate `Z` is truncated two-sided to rank `r`: `P(Z) = U_rU_rᵀ Z V_rV_rᵀ` | L (matrices are leaves, law = matrix product) | adaptive | `analytic` = 1 (`‖XY‖_F ≤ ‖X‖_F‖Y‖_F`, attained) |
| F2 | Binary TTN on `n` unit leaf vectors in `ℝ^4`; node law `W_v(a, b, ·)` | W | fixed, PCA of reduced node outputs on 512 training inputs, rank `r` | `flattening` (canonical `W`: exactly 1) |
| F3 | TFIM ground state (open chain, `J = 1`, field `h`), exact diagonalisation; exact left-canonical MPS by TT-SVD; amplitude evaluation `ψ(s)` and product-state overlaps; bond projectors onto the top-`r` Schmidt vectors | W, chain | fixed (TT-SVD) | `flattening` (= 1 for left-canonical cores) |
| F4 | Exact Hierarchical Tucker (balanced binary, 8 variables, 4 grid points each, unit Frobenius) of smooth functions; point evaluation with leaf data `U_ℓ[i_ℓ]`; node projectors onto top-`r` HT singular vectors | W | fixed (HT-SVD) | `flattening` (coisometric transfer tensors; root normalised) |
| F5 | Unstructured data variants of F1 (Gaussian, scaled orthogonal) and F2 (Gaussian `W` normalised by flattening norm) | L / W | as parent | as parent |
| F6 | Positive control: universal sharp witness (Theorem 8.1) on random trees, equal angles `≤ θ_c(k)` and unequal angles | — | `Re` | `analytic` = 1 |
| F7 | Adversarial: maximise `E_obs / B_R` over canonical (coisometric) node tensors, orthogonal rank-`r` projectors and unit leaves; PyTorch **CPU float64** | W | fixed per candidate | `flattening` = 1 (exact for coisometries) |
| F8 | Constructed negative controls with analytic ratio: F8a `M` underestimated (ratio `λ`), F8b oblique projector with orthogonal leakage measurement (`√(1+c²)`), F8c self-trace law with `M̂ = 1` claimed (`√d`) | — | — | deliberately invalid |

**Hardware.** CPU only. GPU use is excluded by the active blocker B-0012.

## 4. Metrics per run

* **Structure:** `family, variant, topology, k, n, χ, r, seed`.
* **Budgets:** `M̂, M_provenance, η̂, η̂^full` (F2–F4), per-node `η̂_v`.
* **Norms and errors:** `E_obs, ‖F_r‖, L`.
* **Certificates:** `B_naive, B_R`.
* **Ratios:** `ratio = E_obs/B_R`, `gain = B_R/B_naive`, deflation `D`, `B_R/‖F_r‖`.
* **Validators:** projector orthogonality, and a sampled lower bound on the law norm (F1, F2, F6, F8).
* **Label:** `WITHIN_CERTIFICATE`, `REPLAY_TRIGGERED`, `EXPECTED_VIOLATION_NEGATIVE_CONTROL`,
  `EXPECTED_VIOLATION_MISSING`, `INVALID_PROJECTOR`.
* **Exploratory** (not a certificate): the per-node angle expression `|1 − ∏_v cos θ_v e^{iθ_v}|` with
  `sin θ_v = η̂_v`.

## 5. Hypotheses and criteria

| # | hypothesis | criterion |
|---|---|---|
| **H1** soundness | `E_obs ≤ B_R` for all valid runs of F1–F7 | a float64 excess `ratio > 1 + 1e-10` is a **replay trigger** only (protocol §6); a run is labelled `THEOREM_R_COUNTEREXAMPLE_CANDIDATE` only if the excess survives replay |
| **H2** positive control | F6 equal-angle runs: `ratio = 1 ± 1e-9`; unequal angles: `ratio ≤ 1 + 1e-10` | all runs |
| **H3** negative controls | every F8 run is labelled `EXPECTED_VIOLATION_NEGATIVE_CONTROL` with the analytic ratio (rel. `1e-9`), **and** its validator flags the defect (F8a, F8c: sampled norm lower bound `> M̂`; F8b: non-orthogonal projector) | all runs; otherwise the pipeline is declared unreliable and no other family is interpreted |
| **H4** contraction order (F1) | at fixed data and `k`, differences in `B_R` across bracketings are fully explained by `η̂`; `E_obs` and `η̂` are reported per bracketing | descriptive; report the order that minimises `η̂` at equal cost |
| **H5** sharpness beyond the witness (F7) | the best `ratio` found per topology | reported values; `≥ 0.9` counts as "near-sharp non-witness network" only if the optimum is not supported on 2-dimensional value spans |
| **H6** regime (F7) | for fixed `k`, the adversarial absolute error flattens for `η > η_c(k)` | curve reported |
| **H7** usefulness *(may fail)* | in F2–F4, `B_R/‖F_r‖ < 1` for at least 50% of runs at the largest preregistered rank | fraction reported whatever the outcome |
| **H8** gain | distribution of `B_R/B_naive` in the `(k, η̂)` plane | descriptive |

## 6. Replay protocol (H1)

A run with `ratio > 1 + 1e-10` that is not an F8 control is replayed in this order:

1. recompute `M̂` (flattening norms with SVD in float64, then mpmath 50 digits), `η̂` and all projector
   checks;
2. recompute `E_obs` and `G_k` in mpmath (50 digits) from the frozen instance data;
3. freeze the complete instance (all tensors, projectors, leaves, tree) as JSON with hashes.

Only if `ratio > 1` persists after steps 1–2 is it labelled `THEOREM_R_COUNTEREXAMPLE_CANDIDATE`, and it
is then escalated as evidence against Lemma 3, or against the translation, before any other
interpretation.

## 7. Outputs

Each campaign writes `artifacts/pmt_tn_benchmark/<date>-v1/<family>/`:

* `runs.jsonl`
* `run_manifest.json` (command, commit, environment)
* `final_metrics.json`
* `artifact_hashes.json`
* replay instances, if any

Runs are never overwritten.

**Analysis** (`analyze.py`):

1. `(k, η̂)` plane coloured by `ratio`;
2. box plots per bracketing (F1);
3. gain curve against `kη̂`;
4. deflation histograms per family and translation;
5. cost against certificate Pareto front (F1);
6. H1 table (runs, triggers, candidates, minimum slack `1 − ratio`).

## 8. Order of execution

F6 → F8 (done as tests before freezing) → F1 + F5 → F2 → F3 + F4 → F7 → analysis.

---

## Amendment 1 (2026-09-13, before any analysed run)

* **Seeding.** Instance seeds in F1/F2 were derived with Python `hash()` of tuples containing strings,
  which is salted per process, so instances were not reproducible. Replaced by `stable_seed()` (CRC32
  of the parameter tuple). Random bracketings in F1 are now a deterministic function of
  `(n, seed, kind, index)`, so the same tree is used across ranks and data (needed for H4). The first
  full F1 launch and the smoke runs are kept under
  `artifacts/pmt_tn_benchmark/2026-09-13-v1/*-nondeterministic-seeds/` and excluded from analysis.
  No hypothesis, criterion or grid was changed.
* **Full-subspace certificate.** For fixed-projector families each record also carries
  `B_R_full = G_k(η̂^full) · M̂^k · L`, reported next to the trajectory certificate.

## Amendment 2 (2026-09-13, before any full F7 run)

Written after F1, F3, F4 (and F6, F8) full campaigns and a 200-step F7 smoke run whose output was kept outside
the artifact tree. No criterion of H1–H4, H7, H8 is changed.

* **Autodiff backend.** PyTorch 2.7.1, CPU only (`CUDA_VISIBLE_DEVICES=""` forced in the module), float64.
* **F7 network model.** `k` internal nodes, all value spaces `ℝ^χ`, arbitrary real multilinear node laws,
  unit leaves, fixed orthogonal rank-`r` projectors (`r = 1..χ−1`), root `P = I`. Node arity is 2 for
  chain, balanced and random topologies; the star has a root of arity `k − 1` (no leaves) and `k − 1`
  leaf-only children of arity 2.
* **Two variants.**
  * `coiso` — the preregistered F7: orthonormal-row flattening, `M̂ = 1` rigorous.
  * `opnorm` — added. Each law is normalised by a block-power-iteration estimate of its operator norm, so
    rotation-type laws (the `ℝ² ≅ ℂ` witness has flattening norm `√2` but operator norm 1) are
    representable. Without it, H5 would measure the flattening slack rather than sharpness.
* **Objective.** Maximise `log E − log G_k(η_smooth)` with `M = 1`, where `η_smooth = logsumexp(200 η_v)/200`
  and `G_k` is a 1025-point grid maximum. Adam (lr 0.03, cosine to 0.002), 1500 steps, 16 restarts batched.
  Operator-norm maximisers are warm-started, with global re-initialisation every 100 steps.
* **Final evaluation.** Every restart is one PMT instance evaluated by the standard pipeline (`run_instance`)
  with a **rigorous** `M̂ = max_v M̂^up_v`:
  * `M̂^up_v = min(flattening norm, net bound)`;
  * the net bound (arity 2 only) is `max_{y∈N} σ_max(W_v(y,·)) / (1 − δ)` over a radially projected
    cube-surface net with covering radius `δ = h√(χ−1)/2`, `h = 0.0005` (`χ = 2`) or `0.004` (`χ = 3`);
  * it is computed for every restart when `χ = 2`, and for the best restart of each configuration when `χ = 3`.

  H1 uses this certificate and the §6 replay; an mpmath replay hook is attached to every F7 instance.
  Descriptive only: `ratio_est` with `M̂^low` (128-restart power iteration, a lower bound), and
  `M_gap_rel = (M̂^up − M̂^low)/M̂^low`.
* **Frozen instances.** The best restart per configuration (by `ratio_est`; F7R: by `E_obs`) and every
  replay-triggered restart are written to `instances/` with all tensors, projector bases, leaves and topology.
* **H5 operationalised.** `d_span` is the maximum over nodes of the numerical rank (relative tolerance
  `1e-3`) of `{F_v, μ_v(R_children), R_v}`. A configuration counts as a **near-sharp non-witness network**
  only if its best restart has:
  * **rigorous** `ratio ≥ 0.9`;
  * `χ = 3` and `d_span = 3`;
  * `M_gap_rel ≤ 1e-2`.

  Configurations with `ratio_est ≥ 0.9` but rigorous `ratio < 0.9` (e.g. star roots of arity ≥ 3, which only
  have the flattening bound) are reported as "estimate only".
* **H6 operationalised (family id `F7R`).** Topologies chain and balanced; `k ∈ {3, 5, 7}`; `χ = 2`, `r = 1`;
  `opnorm` variant; `η_t ∈ {0.1, …, 1.0}`. Maximise `E − 10³·relu(η_smooth − η_t)²`.
  * Report the best `E_obs`, its `η̂`, `G_k(η_t)` and `G_k(η̂)`.
  * The flattening claim is supported if `max E_obs` is non-decreasing in `η_t` and constant within 2% for
    `η_t ≥ η_c(k)`.
* **Runner.** The git commit in `run_manifest.json` is captured at launch (before: at the end of the run).
  The F2 full campaign was launched at `3424abc`, before this change; its manifest records the HEAD at the
  time it finished.
