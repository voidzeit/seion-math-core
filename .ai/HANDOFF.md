# Handoff

## Resume sequence

1. Read `AGENTS.md`, `.ai/CURRENT_STATE.md`, `.ai/TASKS.md`, and
   `.ai/KNOWN_BLOCKERS.md`.
2. Run `python -m seion_core.cli.main governance context --task "..."`.
3. Inspect the relevant claim/theorem/run registries before editing.
4. Run the smallest relevant test gate.
5. Run governance audit and postflight with exact command and commit details.

## Do not infer

- Do not infer independent experiments from repeated run rows.
- Do not infer theorem novelty from a new name or a generated figure.
- Do not infer current health from a historical pass.
- Do not infer release approval from a green structural audit.

## Latest postflight: governance and manuscript reconstruction

- Timestamp: 2026-07-29T13:02:42.140869+00:00
- Outcome: **tests and PDF builds passed; non-strict audit passed yellow; strict release gate correctly failed closed**
- Validation: 23 tests passed; paper and companion PDF renders passed; audit yellow without errors
- Resume from commit: `247de089a5fea826fa87f9b9e791c20a5a6fd1b6` on `master`
- Limitation: The strict release gate remains blocked by B-0001 through B-0004; no mathematical novelty or universal claim is approved.

## Latest postflight: final verification

- Timestamp: 2026-07-29T13:03:05.869746+00:00
- Outcome: **24 tests passed; audit remains yellow and non-strict pass; release stays fail-closed**
- Validation: python -m pytest -q: 24 passed
- Resume from commit: `247de089a5fea826fa87f9b9e791c20a5a6fd1b6` on `master`
- Limitation: Final audit reports 75 historical runs, 9 unique scientific instances, 8 duplicate groups, and 66 duplicate records.

## Latest postflight: Research v2 structure-preserving reduction and reproducibility split

- Timestamp: 2026-07-29T15:49:15.967635+00:00
- Outcome: **COMPLETE_WITH_SCIENTIFIC_BLOCKERS**
- Validation: 39 pytest tests passed; 180/180 v2 runs complete; 100 unique scientific instances; 60/60 bound rows respected; max tightness 0.7100467992738069; five CPU/GPU parity rows with max abs error 1.4210854715202004e-14; latexmk builds foundations, draft, and software PDFs; rendered pages and figures visually inspected; v2 audit fail-closed.
- Resume from commit: `247de089a5fea826fa87f9b9e791c20a5a6fd1b6` on `research/structure-preserving-reduction-v2`
- Limitations: A theorem-level novelty claim has not been established; the foundations PDF remains draft/not for submission; verified author email and ORCID metadata are absent; legacy historical duplicates remain preserved; the worktree is dirty and no commit was created.

## Latest postflight: Final research v2 rebuild and strict-gate verification

- Timestamp: 2026-07-29T15:54:40.001229+00:00
- Outcome: **COMPLETE_WITH_SCIENTIFIC_BLOCKERS**
- Validation: one-command generation/compilation/render/audit completed;
  39 tests passed; 180/180 runs complete; 100 unique instances; all bound
  rows respected; five CPU/GPU parity rows passed; PDF logs are clean.
- Resume from commit: `247de089a5fea826fa87f9b9e791c20a5a6fd1b6` on
  `research/structure-preserving-reduction-v2`
- Limitations: theorem-level novelty and verified author email/ORCID remain
  unresolved; no submission approval; worktree dirty and no commit created.

## Latest postflight: Final research v2 rebuild and strict-gate verification

- Timestamp: 2026-07-29T15:54:40.001229+00:00
- Outcome: **COMPLETE_WITH_SCIENTIFIC_BLOCKERS**
- Validation: single-command build exit 2 only because strict gate is intentionally blocked; 39 pytest tests passed; 180/180 runs complete; 100 unique instances; 60/60 bounds respected; max tightness 0.7100467992738069; max CPU/GPU error 1.4210854715202004e-14; all three PDFs compile with no fatal/layout/reference warnings; 36+ rendered PNG pages/previews inspected; v2 audit checks pass except blocker status.
- Resume from commit: `247de089a5fea826fa87f9b9e791c20a5a6fd1b6` on `research/structure-preserving-reduction-v2`
- Limitation: Theorem-level novelty remains unestablished; standard exact-reduction and spectral results are not claimed as new.

## Latest postflight: V3 nodewise tree constants

- Timestamp: 2026-07-29T18:13:56.026823+00:00
- Outcome: **TECHNICAL_AUDIT_PASS; FAIL_CLOSED_NOVELTY**
- Validation: canonical 15-stage workflow completed from immutable source
  commit `b718f4e5178590d1f8b6a090fb696545eb3bfcd4`; 69 tests passed;
  81,445 tree occurrences, 80,870 unique tree hashes, 15,493 unique
  scientific instances, 1,530 leakage masks, 18 vector figures, 17 tables,
  and 37 visually inspected PDF pages.
- Primary deliverables: `papers/tree_stability_v3/build/main.pdf`,
  `papers/software_v3/build/main.pdf`, and
  `artifacts/research_v3/final_report_v3.md`.
- Resume command: `powershell -ExecutionPolicy Bypass -File
  scripts/resume_tree_constants_v3.ps1`; inspect
  `artifacts/research_v3/extended_progress_v3.json` before authorizing more
  compute.
- Limitations: 9/15 release gates pass. Do not claim sharpness, novelty,
  complete global optimality, completed extended experiments, human peer
  review, or publication readiness. Preserve `.obsidian/workspace.json`.

## Latest postflight: SEION nodewise tree constants v3 full execution

- Timestamp: 2026-07-29T18:16:20.089306+00:00
- Outcome: **TECHNICAL_AUDIT_PASS; FAIL_CLOSED_NOVELTY**
- Validation: 69 tests passed; 81445 tree occurrences; 80870 unique hashes; 15493 unique A-I instances; 37 PDF pages visually inspected; 9/15 release gates pass.
- Resume from commit: `b718f4e5178590d1f8b6a090fb696545eb3bfcd4` on `research/nodewise-tree-constants-v3`
- Limitation: Fixed-eta sharpness, theorem-level novelty, complete independent certification, the extended matrix, and independent human review remain unresolved.
