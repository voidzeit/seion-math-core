# SEION V5 evidence contract — v1 freeze (Phase 2)

This document is the exit-gate record for `PASS_FROZEN_EVIDENCE_CONTRACT_V5`.
It does not reinvent typed evidence states from scratch — the strongest
existing implementation (`spectral/certification_v18/GATE_TAXONOMY.md` on
`research/spectral-a-to-n-v18`) already froze 10 typed states and 8 of the
12 critical gates, enforced in code, not by convention. This freeze:

1. Adopts that taxonomy by reference for the gates it already owns.
2. Registers the remaining 4 critical gates (`construction_integrity`,
   `novelty`, `paper`, `release`) in `governance/RELEASE_GATES.yaml` v5.
3. Adds the missing identity/provenance schema
   (`schemas/scientific_instance.schema.json`) so every experiment record
   can distinguish `scientific_instance_id` / `execution_id` /
   `optimizer_restart_id`, per mission section 2.
4. Adds enforceable invariant checks
   (`src/seion_core/governance/evidence_contract.py`) with real mutation
   tests proving each one rejects a violation, not just documents it.
5. Hash-pins the frozen schema files (`schemas/SCHEMA_FREEZE_MANIFEST.json`)
   so silent drift is caught by `tests/governance/test_evidence_contract.py`
   — any legitimate change must be recorded in `schemas/MIGRATIONS.md` and
   the manifest regenerated via `scripts/freeze_schema_manifest.py` in the
   same commit.

## 1. Typed states (adopted by reference)

The 10 typed states (`STRUCTURAL_IDENTITY_PASS` through
`NOT_CERTIFIABLE_AS_DEFINED`) and their non-implications are defined in
`spectral/certification_v18/GATE_TAXONOMY.md` §1. Not duplicated here —
duplicating a frozen taxonomy in two places is itself a drift risk. Any
document restating these states must cite that file, not fork it.

## 2. Critical gates

8 of 12 are owned by the existing v18 taxonomy (`GATE_TAXONOMY.md` §2):
`projector_gate` (maps to `projector_relevance` below),
`algebra_gate`, `dynamic_explanation_gate`, `interscale_gate`,
`gauge_gate`, `persistence_gate`, `reproducibility_gate`,
`mathematical_proof_gate`.

The remaining 4, registered in `governance/RELEASE_GATES.yaml` v5
`critical_gates`:

- **construction_integrity** — a block passes construction-integrity
  (e.g. block A's `PASS_PROJECTOR_CONSTRUCTION`) purely by being built
  correctly (e.g. `P = UU*` with orthonormal `U` is idempotent by
  construction). This is explicitly separated from `projector_relevance`
  — a construction-integrity pass carries **zero** implication about
  whether the constructed object is scientifically meaningful. Owned by
  the same per-block modules as the taxonomy it's carved out of.
- **novelty** — not yet exercised (mission Phase 9). No AI process may
  self-approve this gate; it requires a human decision per
  `claims/novelty_registry.yaml`'s existing authority model.
- **paper** — not yet exercised (mission Phase 11). Contract already
  partially exists as `paper/quality/paper_quality_report.json`
  (see `src/seion_core/governance/audit.py::_paper_issues`, which already
  fails closed on `release_ready_under_critical_gate=true` with a
  critical-dimension score below 4).
- **release** — the terminal gate; may only pass when every other gate in
  `governance/RELEASE_GATES.yaml` (math/software/dataset/extended
  categories, plus all 12 `critical_gates`) is not open. Not yet
  exercised (mission Phase 13).

**Never averaged.** Per the v18 taxonomy's own rule (§2), a gate's status
is the minimum over everything feeding it, never a mean — this rule is
adopted for all 12 gates, not just the original 8.

## 3. Frozen invariants

Implemented as pure functions in
`src/seion_core/governance/evidence_contract.py`, each with a dedicated
mutation test in `tests/governance/test_evidence_contract.py` proving it
actually rejects the violation it claims to catch:

| Invariant | Function |
|---|---|
| `lower_bound <= upper_bound + tolerance` | `check_bound_ordering` |
| Exact-tier status requires a certified gap of exactly zero | `check_exact_status_requires_zero_gap` |
| Empirical-only evidence cannot promote a theorem to proof-grade status | `check_empirical_cannot_promote_theorem_status` |
| Screening-mode runs cannot emit certificate-tier status | `check_screening_cannot_emit_certificate` |
| A resumed run with restored RNG is not a new independent seed | `check_resumed_run_is_not_independent_seed` |
| Every figure value must exist in its declared source artifact | `check_figure_values_exist_in_source` |
| Every table's declared total must equal its actual row count | `check_table_count_reconciles` |

## 4. Terminal claim-status vocabulary — deliberately NOT migrated yet

The mission (section 0) specifies a terminal-status vocabulary
(`PROVED`, `PROVED_UNDER_ASSUMPTIONS`, `EXACT_CERTIFICATE`,
`VALIDATED_NUMERICAL_CERTIFICATE`, `STATISTICALLY_VALIDATED`,
`EMPIRICAL_ONLY`, `REFUTED`, `OPEN_WITH_PROVED_BOUND`,
`OPEN_WITH_CERTIFIED_GAP`, `OPEN_WITH_COUNTEREXAMPLE_TO_STRONG_FORM`,
`NOVELTY_ESTABLISHED_BY_HUMAN_REVIEW`, `NOVELTY_UNESTABLISHED`) that does
not exactly match the pre-existing, already-in-use
`ALLOWED_CLAIM_STATUSES` in `src/seion_core/certification/claims.py`
(`definition`, `proved`, `proved_under_assumptions`,
`symbolically_verified`, `numerically_verified`, `empirical`,
`heuristic`, `conjecture`, `open`, `refuted`, `superseded`).

Silently rewriting that enum now would be a breaking schema change against
every existing entry in `claims/claims_registry.yaml` across every branch,
undertaken as a side effect of a CI-infrastructure session rather than a
deliberate, reviewed migration. That is exactly the kind of change this
freeze exists to prevent from happening casually. `evidence_contract.py`
therefore accepts *both* vocabularies in its invariant checks (see
`EXACT_TIER_STATUSES`, `EMPIRICAL_ONLY_STATUSES`,
`PROOF_GRADE_THEOREM_STATUSES`) so Phases 5–9 can start assigning the
mission's precise terminal states to new/updated claims immediately,
without forcing an untested repo-wide rename first. A dedicated migration
(new `schemas/MIGRATIONS.md` entry, `claims.py` enum update, and a pass
over every existing registry) is left as explicit future work, not done
here.

## 5. What is and is not covered by this freeze

Covered: schema identity fields, the 12-gate registry, the 7 listed
invariants with real tests, hash-pinned schema drift detection.

Not covered (explicitly out of scope for Phase 2, deferred to their own
mission phases): the A–N pilot/adaptive sweep (Phase 3–4), Track T
formalization (Phase 6–7), signed-forest theory (Phase 8), novelty audit
execution (Phase 9), dataset/atlas construction (Phase 10), paper writing
(Phase 11), external review (Phase 12), release (Phase 13). This document
freezes the *contract* those phases must write evidence against — it does
not itself produce or promote any new scientific claim.
