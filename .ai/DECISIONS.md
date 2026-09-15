# Decisions

## 2026-09-14 — Formalized route for Theorem R

- **Decision:** The machine-checked lifted-angle proof is the load-bearing
  proof of Theorem R, in normalized single-space form. The v2 dilation text
  stays frozen as historical and review material.
- **Reason:** Lean 4 / Mathlib checks upper bound, witness admissibility and
  suprema end to end, with standard axioms only. The v2 argument has no
  independent review.
- **Evidence:** `research/pmt_program/lean/` (PR #7, `f219172`),
  `research/pmt_program/lifted_angle/LIFTED_ANGLE_PROOF.md`.
- **Status:** accepted. Open: specification review and the N1 and
  ambient-space reductions.

## 2026-09-14 — Paper style contract and novelty wording

- **Decision:** `research/pmt_program/paper/STYLE_CONTRACT.md` governs all
  paper text.
  - "exact" refers to the formula, "sharp" to the inequality, "attained" to
    the extremizer.
  - No affirmative novelty claim until PRIOR-ART-R meets its stop criterion.
    Interim wording is "what the present argument adds".
- **Reason:** keep claims auditable and aligned with evidence.
- **Status:** accepted.

## 2026-09-14 — PRIOR-ART-R protocol and verdict labels

- **Decision:** Novelty is assessed claim by claim (R1a–R12, R8 as an
  artifact claim), using:
  - a frozen protocol and queries;
  - Level 1/2/3 screening;
  - threat scores 0–5, harmonized with the v5 labels;
  - the deeper reading level overrides a shallower one, with disagreements
    recorded (Feshchenko 2019: reviewers gave 1 and 3; adjudication pending).
- **Evidence:** `research/pmt_program/prior_art/SEARCH_PROTOCOL.md`,
  `CLAIM_NOVELTY_MATRIX.md`, `l3_verdicts.json`.
- **Status:** accepted. Global status `NOVELTY_NOT_ESTABLISHED`.

## 2026-09-14 — Heterogeneous Theorem R: formalize H1+H2+H4, separate H3

- **Decision:**
  - Define the heterogeneous sharp constant exactly as the box maximum `gBox`.
  - Formalize the heterogeneous upper bound, witness, equality of suprema and
    placement/permutation invariance, plus recovery of the uniform case.
  - Do this in a dedicated worktree and branch (`seion-pmt-hetero`,
    `research/heterogeneous-theorem-r`), under
    `research/pmt_program/lean/PMTFormal/Heterogeneous/`.
  - The capped-equal-angle reduction (H3) lives in a separate file
    (`CappedDiagonal`), and nothing depends on it.
- **Reason:** the lifted-angle architecture already implies H1, H2 and H4, so
  H3 is only an efficient-evaluation question. A separate worktree avoids
  mixing with the concurrent session editing `research/pmt_program/heterogeneous/`.
- **Supersedes (partially):** the 2026-09-14 implementation-boundary decision
  below. The uniform envelope remains the production-safe certificate until
  the Lean build of the heterogeneous theorem passes.
- **Status:** accepted, in progress.
- **Update 2026-09-14 (appended):** the Lean build passed. Status is
  implemented and machine-checked on the branch, uncommitted, not
  human-reviewed. Modelling choices made during the formalization:
  - **Trees:** a new inductive `HPMTree` carries `e_v` per node; the class
    `A(T, η)` is given by `dshape = T` and `RootAdmFull`.
  - **Root defect:** the root defect is part of the skeleton and of full root
    closure but not of the constant. The sharp theorems assume `e_root ≥ 0`.
  - **Defect order:** defect lists are in preorder; permutation invariance
    makes the order irrelevant for the constant.
  - **Supremum form:** `gBox` is defined as `sSup` over the box, and
    `gBox_attained` shows it is a max for nonnegative defects.
  - **Scaled form:** a separate `SPMTree` with `(M_v, ρ_v)`, normalized by
    `μ ↦ M⁻¹μ` and `z ↦ ‖z‖⁻¹z` (the convention `0⁻¹ = 0` covers zero
    leaves). `M_v > 0` is part of admissibility.
  - **H3:** stored as a `Prop` definition (`CappedEqualAngle`), never as an
    axiom or `sorry`.
  - **Certificates:** the capped curve is a proven *lower* bound for `gBox`.
    Certificates must not use it until H3 is proved.

## 2026-09-14 — Heterogeneous Theorem R implementation boundary

- **Decision:** Implement the nodewise scalar box evaluator and error-budget
  prototype, but use the existing uniform Theorem R envelope as the only
  feasibility certificate until the heterogeneous upper bound is proved.
- **Reason:** The corner evaluation is numerically invalid in phase-wrap
  regimes, and floating-point global optimization cannot establish H1, H4,
  or the capped-equal-angle reduction.
- **Evidence:** `research/pmt_program/HETEROGENEOUS_THEOREM_R.md`,
  `research/pmt_program/tn_benchmark/POSTHOC_HETEROGENEOUS_ANGLE.md`,
  `research/pmt_program/heterogeneous/`.
- **Status:** accepted for research tooling; mathematical claims remain open.

## 2026-09-09 — PMT k4 chain study authority and preservation

- Scope remains independent-law finite-dimensional canonical PMT. New work
  is on `codex/pmt-k4-chain-gram`; no main edits, history rewriting, push,
  paper publication, or external-repository change.
- Register the chain/mixed formula as a proposal with a complete advisory
  proof draft, not an automatically approved theorem. Existing results and
  the general k>=4 open registry entry retain their status until independent
  review. The proof's upper bound is analytic; SDP precision is not certified.
- Preserve historical ungated M18/M19 phase code and SLSQP failures. Add
  globally admissible leaf-gated phase constructions and explicit negative
  controls under the canonical ambient-leaf convention.
- V2 uses derivative-free Powell with full spectral rescaling after V1's
  SLSQP nonconvergence. Each run is separately registered; V2 snapshots its
  source and does not overwrite V1. No optimizer deficit is landscape proof.

## D-0001 — Keep governance local to SEION Math Core

- **Date:** 2026-07-29
- **Decision:** The other repositories supplied workflow patterns only. No
  governance or integration files are written to them.
- **Reason:** SEION must remain self-contained and reproducible.
- **Evidence:** user scope clarification; `AGENTS.md`.
- **Status:** accepted

## D-0002 — Separate mathematical and software evidence

- **Date:** 2026-07-29
- **Decision:** Mathematical claims live in claims/theorem registries and proof
  files; software/reproducibility claims live in run manifests, schemas, and
  release records.
- **Reason:** A polished runner or artifact ledger cannot substitute for a
  mathematical theorem.
- **Evidence:** `governance/RESEARCH_SOFTWARE_SPLIT.yaml`.
- **Status:** accepted

## D-0003 — Preserve historical runs and deduplicate derived views

- **Date:** 2026-07-29
- **Decision:** Existing run indexes are not rewritten in place. A deterministic
  deduplicated index and audit report are generated alongside them.
- **Reason:** Repeated executions are useful operational history but are not
  independent scientific instances.
- **Evidence:** `artifacts/index/run_index.csv`; `governance/MEMORY_CONTRACT.yaml`.
- **Status:** accepted

## D-0004 — Keep v2 fail-closed until novelty and metadata gates pass

- **Date:** 2026-07-29
- **Decision:** The v2 foundations manuscript is delivered as a rigorously
  scoped draft/not-for-submission artifact, while the software companion is
  the reproducibility output. The strict research audit must remain false
  until a genuinely new theorem and verified author metadata exist.
- **Reason:** Exact invariant restriction, operadic identity inheritance, and
  the spectral gap estimate are standard consequences; a complete numerical
  matrix cannot substitute for theorem-level novelty.
- **Evidence:** `claims/theorem_registry_v2.yaml`,
  `claims/claim_evidence_matrix_v2.csv`,
  `papers/foundations_v2/RESEARCH_BLOCKED.md`,
  `artifacts/research_audit/v2_state.json`.
- **Status:** accepted

## D-0005 — Treat v3 as a certified draft, not a publication approval

- **Date:** 2026-07-29
- **Decision:** Deliver the complete v3 mathematical/software system and its
  reproducible evidence while retaining `FAIL_CLOSED_NOVELTY` until sharpness,
  novelty, global certification, extended experiments, and independent human
  review pass their explicit gates.
- **Reason:** Passing tests, bounds, compilation, and visual QA cannot establish
  theorem-level novelty or independent peer approval.
- **Evidence:** `artifacts/research_v3/release_gate_v3.json`,
  `artifacts/reviews_v3/review_summary_v3.json`.
- **Status:** accepted

## D-0006 — Materialize but do not silently execute the full extended grid

- **Date:** 2026-07-29
- **Decision:** Store deterministic resumable schedules for 460,800 optimizer
  trajectories and 8,400 performance cells, execute a four-trajectory pilot,
  and stop at the explicit resource gate.
- **Reason:** The mandate requires recoverability and honest accounting; it
  does not justify an unbounded compute expenditure or reporting pending rows
  as completed evidence.
- **Evidence:** `artifacts/research_v3/extended_progress_v3.json`,
  `scripts/tree_constants_v3_extended.py`.
- **Status:** accepted

## D-0007 — Start projected-graphs V5 after the finite core freeze

- **Date:** 2026-08-08
- **Decision:** Freeze the finite projected-graphs core at scientific commit
  `1f4984ec8e741049789e0035c7a3ba84c86d3f29` and place theorem-level
  extremal, proof-consolidation, novelty, and formalization work under
  `research/projected_trees_v5` and `src/seion_core/research_v5`.
- **Reason:** The finite computational core is complete; further work must
  distinguish proved restricted-class results from open global sharpness and
  must not silently expand `research_v4` or alter Gate 13.5/Gate 14/KGR.
- **Evidence:** `research/projected_trees_v5/BASELINE_FREEZE.json`,
  `claims/theorem_registry_v5.yaml`, and the V5 truth ledger.
- **Status:** accepted

## D-0008 — Freeze the certified KGE confirmatory protocol before new campaigns

- **Date:** 2026-08-10
- **Decision:** Adopt `experiments/configs/CERTIFIED_KGE_CONFIRMATORY_PROTOCOL_V1.yaml`
  as the declared protocol for the TTN score-space confirmation campaign.
  New runs must preserve train-only calibration, valid-only selection, a
  single final test confirmation, same-backend hardware baselines, seed-level
  statistics, and the G0--G8 advancement gates.
- **Reason:** The exploratory audits demonstrated mathematical opportunity
  but did not establish certificate capture or robust hardware speedup. A
  frozen protocol prevents tolerance/rank cherry-picking and prevents mixing
  dataset, topology, training, and executor changes in one causal comparison.
- **Evidence:** `experiments/configs/CERTIFIED_KGE_CONFIRMATORY_PROTOCOL_V1.yaml`,
  `.ai/CURRENT_STATE.md`, and the score-space benchmark artifacts under
  `runs/TTN_FB15K237_TTN_V2_D128_E10_2026-08-09/`.
- **Status:** accepted_with_B-0012_execution_hold

## D-0011 — Seal TEST and audit provenance before all-entity confirmation

- **Date:** 2026-08-10
- **Decision:** Require `SRATM_NO_LEAKAGE_AUDIT_V1` to pass observed runtime
  access, reciprocal isolation, calibration provenance, and artifact ancestry
  before any future official all-entity/test confirmation. Keep TEST sealed.
- **Reason:** Absence of a direct `test.txt` read is insufficient when
  vocabulary, filters, mining, whitening, projectors, allocator choices,
  checkpoint selection, and hardware policy can leak indirectly.
- **Evidence:** `runs/SRATM_NO_LEAKAGE_AUDIT_V1D_20260810/`,
  `seion_kgr/no_leakage_audit.py`, and
  `tests/kgr/test_no_leakage_audit.py`.
- **Status:** observed_pass_with_declared_limitations

## D-0009 — Separate accuracy-first SOTA discovery from certification

- **Date:** 2026-08-10
- **Decision:** Create a separate exploratory discovery track for maximizing
  validation MRR/Hits with larger models, dynamic hard negatives, EMA queues,
  structural context, and optional teacher/student distillation. The certified
  confirmatory protocol remains unchanged and cannot be selected or rewritten
  from discovery test results.
- **Reason:** A model optimized for SOTA accuracy should not be constrained by
  compression or certification before its predictive ceiling is measured.
  Separation preserves causal interpretation and prevents test leakage.
- **Evidence:** `experiments/configs/KGE_SOTA_DISCOVERY_V1.yaml` and
  `seion_kgr/sota_discovery.py`.
- **Status:** accepted_with_B-0012_execution_hold

## D-0010 — Formalize teacher/student programs and fail closed on leakage

- **Date:** 2026-08-10
- **Decision:** Treat quality maximization and predictor compression as two
  sequential programs. Program A may use larger structural models, hard
  negatives, EMA teachers, retriever unions and validation-fitted ensembles.
  Program B starts only after the teacher is frozen and may not modify it.
  Test identifiers are rejected from discovery/calibration code paths.
- **Reason:** Accuracy, compression, certification, and deployment latency
  are different optimization problems. A single mutable pipeline would make
  leakage and causal attribution difficult to audit.
- **Evidence:** `experiments/configs/KGE_SOTA_DISCOVERY_V1.yaml`,
  `seion_kgr/sota/`, and `tests/kgr/test_sota_components.py`.
- **Status:** accepted_with_B-0012_execution_hold

## D-0012 — Split G6 into certificate, predictive, and historical gates

- **Date:** 2026-08-10
- **Decision:** Report G6A (all-entity certificate validity), G6B
  (predictive preservation under the same sealed protocol), and G6C
  (historical metric reconciliation) separately.
- **Reason:** The all-entity run has zero candidate-bound violations, while
  `uniform_medium` loses MRR against the sealed full-rank control and the
  historical `0.6116475` protocol cannot yet be reconstructed without TEST.
- **Status:** declared_observed; historical cause remains OPEN.

## D-0013 — Treat historical SRATM VALID MRR as unreconciled

- **Date:** 2026-08-10
- **Decision:** Keep `0.6116475462913513` as an observed historical artifact,
  but do not use it for model selection, compression selection, or claims
  until its loader, filter, candidate-universe, tie-policy, command, and
  runtime provenance are reconstructed. Keep TEST sealed.
- **Reason:** The audited checkpoint identity is confirmed and scorer/gold/
  reciprocal differential checks pass, but the historical trainer source
  requires a TEST path and its normal loader includes TRAIN+VALID+TEST in
  vocabulary and filters. The exact historical command and access trace are
  absent, so actual TEST-derived influence is unknown rather than proven.
- **Evidence:**
  `runs/HISTORICAL_EVALUATOR_PROVENANCE_V1_20260810/result/`,
  `runs/HISTORICAL_VALIDATION_RECONCILIATION_V1_20260810_FINAL2/result/`,
  `seion_kgr/data.py`, `seion_kgr/train_spectral_mixture.py`.
- **Status:** accepted_open_cause.

## D-0014 — Keep the canonical PMT facade fail-closed at `k>=4`

- **Date:** 2026-09-09
- **Decision:** Implement the typed finite-dimensional PMT evaluator,
  projected-root bounds, `W_3(eta)` witnesses, and norm/closure brackets in a
  separate `seion_core.pmt` namespace. Expose fixed-eta `k>=4` only as an
  explicit open-problem record.
- **Reason:** The implementation must turn existing definitions and proofs
  into reproducible contracts without allowing a finite numerical optimizer to
  become an exact-constant theorem.
- **Evidence:** `src/seion_core/pmt/`, `docs/pmt/README.md`,
  `research/math_closure/k4_exploration/PMT_K4_FRONTIER.md`,
  `claims/claims_registry.yaml`, and `claims/theorem_registry.yaml`.
- **Status:** accepted_with_external_review_pending.

## D-0015 — Freeze PMT-A and narrow the program to sharp PMT constants

- **Date:** 2026-09-13
- **Decision:** All new sharp-constant statements cite the single class
  `research/pmt_program/ADMISSIBLE_CLASS_PMT_A.md` (real field; complex
  variant tracked as `PMT-A[C]`). The research program is narrowed to the
  question "determine `C_T^P(eta)` and its dependence on depth, leakage and
  topology", organized as Papers I (k<=3, universal bounds, asymptotic
  sharpness), II (rebracketing, certificates, DAGs) and III (higher depth).
  Cosmology, KGE, VECTRA, T4, proteins and mass-gap material are out of scope
  for these papers.
- **Reason:** Class declarations were scattered across three files with a
  real/complex ambiguity (M16 field caveat) and a leaf-closure convention
  conflict (M18/M19). One frozen reference removes both.
- **Evidence:** `research/pmt_program/README.md`.
- **Status:** accepted_with_external_review_pending.

## D-0016 — Replace the conjecture `a_k=(k-2)(2k-3)/4`

- **Date:** 2026-09-13
- **Decision:** Record `a_k=(k-1)(k-2)(k+6)/24` (chains; all trees under
  Conjecture R) and mark `(k-2)(2k-3)/4` refuted at `k=5` (`11/2 != 21/4`).
- **Reason:** The two agree only at `k=3,4`. The general-k chain proof draft
  (`research/pmt_program/CHAIN_ALL_K.md`), the exact Gram SDP at `k=5,6`, and
  exact rational certificates at `k=5` all give `11/2`.
- **Status:** accepted_with_external_review_pending (the refutation of the
  numerical value at k=5 is independent of the proof draft: SDP + certificate).
