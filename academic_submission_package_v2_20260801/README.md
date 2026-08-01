# SEION math+AI closure package v2 (2026-08-01)

Supersedes nothing — the predecessor package (`academic_submission_package/`
in the source repository) remains intact; this is a superset snapshot
built after this session's math-closure (M1-M7) and AI-benchmark
(Sections V/AI1-AI7) work, per `provenance.md`.

## What is proved

- The central k/(k-1) projected-error theorem (papers 01-05, unchanged
  from the predecessor package, verified term-by-term in an earlier
  session).
- M1's collinear-leaves GJI sub-identity, M2's exact k=2 chain closed
  form, M3's exact k=3 chain/branching closed forms, M5's fixed-tree
  continuum convergence, M6's verified Markov construction — all new
  this session, all in `mathematical_certificates/math_closure/`.

## What is numerically certified

The 7,065-row k=2/k=3 sharpness atlas (`results/constants_atlas_v3.csv`,
pre-existing, re-verified). Nothing new this session was promoted from
numerical evidence to a theorem without a corresponding proof.

## What is exploratory

AI benchmark Levels 2 and 3 (teacher-student regression; Burgers
surrogate) — designed and run *after* Level 1's results were seen, so
their comparisons are exploratory, not confirmatory, and are labeled as
such throughout `ai_benchmarks/adaptive_tensor_network/results/CAMPAIGN_FINDINGS.md`.

## What is a negative result

- M1's general GJI claim: disproved by an exact rational counterexample.
- AI benchmark Level 1's primary hypothesis: pathwise global-contribution
  allocation loses to 2 of 3 preregistered baselines (uniform,
  local-error-greedy) at equal budget — retained and reported, not
  omitted.
- AI benchmark Level 2: a full null result (no comparison significant).

## What remains open

M2/M3's general (class-A, arbitrary-law) extremal constants; M4's
signed-identity extremal constants (associator, Filippov); M7's entire
pseudodifferential program (no symbol class has ever been fixed for
this framework). See `STATUS.md` for the complete list with exact
terminal statuses.

## What has been reproduced, and what has not

Self clean-room reproduction (`clean_room/`) was executed this session
in a fresh Docker container — see `clean_room/reproduction_run/reproduction_report.md`
for exactly what ran, one real environment gap found and fixed (missing
`git` binary), and one real pre-existing finding (stale checksums in the
predecessor package, not caused by this reproduction, fixed in this
package's own `checksums.sha256` instead). No independent (third-party)
reproduction has occurred.

## Whether originality has been evaluated

Partially. `originality/novelty_matrix_v5.md` contains real, primary-source
literature searches for this session's most novelty-relevant new claims
(the Markov construction vs. diffusion maps; the AI benchmark's pathwise
allocation vs. rank-adaptive tensor-network literature) plus the
predecessor package's own earlier searches. Every verdict is
`PENDING_HUMAN_REVIEW`; nothing is asserted as `NOVEL` outright, and
several new results (the exact k=2/k=3 closed forms specifically) were
not searched this pass — stated as a gap, not hidden.

## Layout

See `STATUS.md` for statuses, `provenance.md` for exact source commit
and environment, `checksums.sha256` for file integrity, `MANIFEST.json`
for a machine-readable file listing, `CHANGELOG.md` for what changed
since the predecessor package.
