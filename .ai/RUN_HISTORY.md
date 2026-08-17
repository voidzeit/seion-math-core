# Run history

## 2026-08-09T20:54:20Z — global domain-certified allocator

- Commands: `python -m pytest applications/adaptive_tensor_network/tests/test_global_certificate.py -q`;
  `python -m pytest applications/adaptive_tensor_network/tests -q`;
  `python applications/adaptive_tensor_network/experiments/run_global_certificate_probe.py`;
  `git diff --check`.
- Environment: Windows PowerShell, Python 3.12, branch
  `campaign/gate13-closeout`, source commit `cbb6ddb0a050882249054f9044c905e442a561ab`.
- Outcome: **GLOBAL_DOMAIN_CERTIFICATE_ALLOCATOR_ADDED_AND_PROBED**. The
  240-record normalized-leaf probe found certificate-holds fraction `1.0` in
  both topologies and mean RMS reductions `0.0148` and `0.0135` versus the
  empirical pathwise heuristic.
- Limitations: domain bound `||x_leaf||<=1` was declared by normalization;
  Frobenius enclosures are conservative; no universal superiority or release
  claim was made.

## 2026-08-09T20:49:14Z — finite-batch validated certificate allocator

- Commands: `python -m pytest applications/adaptive_tensor_network/tests/test_validated_certificate.py -q`;
  `python -m pytest applications/adaptive_tensor_network/tests -q`;
  `python applications/adaptive_tensor_network/experiments/run_validated_certificate_probe.py`;
  `git diff --check`.
- Environment: Windows PowerShell, Python 3.12, branch
  `campaign/gate13-closeout`, source commit `cbb6ddb0a050882249054f9044c905e442a561ab`.
- Outcome: **FINITE_BATCH_VALIDATED_CERTIFICATE_ALLOCATOR_ADDED_AND_PROBED**.
  The 360-record artifact reports validated-bound no-worse fraction `1.0` in
  both topologies and mean held-out RMS reductions `0.2432` and `0.2250`.
- Limitations: fitting-batch certificate only; Frobenius enclosure is
  conservative; small-case exhaustive allocator is not scalable; no true-error
  superiority or universal-input claim was made.

## 2026-08-09T20:44:35Z — exact fitted-majorant allocation probe

- Commands: `python -m pytest applications/adaptive_tensor_network/tests/test_majorant_optimizer.py -q`;
  `python -m pytest applications/adaptive_tensor_network/tests -q`;
  `python applications/adaptive_tensor_network/experiments/run_majorant_optimizer_probe.py`;
  `python -m compileall -q applications/adaptive_tensor_network/src applications/adaptive_tensor_network/tests`;
  `git diff --check`.
- Environment: Windows PowerShell, Python 3.12, branch
  `campaign/gate13-closeout`, source commit `cbb6ddb0a050882249054f9044c905e442a561ab`.
- Outcome: **EXACT_FITTED_MAJORANT_OPTIMIZER_ADDED_AND_PROBED**. The dynamic
  program exactly minimized the declared fitted-data majorant; the probe
  generated 240 records, with mean true-error reductions `0.3400` and `0.3560`
  for chain and balanced topologies respectively.
- Limitations: exploratory and not preregistered; empirical path factors are
  not validated global operator norms; no allocator-optimality, technology
  superiority, or historical Level 1 result was promoted.

## 2026-08-09T20:37:21Z — growing-tree dimension obstruction certified

- Commands: `python -m pytest tests/math_closure/test_growing_tree_dimension_counterexample.py -q`;
  `python research/math_closure/dimension_rank/growing_tree_dimension_counterexample.py`;
  `git diff --check`.
- Environment: Windows PowerShell, Python 3.12, branch
  `campaign/gate13-closeout`, source commit `cbb6ddb0a050882249054f9044c905e442a561ab`.
- Outcome: **GROWING_TREE_NODEWISE_SUPPORT_OBSTRUCTION_CERTIFIED**. The
  executable family requires support ranks `2,3,5,9` at depths `1,2,4,8`.
- Limitations: this is a negative result for nodewise value-preserving support
  compression under independent laws; it does not settle root-only reductions,
  same-law classes, exact higher-`k` constants, novelty, or human review. No
  release, push, or PR was performed.

## 2026-08-09T17:55:02Z — review snapshot drift detected and repaired

- Commands: `scripts/verify_projected_trees_v5_review_manifest.ps1` (first run
  failed on the stale objective-audit hash); `Get-FileHash` refresh; the same
  gate rerun; JSON/YAML parsing; `git diff --check`.
- Environment: Windows PowerShell, branch `campaign/gate13-closeout`, source
  commit `cbb6ddb0a050882249054f9044c905e442a561ab`.
- Outcome: **REVIEW_MANIFEST_DRIFT_DETECTED_AND_REPAIRED**. The stale hash was
  corrected and the final gate passed **19/19**.
- Limitations: this validates snapshot integrity only; external mathematical
  review and novelty determination remain absent. No release, push, or PR was
  performed.

## 2026-08-09T17:54:07Z — completion audit and external blocker confirmation

- Commands: review-manifest gate; JSON/YAML parsing; `git diff --check`.
- Environment: Windows PowerShell, branch `campaign/gate13-closeout`, source
  commit `cbb6ddb0a050882249054f9044c905e442a561ab`.
- Outcome: **INTERNAL_COMPLETION_AUDIT_CONFIRMED_EXTERNAL_BLOCKER**. The six
  requirements were re-audited against current evidence. Internal manuscript,
  scope, and reproducibility requirements are ready; independent review and
  expert novelty determination remain absent.
- Limitations: this is not a release or completion approval. No release, push,
  or PR was performed.

## 2026-08-09T17:52:37Z — neutral external-reviewer shortlist

- Commands: public-profile/source comparison; refresh of the template SHA-256;
  `scripts/verify_projected_trees_v5_review_manifest.ps1`; JSON/YAML parsing;
  `git diff --check`.
- Environment: Windows PowerShell, branch `campaign/gate13-closeout`, source
  commit `cbb6ddb0a050882249054f9044c905e442a561ab`.
- Outcome: **EXTERNAL_REVIEWER_SHORTLIST_PREPARED**. Added a neutral shortlist
  mapping research profiles to theorem, prior-art, MOR, and provenance review
  roles, with explicit non-endorsement safeguards.
- Limitations: no outreach or review occurred; `PENDING_HUMAN_REVIEW` and
  `NOVELTY_NOT_ESTABLISHED` remain. No release, push, or PR was performed.

## 2026-08-09T17:50:51Z — deterministic review-manifest gate

- Commands: `scripts/verify_projected_trees_v5_review_manifest.ps1`; JSON/YAML
  parsing; `git diff --check`.
- Environment: Windows PowerShell, branch `campaign/gate13-closeout`, source
  commit `cbb6ddb0a050882249054f9044c905e442a561ab`.
- Outcome: **REVIEW_MANIFEST_GATE_ADDED_AND_PASSING**. The gate parses the
  review manifest and verifies all 19 declared hashes and paths.
- Limitations: the gate is reproducibility infrastructure, not independent
  human review, novelty approval, or publication readiness. No release, push,
  or PR was performed.

## 2026-08-09T17:49:19Z — frozen external-review artifact manifest

- Commands: `Get-FileHash -Algorithm SHA256` over the declared review inputs;
  JSONL/YAML parsing; `git diff --check`.
- Environment: Windows PowerShell, branch `campaign/gate13-closeout`, source
  commit `cbb6ddb0a050882249054f9044c905e442a561ab`.
- Outcome: **REVIEW_ARTIFACT_MANIFEST_FROZEN**. The exact manuscript, theorem
  dossiers, registry, novelty records, and review documents are now
  hash-identifiable for a future independent reviewer.
- Limitations: the snapshot is an internal reproducibility aid, not human
  review, novelty approval, or publication readiness. No release, push, or PR
  was performed.

## 2026-08-09T17:46:09Z — external-review normalization and scope sheet

- Commands: cross-read the M8/M14--M20 proof dossiers and
  `claims/theorem_registry_v5.yaml`; JSON/YAML parsing; `git diff --check`.
- Environment: Windows PowerShell, branch `campaign/gate13-closeout`, source
  commit `cbb6ddb0a050882249054f9044c905e442a561ab`.
- Outcome: **EXTERNAL_REVIEW_SCOPE_SHEET_ADDED**. Added a compact scope map
  and normalization sheet covering the universal theorem, M8, M13--M20, and
  optional M21--M23, including explicit exclusions and reviewer checks.
- Limitations: this is an internal preparation artifact, not independent
  human review or novelty approval. No release, push, or PR was performed.

## 2026-08-09T17:41:54Z — systematic theorem-by-theorem novelty audit expansion

- Commands: web searches restricted to primary/publisher records for
  hierarchical/tree projection, multilinear truncation, TTN integration,
  bilinear MOR, semiring provenance, and adaptive-rank HT; source pages were
  opened and recorded in the novelty audit; `git diff --check`.
- Environment: Windows PowerShell, branch `campaign/gate13-closeout`, source
  commit `cbb6ddb0a050882249054f9044c905e442a561ab`.
- Outcome: **NOVELTY_AUDIT_EXPANDED_WITH_CONSERVATIVE_VERDICT**. The targeted
  audit and theorem matrix now contain theorem-family dispositions for the
  universal bound, M8, M13--M23, and the source-resolved DAG calculus.
- Result: adjacent prior art was found, but no exact match was verified for
  the combined V5 object, constants, hypotheses, and equality classes.
- Limitations: this is still a bounded search record, not an exhaustive expert
  novelty determination or publication decision. All novelty fields remain
  `NOVELTY_NOT_ESTABLISHED`; no release, push, or PR was performed.

## 2026-08-09T17:38:01Z — self-contained analytic proof spine in main manuscript

- Commands: `scripts/build_projected_graphs_v5_papers.ps1`;
  `scripts/verify_projected_graphs_v5_papers.ps1`; `python -m pytest
  tests/math_closure -q`; `python -m pytest
  applications/adaptive_tensor_network/tests -q`; M20, M21, and M23 module
  entry points; `git diff --check`.
- Environment: Windows PowerShell, Python 3.12, branch
  `campaign/gate13-closeout`, source commit
  `cbb6ddb0a050882249054f9044c905e442a561ab`.
- Outcome: **MAIN_MANUSCRIPT_ANALYTIC_PROOF_SPINE_ADDED**. The main paper now
  contains the analytic Gram estimate, `W_3` scalar optimization, branching
  nuclear/operator-norm reduction, and finite-arity effective-law argument.
  The main PDF rebuilt successfully at **9 pages**.
- Validation: math closure **60/60 passed**; applied tests **16/16 passed**;
  all three PDFs rendered/audited; M20/M21/M23 module entry points passed;
  `git diff --check` passed. Final `governance audit --json` passed
  non-strict with status `yellow`: 177 historical runs, 9 unique scientific
  instances, 8 duplicate groups, and no missing required files; deduplication
  completed.
- Limitations: this improves internal self-containedness but is not
  independent human review, novelty determination, or publication approval.
  No release, push, or PR was performed.

## 2026-08-09T06:03:33Z — M23 exact operator reduction for strict same-law chain

- Commands: `python research/math_closure/k3/m23_rank_one_same_law_chain_operator_reduction.py`;
  focused M23 pytest; full `tests/math_closure`; KGR non-slow suite; and
  `pytest --collect-only -q`.
- Environment: Windows PowerShell, Python 3.12, CUDA RTX PRO 5000 Blackwell
  Laptop GPU; branch `campaign/gate13-closeout`, source commit
  `cbb6ddb0a050882249054f9044c905e442a561ab`.
- Outcome: **M23_RANK_ONE_SAME_LAW_CHAIN_OPERATOR_REDUCTION_PROVED**. The
  exact reduction passed 3/3 focused tests and 59/59 math closure tests; KGR
  non-slow tests passed 180/180; collection is 493 tests.
- Limitations: the reduction does not evaluate the low-eta supremum. Branching,
  broader same-law/gated classes, fixed-eta independent-law `k>=4`, novelty,
  human review, Lean/lake, and FB15K237 performance remain open or blocked.
  No release, push, or PR was performed.

## 2026-08-09T05:53:11Z — FB15K237 precision/backend probe

- Commands: FB15K237 acceptance with process-level
  `torch.set_float32_matmul_precision('high')`; `python -m pytest -q
  tests/math_closure`; `python -m pytest -q tests/kgr -m 'not slow'`; and
  `python -m pytest --collect-only -q`.
- Environment: Windows PowerShell, Python 3.12, CUDA RTX PRO 5000 Blackwell
  Laptop GPU; branch `campaign/gate13-closeout`, source commit
  `cbb6ddb0a050882249054f9044c905e442a561ab`.
- Outcome: **FB15K237_COMPLETES_BUT_PERFORMANCE_GATE_REMAINS_OPEN**. The
  acceptance epoch completed in **456.6 s** against the preregistered 300 s
  ceiling. The process-level precision probe was not retained as a production
  change.
