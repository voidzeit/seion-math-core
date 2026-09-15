# Tasks

## Active

- [x] Formalize Theorem R (normalized, single ambient space) in Lean 4 /
  Mathlib: upper bound, witness admissibility, equality of suprema.
  Merged in PR #7 (`f219172`).
- [x] Attainment of the max over θ (`theorem_R_max_attained`, `gBox_attained`)
  and the N1 scaling reduction for nodewise `M_v > 0`
  (`heterogeneous_scaled_upper`/`_sSup`). Both are on branch
  `research/heterogeneous-theorem-r`, uncommitted, 2026-09-14.
- [x] `M_v = 0` degenerate lemma (`ScaledZero.lean`,
  `heterogeneous_scaled_upper_nonneg`), 2026-09-14.
- [x] Per-node spaces → common ambient space (`CommonSpace.lean`,
  `heterogeneous_multispace_upper`/`_sSup`), 2026-09-14.
- [x] Agent spec audit paper ↔ Lean (`lean/SPEC_AUDIT.md`), 2026-09-14.
- [ ] Human review of `SPEC_AUDIT.md` and freeze of the PMT-A^het class
  definition (author decision).
- [x] PRIOR-ART-R-CY follow-up, completed 2026-09-14 (`followup_cy/CY_FOLLOWUP_REPORT.md`).
- [ ] Read Yang–Chen–Qiu 2026 (arXiv, phase-capped products) and
  Chaffey–Forni–Sepulchre 2023 Thm 5 in full.
- [ ] Update the R7 attribution: the uncapped equal-angle product of D(½,½)
  disks is rigorous in Chaffey–Forni–Sepulchre 2023.
- [ ] `python cy_round.py retry` once arXiv and Semantic Scholar limits clear.
- [ ] Scholar "cited by" checks for HRY20, RHY22, CY15, Chaffey 2023 and Yang 2026.
- [x] Formalize heterogeneous Theorem R in `PMTFormal/Heterogeneous/`
  (branch `research/heterogeneous-theorem-r`, worktree `seion-pmt-hetero`,
  uncommitted): `gBox`, `heterogeneous_upper`, `heterogeneous_witness`,
  `heterogeneous_lower`, `heterogeneous_sSup`, `gBox_perm`,
  `heterogeneous_placement_independent`, `uniform_gBox_eq`. H3 is kept
  separate in `CappedDiagonal.lean` as a `Prop`. The build is 8723 jobs with no
  sorry, and 39 `#print axioms` checks show only the standard axioms.
- [ ] Prove or refute H3 (`CappedEqualAngle`) for unequal defects. The easy
  half and the equal-defect case are proved.
- [ ] Reconcile `claims/conjecture_registry.yaml` (H1/H4/placement registered
  as conjectures by the other session) with the Lean proof after the user
  reviews; do not edit it silently.
- [x] Freeze the paper style contract (`research/pmt_program/paper/STYLE_CONTRACT.md`).
- [x] PRIOR-ART-R first pass: protocol, harvest, snowball, Level 1/2/3
  screening, matrix, claim matrix, bibliography.
- [ ] PRIOR-ART-R manual steps:
  - MathSciNet and Scholar queries (`MANUAL_QUERIES.md`);
  - download the Zniyed–Boyer 2026 PDF (HAL);
  - adjudicate Feshchenko 2019;
  - second snowball round with anchors for families C, F, G, L, N;
  - targeted heterogeneous mini-round (nonuniform tolerances, nodewise
    budgets, box-constrained disk products).
- [x] Fix the wrong Deutsch–Hundal DOI in `papers/paper_a/references.bib`
  (`10.1006/jmaa.1997.5216` → `10.1006/jmaa.1997.5202`), done 2026-09-14 in
  worktree `seion-pmt-tn`.
- [x] Heterogeneous prior-art mini-round PRIOR-ART-R-HET (families O1–O6,
  preregistered `FREEZE_HET.json`), completed 2026-09-14.
  - **Scope:** 30 queries, pool of 1178, 8 Level-3 comparison files, no threat 4–5.
  - **Result file:** `prior_art/CLAIM_NOVELTY_MATRIX_HET.md`.
