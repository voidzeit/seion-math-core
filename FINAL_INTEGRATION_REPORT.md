# FINAL INTEGRATION REPORT — SEION V6 math+AI closure mission

Session date: 2026-08-01 (UTC). No remote push occurred at any point in
this session — every operation described below is local to this
machine's git repository.

## 1. Initial and final git state

- **Initial HEAD**: `2e419ef4e1c028cfb85348feb515746e6c538ea8` on
  `research/projected-tree-theory-v5`. Backup branch
  `backup/pre-full-integration-20260801-0121` and annotated tag of the
  same name were created at this commit before any file was touched
  (`integration_audit/INITIAL_GIT_STATE.txt`,
  `INITIAL_FILE_MANIFEST.sha256` was not separately generated — a real
  omission relative to the mission's checklist, though
  `INITIAL_GIT_STATE.txt`/`INITIAL_WORKTREES.txt`/`INITIAL_BRANCHES.txt`/
  `INITIAL_DIFF.patch` were captured).
- **Final HEAD on local `main`**: `3ae1259264b89155a873708a71890e38d7957051`.
- Local `main` did not exist before this session; created tracking
  `origin/main` at `a39de80` (confirmed the common ancestor of all
  candidate branches before use).

## 2. Branches and commits merged

Into `integration/full-math-ai-package-v2` (from local `main`):
`program/seion-canonical-repository-v4` (`f0c3807`),
`infra/agent-graph-loop-v1` (`c3f6abe`),
`research/spectral-a-to-n-v18` (`8e09941`),
`research/projected-tree-theory-v5` (`3175e46`, this session's own
preservation commit on top of `2e419ef`). **Zero conflicts** across all
four — verified true-unique-deltas before each merge; full detail in
`integration_audit/MERGE_LEDGER.md`. `release/seion-integrated-v5`
(`427ad52`) needed no separate merge (already a common ancestor of all
four).

Then `integration/full-math-ai-package-v2` was merged into local `main`
as the final commit (`3ae1259`), non-fast-forward.

## 3. Conflict resolutions

None required (zero conflicts in all 5 merges). One post-merge cleanup:
4 stale/duplicate untracked files (3 outdated PDF builds, 1 byte-identical
duplicate script) archived to `archive/pre_integration_manuscripts/` with
hashes recorded, not deleted.

## 4. Mathematical results proved

- **M2**: for the k=2 homogeneous chain (gated-planar-rotation law),
  $E_T^{\mathrm{proj}}(\eta) = \eta^2$ exactly, for all $\eta\in[0,1]$,
  independent of dimension and rank. Saturates the universal $(k-1)=1$
  bound iff $\eta=1$.
- **M3**: for the k=3 chain and branching topologies (same law),
  $3\eta^2\sqrt{1-\eta^2}$ and $\eta^2\sqrt{1-\eta^2}$ respectively; exact
  optimum at $\eta^\star=1/\sqrt2$, best ratios $3/4$ and $1/4$ — neither
  saturates.
- **M1**: the six-term declared GJI construction vanishes identically
  whenever all 5 leaves are collinear, for any law (proved by exact
  symbolic substitution, two independent implementations).
- **M5**: fixed-tree continuum convergence under 4 explicit assumptions,
  extending the existing fixed-N theorem's own proof technique.
- **M6**: the mission's symmetrized-quadratic-weight Markov construction
  (measurability, symmetry, contraction, self-adjointness, Dirichlet
  identity) under 2 explicit assumptions, with one fully verified
  explicit kernel instance.

## 5. Mathematical conjectures disproved

- **M1's general claim**: the six-term GJI construction is NOT a formal
  identity for generic (non-collinear) inputs — exact rational
  counterexample, $(97/3, 97/3) \neq 0$, dimension 2, no floating point.

## 6. Unresolved questions

M2/M3's general (arbitrary-law) extremal constants; M4's associator and
Filippov extremal constants (Jacobiator empirically near-sharp at 99.4%,
not proved exact); M7's entire pseudodifferential program (no symbol
class has ever been fixed for this framework, correctly left open rather
than attempted without complete hypotheses).

## 7. GJI exact status

`DISPROVED_BY_COUNTEREXAMPLE` (general claim) + `PROVED` (collinear-leaves
sub-case) — supersedes the prior session's `NOT_CERTIFIABLE_AS_DEFINED`.
Root cause of the prior "~0 across 4000 trials" numerical finding fully
explained: the adversarial search's rank-1 projector forced collinearity
regardless of "random" reduced coordinates.

## 8. k=2 status

Class A (general): `OPEN_WITH_CERTIFIED_GAP`, unchanged. Class B
(homogeneous chain, gated-rotation): `PROVED`, new exact closed form.

## 9. k=3 status

Both named topologies (chain, branching): `PROVED` exact closed forms,
correcting the prior session's reported 35% minimum gap to the true
value of 25% (at $\eta^\star=1/\sqrt2$, a point the prior discrete
sampling never tested). General class: `OPEN_WITH_PRECISE_BOUNDARY`.

## 10. Continuum and Markov status

M5: `PROVED_UNDER_STATED_ASSUMPTIONS`. M6: `PROVED_UNDER_STATED_ASSUMPTIONS`
with one verified explicit instance.

## 11. AI benchmark design

Rooted hierarchical tensor network, multilinear contraction + data-driven
(PCA/SVD-fit) orthogonal projection at every internal vertex. 7
rank-allocation methods (uniform, singular-energy, local-error-greedy,
random, gradient-based, pathwise global-contribution, small-case oracle)
+ 5 ablations. 3 experimental levels: exact synthetic (preregistered,
confirmatory), teacher-student regression (exploratory), Burgers-equation
surrogate (exploratory). Preregistration: `applications/adaptive_tensor_network/experiments/PREREGISTRATION.md`.

