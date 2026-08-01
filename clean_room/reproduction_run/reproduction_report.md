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

## A real, pre-existing finding: `academic_submission_package/checksums.sha256` is stale

Every file checksum recorded in `academic_submission_package/checksums.sha256`
differs from the file's current content (`checksum_verification.json`
lists every mismatch). **This is not caused by the clean-room process**:
verified directly on the host (`sha256sum` on
`academic_submission_package/statement_evidence_table.md` gives
`48f9adcc...`, matching the container's "actual" hash and differing from
the recorded "expected" hash `00e0e054...`) — the recorded checksums were
computed before later edits to the package (this session's paper 01
updates included) and were never regenerated. This is exactly the kind
of drift Gate 7 ("checksums valid") exists to catch. It will be fixed by
regenerating checksums as part of building `academic_submission_package_v2`
(task in progress), not by editing the existing package's frozen
checksums file in place.

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