- [ ] PRIOR-ART-R-HET manual steps:
  - Zniyed–Boyer 2026 HAL PDF (bot check);
  - MathSciNet and Scholar queries (§6 of the HET matrix);
  - `python het_round.py retry` once arXiv, Semantic Scholar and zbMATH recover;
  - **priority:** is the Combettes–Yamada 2015 (Prop. 2.5) heterogeneous
    composition constant known to be tight for m ≥ 3? If yes, re-assess H4.
- [ ] Review the Lean specification against `ADMISSIBLE_CLASS_PMT_A.md`
  (human reviewer).

- [x] Implement the heterogeneous Theorem R research scaffold: nodewise
  scalar box evaluator, conservative uniform fallback certificate, and small-
  instance discrete error-budget allocator; keep H1/H4 and capped-equal-angle
  reduction explicitly open.
- [ ] Prove or refute the heterogeneous box upper bound and capped-equal-angle
  reduction before using nodewise bounds for production feasibility.
  - Update 2026-09-14: the box upper bound (H1) and sharpness (H4) are
    machine-checked on branch `research/heterogeneous-theorem-r`
    (normalized single-space form plus the scaled `M_v > 0` form).
  - The capped-equal-angle reduction (H3) remains open. The capped curve is
    proved to be a **lower** bound for `gBox` (`sSup_capped_le_gBox`), so it
    is not a safe certificate until H3 is proved. Certified use needs an
    upper enclosure of `gBox`, or the uniform fallback (U).

- [x] Freeze the confirmatory certified-KGE protocol V1 with train-only
  calibration, valid-only selection, final-test lock, G0--G8 gates, seed-level
  statistics, same-backend hardware rules, and the artifact contract.
- [ ] Execute the confirmatory campaign only after B-0012 Windows dump/driver
  safety review clears staged GPU work.
- [x] Run the first bounded D128 training canary at 4 GB with resumable
  checkpoints; retain long-run escalation as gated.
- [x] Complete the sustained 8 GB D128 canary with finite loss, checkpoints,
  and post-run GPU-memory verification.

- [x] Implement candidate whitening, realizable relation projectors,
  water-filling, finite prefix-DP allocation, and top-k ranking certificates.
- [x] Execute a bounded post-crash CUDA canary with a 4 GB cap and verify
  memory release after exit.
- [ ] Resume larger GPU work only after debugger/driver review and another
  bounded canary with checkpointed execution.

- [x] Add an exact dynamic-program optimizer for the declared fitted pathwise
  majorant and run a separate 240-record exploratory comparison; retain the
  need for validated global operator-norm factors before any certificate or
  allocator-superiority claim.
- [x] Add a finite-batch sup-norm certificate using Frobenius operator-norm
  enclosures and probe its small-case exhaustive allocator on 360 records;
  held-out certification and scalable allocation remain open.
- [x] Add a separable bounded-domain certificate and scalable dynamic-program
  allocator; verify it on 240 normalized-leaf held-out records with zero
  certificate violations. General domain selection and sharper operator norms
  remain open.

- [x] Connect the exact invariant-subspace reduction theorem draft to the
  v2 theorem/claim registries and reference/accelerated implementations.
- [x] Prove and test the tree-level approximate-closure recurrence for the
  declared projected-evaluation convention.
- [x] Execute five-seed projector, CP, spectral-gap, closure, and CPU/GPU
  parity experiments with registered summaries and tightness ratios.
- [x] Replace the v2 paper figures with registered multi-seed data,
  uncertainty, vector output, and centralized styling.
- [ ] Establish a genuinely new theorem-level contribution beyond the
  standard restriction and perturbation consequences, or keep the work as a
  technical/preprint draft.
- [ ] Obtain verified author email and ORCID metadata.
- [ ] Obtain independent human mathematical and numerical review before any
  submission claim.
- [x] Add a corrected growing-tree convergence theorem under explicit
  downstream-gain weighted summability; retain unrestricted growth as open.

## Operational

- [ ] Investigate the two recent Windows bugchecks before resuming GPU work;
  inspect the saved dump metadata/driver path and keep future jobs below a
  conservative VRAM ceiling with short checkpoints.

- [x] Run `seion-core governance audit --strict`; it correctly fails closed
  while scientific warnings remain.
- [x] Review and generate the deduplicated run index before using historical
  aggregates.
- [x] Update the KGR leakage negative-control fixture for the current
  context-aware evaluator signature; both declared negative controls pass.
