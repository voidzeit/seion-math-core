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