- Validation: math closure **56/56 passed**, KGR non-slow **180/180 passed**,
  and total collection **490 tests**. The low-eta same-law search was
  exploratory numerical evidence only and did not change theorem status.
- Limitations: the performance gate remains open; novelty, human review,
  formal proof-assistant verification, and unresolved mathematical classes
  remain blocked or open. No release, push, or PR was performed.

## 2026-08-09T05:33:52Z — KGR path-frontier reuse and FB15K237 performance gate

- Commands: score/gradient reuse tests; KGR non-slow suite; WN18RR and
  FB15K237 full acceptance tests; paper build and PDF verification; JSON/YAML
  parse; governance audit and run deduplication.
- Environment: Windows PowerShell, Python 3.12, CUDA RTX PRO 5000 Blackwell
  Laptop GPU; branch `campaign/gate13-closeout`, source commit
  `cbb6ddb0a050882249054f9044c905e442a561ab`.
- Outcome: **KGR_PATH_OUTPUT_REUSE_CORRECT_FB15K237_PERFORMANCE_GATE_OPEN**.
- Validation: 490 tests collected, 489 passed, 1 failed because FB15K237
  completed in 424.8 s against the preregistered 300 s ceiling; WN18RR passed
  in 123.16 s. The failure is an engineering performance result, not a
  correctness failure.
- Limitations: the performance gate remains open; no causal, MRR, novelty,
  theorem, release, push, or PR claim was promoted.

## 2026-08-09T05:05:26Z — M22 high-eta rank-one/common-leaf same-law chain closure

- Commands: focused M13--M22 tests; segmented pytest verification for all
  non-slow selections; `pytest --collect-only -q`; paper build and PDF
  verification; JSON/YAML parse; `git diff --check`; governance audit and run
  deduplication.
- Environment: Windows PowerShell, Python 3.12 project environment,
  MiKTeX/pdfLaTeX; branch `campaign/gate13-closeout`, source commit
  `cbb6ddb0a050882249054f9044c905e442a561ab`.
- Outcome: **M22_RANK_ONE_SAME_LAW_HIGH_ETA_CHAIN_EXACT_CLOSED_487_OF_488_TESTS**.
- Summary: a repeated gated rotation law with common projected leaf and
  rank-one projector attains the exact high-eta value `W_3(eta)` for the
  strict binary chain.
- Validation: focused checks **26/26 passed**; **488/489** collected tests
  passed through segmented execution and individual slow-test checks.
  WN18RR full batched training passed in 123.16 s; FB15K237 completed but
  exceeded the preregistered 300 s ceiling at 424.8 s in the optimized run.
  Three PDFs rebuilt/audited;
  no overfull box in the main paper; governance `yellow`, 177 historical
  runs, 9 unique instances, 8 duplicate groups, and 177 complete contracts.
- Limitations: low-eta rank-one/common-leaf same-law, branching/gated
  variants, fixed-eta independent-law sharpness for `k>=4`, growing-tree
  uniformity, signed-forest constants, globally tight norms, novelty, human
  review, Lean/lake, and resource-gated schedules remain open or blocked.
  No release, push, or PR was performed.

## 2026-08-09T03:41:12Z — M21 tagged same-law binary k=3 closure

- Commands: focused M13--M21 tests; full `python -m pytest -q`; paper build
  and PDF verification; JSON/YAML parse; governance audit and run
  deduplication.
- Environment: Windows PowerShell, Python 3.12 project environment,
  MiKTeX/pdfLaTeX; branch `campaign/gate13-closeout`, source commit
  `cbb6ddb0a050882249054f9044c905e442a561ab`.
- Outcome: **M21_TAGGED_SAME_LAW_K3_EXACT_FIXED_ETA_CLOSED_FULL_SUITE_GREEN**.
- Summary: a single repeated bilinear law with orthogonal projected leaf tags
  uses direct-sum blocks to reproduce the exact M14 chain and M15 branching
  witnesses, preserving norm one and closure defect at most `eta`.
- Validation: focused checks **25/25 passed**; full suite **487/487 passed**
  in 428.82s; three PDFs rebuilt and audited; no overfull box in the main
  paper; governance status `yellow`, 174 historical runs, 9 unique instances,
  8 duplicate groups, and 174 complete artifact contracts.
- Limitations: rank-one/common-leaf same-law and gated variants, fixed-eta
  independent-law sharpness for `k>=4`, growing-tree uniformity, signed-forest
  constants, globally tight norms, novelty, human review, Lean/lake, and
  resource-gated schedules remain open or blocked. No release, push, or PR was
  performed.

## 2026-08-09T03:23:19Z — M20 exact k=3 all-finite-arity constant

- Commands: focused M14--M20 tests; full `python -m pytest -q`; paper build
  and PDF verification; JSON/YAML parse; governance audit and run
  deduplication.
- Environment: Windows PowerShell, Python 3.12 project environment,
  MiKTeX/pdfLaTeX; branch `campaign/gate13-closeout`, source commit
  `cbb6ddb0a050882249054f9044c905e442a561ab`.
- Outcome: **M20_K3_ALL_FINITE_ARITY_EXACT_FIXED_ETA_CLOSED_FULL_SUITE_GREEN**.
- Summary: freezing unit leaf slots reduces every finite k=3 arity profile to
  the M14 chain or M15 branching effective class; unit `e0` gates transfer the
  matching witnesses, giving `C_{T,ind}^P(eta)=W_3(eta)` for `0<eta<=1`.
- Validation: focused checks **22/22 passed**; full suite **486/486 passed**
  in 430.78s; three PDFs rebuilt and audited; no overfull box in the main
  paper; governance status `yellow`, 173 historical runs, 9 unique instances,
  8 duplicate groups, and 173 complete artifact contracts.
- Limitations: same-law/gated variants, fixed-eta independent-law sharpness
  for `k>=4`, growing-tree uniformity, signed-forest constants, globally tight
  norms, novelty, human review, Lean/lake, and resource-gated schedules remain
  open or blocked. No release, push, or PR was performed.

## 2026-08-09T03:00:11Z — M19 finite-arity asymptotic sharpness

- Commands: focused M18/M19 evaluators and tests; full 'python -m pytest -q';
  paper build and PDF verification; YAML/JSON parse; 'git diff --check';
  governance audit and run deduplication.
- Environment: Windows PowerShell, Python 3.12 project environment,
  MiKTeX/pdfLaTeX; branch 'campaign/gate13-closeout', source commit
  'cbb6ddb0a050882249054f9044c905e442a561ab'.
- Outcome: **M19_FINITE_ARITY_ASYMPTOTIC_K_MINUS_ONE_CLOSED_FULL_SUITE_GREEN**.
- Summary: real-plane product laws at non-root vertices and the imaginary-part
  root law give the exact witness
  'E_proj=|sin((k-1) arcsin(eta))|' for every finite arity profile.
- Validation: full suite **485/485 passed** in 442.92s; three PDFs rebuilt and
  audited; no overfull box in the main paper; governance status 'yellow',
  172 historical runs, 9 unique instances, 8 duplicate groups, and 172
  complete artifact contracts.
- Limitations: fixed-eta sharpness, broader same-law/gated classes, growing-tree
  uniformity, signed-forest constants, globally tight norms, novelty, human
  review, Lean/lake, and resource-gated schedules remain open or blocked. No
  release, push, or PR was performed.

## 2026-08-09T02:39:46Z — M18 finite-binary asymptotic sharpness

- Commands: M18 focused evaluator/test; full `python -m pytest -q`; paper
  build and PDF verification; YAML/JSON parse; `git diff --check`; governance
  audit and run deduplication.
- Environment: Windows PowerShell, Python 3.12 project environment,
  MiKTeX/pdfLaTeX; branch `campaign/gate13-closeout`, source commit
  `cbb6ddb0a050882249054f9044c905e442a561ab`.
- Outcome: **M18_BINARY_ASYMPTOTIC_K_MINUS_ONE_CLOSED_FULL_SUITE_GREEN**.
- Summary: for every fixed finite ordered full-binary topology, the complex
  two-dimensional witness gives `E_proj=|sin((k-1) arcsin(eta))|`; the
  universal projected-root theorem yields the matching asymptotic limit.
- Validation: full suite **483/483 passed** in 456.41s; three PDFs rebuilt and
  audited; no new overfull box; governance status `yellow`, 171 historical
  runs, 9 unique instances, 8 duplicate groups, and 171 complete artifact
  contracts.
- Limitations: fixed-eta, higher-arity and growing-tree extensions, broader
  same-law/gated variants, signed-forest constants, globally tight norms,
  novelty, human review, Lean/lake, and resource-gated schedules remain open
  or blocked. No release, push, or PR was performed.

## 2026-08-09T02:16:47Z — M17 contractive gated-planar repeated-law closure

- Commands: M17 focused evaluator/test; full `python -m pytest -q`; paper
  build and PDF verification; YAML/JSON parse; `git diff --check`; governance
  audit and run deduplication.
- Environment: Windows PowerShell, Python 3.12 project environment,
  MiKTeX/pdfLaTeX; branch `campaign/gate13-closeout`, source commit
  `cbb6ddb0a050882249054f9044c905e442a561ab`.
- Outcome: **M17_CONTRACTIVE_GATED_REPEATED_CLOSED_FULL_SUITE_GREEN**.
- Summary: proved the exact identity `P*A*(I-P)*A*e0`, upper bounded it by
  `M*rho`, and attained equality with an off-diagonal planar contraction.
- Validation: full suite **481/481 passed** in 460.50s; three PDFs rebuilt and
  audited; governance status `yellow`, 170 historical runs, 9 unique
  instances, 8 duplicate groups, and 170 complete artifact contracts.
- Limitations: variable-gate/arbitrary-leaf/non-planar variants, higher-arity
  and arbitrary finite topologies, growing-tree sharpness, signed-forest
  constants, norms, novelty, human review, Lean/lake, and resource-gated
  schedules remain open or blocked. No release, push, or PR was performed.

## 2026-08-09T02:03:39Z — M16 arbitrary-node-law binary k=3 corollary

- Commands: focused M16/M14/M15 tests; full `python -m pytest -q`; PDF build
  and verification; YAML/JSON parse; `git diff --check`; governance audit
  and run deduplication.
- Environment: Windows PowerShell, Python 3.12 project environment,
  MiKTeX/pdfLaTeX; branch `campaign/gate13-closeout`, source commit
  `cbb6ddb0a050882249054f9044c905e442a561ab`.
- Outcome: **M16_BINARY_GENERAL_NODE_LAW_CLASS_CLOSED_FULL_SUITE_GREEN**.
- Summary: made explicit that the M14/M15 independently selectable-node-law
  convention is the full arbitrary-node-law binary class, so both chain and
  branching constants are exactly `W_3(eta)`.
- Validation: focused checks **16/16**; full suite **480/480 passed** in
  414.50s; three PDFs rebuilt/audited; governance status `yellow`, 169
  historical runs, 9 unique instances, 8 duplicate groups, and 169 complete
  artifact contracts.
- Limitations: repeated same-law/gated subclasses, higher-arity/arbitrary
  finite topologies, growing-tree sharpness, signed-forest constants, norms,
  novelty, human review, Lean/lake, and resource-gated schedules remain open
  or blocked. No release, push, or PR was performed.

## 2026-08-09T01:48:13Z — k=2 class-A closure and M14/M15 final verification

- Commands: focused `k=2` class-A and M14/M15 tests; full
  `python -m pytest -q`; PDF build and verification; YAML/JSON parse;
  governance audit and run deduplication.
- Environment: Windows PowerShell, Python 3.12 project environment,
  MiKTeX/pdfLaTeX; branch `campaign/gate13-closeout`, source commit
  `cbb6ddb0a050882249054f9044c905e442a561ab`.
- Outcome: **K2_CLASS_A_M14_M15_CLOSED_FULL_SUITE_GREEN**.
- Summary: closed the declared finite-dimensional real binary `k=2`
  class-level constant at `C_{2,A}^P(eta)=1` by matching the universal upper
  bound with the embedded repeated-law witness; corrected superseded current
  ledger formulations without deleting historical provenance.
- Validation: focused checks **18/18**; full suite **479/479 passed** in
  426.02s; three V5 PDFs rebuilt/audited; governance status `yellow`, 168
  historical runs, 9 unique instances, 8 duplicate groups, and 168 complete
  artifact contracts.
- Limitations: broader gated-planar repeated-law classes, same-law/gated k=3,
  arbitrary-tree sharpness, unbounded-tree uniformity, globally tight norms,
  novelty, human review, Lean/lake, and resource-gated schedules remain open
  or blocked. No release, push, or PR was performed.

This file is append-only. Each entry must be produced or reviewed after an
executed command and must include command, date, branch, commit, outcome,
changed paths, and limitations. Historical artifact runs remain under
`artifacts/runs/` and are not replaced by this summary.

