# M33 — the coupled allocator works, and the coupling is almost all of the cost and almost none of the gain

**EXPLORATORY, NOT CONFIRMATORY.**

Raw: `coupled_allocator_raw.json` (12 configurations). Analysis by
`../experiments/analyze_coupled_allocator.py`.

Protocol: D = 16, 15 internal nodes, all ranks starting at 2, six rounds of
`+1` to each of three nodes, every method following its own trajectory from its
own state. Surrogate optimization is **exhaustive** over all `C(14,3) = 364`
bundles, and the exact oracle searches the same 364 candidates with the true
objective — so any difference between methods is the model, not the solver.
`first_order` uses **measured** `U_v`, making it a first-order oracle rather
than a heuristic.

## The i.i.d. regime is inert, not tied

All seven methods appeared identical at four decimals. They are not tied — the
root error barely responds to rank at all. Adding 18 units of rank across 15
nodes moves it from 4.03884 to 4.03882, a relative change of **~5×10⁻⁶**.

With i.i.d. Gaussian cores at D = 16 the nodewise spectra are near-flat, so
truncating to rank 2 versus rank 5 out of 16 discards comparably vast energy
either way and the error has already saturated. **No allocator can distinguish
itself in a regime where the objective does not move.** This is a degenerate
operating point, not a null result about the methods, and the earlier table's
`1.0000` entries were a rounding artifact of normalizing to four decimals.

## The heterogeneous regime: the target pattern holds

True root error after six rounds, normalized per instance to the round-1
uniform value, with acquisition cost in forward evaluations:

| method | r1 | r3 | r6 | evaluations |
|---|---|---|---|---|
| uniform | 1.0000 | 1.0058 | 0.9716 | 0 |
| local_greedy | 1.0188 | 0.9956 | 0.9760 | 0 |
| pathwise | 1.0088 | 0.9892 | 0.9692 | 0 |
| first_order | 0.9795 | 0.9439 | **0.9128** | 90 |
| full_pairwise | 0.9747 | 0.9429 | **0.9111** | 636 |
| lowrank_pairwise | 0.9747 | 0.9422 | **0.9125** | 636 |
| oracle | 0.9741 | 0.9420 | **0.9057** | 2274 |

Paired against `local_greedy` on the final round:

| | mean | 95% CI | |
|---|---|---|---|
| first_order | +0.0632 | [+0.0278, +0.1089] | **+** |
| full_pairwise | +0.0649 | [+0.0290, +0.1103] | **+** |
| lowrank_pairwise | +0.0635 | [+0.0279, +0.1094] | **+** |
| oracle | +0.0702 | [+0.0369, +0.1125] | **+** |
| lowrank vs full | −0.0014 | [−0.0027, +0.0001] | 0 |

Two things hold as predicted. Second-order allocation significantly beats every
heuristic. And **low-rank ≈ full pairwise**: the difference is −0.0014 with a
CI that includes zero, so `q = 4` costs nothing measurable in allocation
quality, exactly as M32A's prediction result implied.

## But the interaction term buys almost nothing over measured first order

This is the finding that matters, and it cuts against the applied promise of
M29–M32.

The gap from `local_greedy` to `first_order` is **0.0632**. The further gap
from `first_order` to `full_pairwise` is **0.0017** — under 3% of it. The
headroom above first order, measured by the oracle, is only
`0.9128 − 0.9057 = 0.0071`, and the pairwise surrogate captures 0.0017 of it,
about **24%**; the low-rank version captures 0.0003, about **4%**.

The cost of that is **636 evaluations against 90**, a factor of 7.1.

So: essentially all of the achievable gain comes from *measuring* `U_v`
instead of estimating it with a heuristic score. The interaction term, whose
low-rank structure M29–M31 established and whose predictive value M32A
confirmed, contributes a quarter of a residual 0.8% at seven times the
acquisition cost.

**Why this does not contradict M32A.** That pass measured predictive quality
over bundles sampled uniformly across the whole range, where the pairwise term
raised R² from 0.767 to 0.970. M33 measures *selection at the top of the
distribution*. A model can be far better across the range while barely
improving the argmax, because near the optimum the leading candidates are
close together and first order already ranks them adequately. Prediction
quality and selection quality are different things, and only the second one
is what an allocator needs.

## Status of the allocation programme

- Incremental binary rounds with measured `U`: **works**, +6.3% over the best
  heuristic, significant, and reaches 91% of the oracle's improvement.
- The low-rank compression of `I`: **validated** — it costs nothing relative
  to full pairwise, in both prediction (M32A) and selection (here).
- The interaction term itself: **not worth its cost at this scale**. 7× the
  evaluations for 24% of a 0.8% residual.
- The i.i.d. regime: **objective is inert**; no allocation question exists
  there at this operating point.

The honest summary is that M29–M33 discovered a real and compressible
structure, and simultaneously showed that exploiting it is not where the value
is. The value is in measuring first-order utility directly rather than
predicting it — which is a much cheaper conclusion than the one this line was
pursuing, and would not have been visible without the oracle comparison.

## Scope

12 configurations (2 families × 2 regimes × 3 seeds), one starting allocation,
one budget schedule, D = 16, m = 14 allocatable. The relative standing of
first-order versus pairwise may change at larger `m`, where heuristics degrade
further and the interaction has more room to matter; that is untested. Nothing
here is a claim about trained networks.
