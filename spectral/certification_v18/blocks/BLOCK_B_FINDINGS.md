# Block B (dynamic commutator explanation) — v18 findings

Three experiments, all in `block_b_commutator.py` / their tests, plus one
cross-check against the legacy historical data already ingested in Phase 0.

## 1. Null control (untrained, random instances)

`run_block_b_ablation(...)` over 30 training + 20 held-out random instances
(n=24, rank=6, float64): `c_theta_as_given` and `randomized_phi_control`
are statistically indistinguishable (held-out means 1.0001 vs 0.99995,
i.e. both ~100% unexplained). **Expected and uninformative on its own** —
at random initialization nothing is aligned with anything. `best_rank_2r`
recovers `raw_comm` to numerical zero (1.5e-15), confirming the rank-<=2r
algebraic bound derived in `model.py` and checked in `test_model.py`.

## 2. Capacity ceiling (isolated single-objective training)

`run_block_b_capacity_test(...)`: train `U` with gradient descent against
**only** the `comm_unexplained_rel` loss (no competing objectives), then
solve in closed form for the best-possible Phi for that same trained `U`
(`solve_optimal_phi` — C_theta is R-linear in Phi for fixed U/K/Delta, so
this is an exact least-squares solve, not an approximation).

Result over 5 seeds (n=24, rank=6, 500 steps, lr=5e-3): both
`trained_real_phi_unexplained_rel` and `optimal_free_phi_unexplained_rel`
converge to ~0 (mean gap 1.7e-9). **The C_theta functional form is not
fundamentally incapable** — mission diagnosis candidate #3 ("insufficient
expressive capacity") is refuted as a general claim about the formula:
when it is the only thing being optimized, it can match the target
essentially exactly.

## 3. Cross-check against the actual historical (multi-objective) checkpoints

This is the decisive, honest finding. The legacy runs never optimize
`comm_unexplained_rel` in isolation — they optimize a weighted sum of ~16
loss terms simultaneously (closure, associator, cyclic, gauge, rigidity,
interscale, ... — see `configure_run_mode`,
`spectral/legacy/v17/seion_master_audit_A_to_N_v17_blackwell_repro_fix.py:1908`).
Per `spectral/legacy/v17/legacy_claim_reclassification.yaml`, every
logged historical run reports `coherence_ratio` at or below ~0 (e.g.
-0.000176 in `BLACKWELL_ULTRA_ASSOC_PASS_900_R6`). Since
`coherence = 1 - unexplained_comm_norm / (raw_comm_norm + eps)`, a
negative coherence means **the trained C_theta performed WORSE than the
trivial zero predictor** at the actual, multi-objective-trained
checkpoints — worse than the crudest baseline in this suite's own list.

## 4. Full ablation matrix (`block_b_ablation_matrix.py`) — mechanism identified

Seven regimes, same seed/dims (n=16, rank=4, cp_rank=4, 400 steps),
isolating each of the mission's candidate mechanisms:

| regime | comm_unexplained_rel | closure_defect | associator_defect |
|---|---|---|---|
| isolated_B_only | 0.000081 | 0.310 | 464.1 |
| plus_closure | 0.000351 | 0.000004 | 74.6 |
| **plus_associator** | **0.008486** | 0.111 | 0.000005 |
| joint_all | 0.005995 | 0.000479 | 0.000001 |
| **frozen_law_train_projector** | **0.992488** | 0.0156 | 0.233 |
| **frozen_projector_train_law** | **0.000000** | 0.738 | 580.9 |
| staged_competing_then_B | 0.000465 | 0.217 | 141.1 |

This resolves the mechanism precisely, ruling out four of the mission's
candidates and confirming one:

