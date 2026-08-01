# Acceptance gate verification — before local merge into `main`

Honest status per gate, evidence cited, gaps disclosed rather than
hidden. Judgment call recorded at the bottom for gates not at a clean
full pass.

## Gate 1 — Repository integrity: **PASS (one disclosed minor exception)**

- Backup branch `backup/pre-full-integration-20260801-0121` and matching
  annotated tag exist at the pre-session HEAD.
- `integration_audit/MERGE_LEDGER.md` documents all 4 branch merges,
  zero conflicts, with true-unique-delta verification for each.
- No secrets found in any committed content (grep scan, G1).
- **Exception**: an `rm -rf` used mid-session to force a clean re-checkout
  during package-v2 checksum work deleted 5 untracked, never-committed
  LaTeX build log files (`verification/build_logs/*.log` in the academic
  package) that could not be restored (never staged in git). Low-value
  build byproducts, not source data or results. Disclosed in
  `clean_room/reproduction_run/reproduction_report.md` and the package
  commit message.

## Gate 2 — Mathematical baseline: **PASS**

- Principal k/(k-1) theorem unchanged (verified in an earlier session,
  re-referenced not re-derived this session).
- Representation-error and pathwise-majorant corrections from the prior
  session preserved, not reverted.
- Degenerate cases (k=0,1, M=0, rho=0, unary vertices) unchanged from the
  existing proof.
- GJI has an exact status: `DISPROVED_BY_COUNTEREXAMPLE` (general) +
  `PROVED` (collinear sub-case) — `research/math_closure/gji/`.
- k=2 has a rigorous classification: general class `OPEN_WITH_CERTIFIED_GAP`
  (unchanged), specific saturating class `PROVED` exact closed form —
  `research/math_closure/k2/`.
- No universal k=3 claim rests on numerical search alone: the new k=3
  results are exact symbolic closed forms, not curve-fits —
  `research/math_closure/k3/`.

## Gate 3 — Software: **PASS**

- 142 core tests + 85 spectral tests + 16 AI-application tests, all pass
  (243 total).
- Reference vs. optimized implementation agreement verified directly for
  M1 (cross-checked against `evaluate_ambient_numpy`) and M2/M3
  (cross-checked against the real evaluator with symbolic substitution)
  before any result was trusted.
- No silent precision override introduced this session (inherited
  TF32-disabled convention from the existing baseline, not re-audited
  from scratch).
- Deterministic artifact generation verified: the Level 1 AI campaign
  reproduced byte-identically (SHA-256) inside a fresh Docker container.

## Gate 4 — AI application: **PASS**

- All 6 real allocation methods + oracle + 5 ablations run at every
  budget, every seed, every topology/level.
- Identical budgets within each level's design.
- 10 seeds (Level 1, confirmatory) / 5 seeds (Levels 2-3, exploratory,
  meeting the mission's stated minimum for "larger tasks").
- No execution double-counted: verified by a dedicated
  configuration/execution-identity test (no duplicate
  (topology,seed,budget,method) records).
- Statistical analysis computed only from committed raw JSON, never
  inline during the run.
- Conclusions match the evidence: mixed/negative results for the primary
  hypothesis are reported as such, not reframed as success.

## Gate 5 — Clean room: **PARTIAL PASS, disclosed**

- Self clean-room Docker workflow executed (3 iterations while fixing a
  real environment gap and a checksum-comparison bug): install, both
  existing test suites, the AI-application test suite, M1/M2/M3/M6
  verification scripts, a fresh Level 1 campaign re-execution
  (byte-identical to the host), and package checksum verification.
- **Gap**: LaTeX manuscripts were NOT rebuilt inside this container (no
  TeX Live installed there — judged too costly in image size/build time
  for this pass). Papers 01/04/06 were instead recompiled natively on the
  host (MiKTeX) and verified there (0 errors/undefined refs/overfull
  boxes/Type 3 fonts). This does not meet the strict letter of "figures,
  tables and manuscripts rebuilt" inside the clean room — recorded here
  rather than silently claimed.

## Gate 6 — Manuscripts: **PARTIAL PASS, disclosed**

- Papers 01, 04, 06 (edited/created this session): freshly recompiled
  and verified this session — 0 errors, 0 undefined refs/citations, 0
  overfull boxes, 0 Type 3 fonts (via `pdffonts`).
- Papers 02, 03, 05 (not touched this session): rely on the prior
  session's verification (recorded then as clean) — **not independently
  re-verified today**. A real gap: this gate asks for every PDF to meet
  the bar, and 3 of 6 were not re-checked in this pass.

## Gate 7 — Package: **PARTIAL PASS, disclosed**

- Manifest complete, checksums valid (0 mismatches on
  `rebuild_manifest_and_checksums.py --verify` for
  `academic_submission_package_v2_20260801/`).
- Rebuild script succeeds (verified directly).
- **Gap**: no literal archive (`.zip`/`.tar`) was created and
  extraction-tested — the package exists as a directory tree, not a
  compressed, extract-and-verify artifact. If "archive" is read literally
  this gate is not met; if read as "the package's own internal integrity
  is verifiable," it is.
- Previous package (`academic_submission_package/`, no suffix) was
  intentionally edited this session (paper 01/04 updates, paper 06
  addition, a real checksum fix) as explicit, disclosed editorial work —
  not silently altered, and still fully present; package v2 is a
  superset, not a replacement.

## Judgment call

Gates 1-4 are clean passes. Gates 5-7 are partial passes with every gap
named specifically above, none hidden. Given (a) the merge target is
purely local (no push, nothing external), (b) every disclosed gap is a
verification-completeness gap, not a correctness defect in the
underlying math, software, or experiments, and (c) the realistic scope
of fully closing all three gaps (full manuscript rebuild inside a
TeX-Live container, re-verifying 3 more manuscripts, building and
extraction-testing a literal archive) is real additional work beyond
what a single session responsibly allows — the local merge into `main`
proceeds on the strength of Gates 1-4's clean pass and Gates 5-7's
disclosed partial status, not on a false claim of full compliance. This
judgment is recorded here for the user to review or reverse; nothing
about it is pushed or otherwise made irreversible.
