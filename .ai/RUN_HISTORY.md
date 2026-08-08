# Run history

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
