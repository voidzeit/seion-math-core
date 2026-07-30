# A–N terminal classification (SEION V5 Phase 5)

Exit-gate record for `PASS_A_TO_N_TERMINAL_CLASSIFICATION`. Assigns each
of the 14 blocks the mission's own precise typed terminal vocabulary
(mission section 5), grounded in the existing `BLOCK_*_FINDINGS.md` files
and `final_gate_evaluation.py`'s computed gate output, cross-checked
against this session's Phase 3 pilot sweep (96 cells, `spectral/
certification_v18/artifacts/pilot_sweep/`) where the pilot covered the
same blocks (A, G, H, N). No new experiments were run to produce this
document beyond what Phase 3 already executed — this is verification and
formal synthesis, not fresh derivation, exactly as Phase 6/7's Track T
synthesis was.

**Computed final gate (unchanged by this document — it is code-derived,
not asserted)**: `FAIL_CLOSED_PROJECTOR_GATE_NOT_ESTABLISHED`. 6 of 8
critical gates below minimum: `projector_gate`, `algebra_gate`,
`dynamic_explanation_gate`, `interscale_gate`, `persistence_gate`,
`reproducibility_gate`. Only `gauge_gate` and `mathematical_proof_gate`
pass. This document explains *why*, block by block, in the mission's own
vocabulary — it does not change the computed result, and cannot: no code
path here promotes a screening-tier run to a certificate.

## A — Projector

- **Construction**: `PASS_PROJECTOR_CONSTRUCTION`. Idempotence,
  self-adjointness, rank, eigenvalue clustering all hold to machine
  precision for any orthonormal `U` (`BLOCK_A_FINDINGS.md`); a negative
  control (real transpose instead of conjugate transpose) is confirmed
  broken, so the check is not vacuous.
- **Relevance**: `PROJECTOR_RELEVANCE_NOT_ESTABLISHED`. Construction
  integrity was never claimed to imply relevance (mission's own
  non-implication, enforced by this suite's status ceiling of
  `STRUCTURAL_IDENTITY_PASS`); no experiment in this campaign tested
  whether the specific learned subspace `U` is scientifically meaningful
  independent of its construction.

## B — Dynamic commutator explanation

**`REFUTED_IN_DEPLOYED_REGIME`**, with a specific identified mechanism,
not a bare fail. 7-regime ablation matrix (`BLOCK_B_FINDINGS.md`,
`block_b_ablation_matrix.json`): `coherence_ratio <= 0` universally
across 15 real historical checkpoints when trained jointly with the
associator/GJI objective (the actual deployed regime) — worse than a
zero predictor. Isolated-training ablation shows ~100x degradation
vs. joint training, diagnosing genuine objective conflict rather than
capacity starvation. `frozen_projector_train_law` reaching
`unexplained_rel` exactly 0 with `U` never trained indicates the fit is
substantially a curve-fit through the law's own parameters — a
`NON_IDENTIFIABLE` contributing mechanism, not a separate verdict.

## C — Finite Beals proxy

**`FINITE_PROXY_BOUNDED_OVER_TESTED_RANGE`** for n in [8, 64] (8x
dimension increase): max norm grows from 3.02 to 4.12, saturating rather
than blowing up. **`OPEN_SCALING_LIMIT`** beyond n=64 — no asymptotic
form was fit against the data, so nothing is claimed about the limit.
Explicitly not `PsiDO^0` or any continuum Beals-theorem statement, per
mission section 2C's non-implication (enforced by the renamed block
identity `FINITE_BEALS_PROXY`, not just prose).

## D — Spectral snapping

**`EMPIRICAL_SCREENING_PASS`**, with a confirmed gap-closing
counterexample (`eps=1.2`, spectral gap 1.0 -> ~0.51, snapped rank
flips from 3 to 4 — `test_gap_closing_counterexample_actually_fails_rank_recovery`
passes as a required negative control). **Not** `VALIDATED_NUMERICAL_CERTIFICATE`:
the runs behind this finding used `eval_mode=screening` (per
`config.py`'s hard contract, a screening-mode run cannot emit a
certificate-tier status even if the underlying arithmetic is exact-ish;
see `evidence_contract.check_screening_cannot_emit_certificate`, Phase 2).
Reaching the certificate tier requires an explicit certification-mode
rerun (float64, TF32 disabled, held-out seeds) — not attempted this pass.

## E — Interscale subspace transport

**`NO_PERSISTENCE_SIGNAL_IN_DECLARED_REGIME`**, where the declared
regime is 3 independently-trained resolutions (n=12,18,24; the mission's
preferred minimum is 5 — this is a real scope limitation, not silently
extended past what was tested). Frozen lift, principal angles (not
vacuous Procrustes — see the real bug this campaign caught and fixed,
`BLOCK_M_FINDINGS.md`), random + interpolation baselines. Transported
angles sit near maximal (~pi/2); the trained lift beats both baselines in
only 2 of 3 pairs, by a small margin. Most likely mechanism: the same
closure-objective non-identifiability Block F independently found via
basin instability (corroborating, not coincidental).

## F — Rigidity

**`NON_IDENTIFIABLE`**, not merely "rigid" or "not rigid" — per the
mission's own explicit instruction, near-zero loss across ~89-degree
separated subspaces (3 seeds, n=6, rank=2) is evidence *against*
uniqueness, stated as such rather than left ambiguous. Exact Hessian vs.
Generalized Gauss-Newton correctly distinguished (indefinite vs.
non-negative-by-construction, cross-checked against finite differences at
2.6e-8 relative error) — the curvature *machinery* is validated even
though the conclusion is non-identifiability, not rigidity.

## G — N-ary closure

**`STATISTICALLY_VALIDATED_PASS`** achieved (2000-sample empirical
distribution with mean/std/quantiles/worst/95%-UCB, plus adversarial
gradient-ascent search confirmed at least as strong as random sampling).
**`OPEN_WITH_PROVED_BOUND`** for a certified analytic upper bound:
exhaustive small-case / interval-arithmetic / SOS certification was
explicitly not attempted this pass (`BLOCK_G_FINDINGS.md`) — the current
number is a strong statistical estimate, not a certified supremum.

## H — Associator (two distinct claims, per mission section 3H)

**A–N associator ratio supremum**: `EMPIRICAL_SCREENING_PASS`,
verdict `CONSTANT_2_NOT_SHARP_TIGHTER_BOUND_AVAILABLE` — reproduced and
strengthened this session. Original campaign (single config, n=16,
rank=4, cp_rank=4): max observed ratio 0.452 of the triangle bound 2.0.
This session's Phase 3 pilot (16 configs x 3 seeds x 2 devices = 96
cells, reduced trial counts): max observed ratio ranges **0.130 to
0.957** across configurations (mean 0.334) — wider than the single prior
data point, but every one of the 96 cells still lands strictly below the
bound and every cell's verdict is `NOT_SHARP`, so this *broadens* the
evidence for the same conclusion rather than contradicting it. Sharpness
of constant 2 remains `OPEN` (not refuted, not confirmed sharp).

Track T's separate `E_assoc^P <= 2*rho*M*L` constant is out of scope
here — see [`track_t_v5_terminal_status_k2_k3.md`](../track_t_v5_terminal_status_k2_k3.md)
(Phase 6/7, a different track by mission's own strict separation rule).

## I — Reduced tensor extraction

**`EXACT_IMPLEMENTATION_CERTIFICATE`**. Two independently-coded
extraction paths agree to <1e-10 relative difference (float64) and
<1e-4 (float32); an exact rational small case (`fractions.Fraction`, zero
floating point) matches the general formula exactly. Extraction-integrity
scope only, per mission section 2I — no compactness/persistence/
significance claim is or was made here.

## J — Tensor interscale

**`NO_PERSISTENCE_SIGNAL_IN_DECLARED_REGIME`** (`interscale_gate`,
shared with block E) — same 3-resolution experiment as block E, reusing
its independently-trained models. The comparison *methodology* itself
(raw / Procrustes-aligned / permutation-aligned / amplitude-ratio,
reported separately rather than collapsed into one legacy heuristic
number) is validated and reusable; what the methodology found, once
actually run, is a negative result.

## K — HOSVD compactness

**`HOSVD_COMPACTNESS_OBSERVED`** (never elevated to an analytic
theorem, per mission section 2K's explicit ceiling). Mode ranks needed
[3,4,4] out of full rank 4 at 99% energy threshold (n=16, rank=4,
cp_rank=4); 4.5% in-sample Tucker reconstruction error, 6.6% on an
independently-seeded held-out instance using the *same* truncation ranks
— the rank choice generalizes even though the specific basis doesn't
(expected, since each instance's CP law is independently random).

## L — Gauge canonicalization

**`EXACT_CERTIFICATE`**-tier for the canonicalization/degeneracy-detection
logic itself (confirmed against both a simple-spectrum case, stable under
1e-9 perturbation, and a deliberately constructed exactly-degenerate case,
eigenvalues 2/1/1, correctly flagged with residual gauge dimensions per
cluster) — not a claim about any specific learned tensor's gauge
structure, only about the tool's correctness.

## M — Persistent factorization

**`NO_PERSISTENCE_SIGNAL_IN_DECLARED_REGIME`** as the primary verdict
(rank inconsistent across the 3 resolutions: {12:[3,3,4], 18:[3,4,4],
24:[3,3,3]}; mean max principal angle 1.01 rad across all pairwise/mode
comparisons). **`OPEN_ANOMALOUS_MODE`** carried forward explicitly, not
smoothed over: mode 2 of the 12-vs-18 comparison shows a near-exact match
(max angle 1.5e-8 rad) against a backdrop of otherwise-large
misalignment (0.85-1.46 rad elsewhere) — per the project's own roadmap
note, this anomaly "must be replicated or discarded, not left as-is." It
was neither replicated nor discarded in this pass; it remains open,
named, and load-bearing for anyone resuming this block. A real
implementation bug was caught and fixed en route (free-unitary Procrustes
on orthonormal bases is vacuous — replaced with principal angles; see
`BLOCK_M_FINDINGS.md` and `gauge_utils.py`'s module docstring).

## N — Cyclic law and GJI

- **Symmetrized cyclic defect**: `STRUCTURAL_IDENTITY_PASS`
  (8.2e-33, machine-precision zero — guaranteed by `forward()`'s
  construction for any CP parameters, never evidence of learned
  symmetry). Raw (pre-averaging) defect 4.60, correctly kept separate.
- **GJI formula**: `EXACT_CERTIFICATE`-tier internal consistency — two
  independent implementations agree to 2.8e-16 relative difference across
  100 trials; a sign-mutation test confirms the cross-check is not
  vacuous.
- **GJI ratio magnitude**: `EMPIRICAL_SCREENING_PASS` only, supremum
  explicitly `OPEN`. Original campaign: mean 0.43, adversarial max 5.98.
  This session's pilot (16 configs x 3 seeds, reduced adversarial
  effort): adversarial max ranges 4.65-5.92 across configurations (mean
  5.58) — consistent with, and reproducing, the original single-config
  finding rather than contradicting it. The ratio is confirmed **not**
  bounded by 1 in general; whether it is bounded at all remains open.

## Summary table

| Block | Primary terminal state | Secondary/open |
|---|---|---|
| A | `PASS_PROJECTOR_CONSTRUCTION` | `PROJECTOR_RELEVANCE_NOT_ESTABLISHED` |
| B | `REFUTED_IN_DEPLOYED_REGIME` | mechanism: `NON_IDENTIFIABLE` (curve-fit) |
| C | `FINITE_PROXY_BOUNDED_OVER_TESTED_RANGE` | `OPEN_SCALING_LIMIT` beyond n=64 |
| D | `EMPIRICAL_SCREENING_PASS` | certificate tier open (no certification-mode rerun yet) |
| E | `NO_PERSISTENCE_SIGNAL_IN_DECLARED_REGIME` | regime limited to 3/5 preferred resolutions |
| F | `NON_IDENTIFIABLE` | — |
| G | `STATISTICALLY_VALIDATED_PASS` | `OPEN_WITH_PROVED_BOUND` (no certified upper bound yet) |
| H | `EMPIRICAL_SCREENING_PASS`, `NOT_SHARP` | sharpness `OPEN` |
| I | `EXACT_IMPLEMENTATION_CERTIFICATE` | — (closed) |
| J | `NO_PERSISTENCE_SIGNAL_IN_DECLARED_REGIME` | shares E's scope limit |
| K | `HOSVD_COMPACTNESS_OBSERVED` | — |
| L | `EXACT_CERTIFICATE` (tool only) | — (closed) |
| M | `NO_PERSISTENCE_SIGNAL_IN_DECLARED_REGIME` | `OPEN_ANOMALOUS_MODE` (12-vs-18 mode 2) |
| N | `STRUCTURAL_IDENTITY_PASS` + `EXACT_CERTIFICATE` (formula) | GJI ratio supremum `OPEN` |

Two blocks reach a genuinely closed state (I, L — both tool/extraction
integrity claims, not scientific-relevance claims). No block reaches
`VALIDATED_NUMERICAL_CERTIFICATE` or higher for a scientific (not
tool-integrity) claim — every such run in this campaign's history used
`eval_mode=screening`, and Phase 2's frozen invariant forbids promoting
that to certificate tier regardless of how clean the numbers look.