- **Not parameterization/capacity**: `frozen_projector_train_law` — `U`
  frozen at its RANDOM initial value, never moved at all, only the CP
  law's parameters (which determine `Phi`) trained — reaches
  `comm_unexplained_rel = 0.000000`, better than every other regime. The
  formula's flexibility through `Phi` alone is enough to explain the
  commutator of an arbitrary, untouched projector. This means `C_theta`'s
  fit is substantially a **`Phi` curve-fit**, not evidence of a special
  geometric relationship between `Delta` and a *learned* `P` — a sharper,
  more concerning version of the capacity finding in section 2 above.
- **Not "the projector needs to be found"**: `frozen_law_train_projector`
  (law frozen at random init, only `U` trained) reaches
  `comm_unexplained_rel = 0.992` — barely moves. Without the freedom to
  also adjust the law, no choice of subspace comes close. Confirms the
  explanatory power lives almost entirely in `Phi`/the law, not in `U`.
- **Not gradient starvation**: `staged_competing_then_B` (competing
  objectives trained first, then switched to B-only) still reaches
  `0.000465` — close to the isolated result — showing B recovers quickly
  regardless of starting point once it is the sole objective.
- **Not closure conflict**: `plus_closure` reaches `0.000351`, barely
  worse than isolated, AND drives closure itself to `0.000004` — B and
  closure are compatible objectives.
- **Confirmed: genuine objective conflict, specifically with the
  associator/GJI-family objective.** `plus_associator` reaches
  `0.008486` — **~100x worse** than isolated training — while satisfying
  the associator objective nearly exactly (`0.000005`). `joint_all`
  lands at a similar order of magnitude (`0.005995`). This is the closest
  reproduction this pass achieves of the real historical regime's order of
  magnitude (`comm_unexplained_rel` 0.03-0.19, `coherence_ratio` <= 0 in
  every logged run) using only two competing terms at equal weight — the
  real 16-term historical loss would compound this further, and scale
  imbalance among those weights likely compounds it more, but the
  fundamental conflict is present and measurable even in this minimal
  two-term setting.

## Honest diagnosis (revised, mechanism-level)

The deployed WARN/FAIL result is best explained by a **real, structural
trade-off between the commutator-explanation objective and the
associator/GJI-family objective**, mediated through `Phi`/the law
parameters — not by insufficient capacity, not by the projector search
being hard, not by gradient starvation, and not by simple scale imbalance
alone (the conflict appears even at equal weight). This is a
mechanism-level answer, not just "multiple objectives compete" — it
specifically implicates the associator/GJI family as the term in
tension with `C_theta`, identifiable and testable in future work (e.g.
sweeping the relative weight between these two specific terms to map the
Pareto frontier, rather than treating the historical fixed-weight choice
as given).

## Gate status (GATE_TAXONOMY.md)

`dynamic_explanation_gate` requires beating every baseline held out or the
gate is `FAIL`, not `WARN`. Given finding 3 (worse than the zero baseline
in the actual trained regime) and the ablation matrix's confirmation of a
genuine, mechanism-level objective conflict:

- `TypedStatus.FAIL` for the "coherent dynamic curvature has real
  explanatory content in the actual multi-objective training regime"
  claim — it does not even beat zero there, and the ablation matrix shows
  why: it trades off against the associator/GJI objective by construction.
- `TypedStatus.FAIL` (not merely "insufficient capacity") for the
  "coherent DYNAMIC curvature" framing specifically — `Phi` alone (with
  `U` frozen at a random, unlearned value) can drive the residual to
  exactly zero, meaning the fit is substantially independent of what the
  projector subspace actually is.
- `TypedStatus.STRUCTURAL_IDENTITY_PASS` only for the narrow claim that
  `raw_comm` is exactly the algebraic identity `K@Delta@P - P@Delta@K`
  (true by construction, checked in `test_model.py`).
- Recommended follow-up: sweep the relative weight between the commutator
  and associator/GJI objectives to map the Pareto frontier (rather than
  the single fixed historical weight choice), and repeat with the actual
  16-term historical loss for full fidelity.