## 2026-07-29 — governance bootstrap

- Command: repository inventory and governance bootstrap
- Branch/commit: `master` / `247de089a5fea826fa87f9b9e791c20a5a6fd1b6`
- Outcome: local contracts created; verification pending
- Changed paths: `AGENTS.md`, `.ai/`, `governance/`, `schemas/`, `src/seion_core/governance/`, tests and CLI integration
- Limitation: this entry records setup, not a claim that the full test or paper gates passed.

## 2026-07-29T13:02:42.140869+00:00 — governance and manuscript reconstruction

- Command: `python -m pytest -q; scripts/build_paper.ps1; scripts/build_companions.ps1; governance audit --json`
- Branch/commit: `master` / `247de089a5fea826fa87f9b9e791c20a5a6fd1b6`
- Outcome: **tests and PDF builds passed; non-strict audit passed yellow; strict release gate correctly failed closed**
- Summary: Implemented local SEION governance, durable memory, evidence controls, deduplicated run index, theorem-focused research paper, and software reproducibility companion.
- Validation: 23 tests passed; paper and companion PDF renders passed; audit yellow without errors
- Changed files:
  - `papers/foundations/main.tex`
  - `papers/software/main.tex`
  - `scripts/build_companions.ps1`
  - `governance/RESEARCH_SOFTWARE_SPLIT.yaml`
- Limitations:
  - The strict release gate remains blocked by B-0001 through B-0004; no mathematical novelty or universal claim is approved.
  - All external inspiration repositories remain outside the edit scope.

## 2026-07-29T13:03:05.869746+00:00 — final verification

- Command: `python -m pytest -q; python -m seion_core.cli.main governance audit --json`
- Branch/commit: `master` / `247de089a5fea826fa87f9b9e791c20a5a6fd1b6`
- Outcome: **24 tests passed; audit remains yellow and non-strict pass; release stays fail-closed**
- Summary: Completed final regression suite and refreshed the governance audit after building both manuscript tracks.
- Validation: python -m pytest -q: 24 passed
- Changed files:
  - `src/seion_core/cli/main.py`
  - `tests/governance/test_governance.py`
- Limitations:
  - Final audit reports 75 historical runs, 9 unique scientific instances, 8 duplicate groups, and 66 duplicate records.
  - Strict release remains blocked by B-0001 through B-0004.

## 2026-07-29T15:49:15.967635+00:00 — Research v2 structure-preserving reduction and reproducibility split

- Command: `python scripts/run_research_v2.py; python scripts/build_research_v2_tables.py; python scripts/build_research_v2_figures.py; latexmk; python -m pytest -q; python scripts/research_v2_audit.py`
- Branch/commit: `research/structure-preserving-reduction-v2` / `247de089a5fea826fa87f9b9e791c20a5a6fd1b6`
- Outcome: **COMPLETE_WITH_SCIENTIFIC_BLOCKERS**
- Summary: Built the v2 foundations draft, software companion, theorem/counterexample ledgers, prior-art matrix, registered experiment matrix, vector figures, tables, audits, and adversarial reviews. Kept legacy 0.1 outputs and historical runs separate.
- Validation: 39 pytest tests passed; 180/180 v2 runs complete; 100 unique scientific instances; 60/60 bound rows respected; max tightness 0.7100467992738069; five CPU/GPU parity rows with max abs error 1.4210854715202004e-14; latexmk builds foundations, draft, and software PDFs; rendered pages and figures visually inspected; v2 audit fail-closed.
- Changed files:
  - `papers/foundations_v2/`
  - `papers/software_v2/`
  - `src/seion_core/research_v2/`
  - `tests/research_v2/`
  - `claims/*_v2.*`
  - `artifacts/research_audit/v2_state.*`
- Limitations:
  - A theorem-level novelty claim has not been established; the foundations PDF remains draft/not for submission.
  - Verified author email and ORCID metadata are absent.
  - Legacy historical duplicate runs remain preserved and are not independent replicates.
  - Finite registered experiments do not support continuum, universal, or asymptotic claims.
  - Worktree was already dirty and remains dirty; no commit was created.

## 2026-07-29T15:54:40.001229+00:00 — Final research v2 rebuild and strict-gate verification

- Command: `powershell -ExecutionPolicy Bypass -File scripts/build_research_v2.ps1; python -m pytest -q; python -m seion_core.cli.main governance audit --json`
- Branch/commit: `research/structure-preserving-reduction-v2` / `247de089a5fea826fa87f9b9e791c20a5a6fd1b6`
- Outcome: **COMPLETE_WITH_SCIENTIFIC_BLOCKERS**
- Summary: Rebuilt the v2 matrix, vector figures, tables, foundations PDF, draft_not_for_submission PDF, software companion PDF, rendered-page set, and v2 audit from the single-command PowerShell workflow. Corrected degenerate-reference effect-size reporting and preserved the fail-closed novelty gate.
- Validation: single-command build exit 2 only because strict gate is intentionally blocked; 39 pytest tests passed; 180/180 runs complete; 100 unique instances; 60/60 bounds respected; max tightness 0.7100467992738069; max CPU/GPU error 1.4210854715202004e-14; all three PDFs compile with no fatal/layout/reference warnings; 36+ rendered PNG pages/previews inspected; v2 audit checks pass except blocker status.
- Changed files:
  - `scripts/build_research_v2.ps1`
  - `scripts/run_research_v2.py`
  - `scripts/research_v2_audit.py`
  - `README.md`
  - `.ai/`
  - `artifacts/index/research_v2_summary.csv`
- Limitations:
  - Theorem-level novelty remains unestablished; standard exact-reduction and spectral results are not claimed as new.
  - Verified author email and ORCID metadata remain absent.
  - The foundations PDF is draft/not for submission; no submission approval is asserted.
  - Legacy historical runs and duplicates remain preserved; the worktree remains dirty and no commit was created.

## 2026-07-29T18:13:56.026823+00:00 — Canonical v3 nodewise tree-constant execution

- Command: `powershell -ExecutionPolicy Bypass -File scripts/run_tree_constants_v3_full.ps1`, followed by post-canonical visual signoff and `python scripts/tree_constants_v3_audit.py audit`.
- Branch/commit: `research/nodewise-tree-constants-v3` / `b718f4e5178590d1f8b6a090fb696545eb3bfcd4`.
- Outcome: **TECHNICAL_AUDIT_PASS; FAIL_CLOSED_NOVELTY**.
- Validation: 69/69 tests passed including CUDA parity; 81,445 tree occurrences and 80,870 unique tree hashes enumerated; all A--I base blocks completed with 15,493 unique scientific instances and no duplicate scientific hashes; 1,530 leakage masks executed; 69 manifest outputs and 22 run artifacts hash-validated; theorem DAG has no cycles; maximum CPU/GPU absolute difference is `1.922112502494855e-08`; no negative theorem-bound margin was found.
- Publications: mathematical paper 31 pages and software companion 6 pages; 18 principal vector figures and eight topology atlases; 16 mandatory and one supplementary table; all 37 pages and the figure contact sheet visually inspected with matching PDF hashes.
- Release gate: 9/15 gates pass; result is `FAIL_CLOSED_NOVELTY`. The canonical command's nonzero terminal status is the mandated fail-closed publication status, not an interrupted pipeline.
- Changed paths: `src/seion_core/research_v3/`, `tests/research_v3/`, `scripts/*tree_constants_v3*`, `scripts/figures_v3/`, `claims/*_v3.*`, `experiments/matrices/tree_constants_v3*`, `papers/tree_stability_v3/`, `papers/software_v3/`, `artifacts/*v3*`, and `.ai/`.
- Limitations: fixed-eta sharpness and theorem-level novelty remain open; global certification is incomplete; only 4/460,800 extended optimizer trajectories and 0/8,400 extended performance cells are complete; there are no independent human reviews; the user-owned `.obsidian/workspace.json` change was preserved.

## 2026-07-29T18:16:20.089306+00:00 — SEION nodewise tree constants v3 full execution

- Command: `powershell -ExecutionPolicy Bypass -File scripts/run_tree_constants_v3_full.ps1`
- Branch/commit: `research/nodewise-tree-constants-v3` / `b718f4e5178590d1f8b6a090fb696545eb3bfcd4`
- Outcome: **TECHNICAL_AUDIT_PASS; FAIL_CLOSED_NOVELTY**
- Summary: Implemented and canonically executed the self-contained v3 governance, memory, mathematics, experiments, visualization, paper, and software system.
- Validation: 69 tests passed; 81445 tree occurrences; 80870 unique hashes; 15493 unique A-I instances; 37 PDF pages visually inspected; 9/15 release gates pass.
- Changed files:
  - `src/seion_core/research_v3`
  - `papers/tree_stability_v3`
  - `papers/software_v3`
  - `artifacts/research_v3`
- Limitations:
  - Fixed-eta sharpness, theorem-level novelty, complete independent certification, the extended matrix, and independent human review remain unresolved.
  - The pre-existing .obsidian/workspace.json change was preserved and no external repository was edited.

## 2026-08-08T09:34:44.299483+00:00 — Projected-tree theory v4 P0 baseline and truth ledger

- Command: `python research/math_closure/k3/certificates/chain_and_branching_closed_forms.py`
- Branch/commit: `campaign/gate13-closeout` / `c491c032579b9239f2c7216801d174f86c11c4de`
- Outcome: **P0_COMPLETE_BASELINE_REPRODUCED**
- Summary: Reproduced the current projected-tree mathematical baseline and created an epistemically separated truth ledger without modifying Gate 13.5 or Gate 14 artifacts.
- Validation: 30 research_v3 tests passed; k2 exact construction passed; k3 closed-form construction passed; governance audit passed yellow; run deduplication completed.
- Changed files:
  - `research/projected_trees_v4/truth_ledger/PROJECTED_TREES_TRUTH_LEDGER.md`
  - `research/projected_trees_v4/truth_ledger/PROJECTED_TREES_TRUTH_LEDGER.json`
  - `.ai/TASKS.md`
- Limitations:
  - Fixed-eta sharpness, DAG-native certificates, cancellation-aware constants, and theorem-level novelty remain open.

## 2026-08-08T09:40:54.488028+00:00 — Projected-tree theory v4 P1-P5 equality, sharpness, dimension/rank, topology, and DAG scalar certificate

- Command: `python research/math_closure/k3/certificates/chain_and_branching_closed_forms.py`
- Branch/commit: `campaign/gate13-closeout` / `c491c032579b9239f2c7216801d174f86c11c4de`
- Outcome: **P1_P5_SCOPED_PROGRESS**
- Summary: Audited equality/slack conditions, formalized restricted k2/k3 sharpness and dimension/rank boundaries, and implemented/tested a scalar DAG-native source-resolved certificate without changing historical KGE/Gate14 evidence.
- Validation: 34 tests passed across research_v3 and research_v4; k2 and k3 exact scripts passed; governance audit passed yellow; deduplication completed.
- Changed files:
  - `src/seion_core/research_v4/equality_slack.py`
  - `src/seion_core/research_v4/dag_certificate.py`
  - `tests/research_v4/test_frontier.py`
  - `research/projected_trees_v4`
  - `.ai/TASKS.md`
- Limitations:
  - General fixed-eta sharpness, universal dimension/rank reduction, correlation-aware/cancellation-aware DAG certificates, and theorem-level novelty remain open.

## 2026-08-08T09:51:57.064230+00:00 — Projected-tree theory v4 P6A first-order source-aware vector DAG and P7A signed-source certificate

- Command: `python -m pytest tests/research_v3 tests/research_v4 -q; python research/math_closure/k2/exact_examples/chain_gated_rotation_eta_squared.py; python research/math_closure/k3/certificates/chain_and_branching_closed_forms.py; python -m seion_core.cli.main governance audit --json; python -m seion_core.cli.main governance dedupe-runs`
- Branch/commit: `campaign/gate13-closeout` / `c491c032579b9239f2c7216801d174f86c11c4de`
- Outcome: **P6A_P7A_SCOPED_PROGRESS**
- Summary: Implemented and tested first-order source-aware vector DAG propagation and signed source aggregation with strict cancellation witnesses; P1-P5 and historical Gate evidence preserved.
- Validation: python -m pytest tests/research_v3 tests/research_v4 -q => 40 passed; k2 exact construction PASS; k3 chain/branching exact constructions PASS; governance audit passed yellow; JSON validation and git diff --check passed
- Changed files:
  - `src/seion_core/research_v4/source_aware_dag.py`
  - `src/seion_core/research_v4/signed_certificate.py`
  - `src/seion_core/research_v4/__init__.py`
  - `tests/research_v4/test_source_aware.py`
  - `research/projected_trees_v4/dag/source_aware/proof/P6A_first_order_source_aware.md`
  - `research/projected_trees_v4/dag/source_aware/P6A_status.md`
  - `research/projected_trees_v4/dag/source_aware/P6A_first_order_status.json`
  - `research/projected_trees_v4/cancellation/associator/P7A_signed_source_certificate.md`
  - `research/projected_trees_v4/cancellation/associator/P7A_status.json`
  - `research/projected_trees_v4/truth_ledger/PROJECTED_TREES_TRUTH_LEDGER.md`
  - `research/projected_trees_v4/truth_ledger/PROJECTED_TREES_TRUTH_LEDGER.json`
  - `.ai/TASKS.md`
