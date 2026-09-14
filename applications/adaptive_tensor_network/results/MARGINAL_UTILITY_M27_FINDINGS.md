# M27 — why no allocator score works: the objective is not separable

**EXPLORATORY, NOT CONFIRMATORY.** Same label as the depth sweep it reuses.

Raw: `marginal_utility_raw.json` (400 configs, 5,200 measured marginal
utilities). Analysis: `marginal_utility_analysis.json`, by
`../experiments/analyze_marginal_utility.py`, reusing Level 1's
`metrics.spearman_corr` / `bootstrap_ci`.

## What was measured

For every node `v` eligible for more rank, at a `uniform` base allocation
(chosen so no score is evaluated at a point it selected):

    U_v = E_out(r) - E_out(r + e_v)

the **measured** drop in root error from one more unit of rank — both forward
passes run, nothing predicted. Cost is the rank sum, so the denominator is 1.
Four scores were ranked against it: `eps_v` (local truncation error),
`w_v·eps_v` (pathwise), and the marginal tightening of the M24 and M25 bounds,
`B_root(r) − B_root(r+e_v)`, which is what a certificate-driven greedy step
would rank on.

The root is excluded (it is never projected, so its rank is not a decision
variable). At k=3 that leaves only two allocatable nodes, too few to rank —
**k=3 produces no records**, which is itself a comment on Level 1's design.

## Headline: rank utility is non-monotone, and increasingly so with depth

**42.7% of the 5,200 measured marginal utilities are negative.** Giving a node
*more* rank *increases* root error, almost half the time.

This is not numerical noise:

| | median &#124;U&#124; | p90 | max |
|---|---|---|---|
| positive | 7.24e−03 | 1.27e−01 | 1.57e+01 |
| negative | 2.64e−03 | 6.17e−02 | 9.63e+00 |

87.7% of the negatives exceed 1e−6 of the base root error and 22.6% exceed 1%
of it. And the fraction grows monotonically with depth:

| k | iid | heterogeneous |
|---|---|---|
| 6 | 23.6% | 26.0% |
| 10 | 32.9% | 38.2% |
| 16 | 44.7% | 43.9% |
| 24 | **50.3%** | 46.3% |

At k=24 in the i.i.d. regime, whether more rank helps is a coin flip.

The mechanism is error cancellation: truncation residuals at different nodes
partially cancel in the root, so removing one can destroy a cancellation and
raise the total. It is the applied face of the same fact the extremal theory
is built on — that projected errors compose geometrically rather than adding.

## Spearman rank correlation with U_v

Only the cells with a CI excluding zero are signal; everything else is noise.

| regime | k | eps_v (local) | w_v·eps_v (path) | M24 marginal | M25 marginal |
|---|---|---|---|---|---|
| iid | 6 | +0.066 [−0.068,+0.214] | +0.140 [−0.002,+0.276] | −0.010 | −0.024 |
| iid | 10 | **−0.118** [−0.208,−0.027] | +0.073 | −0.024 | −0.004 |
| iid | 16 | +0.014 | −0.010 | +0.035 | +0.025 |
| iid | 24 | **−0.062** [−0.122,−0.002] | +0.019 | −0.026 | −0.039 |
| het | 6 | **+0.540** [+0.446,+0.630] | **+0.558** [+0.470,+0.638] | **+0.212** | **+0.302** |
| het | 10 | **+0.205** [+0.094,+0.308] | **+0.246** [+0.141,+0.349] | −0.038 | +0.041 |
| het | 16 | +0.071 | +0.054 | +0.011 | +0.054 |
| het | 24 | +0.043 | +0.021 | +0.041 | −0.014 |

Top-1 accuracy — did the score pick the genuinely best node — falls from
0.50–0.56 (het, k=6) to **0.04–0.14** at k=24. Normalized regret is ≈1.0 or
worse at depth, i.e. selecting by score is no better than selecting badly.

## This is outcome 4: no score predicts U_v

The only regime with real signal is `heterogeneous` at k=6, and there the
**naive local error wins** (+0.540) over the pathwise score's +0.558 within
overlapping CIs, and clearly over both certificate marginals (+0.212, +0.302).
By k=16 nothing correlates with anything.

Three consequences:

**1. The allocator comparison was mis-posed, not merely inconclusive.** `U_v`
is not a property of node `v`; it is a function of the entire allocation,
`U_v = U_v(r)`. Both `eps_v` and `w_v·eps_v` are separable scores, and the
measurements show that **the separable scores tested here do not predict deep
marginals** — which is why neither wins, and why `uniform`, the correct hedge
when there is no exploitable signal, is hard to beat.

This is evidence of non-separability, not a proof that no separable score can
work: a non-separable function may still be well approximated by a separable
score in some regime. Establishing impossibility would require exhibiting two
allocations `r`, `r'` that a given score cannot distinguish — identical in the
local information it consumes — with `U_u(r) > U_v(r)` but `U_u(r') < U_v(r')`.
That is a no-go statement about a specific score class and is deferred to M29.

**2. A tighter certificate will not fix the allocator.** This answers the
prioritization question directly. In the one regime with signal, the M24/M25
marginals are *worse* predictors of true utility than the raw local error. The
certificate bounds a worst case; the allocator needs a causal derivative, and
tightening the former does not produce the latter. M28 retains its independent
mathematical motivation — closing the remaining slack in the bound — but
should not be expected to improve allocation.

**3. The certificate under-detects non-monotonicity by about 3×.** The M24 and
M25 marginals are themselves negative 14.3% and 8.8% of the time — so the
bound is *not* monotone in rank, which is worth recording on its own — but
true utility is negative 42.7% of the time. The certificate sees roughly a
third of the non-monotonicity that is actually there.

## What this opens

If `U_v = U_v(r)` with strong inter-node interaction, the next object is the
second-order structure

    d²E / dr_v dr_u

and the question is whether the interaction is low-rank or local (a few
strongly coupled pairs) or dense. That determines whether coupled allocation
is tractable at all, and it is a different problem from anything in the
current campaign. Nothing here says a good allocator is impossible — only that
no *separable* one can work, and that the search should move to the pairwise
structure rather than to more single-node scores.

## Scope

Chain topologies, ambient dimension 6, synthetic cores, `uniform` base
allocation, Δrank = +1. Marginal utility is measured at one base point per
budget; the interaction structure itself was not measured this pass. No
multiple-comparison correction across the 32 reported cells.
