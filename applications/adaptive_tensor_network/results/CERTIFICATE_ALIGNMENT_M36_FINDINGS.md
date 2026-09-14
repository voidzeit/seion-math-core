# M36 — certificates bound well and rank badly

**EXPERIMENTAL. Nothing here is a theorem.** m = 8, 5 seeds, 3 probed states
per seed along a measured-first-order trajectory (steps 0, 2, 4), all
C(8,3) = 56 bundles evaluated at each state. Raw:
`certificate_alignment_raw.json`. Analysis: `m36_analysis.json`,
`m36_alignment_table.csv`.

## The question

M24/M25 are proved upper bounds: `E ≤ G ≤ B ≤ min(B̄, A)`. They claim nothing
about `argmin`. This asked whether they nonetheless rank actions usefully —
which would turn an output of the certification line into an input of the
allocation line.

The bet was asymmetric: a negative result cannot weaken M24/M25, since ranking
is not what they assert. It came out negative.

## Result: no usable ranking information

| surrogate | Spearman | Kendall | top-1 | top-3 | top-5 | regret |
|---|---|---|---|---|---|---|
| A scalar/Frobenius (loosest) | **+0.187** [+0.027, +0.343] | 0.119 | **0.00** | 0.07 | 0.12 | 0.402 |
| B restricted, M24 | +0.102 [−0.077, +0.277] | 0.061 | **0.00** | 0.02 | 0.05 | 0.425 |
| G Gram-aware, M25 (tightest) | +0.108 [−0.052, +0.276] | 0.058 | **0.00** | 0.02 | 0.08 | 0.480 |

**Top-1 agreement is 0.00 for all three surrogates across all 15 states.** Not
once did the action minimizing a certificate delta coincide with the action
minimizing the true objective. Normalized decision regret is 0.40–0.48 of the
candidate spread.

`R²` is omitted from the table: certificate deltas live on a scale orders of
magnitude above `ΔE`, so raw-scale `R²` returns values like −10¹⁰ and is not a
meaningful statistic. The bounds were never calibrated predictors of magnitude
and are not being faulted for failing a test they do not claim to pass.

## Tightness does not imply ranking fidelity — if anything, the reverse

The ordering by certificate tightness is `G ≤ B ≤ A`. The ordering by rank
correlation is the opposite: the **loosest** bound (A, Frobenius) has the only
Spearman interval excluding zero (+0.187 [+0.027, +0.343]), while the two
tighter, sample-wise bounds are statistically indistinguishable from no
correlation.

So the M24/M25 improvements — which recover a factor of 2.4×10¹⁸ in tightness
at depth 24 — buy nothing for decisions, and the effort that made them tight
does not transfer. **Tight upper bounds and good decision surrogates are
distinct objects.**

## What the norm relaxation destroys, quantified

This is the most useful row of the campaign for M28.

| surrogate | fraction of actions predicted to improve | true fraction |
|---|---|---|
| A | 0.976 | **0.354** |
| B | 0.989 | **0.354** |
| G | 0.986 | **0.354** |

The certificates say "adding rank lowers the bound" for **97.6–98.9%** of
actions. The truth is that adding rank lowers the error for **35.4%** of them.
Sign agreement is 0.33–0.36, i.e. the base rate.

The bounds are therefore *near-monotone in rank in practice*, and structurally
blind to the non-monotonicity that M27 established as the defining feature of
this objective. Monotonicity was not assumed by the measurement — `ΔB` was
allowed either sign, and 1.1–2.4% of deltas are indeed positive, so a trace of
non-monotonicity survives the relaxation. But 2% against 65% is not detection.

**This is a direct, quantified statement of what replacing vectors by norms
costs**, and it is the sharpest motivation M28 has so far: the information that
allocation needs is exactly the sign and direction information that the scalar
relaxation discards.

## The terminal-alignment hypothesis is refuted

M35c raised the possibility that a conservative bound might be accidentally
better aligned with terminal value than the one-step objective itself. Using
the exact m = 8 landscape, `V(r+a)` is the best terminal error still reachable
from `r+a`:

| ranking of actions by | Spearman against V(r+a) |
|---|---|
| **true one-step ΔE** | **+0.500** [+0.407, +0.592] |
| A | +0.160 [−0.035, +0.344] |
| B | +0.147 [−0.037, +0.325] |
| G | +0.179 [−0.004, +0.350] |

The certificates are worse than `ΔE` at the terminal question as well as the
immediate one. The hypothesis is dead.

## An independent measurement of myopia

The same table gives something M35c could only infer: **the true one-step
objective explains only half the terminal ordering**, ρ = 0.500 [0.407, 0.592].
Perfect one-step information is a mediocre proxy for terminal value, measured
directly against the exact landscape rather than inferred from policy outcomes.
That supports the M35c reading from a completely independent direction.

## Consequences

- The certification line does **not** feed the allocation line. The proposed
  bridge does not exist as tested.
- M24/M25 are unaffected: they bound, and they were never claimed to rank.
- M28 gains a quantified target: recover sign/direction information, not more
  tightness. Tightness has now been shown not to be the missing ingredient.
- Any future certificate intended as a screening device must be evaluated on
  ranking metrics from the start; tightness is not a proxy for it.

## Scope

m = 8, heterogeneous synthetic regime, 15 states, 56 candidates each,
`b = 3`. Sign statistics pool all 840 candidate evaluations. No claim about
other certificate families or about larger m.
