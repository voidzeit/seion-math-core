# Preregistered hypotheses — adaptive tensor network rank allocation (AI4)

Written before the final Level 1 campaign run (`run_level1_campaign.py`)
that produces `results/level1_raw.json`. Any deviation from this plan,
if made after seeing results, will be recorded explicitly in
`results/level1_analysis.md`'s "deviations" section rather than silently
folded in.

## Primary hypothesis

At equal total rank budget $B$, **pathwise global-contribution
allocation** (`pathwise_global`) produces lower true root reconstruction
error than uniform, singular-energy, and local-error-greedy allocation,
averaged over topologies and seeds.

**Test**: paired comparison (same seed, same topology, same budget,
different method) of true root RMS error; Wilcoxon-signed-rank-style sign
test via bootstrap CI on the mean paired difference; report Cohen's d.
Significance threshold: 95% bootstrap CI for the mean paired difference
excludes 0, in the direction predicted (pathwise_global lower).

## Secondary hypothesis

At equal true-root-error tolerance, pathwise_global reaches that
tolerance at a lower total rank budget than the other methods (rank
efficiency).

**Test**: for each (topology, seed), find the smallest budget at which
each method's true error drops below a fixed tolerance $\tau$ (swept
over a small grid); compare the resulting budgets paired by
(topology, seed).

## Design

- **Topologies**: chain (depth 3, 4 leaves... 4 internal nodes for
  depth=4) and balanced-binary (4 leaves, 3 internal nodes), leaf
  dimension 6, ambient dimension 6 at every internal node.
- **Seeds**: 10 independent seeds per topology (network core tensors +
  leaf-data batch both reseeded per trial) — satisfies the mission's
  "at least 10 seeds for synthetic tasks."
- **Budgets**: swept over a grid from the minimum feasible (1 per node)
  to near-full-rank, at least 5 distinct budgets per topology.
- **Methods compared**: `uniform`, `singular_energy`,
  `local_error_greedy`, `random`, `gradient_based`, `pathwise_global`,
  plus `oracle` (exhaustive search, small trees only — the chain/balanced
  topologies above are small enough: at most $6^4$ combinations, capped
  at 2000 evaluated combinations per the oracle's own cap).
- **Ablations** (AI6): `local_source_only`, `path_amplification_only`,
  `universal_coarse_k_minus_1`, `root_residual_negative_control`,
  `random_path_coefficients` — same budgets/seeds/topologies.
- **No test-set leakage**: projectors are fit once per (topology, seed)
  from a fixed fitting batch; true error is measured on an
  \emph{independent} held-out evaluation batch, same seed's RNG stream
  advanced (not reused) — verified by a dedicated test
  (`tests/test_no_leakage.py`).
- **Independent samples**: each (topology, seed, budget, method)
  combination is one independent execution; no run is repeated or
  resumed and counted twice (single-process, deterministic, no
  CPU/GPU duplicate-counting risk at this scale — Level 1 does not use
  the GPU).

## Success criteria (mission AI7)

Declared **before** running: primary hypothesis supported if the 95%
bootstrap CI for pathwise_global's mean paired error reduction vs. the
best of {uniform, singular_energy, local_error_greedy} excludes 0 in the
predicted direction. If not supported, that is reported as a stated
negative result — not omitted, not re-run with a different design to
find significance.