- [ ] Fill author contact and ORCID metadata only from an explicit source.

## Completed in this bootstrap

- [x] Establish local governance, memory, lifecycle, authority, and research/
  software split contracts.
- [x] Draft and compile independent mathematical and reproducibility
  manuscripts with vector-capable PDF sources and render checks.
- [x] Expand the prior-art matrix and bibliography with conservative primary
  and official sources.
- [x] Pass the full Python test suite: 39 tests.
- [x] Generate and audit separate v2 foundations/software PDFs, nine vector
  figure pairs, claim/evidence matrices, and adversarial review records.

## V3 nodewise tree constants

- [x] Freeze the pre-v3 state and create the dedicated
  `research/nodewise-tree-constants-v3` branch.
- [x] Implement the typed-tree mathematical kernel and all required exact,
  projected, certificate, optimization, interval, SOS, signed-forest, and CP
  modules.
- [x] Enumerate the declared exact tree grammars and execute the complete A--I
  base matrix with unique scientific-instance hashes.
- [x] Generate the theorem/claim/prior-art registries, 18 vector figures,
  scientific tables, two independent manuscripts, PDF renders, four
  adversarial reviews, and strict release evidence.
- [x] Execute the canonical 15-stage workflow from source commit `b718f4e` and
  record the expected fail-closed publication result.
- [ ] Resolve fixed-eta sharpness for the ambient `k` and projected-root
  `k-1` coefficients, or state the strongest provable non-sharp result.
- [ ] Obtain independent certification for every claimed small-case global
  optimum.
- [ ] Resume the resource-gated 460,800-trajectory optimizer schedule and
  8,400-cell performance schedule only when the declared compute budget is
  authorized.
- [ ] Obtain independent human reviews from multilinear analysis, operads,
  verified numerics, and scientific reproducibility specialists.
- [ ] Establish theorem-level novelty through a comprehensive independent
  literature review, or retain the output as a research draft/software
  companion.
- [x] Perform a bounded primary-source novelty audit for the V5 tree/DAG
  claims; retain all verdicts as `NOVELTY_NOT_ESTABLISHED` pending expert review.
- [x] Rebuild the V5 mathematical, source-calculus, and software manuscripts
  with M8/M9/M10 and render/verify all three PDFs.

## Projected-tree theory v4

- [x] Reproduce the current projected-tree baseline and freeze a truth ledger.
- [x] Audit equality/slack conditions for the projected `(k-1)` bound; general
  fixed-eta compatibility remains open.
- [x] Narrow fixed-eta sharpness for k=2 with the exact restricted class and
  preserve the gated-planar repeated-law open boundary; the explicitly
  declared repeated-map class is now sharp at fixed eta.
- [x] Prove the scalar DAG-native source-resolved certificate in `O(|V|+|E|)`.
- [x] Prove P6A first-order source-aware vector DAG propagation; higher-order
  source interactions remain open.
- [x] Prove P7A first-order signed-source aggregation and strict cancellation
  witness; nonlinear signed-identity constants remain open.
- [x] Implement P6B exact finite higher-order DAG source-polynomial expansion
  with repeated-source multi-indices and certified order truncation.
- [x] Implement P7B nonlinear signed source-polynomial certificate over
  retained and exact higher-order terms.
- [x] Instantiate P7C generic signed expressions for associator, Jacobiator,
  and Filippov defects without assuming identity satisfaction.
- [x] Prove and register the exact zero projected Jacobiator identity for the
  declared gated-planar rotation law; retain generic-law constants as open.
- [x] Implement P8 validated multilinear operator-norm enclosures and a
  sound certificate selector.
- [x] Separate approximate-law representation, closure, and interaction
  budgets (P10).
- [x] Register finite topology metrics and monotone sharpness bands without
  declaring global sharpness.
- [ ] Resolve exact global fixed-eta sharpness and growing-tree uniformity;
  the quantitative chain gap and endpoint strictness are tracked below.

## Canonical PMT API (2026-09-09)

- [x] Develop an isolated k4 chain study with full source Gram, global
  closure audits, seeded CPU searches, source snapshots and negative controls.
- [x] Supply the advisory chain/mixed sharp formula proof via isometric
  dilation and angular optimization, including a_chain=5/2 and explicit
  attaining witnesses; see `k4_exploration/CHAIN_GRAM_REPORT.md`.
