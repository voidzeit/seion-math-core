# Current state

## Observation

- Observed on **2026-07-29** from branch `master` at commit
  `247de089a5fea826fa87f9b9e791c20a5a6fd1b6`.
- The worktree was already dirty before the governance bootstrap. Existing
  generated artifacts, figures, indexes, and `.obsidian/` content are retained
  as user-owned state; this bootstrap must not be attributed to those changes.
- The repository contains typed finite-dimensional algebra modules, claim and
  theorem registries, canonical experiment configurations, run artifacts,
  deterministic generators, and a compiled-paper workflow.

## Scientific status

- The legacy `paper/main.tex` remains a broad finite-dimensional release note;
  its registered formal results are the curvature/associator expansion and
  finite cohomology descent under explicit hypotheses.
- A separate working-paper source now exists at
  `papers/foundations/main.tex`. It states and proves, within the declared
  finite-dimensional hypotheses, exact invariant reduction, a tree-level
  approximate-closure bound, associator stability, and spectral snapping with
  a no-gap counterexample. It is not yet an independently reviewed or
  release-approved mathematical contribution.
- Projector recovery, convergence, precision, and CP results are finite
  numerical observations unless their registry says otherwise.

## Operational status

- The new governance contract is local to this repository.
- Run deduplication and claim/evidence audits are required before release
  claims.
- The paper/software split has independent sources at
  `papers/foundations/main.tex` and `papers/software/main.tex`; both compile
  and render through `scripts/build_companions.ps1`.
- The latest structural audit is yellow and passes only in non-strict mode:
  all required files and run contracts are present, but duplicate historical
  runs and the paper quality flag keep release fail-closed.

## Latest postflight observation

- Observed on **2026-07-29T15:49:15Z** from branch
  `research/structure-preserving-reduction-v2` at commit
  `247de089a5fea826fa87f9b9e791c20a5a6fd1b6`; the worktree remains dirty.
- The v2 track now has separate foundations and software sources, theorem and
  counterexample registries, a conservative prior-art matrix, 180 registered
  runs, 100 unique scientific instances, nine vector figure pairs, and
  fail-closed audit output under `artifacts/research_audit/`.
- The v2 numerical gates pass for the declared finite regime: 39 tests pass,
  all 180 rows complete, all 60 closure-bound rows respect the bound, and the
  five CPU/GPU parity rows have maximum absolute error below `1.5e-14`.
- The v2 research gate remains blocked because theorem-level novelty has not
  been established and verified author email/ORCID metadata are absent. The
  foundations PDFs are drafts/not for submission; the software companion is
  the reproducibility deliverable.
- Other repositories remain inspiration-only and were not edited.

## Final postflight observation

- Observed on **2026-07-29T15:54:40Z** from the same v2 branch and commit;
  the worktree remains dirty by design.
- The one-command rebuild completed all generation, compilation, rendering,
  and audit checks. Its exit code is `2` solely because the strict research
  gate correctly remains fail-closed on the two scientific/editorial
  blockers.
- Final regression status is 39 tests passed, 180 complete v2 runs, 100
  unique scientific instances, 60 bound checks passed, and five CPU/GPU
  parity rows with maximum absolute error `1.4210854715202004e-14`.

## V3 postflight observation

- Observed on **2026-07-29T18:13:56Z** from branch
  `research/nodewise-tree-constants-v3` at immutable source commit
  `b718f4e5178590d1f8b6a090fb696545eb3bfcd4`.
- The v3 system implements typed ordered n-ary trees, exact and recursively
  projected evaluation, nodewise and path-sum certificates, exact subset
  expansions, telescoping-order optimization, signed forests, CP projection
  budgets, interval/SOS adapters, adversarial search, resumable experiments,
  artifact governance, and strict publication gates.
- The canonical 15-stage run completed generation, testing, CUDA parity,
  exact enumeration, the A--I base matrix, benchmark registration, vector
  figures, scientific tables, both manuscripts, page rendering, adversarial
  reviews, and technical audit. The technical audit passes.
- Verified totals are 69 passing tests, 81,445 enumerated tree occurrences,
  80,870 unique mathematical hashes, 15,493 deduplicated scientific
  instances, 1,530 exhaustive leakage masks, 18 principal vector figures,
  16 mandatory plus one supplementary table, and 37 visually inspected PDF
  pages. No registered theorem-bound violation was observed.
- Publication remains deliberately fail-closed (`FAIL_CLOSED_NOVELTY`, 9/15
  gates passing). Fixed-eta sharpness, theorem-level novelty, complete
  independent global certification, the resource-gated extended matrix, and
  independent human review remain unresolved. The pre-existing user-owned
  `.obsidian/workspace.json` modification is preserved and also keeps the
  clean-worktree gate false.
- Other repositories were used as inspiration only and were not edited.

## Update rule

This file is updated only by a postflight that records the command, environment,
commit, result, and limitation. Do not replace an old observation with an
unqualified present-tense statement.
