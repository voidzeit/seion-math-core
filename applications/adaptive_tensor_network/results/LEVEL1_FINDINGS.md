# Level 1 findings — exact synthetic validation

Raw data: `level1_raw.json` (1,440 records: 2 topologies x 10 seeds x 6
budgets x 12 methods/ablations). Analysis: `level1_analysis.json`,
computed by `analyze_level1.py` per the preregistered design in
`../experiments/PREREGISTRATION.md`. All numbers below are read directly
from that file — none are asserted from memory.

## Primary hypothesis: MIXED, honestly reported

Preregistered claim: pathwise_global beats uniform, singular_energy, and
local_error_greedy at equal budget.

| Baseline | Mean error reduction (pathwise vs baseline) | 95% CI | Supported? |
|---|---|---|---|
| uniform | −0.055 | [−0.074, −0.036] | **No** — uniform is significantly *better* |
| singular_energy | +0.095 | [0.028, 0.163] | **Yes** |
| local_error_greedy | −0.077 | [−0.100, −0.057] | **No** — local_error_greedy is significantly *better* |

**This is a negative result for 2 of 3 preregistered comparisons**,
retained and reported per the preregistration's own commitment, not
omitted or re-run to find significance. Regret-vs-oracle confirms this:
`local_error_greedy` has the *lowest* mean regret (0.345) of all 6 real
methods, ahead of `pathwise_global` (0.423) and `uniform` (0.368).

## Secondary hypothesis (rank efficiency): also not supported

At every tested error tolerance, pathwise_global did **not** reach the
tolerance at a lower budget than uniform or local_error_greedy (negative
or zero mean budget savings across all three tolerances tested).

## What worked: calibration and correlation (success criterion 3)

- The pathwise majorant is a genuine upper bound in every one of 100
  measured (topology, seed, budget) triples for pathwise_global
  (ratio true-error/majorant always in $[0.35, 0.93]$, never $>1$) —
  consistent with, though not a proof of, the theory's own bound.
- Predicted majorant correlates strongly with true error across **all**
  methods and configs: Pearson $r=0.933$, Spearman $\rho=0.922$
  ($n=1320$) — this is real, positive, statistically strong support for
  AI7's success criterion 3 ("consistent correlation between the
  theoretical contribution and measured marginal benefit"), even though
  criteria 1 and 2 (lower error / lower rank at equal budget) were not met
  in this design.

## Ablations: informative, not merely confirmatory

- `local_source_only` (drop the path-amplification factor entirely)
  **outperforms** full `pathwise_global` in this design (mean error
  −0.077 relative to pathwise, i.e. lower) — suggesting that in this
  experiment's fully-random (untrained) core tensors, the path-
  amplification term is not adding value over local truncation error
  alone, and may even be actively unhelpful.
- `path_amplification_only` (drop local error, keep only path structure)
  is clearly **worse** than full pathwise_global (+0.232) — local
  information does matter; it just isn't improved by multiplying with
  this experiment's path amplification estimate.
- `root_residual_negative_control` (deliberately wrong) is confirmed
  **worse** than pathwise_global (+0.043, CI excludes 0) — the intended
  negative control behaves as expected, after a bug fix (the first
  version used a per-tree constant factor that couldn't perturb the
  greedy ranking at all — caught and fixed before trusting the result;
  see git history for `ablation_root_residual_negative_control`).
- `random_path_coefficients` is **statistically indistinguishable** from
  the real path amplification (CI $[-0.079, 0.042]$ includes 0) — a
  genuine negative finding: in this design, the *actual measured* path
  amplification factors perform no better than random positive
  coefficients of similar scale, reinforcing the `local_source_only`
  finding that path amplification is not pulling its weight here.

## Interpretation — why the primary hypothesis failed here, honestly

The network cores in this Level 1 design are **fully random, untrained
tensors** (mission's own Level 1 spec: "exact synthetic validation").
Under fully random composition, path amplification factors are
themselves noisy estimates with no consistent long-range structure to
exploit — the pathwise method's theoretical advantage (correctly
weighting deep, high-leverage nodes) may require either (a) trained/
structured networks where amplification factors are stable and
meaningful (Level 2/3, where cores are fit to real data), or (b) deeper
trees than the depth-3/3-node topologies tested here, where propagation
effects compound more. Both are testable follow-ups, not attempted this
pass.

## Explicitly not measured this pass

Per-node Spearman/Pearson correlation between predicted node
contribution (`score_v`) and each node's individually-ablated marginal
benefit (AI5 asks for this at node granularity, not just whole-tree
majorant-vs-error) — would require one additional rank-perturbation
experiment per node per config, not run this pass. The whole-tree
correlation above (0.93/0.92) is a real, positive, but coarser proxy for
the same underlying question.
