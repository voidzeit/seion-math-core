# V5 theorem-closure campaign — closure report (2026-08-08)

Scope executed: a single autonomous session against the 33-section,
16-phase mission brief ("SEION / Projected Multilinear Graphs — Theorem-
Closure, Extremal Theory, Source-Calculus, Formal Verification, Novelty,
and Publication Campaign"). This report answers the brief's Section XXXII
questions directly and honestly distinguishes what was actually executed
from what was not attempted. It does **not** claim the 16-phase program is
complete.

## 1. What is now proved?

Two new theorems, both mechanically verified and numerically corroborated
(not merely asserted):

- **k=2 saturation iff characterization**
  (`research/math_closure/k2/saturation_iff_theorem.tex`,
  `src/seion_core/research_v5/k2_characterization.py`). For a binary k=2
  chain, `E_proj = rho*M*L_T` holds iff three explicit local conditions
  (EQ1 outer-law norm saturation, EQ2 closure-map saturation, EQ3
  root-projection alignment) hold simultaneously. Proved by an elementary
  real-number chain-of-inequalities argument.
- **k=3 general upper envelope**
  (`research/math_closure/k3/general_upper_envelope.tex`,
  `src/seion_core/research_v5/k3_upper_bound.py`). `C_3,ind^P(eta) <=
  U_3(eta)`, strictly below the trivial universal bound `2` for every
  `eta>0`, proved unconditionally (no rank-one restriction, arbitrary
  dimension/rank), identical for chain and branching topologies.

Both are new proofs, not restatements of prior registry entries.

## 2. Under exactly which admissible class is each theorem proved?

- k=2 iff theorem: finite-dimensional real or complex Hilbert spaces,
  binary k=2 chain, arbitrary ambient dimension and orthogonal-projector
  rank, bilinear laws bounded by `M` with closure-residual `<=rho`,
  independent or repeated laws, `0<eta<=1`.
- k=3 upper envelope: same field/dimension/rank generality, binary k=3
  chain **and** branching trees, independently chosen bilinear laws,
  `0<eta<=1`.

## 3. Which constants are exactly sharp?

Unchanged from before this session: `C_2,ind^P(eta)=1` and
`C_2,same-law^P(eta)=1` (both exact, prior work). No new exact fixed-eta
sharpness result was obtained this session.

## 4. Which constants are only asymptotically sharp?

Unchanged: `lim_{eta->0} C_3,ind^P(eta)=2` (prior work, V5-B).

## 5. Which have certified lower/upper gaps?

- k=3 fixed-eta: `L_3(eta) <= C_3,ind^P(eta) <= U_3(eta) < 2`. Gap
  narrowed this session (e.g. at `eta=1`: relative gap `50%->29%`; at
  `eta=0.9`: `44%->26%`) but **did not close**. New terminal status entry
  `OPEN_V5_K3_FIXED_ETA_SHARPNESS` records this precisely.
- Signed-forest associator/Filippov/GJI-general constants: unchanged,
  still `OPEN_WITH_CERTIFIED_GAP` (not revisited this session).

## 6. Which conjectures were disproved?

None disproved this session. (Prior session: the general six-term GJI
identity was disproved by exact-rational counterexample, `M1` in
`status_registry.yaml` — unchanged, not revisited.)

## 7. Which restricted subfamilies were solved exactly?

None newly solved this session (prior: gated-planar k=2/k=3 chain/branch,
same-law k=2 — all unchanged).

## 8. Which dimension/rank results were proved?

None. Section XI (dimension/rank reduction) was **not attempted** this
session — explicitly deferred, remains `OPEN_V5_DIMENSION_RANK_REDUCTION`.
Notably, both new theorems this session *are* dimension/rank-agnostic in
their hypotheses (arbitrary finite dimension, arbitrary projector rank),
which is a partial, incidental step in the spirit of Section XI, but no
reduction theorem (bounding the *relevant* dimension to a fixed small
value) was proved or attempted.

## 9. Which source-calculus theorems were consolidated?

None. Section XVI's consolidation into a numbered Definition/Theorem
sequence was **not attempted** this session. P5–P7C remain as prior
implementation-level artifacts, not yet rewritten into the requested
theorem sequence.

## 10. What was formally verified in a proof assistant?

Nothing. Lean 4/`lake` are **not installed** on this machine (`which
lean`, `which lake` both empty). Status: `BLOCKED_BY_MISSING_TOOLING`, per
the brief's own required fallback — no theorem in this repository is
described as formally verified by this session, and none should be.

## 11. What novelty evidence exists?

No new novelty/prior-art search was performed this session (Section XXII
was **not attempted** — a serious literature audit against numerical
analysis, model reduction, tensor methods, and provenance-semiring
literature requires dedicated search passes not run in this pass). The
existing prior-art matrix
(`research/projected_trees_v5/novelty/THEOREM_TO_THEOREM_MATRIX.md`) was
not updated to include the two new theorems.

## 12. What remains NOVELTY_NOT_ESTABLISHED?

Everything, including both new theorems. `novelty_status:
NOVELTY_NOT_ESTABLISHED` was set explicitly on both new registry entries.

## 13. What remains PENDING_HUMAN_REVIEW?

Everything, including both new theorems (`approval_status:
PENDING_HUMAN_REVIEW` set explicitly on both). No result in this
repository is self-approved.

## 14. Which papers are mathematically current?

Not assessed this session. Section XXIII (manuscript reconstruction into
Paper A / Paper B / Paper C) was **not attempted**. The two new theorems
are documented only in `research/math_closure/` and the registries listed
above, not yet incorporated into any `papers/` manuscript.

## 15. Which old statements were superseded?

- `src/seion_core/research_v5/equality_conditions.py`'s K2-EQ-05 status
  (was `OPEN_IF_REPEATED`, corrected to `COMPATIBLE` — it had already been
  resolved by the pre-existing V5-B repeated-law witness but the audit
  function was never updated to reflect that). Corresponding test
  `test_repeated_law_requirement_remains_open` renamed and corrected to
  `test_repeated_law_requirement_is_resolved_by_the_v5b_witness`.
- `v5b_extremal.py`'s `CONDITIONAL_ON_UNPROVED_SCALAR_REDUCTION` bookkeeping
  entry is superseded by the proved `THM_V5_K3_GENERAL_UPPER_ENVELOPE`; the
  old entry's assumptions were dimensionally inconsistent with the actual
  witness value (a stray factor of `M` was missing) and were never proved.
  The old code is left in place (still functions correctly as the
  conditional/historical record it now is) but should not be cited as an
  upper bound going forward.

## 16. What tests were actually executed and passed?

Full honest reconstruction (Section XXVI discipline):

- `pytest --collect-only -q`: **365 tests collected**.
- Full suite executed with a 580s budget (no partitioning needed): **365
  executed, 364 passed, 1 failed, 0 skipped/xfailed, elapsed 444.13s**
  (`0:07:24`).
- The one failure —
  `tests/kgr/test_campaign_negative_controls.py::test_queried_edge_leakage_inflates_metrics_when_deliberately_enabled`
  (`TypeError: ...leaky_score_tail_candidates() got an unexpected keyword
  argument 'context'`) — is **pre-existing and out of scope**: it lives
  entirely in the Gate 12/KGR track, last touched 2026-08-01 (commit
  `49e4bfc`), before this session and before this campaign's own branch
  point. Per the mission's explicit instruction to preserve Gate 13.5,
  Gate 14, and KGR untouched, this failure was **not fixed** and no KGR
  file was modified this session.
- The 8 new/modified tests specific to this session's theorems
  (`tests/research_v5_test_k2_characterization.py`,
  `tests/research_v5_test_k3_upper_bound.py`, plus the corrected
  `tests/research_v5_test_equality_conditions.py`) all pass, re-confirmed
  after every registry edit.
- No test in this session's scope timed out or was skipped.

## 17. What timed out?

Nothing timed out. (Prior session's V5-B postflight recorded a 120s
pytest timeout; this session used a longer budget and the full suite
completed in 444s — see item 16.)

## 18. What exact artifacts reproduce the core results?

```bash
pytest tests/research_v5_test_k2_characterization.py tests/research_v5_test_k3_upper_bound.py -q
python scripts/verify_k3_bound.py
```

The second command re-runs the 42-trial numerical corroboration
(non-adversarial sanity check, not a proof) referenced in
`general_upper_envelope.tex`.

## 19. What commits were created?

Recorded at commit time, locally only (see `git log` on
`campaign/gate13-closeout`) — **no push, no PR, per the mission's explicit
instruction.**

## 20. Confirmations

- Gate 13.5: unchanged (no file under its scope touched).
- Gate 14: unchanged.
- KGR / SEION-KGR: unchanged (the one pre-existing test failure discussed
  in item 16 was left as-is, not fixed, not hidden).
- Historical evidence (`.ai/evidence/ledger.jsonl`,
  `artifacts/index/*`): only touched by the standard governance
  audit/dedupe refresh (append-only ledger, regenerated derived indices),
  consistent with every prior postflight in `.ai/HANDOFF.md`.
- No push. No PR. No remote merge. No destructive cleanup.
- `.obsidian/workspace.json` and other unrelated user-owned files: not
  touched.

## What was explicitly NOT attempted this session (honest scope accounting)

Per the brief's own "no documentation-shaped substitutes" discipline, the
following phases from the mission brief were **not executed** and must not
be read as complete. Each remains at its pre-session status:

- **Phase 3** (gated-planar k=2 exact extremal problem): not attempted.
- **Phase 4** (dimension/rank reduction theorem): not attempted (see
  item 8).
- **Phase 5** (k=3 same-law and arbitrary-tree conjecture): not
  attempted.
- **Phase 6** (signed-forest exact extremal constants, esp. Jacobiator):
  not attempted; existing `OPEN_WITH_CERTIFIED_GAP` / near-saturation
  figures (99.4% Jacobiator, etc.) are unchanged from prior sessions.
- **Phase 7** (source-calculus theorem consolidation into the numbered
  Definition/Theorem sequence of Section XVI): not attempted.
- **Phase 8** (growing-tree corrected theorem under summability
  hypotheses): not attempted.
- **Phase 9** (P8/P10 rigorous hardening — validated operator-norm
  enclosures, approximate-law error decomposition): not attempted.
- **Phase 10** (novelty audit): not attempted (see items 11-12).
- **Phase 11** (formal verification): blocked, Lean/lake not installed
  (see item 10).
- **Phase 12** (manuscript rebuild, Papers A/B/C): not attempted (see
  item 14).
- **Phase 13** (certified adaptive-rank application theorem): not
  attempted.
- **Phase 14** (clean-room `scripts/reproduce_projected_graphs_core.py`
  entrypoint, SHA256 manifest, environment record): not attempted; the
  narrower `scripts/verify_k3_bound.py` (item 18) is not a substitute.
- **Phase 15** (external mathematical review package, the 11-file
  structure of Section XXVIII): not attempted.
- **Blocker reconciliation** (Section XXVII, e.g. reassessing B-0001
  against the strengthened theorem program): not attempted as a formal
  pass; this report itself is the first step toward it but
  `.ai/KNOWN_BLOCKERS.md` was not edited this session.

## Overall scientific status

`EXTREMAL_PROGRAM_PARTIALLY_CLOSED` — two genuine, non-trivial theorem-
level results were added (a complete k=2 saturation characterization, and
an unconditional, non-trivial-margin k=3 upper-bound improvement), both
mechanically verified and numerically corroborated. The large majority of
the mission brief's 16 phases remain unattempted or open, most
consequentially: fixed-eta k=3 sharpness, the arbitrary-tree conjecture,
signed-forest exact constants, source-calculus consolidation, novelty, and
formal verification. This status label should be read literally — not as
`FINITE_CORE_CLOSED` and not as `CLOSED` in any broader sense.

`novelty_status: NOVELTY_NOT_ESTABLISHED` and `approval_status:
PENDING_HUMAN_REVIEW` apply to every result mentioned in this report
without exception.
