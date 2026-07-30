# Typed-gate taxonomy — spectral A-N certification, v18

This replaces the v17 scoring system (`compute_master_score`: WARN -> 0.5,
N/A -> 1.0, then averaged across 14 blocks — see
`spectral/legacy/v17/legacy_run_dedup_report.md` for the historical
consequence: every logged run capped near 75-89/100 even under that
inflated scheme, none reaching 100, and none run in `eval_mode=certification`).

No status here carries partial credit. Nothing is averaged across critical
gates. A block or gate either earns a specific typed status with a stated
meaning, or it does not.

## 1. The 10 typed states

Applied per-block-per-run. Ordered here from weakest to strongest evidence,
but they are **not** a numeric scale — a `STRUCTURAL_IDENTITY_PASS` is not
"worth less" than a `NUMERICAL_SANITY_PASS`, it is a *different kind of
claim* with different non-implications (see per-state notes).

| State | Meaning | What it does NOT mean |
|---|---|---|
| `STRUCTURAL_IDENTITY_PASS` | The check verifies a property that is true by construction (e.g. `P = UU*` is idempotent because it is literally constructed as `UU*` with orthonormal `U`). | Does not mean the underlying object (e.g. the subspace `U` spans) is meaningful, learned, or non-trivial. |
| `NUMERICAL_SANITY_PASS` | A quantity stayed within a loose blow-up/sanity range (no NaN/Inf, no runaway magnitude). | Does not mean the quantity is small in any scientifically meaningful sense, or that any hypothesis is supported. |
| `EMPIRICAL_SCREENING_PASS` | A metric beat a *screening*-mode threshold, i.e. one from `thresholds_for_mode(eval_mode="screening")`, which the legacy code sets at least as loose as the certification threshold (observed up to ~1000x looser, e.g. block A: 1e-5 vs 1e-10). | Does not license certification language. Not comparable across a screening/certification boundary. |
| `STATISTICALLY_VALIDATED_PASS` | A stochastic claim (e.g. n-ary closure over random trials) has a reported confidence interval or held-out validation across independently-seeded trials that supports the claim beyond a single trial. | Does not mean the bound is provably worst-case; still an empirical estimate with a stated confidence level, not a supremum. |
| `VALIDATED_NUMERICAL_CERTIFICATE` | float64/complex128, TF32 disabled, deterministic algorithms, strict checkpoint loading, restored RNG, held-out seed(s) never used in training, independent CPU/GPU-parity rerun — full certification-mode discipline per mission section 3 — and the metric beats the certification threshold. | Does not mean the result is exact or that the constant involved is sharp/optimal. |
| `EXACT_CERTIFICATE` | A closed-form, symbolic, interval-arithmetic, or exhaustive finite-case verification with no floating-point tolerance involved (e.g. small-case symbolic idempotency, exhaustive small-arity closure, interval eigenvalue enclosure). | Does not extend to cases outside what was actually exhausted/enclosed. |
| `WARN` | A metric was computed under adequate discipline (screening or certification) but did not beat its threshold, or a caveat (non-strict resume, seed=3 constant across the historical lineage, lr=0 replay, etc.) materially weakens the evidence quality. | Never averaged into a numeric score. A run with any `WARN` on a required block cannot support a passing claim for that block. |
| `FAIL` | A metric was computed under adequate discipline and clearly violates the defining property being tested (this state did not exist in v17 at all — see legacy dedup report; v17's worst case was always `WARN`). | — |
| `NOT_APPLICABLE` | The check's precondition does not hold for this configuration (e.g. block E/J/M interscale checks when no hi-resolution scale exists). | **Does not count toward a pass and carries zero weight** — this corrects v17's `compute_master_score`, which scored N/A as full credit (1.0), inflating scores for runs that never exercised the block at all. |
| `NOT_CERTIFIABLE_AS_DEFINED` | The check as currently specified cannot in principle distinguish a true positive from a false positive for this claim (e.g. a cyclic-symmetry check applied to a law with cyclic averaging built structurally into its `forward()` — see block N below) — the definition itself needs to change before any status here is informative. | Not a temporary data problem; a spec problem. Re-running with more compute does not resolve it. |

## 2. The 8 critical gates

Each of the 14 blocks (A-N) feeds exactly one or more of these. A gate's
status is the **minimum** (weakest, per the ordering below) over every
block that feeds it — never an average.

Gate strength ordering (weakest to strongest, used only to pick the
minimum, not to compute a mean): `NOT_CERTIFIABLE_AS_DEFINED` <
`FAIL` < `WARN` < `NOT_APPLICABLE` (excluded from the pass condition
entirely, see below) < `STRUCTURAL_IDENTITY_PASS` <
`NUMERICAL_SANITY_PASS` < `EMPIRICAL_SCREENING_PASS` <
`STATISTICALLY_VALIDATED_PASS` < `VALIDATED_NUMERICAL_CERTIFICATE` <
`EXACT_CERTIFICATE`.

| Gate | Fed by blocks | Required minimum for gate PASS |
|---|---|---|
| `projector_gate` | A (projector validity), D (spectral snapping) | `EMPIRICAL_SCREENING_PASS` (screening) / `VALIDATED_NUMERICAL_CERTIFICATE` (certification) |
| `algebra_gate` | G (n-ary closure), H (associator), N (cyclic law/GJI) | same as above; G/H additionally require `STATISTICALLY_VALIDATED_PASS` before any certification-tier claim, since they are stochastic-trial estimates |
| `dynamic_explanation_gate` | B (commutator explanation), C (finite Beals proxy) | `EMPIRICAL_SCREENING_PASS` minimum; B additionally requires beating every mission-mandated baseline (zero/scalar/linear/low-rank/regression/randomized) held out, or the gate is `FAIL`, not `WARN` — a coherent-curvature claim that cannot beat a trivial baseline is a refutation, not a near-miss |
| `interscale_gate` | E (subspace transport), J (tensor interscale) | `NOT_APPLICABLE` when no hi-resolution scale exists (excluded from pass condition, not counted as passing); otherwise same tiers as above |
| `gauge_gate` | L (gauge canonicalization) | `EMPIRICAL_SCREENING_PASS` minimum; must report residual gauge group under degenerate spectra, not just the unitarity check |
| `persistence_gate` | K (HOSVD compactness), M (persistent factorization) | `NOT_APPLICABLE` when no hi-resolution scale exists; otherwise same tiers |
| `reproducibility_gate` | cross-cutting (not a single letter block) — derived from `legacy_claim_reclassification.yaml` / v18 run manifests | requires `restore_rng=true`, `strict_resume=true` (if resumed), `lr>0` (if claiming optimization evidence), and at least one held-out seed distinct from any training seed |
| `mathematical_proof_gate` | F (rigidity), I (reduced tensor extraction, artifact-integrity only) | `I` can only ever reach `STRUCTURAL_IDENTITY_PASS` (it is extraction/parity, not a scientific claim per mission section 2I); `F` requires an explicitly-named matrix (Hessian / GGN / Fisher-like) per mission section 2F, or it is `NOT_CERTIFIABLE_AS_DEFINED` until renamed/recomputed |

## 3. Fail-closed combination rule

- A **global A-N certificate** requires every required critical gate above
  to independently reach at least `EMPIRICAL_SCREENING_PASS` (screening
  run) or `VALIDATED_NUMERICAL_CERTIFICATE` (certification run). There is
  no aggregate numeric score. `NOT_APPLICABLE` gates are excluded from the
  requirement (not counted as passing, not counted as failing) and must be
  listed explicitly as excluded, with the reason, in every certificate
  artifact — never silently omitted.
- If **any** required critical gate is `WARN`, `FAIL`, or
  `NOT_CERTIFIABLE_AS_DEFINED`, the global state is one of the mission's
  `FAIL_CLOSED_*` states, named after the specific gate (e.g.
  `FAIL_CLOSED_BLOCK_B_REFUTED`, `FAIL_CLOSED_INTERSCALE_PERSISTENCE_NOT_ESTABLISHED`),
  never a generic low percentage.
- `eval_mode=screening` runs may never emit a certificate-tier status
  (`VALIDATED_NUMERICAL_CERTIFICATE` or `EXACT_CERTIFICATE`) for any gate,
  enforced in code (see `spectral/certification_v18/gates.py`), not by
  convention — this is the single specific defect the legacy data shows
  being violated in spirit (runs named `*_CERT_*` that were actually run in
  `eval_mode=screening`; see `legacy_claim_reclassification.yaml`).
- No AI process may self-issue `PASS_A_TO_N_FULL_CERTIFICATION`. The
  ceiling this suite can self-issue is `PASS_A_TO_N_PARTIAL_CERTIFICATION`,
  pending the human review mission section 10 requires.

## 4. Known-unresolved blocks (do not let these masquerade as near-passes)

Per the legacy data already ingested in Phase 0
(`spectral/legacy/v17/legacy_claim_reclassification.yaml`):

- **B (dynamic commutator explanation)**: `coherence_ratio` observed
  slightly negative (e.g. -0.000176 in `BLACKWELL_ULTRA_ASSOC_PASS_900_R6`),
  `comm_unexplained_rel` ~3.8e-2, `normal_unexplained_rel` ~2.6e-1 — matches
  the mission's own stated historical values almost exactly. `WARN` in
  every historical run. Must run the full baseline ablation set (Phase 2)
  before any claim about `C_theta`'s explanatory power is made.
- **J (tensor interscale)**: `WARN` in every run that has a hi-resolution
  scale.
- **M (persistent factorization)**: `WARN` in every run that has a
  hi-resolution scale; has the loosest legacy tolerance in the whole suite
  (0.25), which itself should be questioned in Phase 2 rather than treated
  as a validated threshold.