- Limitations:
  - P6A/P7A are first-order source-linear results; higher-order source polynomials, nonlinear associator constants, universal sharpness, and theorem-level novelty remain open.
  - The worktree remains dirty and no commit or push was requested.

## 2026-08-08T10:05:14.183167+00:00 — Projected-tree theory v4 D1 P6B exact higher-order source polynomial

- Command: `python -m pytest tests/research_v3 tests/research_v4 -q; python -m seion_core.cli.main governance audit --json; python -m seion_core.cli.main governance dedupe-runs`
- Branch/commit: `campaign/gate13-closeout` / `9adc7aa2b6d91944f3aa2573531107b871cbf658`
- Outcome: **D1_P6B_COMPLETE_P7B_P8_DEFERRED**
- Summary: Implemented exact finite higher-order source provenance on multilinear DAGs using source multi-indices, repeated-source convolution, recursive reference agreement, and certified finite truncation bounds for orders 1–3.
- Validation: python -m pytest tests/research_v3 tests/research_v4 -q => 47 passed; JSON validation PASS; git diff --check PASS; P1-P7A freeze commit aba0b13 preserved; P6B implementation commits 8b3341f and 9adc7aa
- Changed files:
  - `src/seion_core/research_v4/higher_order_source_polynomial.py`
  - `tests/research_v4/test_higher_order_source_polynomial.py`
  - `research/projected_trees_v4/dag/source_aware/proof/P6B_exact_source_polynomial.md`
  - `research/projected_trees_v4/dag/source_aware/P6B_status.json`
  - `research/projected_trees_v4/truth_ledger/PROJECTED_TREES_TRUTH_LEDGER.json`
  - `research/projected_trees_v4/truth_ledger/PROJECTED_TREES_TRUTH_LEDGER.md`
  - `.ai/TASKS.md`
- Limitations:
  - P6B is exact for finite declared numeric DAGs with fixed source directions and formal scalar amplitudes; scalable tail envelopes, nonlinear signed associator P7B, validated norms P8, and global sharpness remain open.
  - No Gate 13.5/Gate 14/KGR artifacts were modified.

## 2026-08-08T10:12:34.960315+00:00 — Projected-tree theory v4 D2 P7B nonlinear signed source-polynomial certificate

- Command: `python -m pytest tests/research_v3 tests/research_v4 -q; python -m seion_core.cli.main governance audit --json; python -m seion_core.cli.main governance dedupe-runs`
- Branch/commit: `campaign/gate13-closeout` / `26345c1aaa5231accca852c6e208492ee8fcb74f`
- Outcome: **D2_P7B_COMPLETE_P7C_P8_DEFERRED**
- Summary: Implemented generic nonlinear signed source-polynomial aggregation over P6B multi-indices, with exact and truncated certified bounds, higher-order cancellation witnesses, projected-root semantics, and direct-evaluation validation.
- Validation: python -m pytest tests/research_v3 tests/research_v4 -q => 53 passed; JSON validation PASS; git diff --check PASS; P7B commits 5c12adb and 26345c1
- Changed files:
  - `src/seion_core/research_v4/signed_source_polynomial.py`
  - `tests/research_v4/test_signed_source_polynomial.py`
  - `research/projected_trees_v4/cancellation/associator/P7B_nonlinear_signed_source_polynomial.md`
  - `research/projected_trees_v4/cancellation/associator/P7B_status.json`
  - `research/projected_trees_v4/truth_ledger/PROJECTED_TREES_TRUTH_LEDGER.json`
  - `research/projected_trees_v4/truth_ledger/PROJECTED_TREES_TRUTH_LEDGER.md`
  - `.ai/TASKS.md`
- Limitations:
  - P7B is sound for finite signed expressions over exact finite P6B polynomials; P7C identity instantiations, universal nonlinear sharpness, validated norms, and approximate-law error remain open.
  - Gate 13.5, Gate 14, KGR, and historical artifacts were not modified.

## 2026-08-08T10:19:51.747702+00:00 — Projected-tree theory v4 P7C generic signed compositional expressions

- Command: `python -m pytest tests/research_v3 tests/research_v4 -q; python -m seion_core.cli.main governance audit --json; python -m seion_core.cli.main governance dedupe-runs`
- Branch/commit: `campaign/gate13-closeout` / `51687822e03e542c29881ac907ec562480f716be`
- Outcome: **P7C_COMPLETE_P8_DEFERRED**
- Summary: Frozen a single generic signed compositional-expression engine over P6B/P7B source polynomials, with associator regression, Jacobiator certificate, and Filippov-defect certificate under explicit conventions and conservative truncation.
- Validation: python -m pytest tests/research_v3 tests/research_v4 -q => 59 passed; JSON validation PASS; git diff --check PASS; P7C commits c7300be and 5168782
- Changed files:
  - `src/seion_core/research_v4/signed_compositional_expression.py`
  - `tests/research_v4/test_signed_compositional_expression.py`
  - `research/projected_trees_v4/cancellation/P7C_generic_signed_compositional_expression.md`
  - `research/projected_trees_v4/cancellation/P7C_status.json`
  - `research/projected_trees_v4/truth_ledger/PROJECTED_TREES_TRUTH_LEDGER.json`
  - `research/projected_trees_v4/truth_ledger/PROJECTED_TREES_TRUTH_LEDGER.md`
  - `.ai/TASKS.md`
- Limitations:
  - P7C certifies calculated defects under explicit conventions; it does not prove universal Jacobi or Filippov identity satisfaction, nonlinear sharpness, validated norms, or approximate-law bounds.
  - P8 and sharpness remain deferred; Gate 13.5, Gate 14, KGR, and historical artifacts were not modified.

## 2026-08-08T10:28:39.622823+00:00 — Projected-tree theory v4 completion package P8 P10 topology and extremal registry

- Command: `python -m pytest tests/research_v3 tests/research_v4 -q; python -m seion_core.cli.main governance audit --json; python -m seion_core.cli.main governance dedupe-runs`
- Branch/commit: `campaign/gate13-closeout` / `1f4984ec8e741049789e0035c7a3ba84c86d3f29`
- Outcome: **FINITE_SCOPE_COMPLETE_GLOBAL_THEOREMS_OPEN**
- Summary: Completed all remaining finite-scope implementation work: validated norm enclosures, sound certificate selector, separated approximate-law budget, topology metrics, and monotone sharpness bands. Global sharpness and universal spectral optima remain explicitly open.
- Validation: python -m pytest tests/research_v3 tests/research_v4 -q => 68 passed; all research_projected_trees JSON parsed; git diff --check PASS; completion commits 1f3303d and 1f4984e
- Changed files:
  - `src/seion_core/research_v4/operator_norm_enclosures.py`
  - `src/seion_core/research_v4/certificate_selector.py`
  - `src/seion_core/research_v4/approximate_law_error.py`
  - `src/seion_core/research_v4/topology_registry.py`
  - `src/seion_core/research_v4/extremal_registry.py`
  - `tests/research_v4/test_p8_p10_registry.py`
  - `tests/research_v4/test_extremal_registry.py`
  - `research/projected_trees_v4/norms/P8_validated_norms.md`
  - `research/projected_trees_v4/approximation/P10_approximate_law_error.md`
  - `research/projected_trees_v4/sharpness/extremal_registry.json`
  - `research/projected_trees_v4/truth_ledger/PROJECTED_TREES_TRUTH_LEDGER.json`
  - `.ai/TASKS.md`
- Limitations:
  - Finite-scope P8/P10 and registry work is complete; global fixed-eta sharpness, universal dimension/rank reduction, globally tight multilinear spectral norms, and theorem-level novelty remain open.
  - Gate 13.5, Gate 14, KGR, and historical artifacts were not modified.

## 2026-08-08T10:45:35.394842+00:00 — Projected-graphs V5 finite-core freeze and k2 independent-law sharpness

- Command: `python -m pytest tests/research_v3 tests/research_v4 tests/research_v5_test_k2_sharpness.py tests/research_v5_test_equality_conditions.py -q; python -m seion_core.cli.main governance audit --json; python -m seion_core.cli.main governance dedupe-runs`
- Branch/commit: `campaign/gate13-closeout` / `773fa9c4d4d3d77f3a52cf7e1adf5a0dc781ff05`
- Outcome: **PASS_WITH_KNOWN_GOVERNANCE_WARNINGS**
- Summary: Frozen finite projected-graph core and registered V5 theorem-level k2 independent-law saturation package.
- Validation: 77 pytest tests passed; git diff --check clean before generated governance outputs; governance audit passed with 0 missing required artifacts; V5 ledger and theorem registry updated.
- Changed files:
  - `claims/theorem_registry_v5.yaml`
  - `research/projected_trees_v5`
  - `src/seion_core/research_v5`
  - `tests/research_v5_test_k2_sharpness.py`
  - `tests/research_v5_test_equality_conditions.py`
- Limitations:
  - This proves the declared independent-law real binary k=2 class only; repeated-law sharpness, universal dimension/rank reduction, global k=3 sharpness, theorem-level novelty, and independent human review remain open. No Gate13.5, Gate14, KGR, or historical artifacts were modified.

## 2026-08-08T10:54:48.436514+00:00 — Projected-graphs V5-A independent-law k3 lower witnesses

- Command: `python -m pytest tests/research_v3 tests/research_v4 tests/research_v5_test_k2_sharpness.py tests/research_v5_test_equality_conditions.py tests/research_v5_test_k3_independent_candidates.py -q; python -m seion_core.cli.main governance audit --json; python -m seion_core.cli.main governance dedupe-runs`
- Branch/commit: `campaign/gate13-closeout` / `997e745265cad8131e3122f192ce373c79ae57e4`
- Outcome: **LOWER_BOUNDS_CERTIFIED_GLOBAL_SHARPNESS_OPEN**
- Summary: Added analytic lower-bound witnesses for independent-law k3 binary chain and branching topologies; recorded repeated-law band and finite-tree sharpness conjecture as open.
- Validation: 85 pytest tests passed; git diff --check clean before generated governance outputs; JSON validation passed; governance audit passed with 0 missing required artifacts; deduplicated run index regenerated.
- Changed files:
  - `src/seion_core/research_v5/k3_independent_candidates.py`
  - `tests/research_v5_test_k3_independent_candidates.py`
  - `claims/theorem_registry_v5.yaml`
  - `research/projected_trees_v5`
  - `.ai/TASKS.md`
- Limitations:
  - The k3 results are certified construction lower bounds only; independent-law global sharpness, repeated-law k2 sharpness, finite-tree induction, dimension/rank reduction, theorem-level novelty, and independent human review remain open. Gate13.5, Gate14, KGR, and historical artifacts were not modified.

## 2026-08-08T11:21:32.373674+00:00 — V5-B extremal tightening

- Command: `python -m seion_core.cli.main governance dedupe-runs`
- Branch/commit: `campaign/gate13-closeout` / `d26b4b0462611050c3274ee9cd367e7e3e0d26a9`
- Outcome: **PARTIAL_COMPLETION**
- Summary: Implemented exact scalar V5-A k=3 optimization, certified piecewise lower curve and eta->0 asymptotic sharpness; added exact same-map repeated-law k=2 saturation; fixed-eta global k=3 upper bound and gated-planar repeated-law sharpness remain open.
- Validation: full pytest timed out at 120s; heavy V3 exact/adversarial/GPU segments not completed
- Changed files:
  - `src/seion_core/research_v5/v5b_extremal.py`
  - `src/seion_core/research_v5/k2_sharpness.py`
  - `tests/research_v5_test_v5b_extremal.py`
  - `tests/research_v5_test_k2_sharpness.py`
  - `claims/theorem_registry_v5.yaml`
  - `research/projected_trees_v5/V5_STATUS.json`
  - `research/projected_trees_v5/truth_ledger/PROJECTED_GRAPHS_V5_TRUTH_LEDGER.md`
  - `research/projected_trees_v5/truth_ledger/PROJECTED_GRAPHS_V5_TRUTH_LEDGER.json`
  - `research/projected_trees_v5/extremal/V5B_EXTREMAL_STATUS.md`
  - `artifacts/research_v5/v5b_extremal_analysis.json`
- Limitations:
  - The conditional k=3 scalar upper envelope is not a global theorem until the reduction inequalities are proved.
  - Gated-planar repeated-law subclass remains open.

## 2026-08-08T19:56:01.068976Z — V5 theorem-closure campaign (M8/M9)

