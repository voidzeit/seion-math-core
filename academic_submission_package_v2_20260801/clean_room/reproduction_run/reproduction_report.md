# Clean-room reproduction report — `SELF_CLEAN_ROOM_REPRODUCTION_PASS`

Author-run reproduction (this session, on this machine, via a freshly
built Docker container distinct from and broader in scope than
`academic_submission_package/clean_room/`). Reserving
`INDEPENDENT_REPRODUCTION_PASS` for a third party — no claim of
independent reproduction is made here.

## What ran, inside a fresh container built from `python:3.12-slim-bookworm`

1. Fresh dependency install from `pyproject.toml` (no cached host wheels) — succeeded.
2. Core test suite (`tests/`): **132 passed, 0 failed** (2 GPU tests correctly skipped, no CUDA in this container).
3. Spectral test suite (`spectral/certification_v18/tests`): **85 passed, 0 failed**.
4. `adaptive_tensor_network` application test suite: **16 passed, 0 failed**.
5. M1 GJI symbolic verification (`scripts/math_closure_m1_gji_symbolic.py`): exit 0, output matches the committed `research/math_closure/gji/mutation_test_report.json`.
6. M2 k=2 exact closed-form verification: exit 0.
7. M3 k=3 exact closed-form verification: exit 0.
8. M6 verified Markov construction example: exit 0.
9. Level 1 AI campaign, re-executed fresh inside the container: exit 0, **1,440 records, byte-identical SHA-256 to the host-committed `level1_raw.json`** (`hash_comparison.json`: both hashes `28eb217...` — confirms full determinism given fixed seeds, independent of host vs. container environment).
10. `academic_submission_package/checksums.sha256` verification.

**Overall: `overall_pass: true`** (`summary.json`) after one real, documented fix (below).

## One real problem found and fixed before declaring pass

The first container build lacked the `git` binary (a minimal
`python:3.12-slim-bookworm` base does not include it). 8 tests in
`tests/governance/test_lifecycle.py` and
`tests/research_v3/certificates/test_run_schema.py` shell out to `git`
to record commit-hash lineage in evidence records, and failed with
`FileNotFoundError` as a result — a genuine environment gap, not a code
regression (confirmed: these same tests pass on the host, which has
`git`). Fixed by adding `git ca-certificates` to the Containerfile and
rebuilding; rerun then passed cleanly. Both runs' full logs are
preserved (`test_report_core.txt` reflects the second, passing run;
the first run's failing log was not separately retained, but the
finding and fix are recorded here and in the Containerfile's own
comments).

## A finding that looked like drift and mostly wasn't: correcting an earlier misdiagnosis in this same report

The first version of this report claimed every checksum mismatch was
"pre-existing content drift." That was wrong, and is corrected here
rather than left standing. Root-caused after the fact: this repository's
Windows checkouts use `core.autocrlf=true`, and at the time this
clean-room run first executed, `.gitattributes` had no LF-forcing rule
for `academic_submission_package/`, so text files inside it were
smudged to CRLF on disk while the actual git-committed blob (what any
fresh clone anywhere gets) stayed LF — the exact same false-positive
mechanism as the `schemas/scientific_instance.schema.json` bug found and
fixed earlier in this session's G2/G3 phase, just not yet applied to
this directory. Comparing raw disk bytes (`sha256sum` on the working
tree) against a checksum computed from the canonical LF blob will always
disagree for this reason alone, regardless of whether any real edit ever
happened.

Fixed by extending `.gitattributes`'s LF rule to both
`academic_submission_package/**` and
`academic_submission_package_v2_20260801/**` (by specific text
extension, not a blanket rule, so the existing `*.pdf`/`*.png`/etc.
binary declarations are not overridden), renormalizing, and regenerating
`checksums.sha256` from git-indexed content via `git show :path` rather
than raw disk reads (see
`academic_submission_package_v2_20260801/rebuild_manifest_and_checksums.py`'s
module docstring for why raw-disk reads are the wrong primitive for this
comparison in general). After that fix, only **4 files** in
`academic_submission_package/checksums.sha256` actually changed for a
real reason: `papers/01_recursive_projection_of_multilinear_trees.pdf`,
`sources/recursive_projection_of_multilinear_trees/main.tex`,
`papers/04_software_and_reproducibility.pdf`, and
`sources/software_and_reproducibility/main.tex` — exactly the four files
this session's own paper 01/04 edits touched. A further ~42 entries
changed only because renormalizing `.gitattributes` rewrote their
committed line endings from CRLF to LF (a real, intended, one-time
repository hygiene fix, not new content). 5 checksum entries
(`verification/build_logs/*.log`) reference files that exist on disk but
were never tracked in git; left as their originally-recorded value since
there is no canonical git-indexed content to regenerate them from — a
real, narrow, honestly-stated gap, not fabricated.

## Explicitly out of scope for this pass (stated, not hidden)

- **No LaTeX manuscript rebuild inside this container** (no TeX Live
  installed here — judged not to be the load-bearing part of this
  specific reproduction pass, given the multi-GB/many-minute image cost).
  Manuscript rebuilds in this session were done natively on the host
  (MiKTeX) — see the git log for paper 01's post-edit recompilation
  (bibtex + 2 pdflatex passes, 0 errors, 0 undefined refs/citations,
  0 Type 3 fonts, 0 overfull boxes, verified directly with `pdffonts`
  and `grep` on the compile log).
- **Level 2/3 AI campaigns were not re-executed inside the container**
  this pass (only Level 1, the fastest and most exactly reproducible) —
  their determinism was not independently re-verified here, though they
  use the same seeded-RNG discipline as Level 1.
- The academic package's OWN clean-room
  (`academic_submission_package/clean_room/`) is a separate, narrower
  container (manuscript-focused, includes TeX Live) built in an earlier
  session; it was not re-run this pass.
