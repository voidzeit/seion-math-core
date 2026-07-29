# Adversarial numerical/reproducibility review — v2 draft

Recommendation: major revision; reproducibility infrastructure is strong,
scientific conclusions remain bounded by the theorem scope.

## Verified evidence

- 180 v2 rows completed with zero recorded failures.
- 100 unique scientific instances after object/input/seed/experiment
  identity tracking.
- Five seeds are present for every principal family; the no-gap controls are
  exact boundary constructions and are intentionally not treated as ordinary
  five-seed stochastic experiments.
- All 60 approximate-closure rows respect the registered bound. The largest
  observed tightness ratio is `0.7100467992738069`.
- Five CPU/GPU parity rows completed with maximum absolute discrepancies below
  `1.5e-14` in the recorded run index; CUDA peak memory is recorded.
- Quantitative figures are generated from registered v2 CSVs and emitted as
  PDF/SVG vectors. The conceptual diagrams are separated from measured plots.

## Major concerns

1. The closure bound is tested on small finite tensors and does not establish
   asymptotic sharpness. A ratio below one is evidence of validity, not of
   optimality.
2. Projector recovery is an empirical comparison on one configured object
   family. It is not a recovery theorem and should not be generalized to all
   n-ary laws.
3. The CP sweep is a deterministic diagnostic. It does not establish CP
   identifiability, optimality, or a rank-selection theorem.
4. Runtime, RAM, and VRAM are environment-specific and must remain labelled
   as such.
5. The legacy 0.1 index contains duplicate historical records; the v2 index
   correctly avoids treating those records as independent evidence.

## Required revisions

- Preserve run-level hashes in any release archive and regenerate all tables
  from the v2 matrix in one command.
- Report effect sizes only when a non-degenerate reference variance exists;
  use an explicit not-estimable label otherwise.
- Retain the negative controls and include their exact construction in the
  caption or appendix.
- Do not merge v2 evidence into the legacy release index.

## Verdict

The computational evidence is reproducible and internally consistent for the
finite test regime. It supports the stated bounds and implementation parity,
but it cannot remove the mathematical novelty blocker.