- Command: `python -m pytest -q --durations=15` (full suite); `python -m seion_core.cli.main governance audit`; `python -m seion_core.cli.main governance dedupe-runs`
- Branch/commit: `campaign/gate13-closeout` / `b817624b5a9be5c6f1c0d0df859d56fb4c655671`
- Outcome: **EXTREMAL_PROGRAM_PARTIALLY_CLOSED**
- Summary: Proved a necessary-and-sufficient saturation characterization for the k=2 chain (M8; EQ1-EQ3, arbitrary dimension/rank, independent or repeated laws), and an unconditional tightened k=3 upper envelope U_3(eta) for chain and branching topologies (M9), superseding the prior unproved, dimensionally inconsistent conditional-scalar-reduction bookkeeping entry. Fixed a stale K2-EQ-05 audit status in `equality_conditions.py`. Fixed-eta k=3 sharpness gap narrowed (relative gap 50%->29% at eta=1) but remains open. Full closure accounting in `research/projected_trees_v5/V5_CLOSURE_REPORT.md`.
- Validation: full pytest suite executed (not partitioned, no timeout): 365 collected, 365 executed, 364 passed, 1 failed, 444.13s elapsed. The one failure (`tests/kgr/test_campaign_negative_controls.py::test_queried_edge_leakage_inflates_metrics_when_deliberately_enabled`) is pre-existing (last touched commit `49e4bfc`, 2026-08-01), lives entirely in the Gate12/KGR track, and was left unmodified per the mission's explicit preserve-KGR instruction. Governance audit passed yellow (same two pre-existing warnings: duplicate_runs_detected, paper_not_release_ready). Lean 4/`lake` not installed on this machine; formal verification (mission Phase 11) is `BLOCKED_BY_MISSING_TOOLING`, not attempted.
- Changed files:
  - `research/math_closure/k2/saturation_iff_theorem.tex`
  - `research/math_closure/k3/general_upper_envelope.tex`
  - `research/math_closure/status_registry.yaml`
  - `src/seion_core/research_v5/k2_characterization.py`
  - `src/seion_core/research_v5/k3_upper_bound.py`
  - `src/seion_core/research_v5/equality_conditions.py`
  - `tests/research_v5_test_k2_characterization.py`
  - `tests/research_v5_test_k3_upper_bound.py`
  - `tests/research_v5_test_equality_conditions.py`
  - `scripts/verify_k3_bound.py`
  - `claims/theorem_registry_v5.yaml`
  - `research/projected_trees_v5/V5_STATUS.json`
  - `research/projected_trees_v5/extremal/V5B_EXTREMAL_STATUS.md`
  - `research/projected_trees_v5/truth_ledger/PROJECTED_GRAPHS_V5_TRUTH_LEDGER.md`
  - `research/projected_trees_v5/V5_CLOSURE_REPORT.md`
  - `research/projected_trees_v5/V5_CLOSURE_REPORT.json`
- Limitations:
  - Fixed-eta k=3 global sharpness remains open (gap narrowed, not closed).
  - The large majority of the mission brief's 16 phases were not attempted this session (gated-planar exact extremal, dimension/rank reduction theorem, arbitrary-tree conjecture, signed-forest exact constants, source-calculus consolidation, growing-tree theorem, P8/P10 hardening, novelty audit, manuscript rebuild, application theorem, clean-room package, external review package) -- see `research/projected_trees_v5/V5_CLOSURE_REPORT.md` for the full accounting.
  - No theorem-level novelty or independent human review performed; every new result carries `approval_status: PENDING_HUMAN_REVIEW`.
  - Gate13.5, Gate14, KGR, and historical artifacts were not modified. No push, no PR.

## 2026-08-08T21:05:03.952610Z — External review corrections to M8/M10

- Command: `python -m pytest -q` (full suite, no partitioning)
- Branch/commit: `campaign/gate13-closeout` / `9c8e755866684194bc09b4a51db34466fe01790c`
- Outcome: **EXTREMAL_PROGRAM_PARTIALLY_CLOSED** (unchanged label; corrects, does not add, mathematical claims)
- Summary: An external review of the M8/M9/M10 write-ups found two real, concrete errors. M8: the theorem and final formula were correct, but the .tex proof's intermediate line wrongly claimed F_out-R_out=mu_out(D,d) directly (missing a (I-P_out)mu_out(R_in,d) term that only vanishes after P_out is applied) -- fixed; also expanded M9's previously-terse branching-topology section into an explicit derivation. M10: (1) Step 1's claim "S1 perp S2" did not follow from the cited lemma for an arbitrary projector -- repaired with a projector-independent self-adjointness/contradiction argument, verified across 20,000 random trials; (2) the conclusion invalidly inferred the strict supremum inequality C_3,ind^P(eta) < U_3(eta) from mere non-attainment (a supremum can be approached without being attained) -- downgraded epistemic_status PROVED -> PROVED_NON_ATTAINMENT throughout every registry, and the strict-gap question is now a separate, explicitly open item (OPEN_V5_K3_STRICT_SUPREMUM_GAP). A correction record is in V5_CLOSURE_REPORT.md/.json.
- Validation: full pytest suite, no timeout: 450 collected, 450 executed, 449 passed, 1 pre-existing out-of-scope KGR failure (same one, unmodified), 457.36s elapsed.
- Changed files:
  - `research/math_closure/k2/saturation_iff_theorem.tex`
  - `research/math_closure/k3/general_upper_envelope.tex`
  - `research/math_closure/k3/m10_non_sharpness_of_m9.tex`
  - `research/math_closure/status_registry.yaml`
  - `src/seion_core/research_v5/k3_non_sharpness.py`
  - `tests/research_v5_test_k3_non_sharpness.py`
  - `claims/theorem_registry_v5.yaml`
  - `research/projected_trees_v5/V5_STATUS.json`
  - `research/projected_trees_v5/truth_ledger/PROJECTED_GRAPHS_V5_TRUTH_LEDGER.md`
  - `research/projected_trees_v5/V5_CLOSURE_REPORT.md`
  - `research/projected_trees_v5/V5_CLOSURE_REPORT.json`
- Limitations:
  - Whether C_3,ind^P(eta) is strictly below U_3(eta) (vs. equal to it as an unattained supremum) remains genuinely open -- M10 does not resolve this, only non-attainment pointwise.
  - No other section of the 12-point follow-up list was attempted this pass; this was purely a correctness pass on the prior session's own claims.
  - Gate13.5, Gate14, KGR, and historical artifacts were not modified. No push, no PR.

## 2026-08-08T20:38:04.673628Z — M10 non-sharpness proof and pytest discovery fix

- Command: `python -m pytest --collect-only -q`; `python -m pytest -q` (full suite, no partitioning)
- Branch/commit: `campaign/gate13-closeout` / `23a2b1a21e78f9dd4cd7f089c492a4c0625043ab`
- Outcome: **EXTREMAL_PROGRAM_PARTIALLY_CLOSED** (unchanged label; M10 strengthens the k=3 gap, does not close it)
- Summary: Derived the equality conditions of M9's k=3 upper envelope by hand and proved they cannot be simultaneously satisfied -- U_3(eta) is not attained, C_3,ind^P(eta) < U_3(eta) strictly for every eta in (0,1) (M10). Proof: a standard operator-norm-attaining-direction lemma applied twice (node 2, then node 3) forces the two propagated-error terms orthogonal whenever both individually saturate, contradicting the triangle-inequality equality M9's derivation needs. Does not produce a replacement tightened value; the joint (magnitude, angle) trade-off optimization is set up (`pareto_frontier_two_direction_norm_budget`) but not solved. A separate gradient-based numerical search was attempted and discarded as unreliable (failed to recover the already-known L_3(eta) witness). Also fixed a real, repo-wide bug found in the course of honest test accounting: `pyproject.toml` had no `python_files` override, so pytest's default discovery silently excluded every `research_v5_test_*.py` file (7 files, 72 tests, present since prior sessions) from plain `pytest -q` runs -- fixed with a one-line config addition.
- Validation: `pytest --collect-only -q` now reports 437 tests (was 365 before the fix). Full suite: 437 collected, 437 executed, 436 passed, 1 pre-existing out-of-scope KGR failure (same one as the prior entry, unchanged, unmodified), 468.51s elapsed, no timeout, no skips.
- Changed files:
  - `pyproject.toml`
  - `research/math_closure/k2/saturation_iff_theorem.tex` (added non-saturating example)
  - `research/math_closure/k3/m10_non_sharpness_of_m9.tex`
  - `research/math_closure/status_registry.yaml`
  - `src/seion_core/research_v5/k3_non_sharpness.py`
  - `tests/research_v5_test_k3_non_sharpness.py`
  - `claims/theorem_registry_v5.yaml`
  - `research/projected_trees_v5/V5_STATUS.json`
  - `research/projected_trees_v5/truth_ledger/PROJECTED_GRAPHS_V5_TRUTH_LEDGER.md`
  - `research/projected_trees_v5/V5_CLOSURE_REPORT.md`
  - `research/projected_trees_v5/V5_CLOSURE_REPORT.json`
- Limitations:
  - Fixed-eta k=3 global sharpness remains open; M10 narrows what "open" means (U_3 provably unreachable) but does not supply the true value.
  - Points 3-12 of the user's own follow-up priority list (gated-planar exact optimum, dimension/rank reduction, arbitrary-tree/same-law k=3 conjectures, signed-forest exact constants, source-calculus consolidation, growing-tree theorem, formal verification, novelty audit, human review, manuscript rebuild) were not attempted this pass.
  - Gate13.5, Gate14, KGR, and historical artifacts were not modified. No push, no PR.

## 2026-08-08T22:25:19.218645Z — Projected-graphs V5 completion pass

- Commands: bounded context compilation; YAML/JSON parse validation; focused
  V5 pytest command; `scripts/build_projected_graphs_v5_papers.ps1`;
  `scripts/verify_projected_graphs_v5_papers.ps1`; governance audit and run
  deduplication; `git diff --check`.
- Environment: Windows PowerShell, Python project environment, MiKTeX/pdfLaTeX;
  branch `campaign/gate13-closeout`, source commit
  `cbb6ddb0a050882249054f9044c905e442a561ab`.
- Outcome: **INTERNAL_COMPLETION_WITH_EXTERNAL_BLOCKERS**.
- Summary: Added the weighted-summability growing-tree theorem, updated the
  V5 status/task records, added a bounded novelty-audit record and references,
  rebuilt and render-audited the mathematical, source-calculus, and software
  manuscripts, and prepared
  `research/projected_trees_v5/review/REVIEW_PACKET_2026-08-08.md`.
- Validation: YAML/JSON parsing passed; 85 focused V5 tests passed; a fresh
  full `python -m pytest -q` run completed with 450 collected, 449 passed,
  and 1 pre-existing out-of-scope KGR negative-control failure in 431.87s;
  all three V5 PDFs rendered and audited; governance audit passed yellow in
  non-strict mode; the final audit found 157 historical runs, 9 unique
  scientific instances, 8 duplicate groups, and 157 complete artifact
  contracts; the deduplicated run index was regenerated.
- Changed areas: `.ai/` postflight/task/evidence records; governance-derived
  run indexes; V5 mathematical and software paper sources and PDFs; theorem
  status and task registries; growing-tree theorem; novelty audit and
  bibliography; independent-review packet.
- Limitations: exact fixed-eta k=3 value, strict supremum gap, gated-planar
  repeated-law sharpness, dimension/rank reduction, arbitrary-tree/topology
  sharpness, globally tight norms, novelty, human review, Lean/lake, and
  resource-gated V3 schedules remain open or blocked. No Gate13.5, Gate14,
  KGR, historical artifacts, push, or PR were modified.

## 2026-08-08T22:52:22.350205Z — M10b compactness refinement and full-suite repair

- Commands: bounded M10b proof/registry edits; focused theorem and KGR tests;
  `scripts/build_projected_graphs_v5_papers.ps1`;
  `scripts/verify_projected_graphs_v5_papers.ps1`; full `python -m pytest -q`;
  YAML/JSON parsing; `git diff --check`; governance audit and run
  deduplication.
- Environment: Windows PowerShell, Python project environment, MiKTeX/pdfLaTeX;
  branch `campaign/gate13-closeout`, source commit
  `cbb6ddb0a050882249054f9044c905e442a561ab`.
- Outcome: **FINITE_FIXED_CLASS_GAP_CLOSED_FULL_SUITE_GREEN**.
- Summary: Added the compactness-based M10b theorem and its scope boundary;
  clarified the declared gated-planar exact value versus the broader open
  subclass; corrected stale V5 truth-ledger entries; and updated the KGR
  leakage negative control for the context-aware evaluator signature.
- Validation: full suite **450/450 passed** in 418.75s; focused checks passed;
  registries parsed; all three V5 PDFs rebuilt, rendered, and audited;
  governance audit passed yellow with no missing required files.
