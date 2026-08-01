# Block E (interscale subspace transport) — v18 findings

Non-circular design: three `SpectralModelV18` instances independently
initialized and trained (n=12, 18, 24; rank=4; cp_rank=4; 300 gradient
steps each on the same gauge-invariant closure objective as Block F, no
cross-resolution reference anywhere), one frozen Gaussian-kernel lift
operator per pair of dimensions (never trained), transported via principal
angles (not raw distance or vacuous Procrustes), against a random-subspace
baseline and a nearest-index interpolation baseline, with the largest
resolution (n=24) naturally held out from calibrating anything.

**Real result: no meaningful transport signal.**

| pair | trained-lift angle | random baseline | interpolation baseline | beats both? |
|---|---|---|---|---|
| 12->18 | 1.4101 | 1.4797 | 1.5267 | yes (small margin) |
| 12->24 | 1.4721 | 1.4165 | 1.4681 | **no** |
| 18->24 | 1.4067 | 1.5532 | 1.4462 | yes (small margin) |

All angles sit at 1.41-1.53 rad, i.e. essentially at the maximum possible
(pi/2 = 1.571, meaning fully orthogonal subspaces). Where the trained lift
"beats" a baseline, the margin (0.02-0.15 rad) is small relative to how
close every condition already is to maximal orthogonality — this reads as
noise around "no relationship," not a real transport signal, and in one of
the three pairs the trained lift does not even beat the random-subspace
baseline. This is consistent with, and independently corroborates, Block
F's basin-instability finding: even the SAME resolution trained from
different seeds converges to nearly-orthogonal subspaces under this
closure-only objective, so independently-trained DIFFERENT resolutions
landing on unrelated subspaces is the expected consequence of the same
underlying non-identifiability, not a separate new failure.

**Also serves Block M's real-multiresolution requirement**: the three
resolutions share the same reduced-tensor shape (rank=4 fixed across
scales), so `persistence_across_resolutions` (block M) was run directly on
the three trained reduced tensors. Result: rank_needed is NOT consistent
across resolutions ({12: [3,3,4], 18: [3,4,4], 24: [3,3,3]}); mean max
principal angle across all pairwise mode comparisons = 1.01 rad. Notably
NOT uniform failure: mode 2 of the 12-vs-18 comparison shows a near-exact
match (max angle 1.5e-8, i.e. numerically zero) while every other
mode/pair shows substantial misalignment (0.85-1.46 rad) — a genuinely
mixed result the mission's per-mode, per-pair reporting requirement is
designed to surface rather than average away.

## Diagnosis

Neither "persistence holds" nor "persistence definitively fails for all
structure" is fully supported. What the evidence supports: under a
closure-only training objective, independently-trained resolutions do not
reliably converge to related subspaces or reduced-tensor structure, with
one notable per-mode exception whose cause (coincidence vs. a real partial
invariant) this pass does not resolve. Given Block F's basin-instability
finding, the most likely explanation is the same one: a single objective
(closure) under-constrains the subspace enough that resolution-to-
resolution agreement is not expected; the historical multi-objective
training regime (which this pass does not reproduce, matching Block B's
scope boundary) might behave differently and is the natural next
experiment.

## Gate status

`interscale_gate`: `FAIL` for "the current lift/comparison methodology
demonstrates persistent interscale structure" (2 of 3 pairs show no
advantage over a random baseline given the scale of the effect; explicit
`NOT_CERTIFIABLE`-adjacent per mission's fail-closed rule that a single
outlying aligned mode does not license a general persistence claim).
`persistence_gate` (shared with block M): same `FAIL`, with the one
per-mode exception recorded as an open, unresolved anomaly rather than
smoothed over.
