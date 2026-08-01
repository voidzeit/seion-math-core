# Merge ledger — integration/full-math-ai-package-v2

Base: local `main` created tracking `origin/main` at `a39de80` (chore(governance):
seal final v3 release evidence). No local `main` branch existed before this
session; `origin/main` was confirmed as the common ancestor of every
candidate research branch before use (`git merge-base --is-ancestor origin/main <branch>`
returned true for all four below).

`release/seion-integrated-v5` (`427ad52`) was **not** merged separately: it is
already an ancestor of all four branches below (verified with
`git merge-base --is-ancestor`), so its content arrives automatically.
`research/nodewise-tree-constants-v3` and `research/structure-preserving-reduction-v2`
are likewise pure ancestors of `origin/main`/earlier history, nothing to merge.

## Merge 1 — program/seion-canonical-repository-v4

- Source commit: `f0c3807` (Fix pre-existing CI: missing pytest install
  extra, missing torch skip-guard)
- Merge commit: `b7eb582`
- True unique delta vs common ancestor `427ad52` (verified with
  `git diff 427ad52 program/seion-canonical-repository-v4 --stat`): 4 files,
  the pytest/torch CI fix across `.github/workflows/{numerical,symbolic,test}.yml`
  plus one test file.
- Conflicted files: none.
- Tests executed: none in isolation (rolled into the final suite run below).
- Result: clean, no-conflict `ort` merge.

## Merge 2 — infra/agent-graph-loop-v1

- Source commit: `c3f6abe` (Freeze SEION V5 evidence contract v1)
- Merge commit: `06160cf`
- True unique delta vs `427ad52`: 51 files — evidence contract v1
  (`governance/EVIDENCE_CONTRACT_V1.md`, `schemas/scientific_instance.schema.json`,
  `src/seion_core/governance/evidence_contract.py`), agent-graph-loop
  orchestration (`src/seion_core/orchestration/*`), security/quality CI
  (`.github/workflows/{codeql,security-and-quality}.yml`), 23 mutation tests.
- Conflicted files: none (independent CI-fix lines to the same 3 workflow
  files as Merge 1 auto-resolved identically by git's `ort` strategy — both
  branches made the same textual fix).
- Tests executed: none in isolation (rolled into the final suite run below).
- Result: clean, no-conflict `ort` merge.

## Merge 3 — research/spectral-a-to-n-v18

- Source commit: `8e09941` (Expand supplementary visual atlas with 2 new
  figures from the 416-cell sweep)
- Merge commit: `52eda83`
- Content: SPECTRAL_LEGACY_TRACK — `spectral/` (536 real files: 14 blocks
  A-N, gate engine, hardware/job-queue, 85 tests), papers
  `a_to_n_certification_v18`, `software_reproducibility_v5`,
  `supplementary_visual_atlas_v18` (real `.tex` sources + `main.pdf`).
- Conflicted files: none. This merge superseded the stale untracked residue
  documented in `integration_audit/G1_EXCLUDED_FILES.md` (PDF-only paper
  dirs with no `.tex`; `spectral/` with 0 real `.py` source files, only
  `__pycache__` cache) with the real, complete versions.
- Tests executed: `python -m pytest spectral/certification_v18/tests -q`
  after all 4 merges completed -> **85 passed**.
- Result: clean, no-conflict `ort` merge.

## Merge 4 — research/projected-tree-theory-v5

- Source commit: `3175e46` (this session's own G1 preservation commit, on
  top of `2e419ef` Expand tree_stability_v4 with signed-forest and
  k=2/k=3 findings)
- Merge commit: `8f1a13d`
- Content: Track T terminal-status docs (k=2/k=3, signed-forest, novelty
  audit), `papers/kernel_integrated_laws_v5/main.tex`, this session's
  preserved `academic_delivery_work/` + `academic_submission_package/`
  (five rewritten manuscripts, corrections ledger, clean-room tooling,
  external-review kit) and code fixes (optimality reclassification, table
  sanitization, interval-certification repairs).
- `papers/tree_stability_v4/main.tex` was modified by this branch
  (+93/-2 from the `427ad52` merge-base) and **not** touched at all by
  `research/spectral-a-to-n-v18` (verified: `git diff <merge-base>
  research/spectral-a-to-n-v18 -- papers/tree_stability_v4/main.tex`
  produced zero lines) — confirmed before merging that this is a pure
  additive supersession, not a real fork, matching the prior session's
  audit finding.
- Conflicted files: none.
- Tests executed: `python -m pytest tests -q` after all 4 merges completed
  -> 1 failure (see post-merge fix below), 123 passed initially.
- Result: clean, no-conflict `ort` merge.

## Post-merge cleanup (not a merge conflict, discovered by the test suite)

1. **Archived, not deleted**, 4 untracked stale files that predated the
   Merge 3 content (commit `3a44f5d`): three older local pdflatex PDF
   builds (`a_to_n_certification_v18.pdf`, `software_reproducibility_v5.pdf`,
   `supplementary_visual_atlas_v18.pdf`, all dated 2026-07-30 21:16, before
   any `.tex` source existed in this working tree) and one
   byte-identical-mod-CRLF duplicate script now tracked at
   `spectral/legacy/v17/`. Moved to
   `archive/pre_integration_manuscripts/` with sha256 hashes recorded in
   `ORIGINAL_HASHES.txt`, per the "deduplicate only when byte-identical or
   clearly obsolete" rule.
2. **Real bug found and fixed** (commit `1751342`): the merged
   `test_frozen_schema_manifest_matches_actual_file_hashes` test failed —
   `schemas/scientific_instance.schema.json` hashed differently on disk
   than the value frozen in `schemas/SCHEMA_FREEZE_MANIFEST.json`. Root
   cause: the file is stored as LF in the git blob (blob hash matches the
   manifest exactly, confirmed via `git show <ref>:<path> | sha256sum` on
   three different refs), but this Windows machine's global
   `core.autocrlf=true` silently converts it to CRLF on checkout, changing
   the on-disk byte hash. This is a real cross-platform reproducibility
   defect (the schema-drift gate would false-positive on any fresh Windows
   checkout with default autocrlf settings, unrelated to actual schema
   content), not a merge conflict. Fixed by adding
   `schemas/*.json text eol=lf` and `*.sha256 text eol=lf` to
   `.gitattributes` and re-normalizing the two affected files. No schema
   content was changed.

## Final verification

- `python -m pytest tests -q` -> **124 passed**
- `python -m pytest spectral/certification_v18/tests -q` -> **85 passed**
- Total: 209 tests passed, 0 failures, on `integration/full-math-ai-package-v2`
  at commit `1751342`.

## Process note

One operator error during this phase, corrected without data loss: an
exploratory `git checkout infra/agent-graph-loop-v1 -- .` was run to
inspect a file at that branch's tip and accidentally reverted 6 tracked
files in the working tree/index to their pre-merge (infra-branch) content.
HEAD itself was never touched. Recovered with `git checkout HEAD -- <the
6 files>`, verified `git status` was clean afterward, and popped the
stash that held the in-progress archive staging. No commits were lost or
altered.