- Current evidence after the new run: 158 historical runs, 9 unique
  scientific instances, 8 duplicate groups, and 158 complete artifact
  contracts.
- Limitations: M10b is not uniform over dimensions/ranks; global fixed-eta
  k=3 sharpness, arbitrary-tree/topology sharpness, globally tight norms,
  novelty, independent human review, Lean/lake, and resource-gated schedules
  remain open or blocked. No Gate13.5, Gate14, historical artifacts, push, or
  PR were modified.

## 2026-08-08T23:04:34.617999Z — Restricted Jacobiator theorem and full-suite expansion

- Commands: exact restricted-Jacobiator script; focused signed-identity tests;
  registry parsing; `git diff --check`; full `python -m pytest -q`;
  `scripts/build_projected_graphs_v5_papers.ps1`;
  `scripts/verify_projected_graphs_v5_papers.ps1`; governance audit and run
  deduplication.
- Environment: Windows PowerShell, Python project environment, MiKTeX/pdfLaTeX;
  branch `campaign/gate13-closeout`, source commit
  `cbb6ddb0a050882249054f9044c905e442a561ab`.
- Outcome: **RESTRICTED_SIGNED_IDENTITY_CLOSED_FULL_SUITE_GREEN**.
- Summary: Proved and registered exact zero projected error for the declared
  gated-planar rotation Jacobiator class, added symbolic evaluator coverage,
  and explicitly retained the generic-law extremal problem as open.
- Validation: full suite **451/451 passed** in 405.87s; exact script and
  focused tests passed; registries parsed; all three V5 PDFs rendered and
  audited; governance audit passed yellow with no missing required files.
- Current evidence after the new run: 159 historical runs, 9 unique
  scientific instances, 8 duplicate groups, and 159 complete artifact
  contracts.
- Limitations: generic signed-forest constants, global fixed-eta k=3,
  dimension/rank-uniform bounds, arbitrary-tree/topology sharpness, globally
  tight norms, novelty, human review, Lean/lake, and resource-gated schedules
  remain open or blocked. No Gate13.5, Gate14, historical artifacts, push, or
  PR were modified.

## 2026-08-08T23:17:28Z — All-finite-k left-comb gated-rotation formula

- Commands: exact all-k gated-rotation script; focused all-k test; full
  `python -m pytest -q`; PDF build/verify scripts; YAML/JSON parse;
  `git diff --check`; governance audit and run deduplication.
- Environment: Windows PowerShell, Python project environment, MiKTeX/pdfLaTeX;
  branch `campaign/gate13-closeout`, source commit
  `cbb6ddb0a050882249054f9044c905e442a561ab`.
- Outcome: **ALL_FINITE_K_LEFT_COMB_RESTRICTED_FORMULA_CLOSED_FULL_SUITE_GREEN**.
- Summary: proved and registered the exact Chebyshev formula for every finite
  left-comb chain under the declared gated-planar rotation law, while keeping
  global extremal and non-left-comb questions open.
- Validation: full suite **452/452 passed** in 409.83s; exact script and
  focused test passed; registries parsed; all three V5 PDFs rendered/audited;
  governance audit passed yellow with no missing required files.
- Current evidence: 160 historical runs, 9 unique scientific instances,
  8 duplicate groups, and 160 complete artifact contracts.
- Limitations: global fixed-eta k=3, dimension/rank-uniform reduction,
  arbitrary-tree/topology sharpness, generic signed constants, global norm
  sharpness, novelty, human review, Lean/lake, and resource-gated schedules
  remain open or blocked. No Gate13.5, Gate14, historical artifacts, push,
  or PR were modified.

## 2026-08-08T23:44:28Z — Topology-wide and variable-arity gated-rotation closure

- Commands: exact full-binary and general-arity scripts; focused tests; full
  `python -m pytest -q`; PDF verification; YAML/JSON parse; `git diff --check`;
  governance audit and run deduplication.
- Environment: Windows PowerShell, Python project environment, MiKTeX/pdfLaTeX;
  branch `campaign/gate13-closeout`, source commit
  `cbb6ddb0a050882249054f9044c905e442a561ab`.
- Outcome: **TOPOLOGY_WIDE_RESTRICTED_GATED_ROTATION_CLOSED_FULL_SUITE_GREEN**.
- Summary: proved and registered the exact recursive projected-error formula
  for every finite ordered full-binary topology and its arity-compatible
  extension to every finite ordered rooted tree with arity at least two.
- Validation: full suite **454/454 passed** in 437.57s; exact scripts and
  focused tests passed; registries parsed; all three V5 PDFs rendered/audited;
  governance audit passed yellow with no missing required files.
- Current evidence: 162 historical runs, 9 unique scientific instances,
  8 duplicate groups, and 162 complete artifact contracts.
- Limitations: global independent-law fixed-eta sharpness, dimension/rank-
  uniform reduction, arbitrary-law constants, generic signed constants,
  global norm sharpness, novelty, human review, Lean/lake, and resource-gated
  schedules remain open or blocked. No Gate13.5, Gate14, historical artifacts,
  push, or PR were modified.

## 2026-08-09T00:01:58Z — M11 conditional quantitative k=3 gap

- Commands: exact M11 script; focused M11 test; full `python -m pytest -q`;
  PDF verification; YAML/JSON parse; `git diff --check`; governance audit
  and run deduplication.
- Environment: Windows PowerShell, Python project environment, MiKTeX/pdfLaTeX;
  branch `campaign/gate13-closeout`, source commit
  `cbb6ddb0a050882249054f9044c905e442a561ab`.
- Outcome: **M11_CONDITIONAL_K3_GAP_CLOSED_FULL_SUITE_GREEN**.
- Summary: derived the explicit angle–magnitude bound under exact
  first-propagator saturation and retained the unrestricted fixed-eta
  supremum as open.
- Validation: full suite **455/455 passed** in 442.90s; exact script and
  focused test passed; registries parsed; all three V5 PDFs rendered/audited;
  governance audit passed yellow with no missing required files.
- Current evidence: 163 historical runs, 9 unique scientific instances,
  8 duplicate groups, and 163 complete artifact contracts.
- Limitations: global fixed-eta k=3, dimension/rank-uniform reduction,
  arbitrary-law sharpness, generic signed constants, global norm sharpness,
  novelty, human review, Lean/lake, and resource-gated schedules remain open
  or blocked. No Gate13.5, Gate14, historical artifacts, push, or PR were
  modified.

## 2026-08-09T01:26:56Z — M14/M15 exact independent-law k=3 constants

- Commands: M14/M15 scripts and focused tests; regression tests; full
  `python -m pytest -q`; paper build and PDF verification; YAML/JSON parse;
  `git diff --check`; governance audit and run deduplication.
- Environment: Windows PowerShell, Python 3.12 project environment,
  MiKTeX/pdfLaTeX; branch `campaign/gate13-closeout`, source commit
  `cbb6ddb0a050882249054f9044c905e442a561ab`.
- Outcome: **M14_M15_EXACT_INDEPENDENT_K3_CONSTANTS_CLOSED_FULL_SUITE_GREEN**.
- Summary: M14 attains the M13 chain envelope; M15 proves and attains the
  same branching envelope using scalarization and nuclear/operator-norm
  duality. Both independent-law binary `k=3` constants equal `W_3(eta)`.
- Validation: full suite **478/478 passed** in 416.33s; all three V5 PDFs
  rebuilt and audited; governance audit passed yellow with no missing files;
  167 historical runs, 9 unique instances, 8 duplicate groups, and 167
  complete artifact contracts.
- Remaining boundary: same-law/gated subclasses, arbitrary-tree sharpness,
  globally tight norms, novelty, human review, Lean/lake, and resource-gated
  schedules. No release, push, or PR.

## 2026-08-09T01:00:23Z — M13 unconditional chain quantitative envelope

- Commands: M13 focused script/test; focused regression tests; full
  `python -m pytest -q`; paper build and PDF verification; YAML/JSON parse;
  `git diff --check`; governance audit and run deduplication.
- Environment: Windows PowerShell, Python 3.12 project environment,
  MiKTeX/pdfLaTeX; branch `campaign/gate13-closeout`, source commit
  `cbb6ddb0a050882249054f9044c905e442a561ab`.
- Outcome: **M13_UNCONDITIONAL_CHAIN_ENVELOPE_CLOSED_FULL_SUITE_GREEN**.
- Summary: removed M11's first-propagator saturation hypothesis for the
  ordered binary k=3 chain using a contraction Gram-matrix cross-term bound,
  obtaining explicit `W_3<U_3` on `0<eta<=1`.
- Validation: full suite **463/463 passed** in 470.42s; all three V5 PDFs
  rebuilt and audited; governance audit passed yellow with no missing files;
  166 historical runs, 9 unique instances, 8 duplicate groups, and 166
  complete artifact contracts.
- Remaining boundary: branching quantitative tightening, exact chain/
  branching constants, unbounded-tree uniformity, norms, novelty, human
  review, Lean/lake, and resource-gated schedules. No release, push, or PR.

## 2026-08-09T00:41:29Z — finite source calculus and endpoint k=3 gap

- Commands: source-calculus and endpoint scripts/tests; full
  `python -m pytest -q`; paper build and PDF verification; YAML/JSON parse;
  `git diff --check`; governance audit and run deduplication.
- Environment: Windows PowerShell, Python 3.12 project environment,
  MiKTeX/pdfLaTeX; branch `campaign/gate13-closeout`, source commit
  `cbb6ddb0a050882249054f9044c905e442a561ab`.
- Outcome: **FINITE_SOURCE_CALCULUS_ENDPOINT_K3_GAP_CLOSED_FULL_SUITE_GREEN**.
- Summary: consolidated P6A/P6B/P7B into one finite theorem package and
  extended the strict k=3 gap to `0<eta<=1`, with endpoint upper value
  `U_3(1)=sqrt(2)` and nonquantitative strictness.
- Validation: full suite **461/461 passed** in 411.30s; all three V5 PDFs
  rebuilt and audited; governance audit passed yellow with no missing files;
  165 historical runs, 9 unique instances, 8 duplicate groups, and 165
  complete artifact contracts.
- Remaining boundary: exact `C_3`, explicit delta, broader sharpness classes,
  unbounded-tree uniformity, norms, novelty, human review, Lean/lake, and
  resource-gated schedules remain open or blocked. No release, push, or PR.

## 2026-08-09T00:20:31Z — fixed-tree support compression and global k=3 gap

- Commands: support-compression script; focused support-compression tests;
  full `python -m pytest -q`; PDF verification; YAML/JSON parse;
  `git diff --check`; governance audit and run deduplication.
- Environment: Windows PowerShell, Python 3.12 project environment,
  MiKTeX/pdfLaTeX; branch `campaign/gate13-closeout`, source commit
  `cbb6ddb0a050882249054f9044c905e442a561ab`.
- Outcome: **FIXED_TREE_COMPRESSION_GLOBAL_K3_STRICT_GAP_CLOSED_FULL_SUITE_GREEN**.
- Summary: fixed-tree projector-invariant support compression was proved with
  explicit per-type dimension bound `2*(leaves + 2*nodes)`. For binary `k=3`
  this is `20` (`22` with proper-projector padding), and compactness plus M10
  yields `C_3,ind^P(eta) < U_3(eta)` for `0 < eta < 1`.
- Validation: full suite **457/457 passed** in 410.61s; all three V5 PDFs
  rendered/audited; governance audit passed yellow with no missing required
  files; 164 historical runs, 9 unique instances, 8 duplicate groups, and
  164 complete artifact contracts.
- Limitations: exact `C_3^P`, explicit delta, endpoint `eta=1`, unbounded-tree
  uniformity, broader sharpness classes, norms, novelty, human review,
  Lean/lake, and resource-gated schedules remain open or blocked. No release,
  push, or PR was performed.

## 2026-08-09T00:00:08Z — M11 conditional quantitative k=3 gap

- Commands: exact M11 script; focused M11 test; full `python -m pytest -q`;
  PDF verification; YAML/JSON parse; `git diff --check`; governance audit
  and run deduplication.
- Environment: Windows PowerShell, Python project environment, MiKTeX/pdfLaTeX;
  branch `campaign/gate13-closeout`, source commit
  `cbb6ddb0a050882249054f9044c905e442a561ab`.
- Outcome: **M11_CONDITIONAL_K3_GAP_CLOSED_FULL_SUITE_GREEN**.
- Summary: derived the explicit angle–magnitude bound under exact
  first-propagator saturation and retained the unrestricted fixed-eta
  supremum as open.
- Validation: full suite **455/455 passed** in 442.90s; exact script and
  focused test passed; registries parsed; all three V5 PDFs rendered/audited;
  governance audit passed yellow with no missing required files.
- Current evidence: 163 historical runs, 9 unique scientific instances,
  8 duplicate groups, and 163 complete artifact contracts.