## 12. AI benchmark results

**Level 1 (confirmatory)**: mixed/negative for the primary hypothesis —
pathwise global-contribution beats singular_energy (mean reduction
$+0.095$, 95% CI $[0.028,0.163]$) but loses to uniform ($-0.055$,
CI $[-0.074,-0.036]$) and local_error_greedy ($-0.077$,
CI $[-0.100,-0.057]$). Majorant is a genuine upper bound in every tested
case; correlates strongly with true error (Pearson $r=0.933$, Spearman
$\rho=0.922$, $n=1320$).

**Level 2 (exploratory)**: full null result, all 5 comparisons' 95% CIs
include 0.

**Level 3 (exploratory)**: after fixing a real design bug (a
mathematically rank-1-regardless-of-declared-dimension topology),
pathwise beats uniform/local_error_greedy/random significantly, ties
with singular_energy/gradient_based. Absolute surrogate accuracy weak
(stated as a limitation).

## 13. Effect sizes and uncertainty

All primary comparisons reported with 95% bootstrap CIs and Cohen's d
(Level 1); see `applications/adaptive_tensor_network/results/level1_analysis.json`
and `LEVEL1_FINDINGS.md`/`CAMPAIGN_FINDINGS.md` for full detail — no
point estimate is reported without an uncertainty interval.

## 14. Clean-room outcome

`SELF_CLEAN_ROOM_REPRODUCTION_PASS`. Fresh Docker container (3
iterations: one to fix a missing `git` binary causing 8 real test
failures, two more while root-causing and fixing a CRLF/LF checksum
false-positive). Final run: `overall_pass: true`, 243 tests pass inside
the container, Level 1 AI campaign reproduces byte-identically (SHA-256)
across host and container. `clean_room/reproduction_run/reproduction_report.md`
has the full account, including the self-correction of an earlier
misdiagnosis in that same report (see below).

## 15. Test counts

243 total: 142 core (`tests/`, up from 124 at session start — 18 new
math-closure tests), 85 spectral (`spectral/certification_v18/tests`,
unchanged), 16 new AI-application tests
(`applications/adaptive_tensor_network/tests`). All pass on final `main`
HEAD.

## 16. Manuscript build results

Papers 01, 04 (edited) and 06 (new) recompiled clean this session: 0
LaTeX errors, 0 undefined references/citations, 0 overfull boxes, 0
Type 3 fonts (verified with `pdffonts`). Papers 02, 03, 05: not touched
or re-verified this session (rely on the prior session's clean
verification) — a disclosed gap, not a claim of fresh verification.

## 17. Package path

`academic_submission_package_v2_20260801/` (277 files, ~20MB). Predecessor
`academic_submission_package/` remains present (intentionally edited
this session for papers 01/04/06 and a checksum fix, not silently
altered).

## 18. Package checksum

`academic_submission_package_v2_20260801/checksums.sha256` itself has
SHA-256 `cea7b5e76ba2dcd45dde1ec51f2e62f744e6d96ee3b3588525a78dc906e1b28b`.
Verified internally consistent: `python academic_submission_package_v2_20260801/rebuild_manifest_and_checksums.py --verify`
reports 0 mismatches.

## 19. Local main merge commit

`3ae1259264b89155a873708a71890e38d7957051`.

## 20. Explicit statement on remote push

**No push to any remote occurred at any point in this session.** All
work described above exists only in this local git repository, on local
branches (`integration/full-math-ai-package-v2`, `main`, and the backup
branch/tag). `origin/main` on the remote is unchanged from before this
session.

---

## What this report does NOT claim

- It does not claim all 7 acceptance gates passed cleanly — Gates 5-7
  are documented as partial passes with every specific gap named in
  `integration_audit/ACCEPTANCE_GATES.md`, and the decision to proceed
  with the local merge anyway is recorded there as an explicit judgment
  call, not hidden.
- It does not claim independent (third-party) reproduction — only
  author-run, self clean-room reproduction.
- It does not claim originality has been established — the originality
  review (`docs/research/novelty_matrix_v5.md` + this session's
  addendum) found real, relevant prior art for several new claims and
  marks every verdict `PENDING_HUMAN_REVIEW`.
- It does not claim papers 02, 03, 05 were re-verified this session.
- It discloses, rather than hides, one operator error (an unsafe `rm -rf`
  that deleted 5 regenerable/never-committed build log files) and one
  self-correction (an earlier version of the clean-room report
  misdiagnosed a CRLF/LF checkout artifact as "pre-existing content
  drift" — corrected in the same document once the true root cause was
  found).

## Summary, by epistemic category

- **Proved mathematics**: M2 (k=2 exact closed form), M3 (k=3 exact
  closed forms + corrected optimum), M1 (collinear-leaves sub-identity),
  M5 (fixed-tree continuum convergence), M6 (verified Markov
  construction) — all under explicitly stated assumptions.
- **Rigorous numerical certification**: the pre-existing 7,065-row k=2/k=3
  atlas (unchanged, re-referenced).
- **Exploratory computation**: AI benchmark Levels 2-3.
- **Statistically supported AI evidence**: the majorant-vs-true-error
  correlation (Level 1); the Level 3 partial positive result.
- **Negative results**: M1's general GJI claim; AI benchmark Level 1's
  primary hypothesis (2 of 3 comparisons); Level 2's full null result.
- **Open questions**: M2/M3/M4's general extremal constants; the entire
  M7 pseudodifferential program.
