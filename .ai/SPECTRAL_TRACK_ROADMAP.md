# Spectral A-N legacy-audit roadmap

Tracks the campaign to ingest `spectral/` (legacy v17 audit script + run
history) and rebuild it as a fail-closed typed-gate certification suite
(v18), per the 2026-07-30 mission brief. This track is scope class
`SPECTRAL_LEGACY_TRACK` in `claims/scope_registry_v4.yaml` and is
evidentially separate from `CANONICAL_FINITE_CORE` (the v4 finite-algebra
core) — no claim may cross between them without a proved connecting
theorem.

## Deferred (explicit user decision, 2026-07-30)

- [ ] **Track T** — projected n-ary tree mathematics (k / k-1 bounds,
  tangent-normal nodewise calculus, mixed-mask and path-sum certificates,
  fixed-eta extremal constants, signed forests, cancellation-aware
  associator/FI/GJI/Jacobiator bounds). This is a distinct research thread
  from the spectral A-N audit below and was explicitly deferred to a future
  session rather than folded into this roadmap's scope.

## Phase 0 — Legacy preservation, hashing, lineage, dedup

- [x] Hash and immutably copy the two named legacy files into
  `spectral/legacy/v17/` (originals in `spectral/` untouched).
- [x] Hash all 18 on-disk run directories under `spectral/runs/`.
- [x] Parse all 9 runs logged in `REPRO_SUMMARIES_A_TO_M_VALIDATED.txt` and
  cross-reference with on-disk `summary.json` files (19 unique runs total:
  8 in both the txt log and on disk, 1 txt-log-only, 10 directory-only).
- [x] Reconstruct resume-chain lineage
  (`spectral/legacy/v17/legacy_run_lineage.json`): the 9 txt-logged runs
  are one continuous non-strict resume chain rooted at a single seed=3
  bootstrap, not 9 independent trials.
- [x] Dedup by script hash / config fingerprint / seed / dtype / checkpoint
  hash / audit-state hash (`legacy_run_dedup_report.md`) — found 2 distinct
  reported script hashes across the historical runs (the current repo copy
  matches 8 of 9 txt-logged runs but not the earliest bootstrap run).
- [x] Reclassify every run against the typed-gate vocabulary instead of the
  legacy `master_score` (`legacy_claim_reclassification.yaml`) — every
  `eval_mode=screening` run (all 19) capped at `WARN`/`EMPIRICAL_SCREENING_PASS`,
  never a certification-tier state.
- [x] Add additive `SPECTRAL_LEGACY_TRACK` scope class; confirmed
  `governance audit --json` still passes green.

## Phase 1 — Typed-gate taxonomy + v18 skeleton
- [x] `spectral/certification_v18/GATE_TAXONOMY.md` — 10 typed states, 8
  critical gates, fail-closed minimum-combination rule (`gates.py`, 10
  tests) — no code path can emit full certification.
- [x] `config.py` — certification-mode contract enforced in code (dtype,
  TF32, determinism, strict resume, held-out seeds), 6 tests.
- [x] `model.py` — fresh reimplementation of the CP law / projector /
  reduced-curvature geometry (not imported from legacy, to avoid its
  import-time global TF32 side effect), 4 tests including a numerically
  confirmed rank-<=2r bound on both `raw_comm` and `C_theta`.

## Phase 2 — Per-block redesign A-N with controls
- [x] **Block B** (`block_b_commutator.py`, `BLOCK_B_FINDINGS.md`, 9
  tests): null control (untrained C_theta indistinguishable from random
  Phi), capacity ceiling (closed-form optimal-Phi solve shows the formula
  reaches ~0 residual when trained on that objective ALONE), and a direct
  cross-check against every on-disk historical checkpoint showing
  `coherence_ratio <= 0` in all 15 — i.e. C_theta performs at or worse
  than the trivial zero predictor in the actual multi-objective-trained
  regime. Verdict: `FAIL` for practical explanatory content as actually
  deployed; `STRUCTURAL_IDENTITY_PASS` only for the exact algebraic
  identity. Most likely explanation: multi-objective loss competition
  starves this term, not a malformed formula (follow-up: retrain with the
  full historical multi-loss objective and ablate `lambda_cdc`).
- [x] **Block J methodology** (`gauge_utils.py`, `BLOCK_J_FINDINGS.md`, 9
  tests): raw / Procrustes-aligned / permutation-aligned / amplitude-ratio
  reported separately, replacing the legacy single-heuristic comparison.
  Not yet applied to a real independently-trained lo/hi pair (needs block-E
  interscale training infra — not built this pass).
- [x] **Block M methodology** (`block_m_persistent_factorization.py`,
  `BLOCK_M_FINDINGS.md`, 6 tests): >=3-resolution pairwise comparison,
  enforced in code. Caught and fixed a real bug via its own required
  negative control: free-unitary Procrustes on subspace bases is
  mathematically vacuous (transitive group action) — replaced with
  principal angles per mission section 2E. Not yet applied to real
  independently-trained resolutions.
- [ ] Remaining blocks: A, C-I, K, L, N.

## Phase 3 — Certification modes
- [ ] Code-enforced screening/certification split (not just convention).

## Phase 4 — Hardware execution + resumable job queue
- [ ] Hardware inventory, batched GPU execution, resumable job queue.

## Phase 5 — Sweep design and adaptive execution
- [ ] Real sweeps within session budget; explicit partial-coverage logging.

## Phase 6 — Negative controls / anti-gaming tests
- [ ] Per-block negative controls; suite invalid until they reliably fail.

## Phase 7 — Visual atlas (A-N figures)
- [ ] Figures generated from real artifacts only.

## Phase 8 — Release products (A-N scope)
- [ ] Certification companion, atlas doc, reproducibility package, truth
  report section.

## Phase 9 — Fail-closed final gate + final report
- [ ] Expect `PASS_A_TO_N_PARTIAL_CERTIFICATION` or a `FAIL_CLOSED_*` state
  — full certification requires human review this process cannot self-issue.