- Limitations: global fixed-eta k=3, dimension/rank-uniform reduction,
  arbitrary-law sharpness, generic signed constants, global norm sharpness,
  novelty, human review, Lean/lake, and resource-gated schedules remain open
  or blocked. No Gate13.5, Gate14, historical artifacts, push, or PR were
  modified.

## 2026-08-09T17:15:57Z — manuscript concentration, novelty addendum, and review refresh

- Commands: bounded primary-source novelty search; concentrated mathematical
  manuscript update; M23 scope clarification; all three PDF builds and render
  audit; `python -m pytest tests/math_closure -q`; focused V5 regression tests;
  `git diff --check`; governance audit and run deduplication.
- Environment: Windows PowerShell, Python 3.12 project environment,
  MiKTeX/pdfLaTeX; branch `campaign/gate13-closeout`, source commit
  `cbb6ddb0a050882249054f9044c905e442a561ab`.
- Outcome: **MANUSCRIPT_NOVELTY_REVIEW_PACKET_REFRESHED**.
- Validation: math closure **59/59 passed**; focused V5 regression suite
  **85/85 passed**; all three V5 PDFs rebuilt and audited; `git diff --check`
  passed; governance audit passed with status `yellow`, no missing required
  files; run deduplication completed.
- Changes: the main paper now states the independent/same-law/rank-one/common-
  leaf scope distinctions and places M21--M23 after the main finite-arity
  spine; the novelty audit adds bounded comparisons for TTN dynamics,
  stability, randomized rounding, and projection-based MOR; the theorem matrix
  and reviewer packet include M23 and current test counts.
- Limitations: the audit remains bounded and does not establish novelty;
  independent human review, formal proof-assistant verification, publication
  approval, applied allocator superiority, low-eta M23 value, broader same-law
  classes, and unbounded-tree fixed-eta sharpness remain open or blocked. No
  release, push, or PR was performed.

## 2026-08-09T17:22:32Z — internal theorem consistency audit and M20/M21 evidence repair

- Commands: bounded source/proof audit for the universal theorem and M8/M14--M23;
  M20/M21/M23 module checks; focused M20/M21/M23 tests; full
  `python -m pytest tests/math_closure -q`; theorem-registry YAML and ledger
  JSON validation; `git diff --check`.
- Environment: Windows PowerShell, Python 3.12 project environment; branch
  `campaign/gate13-closeout`, source commit
  `cbb6ddb0a050882249054f9044c905e442a561ab`.
- Outcome: **INTERNAL_THEOREM_AUDIT_COMPLETED_WITH_M21_CERTIFICATE_REPAIR**.
- Finding and repair: converting M21's structural norm/defect values from
  declarations to computed direct-sum certificates initially exposed the
  expected high-eta distinction between the realized defect and the external
  cap. The verifier now checks `defect=min(eta,sqrt(2/3))` while preserving
  admissibility `defect<=eta`; no theorem scope was widened.
- Validation: focused M20/M21/M23 tests **6/6 passed**; full math-closure
  suite **60/60 passed**; M20, M21, and M23 module entry points passed; YAML,
  JSON, and `git diff --check` gates passed.
- Deliverables: explicit effective-law budget lemma in M20; computed direct-sum
  certificate and regression test for M21; internal pre-review audit at
  `research/projected_trees_v5/review/INTERNAL_THEOREM_AUDIT_2026-08-09.md`;
  registry scope clarification for M20/M23.
- Limitations: this is not independent human review or a novelty decision;
  those remain pending, as do the M23 low-eta value, broader shared-law
  classes, applied allocator superiority, formalization, and publication
  approval. No release, push, or PR was performed.

## 2026-08-09T17:24:00Z — exact-phrase novelty search extension

- Command: bounded web search for exact/fixed-constant matches to the M14--M20
  projected-root and `W_3` statements, followed by an additive novelty-audit
  update.
- Outcome: **NOVELTY_AUDIT_EXTENDED_WITH_ADJACENT_TTN_RECORDS**.
- Finding: the additional records concern TTN dynamics, stochastic projection,
  and tensor-network/multilinear contraction theory; no exact theorem match was
  verified in the bounded search. `NOVELTY_NOT_ESTABLISHED` remains unchanged.
- Limitations: this is not an exhaustive independent literature review and
  search absence is not evidence of novelty. No theorem status or publication
  status changed.

## 2026-08-09T17:26:02Z — six-requirement completion audit

- Commands: objective-file reread; requirement-by-requirement evidence audit;
  local evidence path checks; focused M20/M21/M23 tests; PDF render audit;
  governance audit and run deduplication.
- Outcome: **OBJECTIVE_REQUIREMENTS_AUDIT_RECORDED**.
- Result: concentrated manuscript, explicit scope, and internal supporting
  reproducibility are verified; bounded novelty review is recorded but not
  exhaustive; independent mathematical review is still missing; applied
  superiority is correctly not claimed.
- Deliverable: `research/projected_trees_v5/review/OBJECTIVE_REQUIREMENTS_AUDIT_2026-08-09.md`.
- Validation: all referenced local evidence paths exist; focused M20/M21/M23
  tests **6/6 passed**; three PDFs rendered/audited successfully.
- Limitations: the matrix does not upgrade novelty, theorem status, or review
  authority. The goal remains active because the external review and exhaustive
  novelty determination have not occurred. No release, push, or PR was done.

## 2026-08-09T17:28:49Z — external review request made actionable

- Deliverable: `research/projected_trees_v5/review/EXTERNAL_REVIEW_REQUEST_TEMPLATE.md`.
- Contents: minimum theorem spine, optional M21--M23 addendum, minimal reading
  set, hypothesis/normalization/admissibility questions, verdict vocabulary,
  novelty-review prompts, and an unfilled reviewer record.
- Authority: preparation only. No human verdict, novelty upgrade, or publication
  recommendation was inferred.

## 2026-08-09T17:30:56Z — canonical review hub

- Added `research/projected_trees_v5/review/README.md` as the single entry point
  for the external review packet, theorem sources, novelty records, and
  verification commands.
- Validation: all review-hub files exist; governance audit passed with status
  `yellow`; deduplication completed; `git diff --check` passed.
- Limitation: the hub organizes a review but does not supply a reviewer or
  approval. No theorem, novelty, or publication status changed.

## 2026-08-09T17:32:46Z — applied validation status separated and rechecked

- Added `applications/adaptive_tensor_network/results/APPLIED_VALIDATION_STATUS_2026-08-09.md`.
- The note records Level 1's mixed/negative allocator result, Level 2's null
  result, Level 3's exploratory partial positive result, and the exact
  matched-error memory/runtime study required before any technology claim.
- Re-ran the registered Level 1 analysis from raw records: Pearson
  `0.9334132264`, Spearman `0.9216239741`; primary comparisons supported only
  against `singular_energy`, not `uniform` or `local_error_greedy`.
- Application tests: **16/16 passed**. No applied-superiority claim was added.

## 2026-08-09T21:10:00Z — finite DAG bounded-domain certificate

- Added a V5 finite-DAG enclosure calculus with topological value/error
  recurrence, repeated-slot accounting, reverse downstream gains, and exact
  finite rank-budget DP under rank-independent enclosures.
- Added theorem and truth-ledger records plus
  `research/math_closure/dag/global_domain_certificate.tex`.
- Validation: DAG plus `tests/math_closure` **69/69**; application tests
  **22/22**; full `python -m pytest -q` **502/503**. The only failure was the
  existing FB15K-237 batched performance ceiling at **406.3 s** versus 300 s;
  the epoch completed. Registry parsing, governance audit, deduplication, and
  `git diff --check` passed.
- Limitations: finite declared DAGs and rank tables only; no sharpness claim,
  universal empirical norm certificate, novelty upgrade, or human approval.

## 2026-08-09T21:35:00Z — shared-DAG tensor-network validation

- Added a numerical shared-subexpression DAG backend and a held-out diamond
  probe driven by the global bounded-domain certificate allocator.
- The probe has 420 records (20 seeds, seven budgets, three methods); both the
  rank-independent and rank-aware certificates held on 140/140 matched cases.
  The rank-aware allocator beat uniform on 16.4% of sup-error comparisons and
  had mean reduction -0.007448, a negative control against universal
  allocator-superiority claims.
- Validation: adaptive tests **28/28**, math plus DAG tests **70/70**, and
  YAML/JSON artifact parsing passed. No applied or theorem status was upgraded.

## 2026-08-09T22:05:00Z — exact nonnegative DAG path constant

- Added the exact path-product constant for the declared nonnegative
  first-order DAG channel class, including shared fan-out and parallel slot
  multiplicity. Registered the theorem, proof note, implementation, and tests.
- Validation: DAG/path/math suite **73/73**; theorem/truth-ledger parsing
  passed. Limitation: this is sharpness of the first-order channel envelope,
  not simultaneous sharpness of the original multilinear operator class.

## 2026-08-09T22:20:00Z — shared-diamond DAG asymptotic sharpness

- Proved and registered the exact asymptotic coefficient 4 for the fixed
  independent-law shared diamond DAG. The planar complex-multiplication
  witness has exact error `|exp(4 i theta)-cos(theta)^4|` with
  `theta=arcsin(eta)` and ratio tending to 4.
- Validation: dedicated tests **2/2**; combined DAG/path/math suite **75/75**;
  registry/truth-ledger parsing passed. Fixed-eta and arbitrary-DAG sharpness
  remain open.

## 2026-08-09T22:40:00Z — fixed-DAG independent-law asymptotic sharpness

- Generalized the asymptotic coefficient-4 diamond theorem to every fixed
  finite ordered acyclic independent-law DAG. The coefficient is the total
  projected source-to-root slot-path multiplicity `K(G)`; the planar product
  witness attains the limit as eta tends to zero.
- Validation: combined DAG/path/math suite **77/77** and theorem/truth-ledger
  parsing passed. Fixed-eta and unbounded-family sharpness remain open.

## 2026-08-09T22:55:00Z — numerical fixed-DAG witness verification

- Added explicit real tensor-core evaluations for chain, shared-diamond, and
  repeated-slot DAGs. Their observed root errors match the exact complex
  witness formula based on `K(G)`.
- Validation: adaptive application tests **31/31**, theory DAG/path tests
  **77/77**, compile, registry parse, and diff checks passed.

## 2026-08-09T21:59:04Z — matched-tolerance DAG resource study

- Added exact compressed-coordinate execution and a liveness-aware analytical
  resource proxy to the shared-DAG tensor backend.
- Commands: `python applications/adaptive_tensor_network/experiments/run_dag_matched_tolerance_probe.py`;
  `python -m pytest applications/adaptive_tensor_network/tests -q`;
  `python -m pytest tests/research_v5_test_dag_asymptotic_sharpness.py tests/research_v5_test_dag_path_constant.py tests/research_v5_test_dag_domain_certificate.py tests/math_closure -q`;
  `python -m compileall -q src/seion_core/research_v5 applications/adaptive_tensor_network/src applications/adaptive_tensor_network/tests applications/adaptive_tensor_network/experiments/run_dag_matched_tolerance_probe.py`;
  deterministic JSON hash rerun; registry parse; governance audit; run
  deduplication; `git diff --check`.
- Results: 33/33 application tests, 77/77 DAG/path/math tests, 180 candidate
  records, 97 selected records, 100% selected-test certificate coverage, and
  partial tolerance transfer. The comparison is negative/context-dependent:
  certificate methods used more contraction units than uniform on average in
  the matched pairs. Resource values are not hardware timings.

## 2026-08-16T07:42:44.820016+00:00 — Engineering advantage audit for adaptive tensor-network allocation

- Command: `python applications/adaptive_tensor_network/experiments/analyze_engineering_pareto.py; python -m pytest applications/adaptive_tensor_network/tests -q; python -m seion_core.cli.main governance audit --json; python -m seion_core.cli.main governance dedupe-runs; git diff --check`
- Branch/commit: `campaign/gate13-closeout` / `a0430ac80704a16122b89d7c871c05cbc72881d1`
- Outcome: **AUDIT_COMPLETE_WITH_DOMAIN_LIMITED_ADVANTAGES_AND_CRITICAL_OPEN_THRESHOLD_BASELINE**
- Summary: Created a falsifiable engineering-advantage register, registered six scoped claims, and generated a deterministic M35b/M38 error-cost Pareto table from preserved raw artifacts.
- Validation: 110 adaptive application tests passed; generator SHA256 stable across rerun; compileall passed; governance audit yellow with no missing required files; dedupe-runs completed; git diff --check passed.
- Changed files:
  - `applications/adaptive_tensor_network/ENGINEERING_ADVANTAGE_REGISTER.md`
  - `applications/adaptive_tensor_network/experiments/analyze_engineering_pareto.py`
  - `applications/adaptive_tensor_network/results/engineering_pareto_front.csv`
  - `claims/claims_registry.yaml`
  - `experiments/README.md`