- [ ] Independently review that proof and explicitly reconcile the historical
  OPEN_PMT_FIXED_ETA_K4_PLUS_V1 boundary before theorem promotion.
- [ ] Resolve the branch-below k4 upper/lower gap and audit theorem-level
  novelty against scaled relative graphs and products of projections.
- [ ] Reconcile M18/M19 phase-law prose with canonical ambient-leaf closure;
  the additive gated witness and negative control are already available.

- [x] Add the `seion_core.pmt` typed finite-dimensional facade with ambient
  leaf semantics, exact ambient/projected evaluation, and root error
  decomposition.
- [x] Expose the universal projected `(k-1)` bound, the exact independent-law
  `W_3(eta)` contract, analytic chain/branch witnesses, and numerical norm
  brackets with fail-closed semantics.
- [x] Register the PMT definition, proved-under-assumptions contracts, and
  the fixed-eta `k>=4` `OPEN_PROBLEM` boundary.
- [ ] Derive and certify an exact fixed-eta constant for `k>=4`; numerical
  optimizer output remains observation-only until an analytic upper envelope
  and independent lower construction are available.

## Projected-graph theory v5

- [x] Freeze the finite projected-graph core at scientific commit
  `1f4984ec8e741049789e0035c7a3ba84c86d3f29`; preserve operational HEAD
  `f88f75bdf3f44407392d6c55dd2affb37d3185ab` as governance history.
- [x] Establish exact `k=2` saturation for the declared real binary chain with
  independent node laws: `C_2^P(eta)=1` for `0 < eta <= 1`.
- [x] Close the declared finite-dimensional binary `k=2` class-level
  supremum: `C_{2,A}^P(eta)=1` by the universal upper bound plus the
  embedded repeated-law witness.
- [x] Audit simultaneous equality conditions for independent laws; the
  explicitly declared repeated-map class is sharp, while the gated-planar
  repeated-law subclass remains open.
- [x] Produce certified lower-bound witnesses for independent-law `k=3`
  chain and branching topologies without claiming global sharpness.
- [x] Create the V5 theorem-consolidation, formalization-target, and
  theorem-to-theorem novelty ledgers without asserting novelty.
- [x] Consolidate the finite DAG/source-polynomial results into one canonical
  theorem package and prepare a bounded independent-review packet.
- [x] Register the finite source-resolved calculus as a unified theorem with
  exact multi-index propagation, truncation, and signed-cancellation bounds.
- [x] Derive and register the exact all-finite-k left-comb formula for the
  declared gated-planar rotation law; retain global tree sharpness as open.
- [x] Derive and register the exact recurrence for every finite ordered
  full-binary topology under the declared homogeneous gated-planar law;
  retain arbitrary-law sharpness as open.
- [x] Extend the restricted recurrence to every finite ordered rooted tree
  with arity at least two under arity-compatible gated rotations; retain
  arbitrary-law and global sharpness as open.
- [x] Derive and register the M11 conditional quantitative angle--magnitude
  gap under exact first-propagator saturation; retain the unrestricted
  fixed-eta supremum as open.
- [x] Prove fixed-tree support compression and close the global strict
  supremum gap below `U_3` for `0<eta<1`; retain exact constants, explicit
  delta, and unbounded growing-tree uniformity as open.
- [x] Extend the M10/compactness strict-gap result to the endpoint `eta=1`;
  the exact independent-law endpoint constants are now closed by M14/M15.
- [x] Prove the unconditional chain-only `W_3(eta)` envelope from the
  contraction Gram-matrix cross-term bound; branching is handled separately
  by nuclear/operator-norm duality.
- [x] Attain the chain-only `W_3(eta)` envelope explicitly in dimension two;
  retain no open boundary for the independent-law chain.
- [x] Prove and attain the independent-law branching `W_3(eta)` envelope via
  nuclear/operator-norm duality; retain same-law/gated and arbitrary-tree
  sharpness as open.
- [x] Resolve ambient same-law-bound saturation inside the explicitly declared
  contractive gated-planar repeated-law `k=2` subclass; its exact normalized
  constant is `1`. Variable-gate, arbitrary-leaf, and non-planar variants remain
  separate open boundaries.
- [x] Resolve exact independent-law `k=3` sharpness for chain and branching;
  both constants are exactly `W_3(eta)`.
