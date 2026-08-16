# M35 — the repair coefficient is ill-posed as specified; the reference is not a bound

**EXPLORATORY, NOT CONFIRMATORY. This pass reports a failed measurement.**

Raw: `trajectory_repair_raw.json` (12 trials: 4 values of m × 3 seeds).
Analysis: `trajectory_repair_analysis.json`.

## What was attempted

    R_t^inst = E(method's pick at t) − min over the pool at t
    R_T^term = E_method(T) − E_step_oracle(T)
    A_T      = 1 − R_T^term / Σ_t R_t^inst

with `A_T ≈ 1` meaning re-measurement repairs what each step gave up.

## What came out

| m | method | final | vs step-oracle | Σ R_inst | A_T |
|---|---|---|---|---|---|
| 8 | first_order | 2.3518 | **−0.2515** | 0.1039 | 2.188 |
| 8 | full_pairwise | 2.6032 | 0.0000 | 0.0000 | **nan** |
| 8 | lowrank | 2.6032 | 0.0000 | 0.0000 | **nan** |
| 14 | first_order | 4.0016 | +0.0527 | 0.0402 | 0.060 |
| 14 | full_pairwise | 3.9231 | **−0.0258** | 0.0051 | 4.394 |
| 14 | lowrank | 3.9138 | **−0.0351** | 0.0133 | 4.685 |
| 23 | first_order | 6.8733 | +0.1711 | 0.0996 | 1.293 |
| 23 | full_pairwise | 6.6995 | **−0.0027** | 0.0012 | 1.903 |
| 23 | lowrank | 6.6870 | **−0.0152** | 0.0028 | 0.972 |
| 31 | first_order | 25.9367 | +0.0923 | 0.0132 | **−5.547** |
| 31 | full_pairwise | 25.9428 | +0.0983 | 0.0060 | **−4.925** |
| 31 | lowrank | 25.9074 | +0.0629 | 0.0006 | **−116.4** |

`A_T` ranges over 2.19, nan, 0.06, 4.39, 4.69, 1.29, 1.90, 0.97, −5.55, −4.93,
−116.4. It is not measuring repair.

## Diagnosis: numerator and denominator live on different trajectories

`Σ_t R_t^inst` accumulates along the method's **own** path. `R_T^term` compares
against the step-oracle's **final state**, reached by a different path. Once the
two diverge — which happens at step 1 — the terminal gap is dominated by *which
basin each ended in*, not by the per-step losses that were supposed to explain
it. At m = 31 first order's terminal gap (0.092) is seven times everything it
gave up along the way (0.013), so `1 − R/Σ` returns −5.5. The ratio is not
bounded, not signed, and not a fraction of anything.

## The load-bearing failure: the step-greedy oracle is not an upper bound

The reference is beaten repeatedly:

- at m = 8, `first_order` ends **0.25 better** than the step-oracle — 10% of
  the final error;
- at m = 14, both pairwise methods end better (3.913 and 3.923 against 3.949);
- at m = 23, both pairwise methods end better again (6.687 and 6.700 against
  6.702).

Choosing the truly best bundle at every step does not produce the best
trajectory. Step-greedy is myopic, and the size of that myopia is comparable to
or larger than the regret the experiment set out to measure. Any statistic
normalized by it inherits the problem.

This is itself a finding, and it also invalidates a reading of M34: `E_oracle`
there is a *single-step* optimum, which is the right reference for a
single-step question, but the M33/M35 trajectory questions have no oracle at
all under this design.

## What the data does and does not support

Terminal error of `first_order` minus `lowrank_pairwise`, relative to the final
error: **−10.7% (m=8), +2.2% (m=14), +2.8% (m=23), +0.11% (m=31)**. No monotone
trend, sign changes, n = 3 seeds. **The question M35 was built to answer — does
re-measurement stop repairing as m grows — is not answered.** It is not
answered negatively either; the experiment cannot distinguish.

Note also that absolute errors are not comparable across m: the final error is
~2.6 at m = 8 and ~25.9 at m = 31, since deeper chains carry more truncation.
Only within-m comparisons are meaningful, which the table above respects.

## The corrected design

The reference must be a common one, and repair must be measured
counterfactually rather than against a divergent path:

    from the method's own state at step t, continue with the step-optimal rule
    to the horizon; call the result E_t^continue. Then the recoverable part of
    step t's loss is E_t^continue − E_T^method, and repair is measured entirely
    within one trajectory.

That costs one sub-trajectory per (method, step), roughly `T` times the current
budget, which is affordable at these sizes. It also removes the need for the
step-greedy oracle to be a bound, since it is only ever used as a continuation
from a state the method actually reached.

Two further changes: seeds must go well above 3 given the effect sizes seen
here (0.1–3% of final error), and the comparison should be reported within m
only.

## Salvaged from this pass

- A reproducibility bug was found and fixed: the pool RNG was seeded with
  `hash(method)`, which Python salts per process, so candidate pools differed
  between runs. Now seeded by method index.
- The step-greedy oracle is documented as **not** a valid trajectory reference
  for this problem, with three concrete counterexamples.