- Limitations:
  - Static and adaptive threshold/cutoff competitors are not implemented; all FO/pairwise/rollout Pareto evidence is synthetic and exact-oracle evidence has five seeds per m.
  - No new FLOP, peak-memory, VRAM, energy, robust timing, real TT/MPS/TTN, or hardware-speed claim was produced; KGE predictive metrics affected by B-0014 were excluded.

## 2026-08-16T08:25:02.219537+00:00 — Close the decisive static/adaptive threshold gate at m=8 and m=10; draft and adjudicate Paper A

- Command: `python applications/adaptive_tensor_network/experiments/run_threshold_gate.py; python applications/adaptive_tensor_network/experiments/run_threshold_gate.py --m 8 10 --seeds 5..34 --policies threshold_static threshold_adaptive measured_first_order --out threshold_gate_v1b_raw.json; python applications/adaptive_tensor_network/experiments/analyze_threshold_gate.py; python applications/adaptive_tensor_network/experiments/analyze_threshold_gate_v1b.py; latexmk -pdf -interaction=nonstopmode -halt-on-error main.tex`
- Branch/commit: `campaign/gate13-closeout` / `a0430ac80704a16122b89d7c871c05cbc72881d1`
- Outcome: **DOMAIN_LIMITED_FO_ADVANTAGE_AT_M10_NO_GENERAL_GO; Paper A draft complete, novelty pending human review**
- Summary: Implemented exact-budget threshold-static and propagated-state threshold-adaptive baselines; executed V1 plus a predeclared fixed-size V1B precision extension; found no general FO GO, with pooled m=10-only terminal advantage and much lower threshold evaluation cost. Drafted and rendered Paper A around k-1 and exact W3 at k=3, and completed scoped full-text theorem adjudication with novelty still unestablished.
- Validation: 113 adaptive tests passed; 48 Paper A math tests passed; 56 governance tests passed; threshold analyzers reproduced byte-identical outputs; LaTeX compiled 11 pages without warnings; every page rendered and visually inspected; compileall and git diff --check passed; governance audit passed yellow with pre-existing duplicate-run and paper-release warnings
- Changed files:
  - `applications/adaptive_tensor_network/src/allocation.py`
  - `applications/adaptive_tensor_network/tests/test_threshold_allocation.py`
  - `applications/adaptive_tensor_network/experiments/run_threshold_gate.py`
  - `applications/adaptive_tensor_network/experiments/analyze_threshold_gate.py`
  - `applications/adaptive_tensor_network/experiments/analyze_threshold_gate_v1b.py`
  - `experiments/configs/ATN_THRESHOLD_GATE_V1.yaml`
  - `experiments/configs/ATN_THRESHOLD_GATE_V1B.yaml`
  - `applications/adaptive_tensor_network/results/threshold_gate_m8_m10_raw.json`
  - `applications/adaptive_tensor_network/results/threshold_gate_v1b_raw.json`
  - `applications/adaptive_tensor_network/results/threshold_gate_summary.csv`
  - `applications/adaptive_tensor_network/results/threshold_gate_v1b_summary.json`
  - `applications/adaptive_tensor_network/results/THRESHOLD_GATE_V1_FINDINGS.md`
  - `applications/adaptive_tensor_network/results/THRESHOLD_GATE_V1B_FINDINGS.md`
  - `applications/adaptive_tensor_network/ENGINEERING_ADVANTAGE_REGISTER.md`
  - `claims/claims_registry.yaml`
  - `experiments/README.md`
  - `papers/paper_a/main.tex`
  - `papers/paper_a/references.bib`
  - `papers/paper_a/main.pdf`
  - `research/projected_trees_v5/novelty/PAPER_A_THEOREM_ADJUDICATION_2026-08-16.md`
- Limitations:
  - All allocator evidence is synthetic fixed-basis D=16 CPU execution; memory is analytical, wall time is not a robust hardware benchmark, and adaptive threshold does not refit bases or shrink ranks.
  - The preregistered V1B extension remained inconclusive; pooled m=10 intervals are descriptive precision evidence and do not rewrite V1.
  - No screened rollout was run because the global threshold gate did not return GO.
  - No equivalent W3 theorem was identified in the scoped full-text corpus, but novelty remains NOVELTY_NOT_ESTABLISHED pending human review, Kayalar-Weinert library access, and Zhang-Solomonik citation-neighborhood review.

## 2026-08-16T18:40:00Z — Geometry of projected rebracketings: the k=2 pair constants

- Goal: open a focused line on the geometry of *pairs* of computation trees
  (RG-0/1/2/4/5 of the user's programme), leaving Hodge/GJI/E8/curvature out.
  The single-tree theory gives `C_2^P = 1` and `C_3^P = W_3`; the pair problem
  asks how a projection distorts the difference between two bracketings.
- New: `research/rebracketing_geometry/` — `RG_CANONICAL.md` (definitions and
  proofs), `rg_witnesses.py` (explicit witnesses + admissibility audit),
  `rg4_s2_search.py` (adversarial falsification harness),
  `tests/math_closure/test_m40_m42_rebracketing_geometry.py` (50 tests).
- Proved and registered (`research/math_closure/status_registry.yaml`):
  - **M40** `J_2(eta) = 2`, attained. The witness uses ONE ternary law and ONE
    rank-2 projector at all four vertices of both trees in dimension 3 with
    every leaf inside `Ran(P)`, so `J_2^free = J_2^same-mu =
    J_2^same-mu,shared-P`: the class hierarchy collapses at k=2 and sharing
    provides no rigidity.
  - **M41** `H_2(eta) = 2`, attained by the same witness: the compressed
    computation reports `R_L = R_M` exactly while the ambient one has
    `F_L = -F_M != 0`. Concealment is total at every leakage level.
  - **M42** `||Ahat|| <= ||PA|| + Sigma_2(eta) rho M L` with
    `Sigma_2(eta) = 2 sqrt(1-eta^2)` below `eta_c = 1/sqrt(2)` and `1/eta`
    above, hence `S_2 = Sigma_2 < 2`, attained with `A = 0` exactly in
    dimension 2. Proof is a two-equation scalarization plus a single
    Cauchy-Schwarz with the interpolation weight
    `lambda = cos a cos a' / cos(a - a')`, which collapses the bound to
    `sin(a + a')`.
- Consequence: the certificate threshold for inferring genuine
  non-associativity from a compressed computation drops from `2 rho M L` to
  `Sigma_2(eta) rho M L`, strictly smaller at every eta (1.9596 at eta=0.2,
  1.4142 at the crossover, 1.0 at eta=1). Recorded in the associator file,
  which previously carried only the constant 2.
- Verification: 24/24 witness audits pass with 19 checks each (operator norms
  and closure defects measured, not assumed, and matched to their analytic
  values at 1e-9); 50/50 tests pass, including randomized admissible pairs
  against all three ceilings.
- Defect found and recorded: `m39a_j2_fused.py` makes the root law feasible
  with `restrict=P_L` on all three slots, but Definition 4.1 restricts only the
  slot whose child is the inner vertex — the root's other children are leaves,
  whose extended projector is the identity. It admits laws whose true
  `rho_r^proj` exceeds eta. No bound proved here depends on it (Lemma 2.2
  shows the root closure budget is never binding), but that script's
  admissibility claim carries the caveat.
- Limitations:
  - k=2 only. `J_3` versus `2 W_3`, and `S_3`, `H_3`, are untouched.
  - `S_2^same-mu` is OPEN: the `S_2` witness uses three different laws, and the
    same-law arm of the sweep is a conservative subset of the true same-law
    class, so a shortfall there is not evidence of a strict gap.
  - All bounds are on the projected defect `P A`, not on `A`; and nothing here
    says which of `||Ahat||` or `||PA||` an experiment can actually estimate.
  - Proofs are repository-internal, `approval_status: PENDING_HUMAN_REVIEW`,
    with no prior-art adjudication yet — the `S_2` extremal problem has not
    been searched for in the literature.

## 2026-08-16T21:10:00Z — RG harness: hardware saturation, positive control, and a grading defect

- Hardware: RTX PRO 5000 Blackwell Laptop (24 GB, 82 SMs, CUDA 12.8, torch
  2.12) + Intel Core Ultra 9 285HX (24 cores), 127 GB RAM.
- The k=2 search was launch-bound, not FLOP-bound: 42% GPU, 2.0 of 24 GB,
  ~34 s/cell. `rg_fused_search.py` folds objective, class, rank and eta into
  per-element vectors so a whole sweep at one dimension is one optimization
  loop -> 100% GPU at 24 GB, 10.3 s/cell at D=3. Group size is sized from a
  two-point measurement of MARGINAL bytes/element; a single probe charges fixed
  workspace overhead to its own elements and underfills the card ~2x.
  `rg_witnesses.py --workers` puts the audit on all 24 cores: 123 audits over
  41 eta values in 15 s (was ~3 min for 24 serially). `rg_cpu_falsify.py` adds
  uniform random sampling as an unbiased complement to gradient ascent:
  1,500,000 admissible pairs over dims 2-6, zero violations, worst excess
  -0.336. `rg_kernels.py` batches restarts into the batch axis (3.5x over the
  sequential-restart M39 kernel), leaving the M39 kernels untouched.
- Class-typing defect found and fixed BEFORE reading any number: the first
  fused same-law arm shared the raw tensor but normalized root and inner
  vertices differently, so it was an unnamed correlated-law class, not
  C^same-mu. Recorded as Warning 2.3: a WLOG reduction valid in the free class
  (here, taking root laws P-valued) can stop being WLOG under shared parameters.
- Positive control (`rg_readout.py`): J_2 = 2 is proved attainable in the
  same-law/shared-P class, so the J arm calibrates the search. Free class
  gamma_J = 0.99968 -> calibrated. Same-law gamma_J = 0.93448 -> NOT
  calibrated; at D=3 rank 2, the very cell where the witness attains 2 for
  every eta, the search returns only 1.5261-1.6848. The observed same-law S
  deficit (0.81-0.87 of Sigma_2) is therefore recorded as an optimizer result;
  S_2^same-mu remains OPEN and no claim is made.
- `rg_harness_selftest.py` separates optimizer failure from a parametrization
  bug by pushing the exact witness through the harness: J = 2.000000000
  (gap 9e-16) at every eta, measured op norm 1.000000, closure = eta, chi = -1.
  The extremizer is inside the search space and undistorted, so the same-law
  shortfall is optimizer failure.
- GRADING DEFECT (the significant finding): the operator-norm estimator is not
  converged at the strengths used. Against a converged reference, worst deficit
  is -18.29% at D=3 and -29.64% at D=4 for the in-loop setting (restarts=3,
  iters=20), and still -3.28% at D=4 for restarts=18/iters=120; D=4 needs
  restarts=64/iters=200. Feasibility DIVIDES by this estimate, so every
  reported sweep value is inflated by an unknown amount up to several percent
  and the 144-cell gamma table is WITHDRAWN pending re-grading. Converged
  grading is now wired in (`--grade-strength`, default 64/200) with the search
  loop left cheap, which is legitimate: the loop only needs a descent direction.
- One cell exceeded a ceiling (S, same-law, D=4, rank 2, eta=1: 1.0794 vs 1).
  RESOLVED as a grading artifact: re-run with converged grading (64/200) the
  same cell gives 0.9009, with the reported configuration's operator norm
  re-measured at 1.000000 and admissibility confirmed. The other same-law ranks
  moved 0.8791->0.8965 and 0.8748->0.8678; the free class barely moved
  (0.997653 -> 0.997704 at D=4, eta=1), so the free arm is insensitive to
  grading strength here while the same-law arm shifted by 0.18. No refutation
  of Theorem 5.1. eta=1 is the unique leakage level where the closure budget is
  vacuous, leaving the operator norm as the only active constraint, which is
  where an adversarial search finds the estimator's slack.
- Estimator-independent verification of Theorem 5.1 added
  (`rg_scalar_verification.py`): the scalar optimization the proof reduces to,
  maximized by sampling the raw feasible set WITHOUT the proof's interpolation
  weight. Over 11 etas the sampled maximum approaches
  sin(min(2 arcsin eta, pi/2)) from within and exceeds it by +0.000e+00; the
  extremizer's active constraint switches at eta_c = 1/sqrt(2) exactly as
  predicted (d = d' = eta below, d^2 + d'^2 = 1 above). This is the one check
  of Sigma_2 that is immune to the operator-norm estimator entirely.
- Not affected: Theorems 3.1/4.1/5.1 and their witnesses. `rg_witnesses.py`
  grades witnesses against ANALYTIC norms, not the estimator; 123/123 audits
  pass over 41 eta values, ratios match 2, 2, Sigma_2(eta) to 1e-12.
- Limitations:
  - The re-graded sweep has not been run; no corrected gamma table exists yet.
  - The admissibility audit uses the same family of lower-bound estimators, so
    it can PROVE inadmissibility (an estimate above 1 certifies the norm
    exceeds 1) but can never certify admissibility.
  - The convergence study is over random laws at D<=4; D>=5 is untested and the
    deficit grows with dimension.