- [x] Record the M16 scope corollary: “independent-law” freely selects node
  laws, so the arbitrary-node-law binary `k=3` chain/branching class also has
  exact constant `W_3(eta)`.
- [x] Close the explicitly defined contractive gated-planar repeated-law
  `k=2` subclass with exact normalized constant `1`; retain variable-gate,
  arbitrary-leaf, and non-planar variants as separate open boundaries.
- [x] Prove the finite ordered full-binary independent-law asymptotic
  `(k-1)` sharpness statement for every fixed topology (M18); fixed-eta,
  higher-arity, and growing-tree variants remain open.
- [x] Extend the asymptotic `(k-1)` sharpness witness to every fixed finite
  ordered rooted topology with internal arities at least two (M19); fixed-eta
  and growing-tree uniformity remain open.
- [x] Close the exact independent-law fixed-eta constant for every finite
  `k=3` arity profile (M20); same-law/gated variants and fixed-eta `k>=4`
  remain open.
- [x] Close the tagged same-law binary `k=3` class by an orthogonal
  direct-sum law simulation of M14/M15 (M21); rank-one/common-leaf same-law
  and gated variants remain open.
- [x] Close the high-eta regime of the strict rank-one/common-leaf same-law
  chain with a repeated rotation (M22); low-eta chain, branching, and broader
  gated/shared-law variants remain open.
- [x] Reduce the remaining strict rank-one/common-leaf same-law chain exactly
  to the unary contraction problem in M23; do not treat the reduction as an
  extremal-value proof.
- [x] Run an internal pre-review consistency audit of the universal theorem and
  M8/M14--M23; preserve external human review as pending.
- [x] Audit the six objective requirements requirement-by-requirement and link
  each one to authoritative evidence, limitations, and its external closure
  condition.
- [x] Reuse identical path frontiers for positive and negative scores in the
  production training loop; score-parity coverage passes. FB15K237 still
  exceeds the preregistered 300-second acceptance ceiling on this hardware
  (latest reversible precision probe: 456.6 s).
- [x] Produce a certified independent-law growing-chain obstruction to any
  nodewise value-preserving dimension/rank bound uniform over unbounded tree
  size/arity; root-only and same-law variants remain open.
- [ ] Evaluate the low-eta rank-one/common-leaf same-law chain operator
  problem, rank-one/common-leaf branching and gated `k=3` values, plus
  fixed-eta independent-law sharpness for `k>=4` beyond M20--M23.
- [ ] Obtain exact or validated multilinear norm results beyond the finite
  enclosure implementation.
- [ ] Complete theorem-to-theorem novelty review and independent human review.
- [x] Implement and register a finite multilinear DAG bounded-domain error
  certificate with shared-subexpression fan-out accounting and an exact
  finite rank-budget dynamic program under rank-independent enclosures.
- [x] Add a shared-subexpression tensor-network DAG backend, verify its global
  domain certificate on held-out normalized inputs, and preserve the negative
  allocator comparison against a uniform baseline.
- [x] Prove and register the exact source-to-root path constant for the
  nonnegative first-order DAG channel envelope, including fan-out and parallel
  slot multiplicity; keep full multilinear sharpness explicitly separate.
- [x] Close the asymptotic path constant for the fixed independent-law shared
  diamond DAG: universal coefficient 4 and a planar witness attaining 4 as
  eta tends to zero; retain fixed-eta and arbitrary-DAG sharpness boundaries.
- [x] Generalize the shared-diamond result to every fixed finite independent-
  law multilinear DAG: the exact asymptotic coefficient is the total
  source-to-root slot-path multiplicity K(G).
- [x] Validate the general witness numerically with real tensor cores on chain,
  shared-diamond, and repeated-slot DAGs.
- [x] Add an exploratory matched-error shared-DAG resource study with exact
  compressed-coordinate execution equivalence, validation-only selection, an
  independent test batch, and an explicit negative/context-dependent result;
  hardware timing and multi-topology policy claims remain open.
- [ ] Formalize the finite algebraic kernel in a proof assistant.
- [x] Implement score-space whitening, spectral projectors, relationwise
  water-filling/DP allocation, and finite-query ranking certificates.
- [x] Complete the dense D128 score-space opportunity audit and identify the
  `G_spectral=1.85055` regime at tolerance `0.0005`.
