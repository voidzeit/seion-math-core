# M35c — lookahead was the bottleneck, not pairwise information

**EXPERIMENTAL. Nothing here is a theorem.** m = 8, 5 seeds, exact terminal
optimum available. Raw: `rollout_calibration_raw.json`. Analysis:
`m35c_analysis.json`, `m35c_rollout_table.csv`.

Rollout scores a candidate action by the outcome of continuing with a base
policy rather than by its immediate cost:

    Q_t^{pi_0,h}(r,a) = E( take a at r, then h-1 rounds under pi_0 )
    pi_rollout(r)     = argmin_a Q_t^{pi_0,h}(r,a)

`h = 1` evaluates `E(r+a)` and is therefore exactly exhaustive step-greedy over
all 56 bundles; `h = 6` continues to the horizon. `h = 0` is the base policy
run alone. Because m = 8 has an exact `E_terminal_star`, the normalization
`Gamma = R_T^rollout / R_T^base` shares a valid reference in both terms.

## Result

Two estimands of `Gamma` are reported because `mean(X)/mean(Y)` is not
`mean(X/Y)` and quoting one as the other invites suspicion. `G_rm` is the
ratio of mean regrets; `G_mr` is the mean of per-seed paired ratios, with a
paired bootstrap CI. Both are correct; they answer slightly different
questions ("how much regret remains in aggregate" versus "by what factor does
a typical instance improve").

| base | h | E_T | true regret | G_rm | G_mr | paired CI95 | rank | percentile | evals |
|---|---|---|---|---|---|---|---|---|---|
| measured_first_order | 0 | 2.1974 | 0.2298 | 1.000 | 1.000 | — | 24,148 | 10.261% | 55 |
| measured_first_order | 1 | 2.3543 | 0.3867 | 1.683 | 1.690 | **[1.052, 2.866]** | 40,073 | 17.027% | 337 |
| measured_first_order | 2 | 2.0785 | 0.1109 | 0.483 | 0.759 | [0.254, 1.508] | 677 | 0.287% | 2,857 |
| measured_first_order | 3 | 2.0086 | 0.0409 | 0.178 | 0.305 | [0.062, 0.732] | 37 | 0.016% | 4,873 |
| measured_first_order | 4 | 2.0027 | 0.0351 | 0.153 | 0.166 | [0.036, 0.299] | 23 | 0.010% | 6,385 |
| measured_first_order | 5 | 2.0157 | 0.0480 | 0.209 | 0.220 | [0.036, 0.420] | 86 | 0.037% | 7,393 |
| measured_first_order | 6 | **1.9895** | **0.0218** | **0.0951** | **0.1217** | **[0.028, 0.245]** | **11** | **0.005%** | 7,897 |
| local_greedy | 0 | 2.3206 | 0.3530 | 1.000 | 1.000 | — | 37,591 | 15.973% | 1 |
| local_greedy | 1 | 2.3543 | 0.3867 | 1.095 | 1.582 | [0.589, 3.091] | 40,073 | 17.027% | 337 |
| local_greedy | 2 | 2.1125 | 0.1448 | 0.410 | 0.691 | [0.134, 1.570] | 6,744 | 2.865% | 337 |
| local_greedy | 6 | 2.2352 | 0.2676 | 0.758 | 0.807 | [0.660, 0.953] | 16,859 | 7.163% | 337 |

So full-horizon rollout on a first-order base closes **90.5%** of the regret in
aggregate and **87.8%** for the mean instance; the paired interval
[0.028, 0.245] excludes 1, so the improvement is significant per instance and
not driven by one landscape.

The `h = 1` row is the sharpest single number in the campaign: its paired
interval **[1.052, 2.866] excludes 1 from above**. Exhaustive one-step
optimization is significantly *worse* than the base policy it replaces, not
merely no better.

Seed-matched true regret, `h = 1` minus `h`, positive meaning lookahead helps:

| base | h=2 | h=3 | h=4 | h=5 | h=6 |
|---|---|---|---|---|---|
| measured_first_order | **+0.276 +** | **+0.346 +** | **+0.352 +** | **+0.339 +** | **+0.365 +** |
| local_greedy | +0.242 (0) | +0.199 (0) | +0.182 (0) | +0.225 (0) | +0.119 (0) |

## Three findings

**1. Full-horizon rollout lands at rank 11 of 235,348** — the 0.005th
percentile of the admissible terminal landscape, regret 0.0218 against the
base policy's 0.2298. That is a 10.5× reduction in true terminal regret, and
every depth `h ≥ 2` beats step-greedy significantly with a first-order base.

**2. Exhaustive one-step optimization is worse than not optimizing at all.**
`h = 1` gives `Gamma = 1.690` against a measured-first-order base and 1.582
against a local-greedy base: choosing the truly best immediate bundle at every
step ends up *worse* than simply following the base policy. This is the
sharpest form of the myopia result — it is not that greedy is merely
suboptimal, it is that exact greedy is actively harmful relative to a cheaper
heuristic.

**3. The base policy determines whether rollout helps.** With a first-order
base every `h ≥ 2` is significant; with a local-greedy base none are. Rollout
inherits the quality of its continuation, which is what policy-improvement
theory would predict, and is a caution against reading "rollout works" as
unconditional.

Depth is not perfectly monotone — `h = 4` (0.0351) beats `h = 5` (0.0480) —
but `h ≥ 3` is uniformly in the top 0.04% while `h = 1` is at the 17th
percentile.

## What this reorders

Placing M35c beside M35b at the same m and reference:

| approach | evals | true regret |
|---|---|---|
| measured first order, no lookahead | 55 | 0.2298 |
| **full pairwise model of the immediate objective** | 228 | **0.3867** |
| exhaustive step-greedy | 342 | 0.3867 |
| rollout, first-order base, h = 2 | 2,857 | 0.1109 |
| rollout, first-order base, h = 6 | 7,897 | **0.0218** |

**Modelling the immediate objective better makes the terminal outcome worse**;
it converges to step-greedy, which is the thing that hurts. Spending the same
kind of budget on lookahead instead reduces terminal regret by an order of
magnitude. The bottleneck in M27–M35b was not missing pairwise information —
it was missing horizon.

## A_action

Per-step action agreement between `h = 1` and deeper rollout is **0.000–0.167**:
the policies choose almost entirely different actions, not the same actions in
a different order. Note this settles the agreement question *between lookahead
depths*, not the M35b question of whether `full_pairwise` and `step_greedy` take
identical actions — their terminal regrets agree to six decimals in all five
seeds, but their action sequences remain unmeasured.

## Scope and caveats

m = 8 only, 5 seeds, one base allocation, `b = 3`, `T = 6`, heterogeneous
synthetic regime. Rollout costs 55 → 7,897 evaluations, a factor of 144; no
claim is made that this is economical, only that it is where the terminal
quality is. Scaling requires first-order screening to a top-K shortlist before
reranking, which is untested. Nothing here is proved.
