# Changelog — relative to `academic_submission_package/`

## Added

- `mathematical_certificates/math_closure/` — the complete M1-M7 math
  closure campaign: GJI resolution (M1), k=2 exact closed form (M2), k=3
  exact closed forms (M3), signed-identity formalization (M4), fixed-tree
  continuum convergence (M5), verified Markov construction (M6), and an
  honest deferral note for the pseudodifferential program (M7).
- `ai_benchmarks/adaptive_tensor_network/` — the complete adaptive
  rank-allocation AI benchmark: core implementation, 7 allocation
  methods, 5 ablations, 3 experimental levels (1,770 total raw records),
  analysis, and 27 tests.
- `clean_room/` (top-level, broader scope than the predecessor package's
  own `clean_room/`) — a full-repository clean-room Docker reproduction,
  executed this session.
- Paper 06 (`sources/adaptive_rank_allocation/`,
  `papers/06_adaptive_rank_allocation_for_hierarchical_tensor_models.pdf`) — new.
- `originality/` addendum covering this session's new claims.
- `integration_audit/` — the G1-G3 git integration ledger (backup
  branch/tag, 4 branch merges with zero conflicts, one caught-and-fixed
  operator error, one caught-and-fixed cross-platform schema-drift bug).

## Changed

- Paper 01 (`recursive_projection_of_multilinear_trees`): three new
  subsections reporting M1's GJI resolution, M2's exact k=2 closed form,
  and M3's exact k=3 closed forms (including a correction to the
  previously-reported 35% minimum relative gap — the true value is 25%,
  at an $\eta$ the original discrete sampling never tested). Recompiled
  clean (0 errors, 0 undefined refs/citations, 0 overfull boxes, 0 Type 3
  fonts).
- Paper 04 (`software_and_reproducibility`): new subsection reporting
  this session's expanded test suites and the clean-room execution.
  Recompiled clean.

## Fixed (this session, documented in place, nothing silently altered)

- `checksums.sha256` in this package is freshly generated from current
  file content (the predecessor package's own `checksums.sha256` was
  found stale during this session's clean-room run — see
  `clean_room/reproduction_run/reproduction_report.md` — and is left
  untouched there, not edited retroactively).

## Unchanged

- Papers 02, 03, 05 and their sources — not revised this session (a
  real scope limitation, stated here rather than silently implied by
  omission).
- The central k/(k-1) theorem and its proof (papers 01-05) — unchanged.