- [x] Benchmark relationwise score-space execution with static bucketing,
  score-only timing, and full-candidate GEMMs under a 20 GB cap.
- [x] Replace relationwise per-group GEMM routing with vectorized/static
  batching and re-run the matched-kernel benchmark at stress size.
- [ ] Resume staged D128 training only after the Windows dump/driver safety
  blocker is resolved; preserve the 23 GB ceiling and frequent checkpoints.
- [x] Register a separate accuracy-first KGE SOTA discovery protocol with
  validation-only selection, hard-negative/EMA primitives, explicit targets,
  and staged GPU safety limits.
- [x] Implement and benchmark the first full-entity spectral-mixture
  discovery runner with blockwise hard-negative mining and no external text
  dependency; structural-context mining remains a separate pending extension.
- [x] Formalize Program A teacher versus Program B frozen student/certification
  boundaries and add leakage-aware split, retriever, EMA, gate, ensemble, and
  distillation primitives.
- [ ] Add the structural contextual reranker and validation-fitted retriever
  union runner; external text remains disabled pending provenance.
- [x] Run the bounded VRAM ramp through 16 GB and preserve the 20 GB thermal
  evidence; the agent-side thermal threshold is removed, while long runs still
  require B-0012 review.
- [x] Remove the agent-side thermal threshold from the discovery protocol while
  preserving system/driver protection behavior.
- [x] Integrate and benchmark the first spectral conditional Tucker mixture
  scorer/trainer; quality finalist selection and full validation remain open.
- [x] Execute `SRATM_CERTIFIED_COMPRESSION_V1` on frozen SRATM step4600 without
  opening TEST; preserve bounded certificate/CCR results and B-0012 hardware hold.
- [x] Execute `SRATM_NO_LEAKAGE_AUDIT_V1` with static scan, runtime sentinel,
  split provenance, reciprocal audit, duplicate report, and artifact DAG.
- [ ] Reconstruct and archive the checkpoint-selection selector log before any
  final TEST confirmation.
- [x] Execute G6 all-entity VALID with the frozen SRATM step4600 and
  TRAIN+VALID-only filtered positives, including candidate-wise certificate
  validation over all 35,070 queries and 14,541 entities.
- [ ] Reconcile the historical `0.6116475` validation protocol with the
  sealed TRAIN+VALID-only control (`0.3958612`) before declaring G6 MRR
  preservation; TEST remains sealed.
- [x] Run `HISTORICAL_VALIDATION_RECONCILIATION_V1` on a deterministic
  sealed sample: scorer-path equivalence, positive/gold extraction,
  reciprocal construction, and TRAIN+VALID versus TRAIN-only filters.
- [ ] Locate the remaining historical-baseline cause from archived rank traces
  or provenance without opening TEST; until then classify `0.6116475` as
  observed-but-protocol-not-reconciled.
- [x] Inventory historical checkpoint identities: `checkpoint_last.pt` is
  step 4600 and matches the audit SHA; `checkpoint_best.pt` is a distinct
  step 4608 artifact and is not the audited reference.
- [x] Execute `HISTORICAL_EVALUATOR_PROVENANCE_V1` over the historical run
  directory, relevant source history, checkpoint identities, and available
  PowerShell history without opening TEST; classify loader/filter, vocabulary,
  tie-policy, and command provenance hypotheses explicitly.
- [ ] Recover an archived historical command, rank trace, filter counts, or
  runtime snapshot sufficient to reconcile `0.6116475` without opening TEST.
- [x] Start a new `SRATM_SEALED_TRAINING_V1` from random initialization with
  TRAIN+VALID-only loading and a fail-closed runtime sentinel; pause at the
  next checkpoint on user request.
- [x] Audit the new sealed step-704 checkpoint on full VALID with the same
  TRAIN+VALID-only filtered evaluator and compare it separately against the
  reproducible sealed control and the unreconciled historical metric.
- [ ] Reconcile the sealed step-704 resume provenance before any continuation:
  the original git/source identity and the checkpoint/config `max_steps`
  conflict must be resolved without opening TEST.
- [ ] Only after the resume gate passes, execute the predeclared full-VALID
  checkpoint schedule, freeze `SEALED_TEACHER_FREEZE_V1`, then launch fresh
  spectral/compression/G6 campaigns descended only from that freeze.
