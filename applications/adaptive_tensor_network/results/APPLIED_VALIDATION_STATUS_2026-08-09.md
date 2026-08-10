# Applied validation status — adaptive tensor-network allocation

This document separates application evidence from the mathematical projected-
tree claims. It does not upgrade a theorem, establish industrial impact, or
replace a preregistered experiment.

## Current evidence

| Level | Design | Result | Interpretation |
|---|---|---|---|
| Level 1 | Preregistered exact synthetic campaign; 2 topologies, 10 seeds, 1,440 raw records | `pathwise_global` beats `singular_energy`, but loses to `uniform` and `local_error_greedy` at equal budget; whole-tree majorant/error correlation is Pearson `0.933`, Spearman `0.922` | Predictive certificate, not a uniformly superior allocator |
| Level 2 | Exploratory teacher-student hierarchical regression; 150 records | No paired comparison is significant | Inconclusive/null at this scale |
| Level 3 | Exploratory Burgers reduced surrogate after a documented design correction; 180 records | `pathwise_global` beats 3/5 baselines, but is tied with some baselines and absolute RMSE is near the mean predictor | Context-dependent relative advantage; weak absolute surrogate |
| Level 4 | Exploratory shared-DAG certificate probe; one diamond topology, 20 seeds, 420 raw records | The domain certificate holds on 140/140 matched cases for both rank-independent and rank-aware allocators; rank-aware beats uniform on 16.4% of sup-error and has mean reduction -0.007448 | Sound DAG certificate validation; negative allocator-superiority result |
| Level 5 | Exploratory shared-DAG matched-tolerance study; one topology, 12 seeds, 180 candidate records and 97 selected records | Validation-selected allocations were evaluated on an independent test batch at tolerances 0.05, 0.10, and 0.15; all selected certificates held, but test tolerance transfer was partial and certificate policies used more contraction units than uniform on average in the matched comparisons | Directly evaluates the requested error/resource tradeoff; still negative/context-dependent and not a technology claim |

Primary evidence is retained in:

- `applications/adaptive_tensor_network/results/LEVEL1_FINDINGS.md`
- `applications/adaptive_tensor_network/results/CAMPAIGN_FINDINGS.md`
- `applications/adaptive_tensor_network/results/level1_raw.json`
- `applications/adaptive_tensor_network/results/level1_analysis.json`

## What is and is not established

Established within the declared experiments:

- the certificate is empirically correlated with whole-tree reconstruction
  error in Level 1;
- the allocation policy is reproducible and its negative controls are
  available;
- relative performance is task-dependent rather than uniformly dominant.
- the shared-subexpression DAG backend is numerically covered by both the
  rank-independent and rank-aware global domain certificates on the declared
  normalized held-out domain;
- the finite-DAG certificate allocator is not uniformly better than a simple
  uniform baseline in the current probe.
- the compressed-coordinate evaluator is algebraically equivalent to the
  projected ambient evaluator, and the matched-tolerance study is reproducible
  with validation-only selection and an independent test batch;
- a valid certificate does not by itself imply lower resource cost at a fixed
  error tolerance: in the Level 5 probe, the certificate policies had negative
  mean contraction-unit reduction relative to uniform.

Not established:

- lower error than every baseline at equal rank budget;
- lower memory or runtime at equal true-error tolerance;
- a general allocator-optimality theorem;
- industrial or technological superiority.
- universal superiority of the shared-DAG certificate allocator.
- lower true error and lower resource cost simultaneously at matched tolerance
  across topologies and structured networks.

The mathematical paper therefore makes no applied-superiority claim. The
application remains a separate exploratory validation track.

## Required next study for a technology claim

A new, preregistered study would need to use train/validation/test separation
and compare all methods at matched true-root-error tolerance. For each method
and task it should report:

1. minimum total rank reaching the tolerance;
2. peak memory and wall-clock reconstruction/training time;
3. error and resource uncertainty over independent seeds;
4. paired comparisons against `uniform`, `singular_energy`,
   `local_error_greedy`, and an oracle where tractable;
5. robustness across structured/trained networks, not only random cores.

Until that study is executed and passes its preregistered criteria, the status
must remain `PREDICTIVE_BUT_NOT_POLICY_SUPERIOR`.
