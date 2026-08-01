# STATUS

Explicit statuses only, per this package's own governance convention.
Mathematical statuses: `PROVED`, `PROVED_UNDER_STATED_ASSUMPTIONS`,
`CERTIFIED_NUMERICALLY`, `COUNTEREXAMPLE`, `OPEN`,
`NOT_CHECKED_EXTERNALLY`. Experimental statuses:
`IDENTITY_BY_CONSTRUCTION`, `NEGATIVE_RESULT_IN_TESTED_REGIME`,
`EXPLORATORY`, `STATISTICALLY_SUPPORTED`, `NOT_REPRODUCED_EXTERNALLY`.

## Mathematics (this session's math-closure work, `mathematical_certificates/math_closure/`)

| Item | Status |
|---|---|
| M1 general GJI claim | `COUNTEREXAMPLE` (exact rational, dimension 2) |
| M1 collinear-leaves sub-identity | `PROVED` |
| M2 class A (general k=2 upper bound) | `OPEN` (certified gap, unchanged from prior session) |
| M2 class B (chain gated-rotation, exact $\eta^2$) | `PROVED` |
| M3 chain/branching exact closed forms | `PROVED` |
| M3 general k=3 class A | `OPEN` |
| M4 signed-identity extremal constants | `OPEN` (Jacobiator empirically near-sharp, not exact) |
| M5 fixed-tree continuum convergence | `PROVED_UNDER_STATED_ASSUMPTIONS` |
| M6 verified Markov construction | `PROVED_UNDER_STATED_ASSUMPTIONS` (with one explicit worked instance) |
| M7 pseudodifferential/microlocal program | `OPEN` (boundary precisely stated, not attempted) |

Full detail and proofs: `mathematical_certificates/math_closure/status_registry.yaml`.

## Central theorem of the pre-existing package (papers 01-05)

`PROVED_UNDER_STATED_ASSUMPTIONS` — unchanged, verified term-by-term in
an earlier session, not re-derived this session (this session only adds
the M1-M7 follow-ups and a corrected exact optimum for the k=3 gap
figure; see paper 01's updated sections).

## AI benchmark (`ai_benchmarks/adaptive_tensor_network/`)

| Level | Design | Status |
|---|---|---|
| 1 (exact synthetic) | confirmatory, preregistered | `NEGATIVE_RESULT_IN_TESTED_REGIME` for the primary hypothesis (2/3 comparisons); `STATISTICALLY_SUPPORTED` for the calibration/correlation finding |
| 2 (teacher-student regression) | exploratory | `NEGATIVE_RESULT_IN_TESTED_REGIME` (null, all CIs include 0) |
| 3 (Burgers surrogate) | exploratory | `STATISTICALLY_SUPPORTED` for 3/5 comparisons, mixed for the rest; absolute surrogate accuracy weak (stated as a limitation) |

## Reproduction

`SELF_CLEAN_ROOM_REPRODUCTION_PASS` — executed this session
(`clean_room/reproduction_run/`), author-run only.
`NOT_REPRODUCED_EXTERNALLY` — no third party has run this package.

## Originality

`NOT_CHECKED_EXTERNALLY` in the sense of formal peer review; a real,
but partial, literature-search-based originality pass was completed
(`originality/novelty_matrix_v5.md`), every verdict marked
`PENDING_HUMAN_REVIEW` per this project's no-self-approval convention.
No claim in this package is asserted as `NOVEL` outright.
