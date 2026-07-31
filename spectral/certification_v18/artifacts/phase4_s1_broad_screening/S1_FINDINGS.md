# Phase 4 Stage S1 — broad GPU/CPU screening findings

320/320 cells completed, 0 failures, 6316.5s (~105 min) real wall time
on the RTX PRO 5000 Blackwell + Core Ultra 9 285HX, screening blocks
A/G/H/N across arity {3,4} x n {12,24,48,96} x rank {3,6} x cp_rank
{4,8} x 5 seeds x {cpu, cuda}.

## Answer to the open question the Phase 3 pilot raised

The pilot (96 cells, n up to 24 only) found GPU 2.97x slower than CPU
and explicitly flagged this as needing verification at larger scale
before committing Phase 4's scheduling strategy. This stage answers
that: **no GPU/CPU crossover was found anywhere in n in {12, 24, 48,
96}** — CPU remained 3.1x-3.5x faster than GPU at every tested scale,
consistently, not just at the small end:

| n | CPU mean (s) | GPU mean (s) | GPU/CPU ratio |
|---|---|---|---|
| 12 | 9.44 | 30.64 | 3.25x |
| 24 | 9.31 | 30.80 | 3.31x |
| 48 | 9.83 | 34.50 | 3.51x |
| 96 | 7.90 | 25.09 | 3.18x |

The ratio is remarkably stable across a 8x range in ambient dimension —
this is not a transient small-n effect that fades with scale, it is a
consistent property of these specific workloads (block A/G/H/N reports
at these trial/step counts) on this hardware. Kernel-launch overhead and
per-call Python/PyTorch dispatch cost, not compute throughput, dominate
at every scale tested.

## Concrete scheduling decision for the rest of Phase 4

Route S2/S3 (intensification, certification) work for blocks A/G/H/N to
**CPU**, not GPU, unless/until a scale far beyond n=96 is tested (this
stage did not test n>96; the mission's suggested grid goes up to n=96,
which is exactly the top of what was tested here, so this recommendation
covers the full suggested range). Reserve GPU for blocks with
substantially larger per-call tensor operations (E/J/K/M's HOSVD and
multiresolution work, not yet GPU-enabled — see the scope note in
`phase4_s1_broad_screening.py`'s docstring) where batch/kernel work might
actually amortize launch overhead — untested claim, not a finding.

## What this stage does not cover

Blocks B, C, D, E, F, I, J, K, L, M remain CPU-only (no `device`
parameter added to their report functions yet) — this screening pass
says nothing about their GPU/CPU behavior. Arity 5 and cp_rank 16/32
(mission's full suggested grid) were not tested — see the scope-reduction
note in the driver script. No certification-tier (eval_mode=certification)
runs were executed — this stage, like the pilot, is screening-only.
