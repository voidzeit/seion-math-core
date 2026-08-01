# Block M (persistent factorization) — v18 findings (methodology pass)

## What was wrong with the legacy comparison

Legacy block M (~1738) compares HOSVD "signatures" of exactly two scales
(lo, hi) via a single normalized distance; historical `persist_rel` sits
above the declared threshold with the loosest tolerance in the whole suite
(0.25). Mission section 2M requires >= 3 independently constructed
resolutions before any persistence-or-not verdict, since a two-point
comparison cannot distinguish "no persistence" from "these two particular
resolutions/gauges don't align."

## What v18 builds instead, and a real mistake caught along the way

`block_m_persistent_factorization.py`: `hosvd_mode_energy` (per-mode
energy/rank profile) and `persistence_across_resolutions` (full pairwise
comparison across N>=3 seeds, refuses to run on fewer than 3 — enforced,
not just documented).

**The comparison tool itself went through a real failure caught by its own
negative control**, exactly the process mission section 8 asks for: the
first version compared HOSVD left-singular-vector subspaces using the same
`gauge_utils.compare_with_gauge` (free-unitary Procrustes) built for block
J. `test_genuinely_different_random_tensors_show_large_gauge_aligned_distance`
(the required negative control) failed: two **independent random** tensors
were reported as gauge-equivalent (near-zero distance) after alignment.
Diagnosis: the unitary group acts transitively on same-size orthonormal
k-frames, so a free unitary Q always exists mapping any subspace basis to
any other, regardless of whether the subspaces are actually related —
Procrustes-on-orthonormal-bases is mathematically vacuous, not merely
imprecise. Fix: replaced it with **principal angles**
(`principal_angles`, via the SVD of `u_a^H @ u_b`) — the mission's own
explicitly-named tool for this in section 2E, which does not have this
failure mode (confirmed by the corrected negative control now passing:
independent random subspaces show large max principal angle, while a
within-subspace rotation of the same subspace correctly shows ~0). See
`gauge_utils.py`'s module docstring, updated with an explicit warning
against reapplying Procrustes to orthonormal-basis inputs.

## Update: real >=3-resolution experiment now run (see BLOCK_E_FINDINGS.md)

Reusing Block E's three independently-trained resolutions (n=12,18,24,
rank fixed at 4 so reduced-tensor shape matches across scales),
`persistence_across_resolutions` was run directly. Result: rank_needed is
NOT consistent across resolutions ({12:[3,3,4], 18:[3,4,4], 24:[3,3,3]});
mean max principal angle across all pairwise/mode comparisons = 1.01 rad.
**Not uniform failure**: mode 2 of the 12-vs-18 comparison shows a
near-exact match (max angle 1.5e-8) while every other mode/pair shows
substantial misalignment (0.85-1.46 rad) — reported per-mode, per-pair as
mission section 2J/2M requires, rather than averaged into one number that
would hide the anomaly. This pass does not resolve whether that one
aligned mode is coincidence or a real partial invariant — recorded as an
explicit open question, not smoothed over.

## Gate status

`persistence_gate`: `FAIL` for a general persistent-factorization claim
(rank inconsistent across resolutions, most mode/pair comparisons far from
aligned) — now backed by a real, executed >=3-resolution experiment rather
than "not yet evaluated." The one aligned mode is logged as an open
anomaly. The comparison tool itself (principal angles) remains
`EXACT_CERTIFICATE`-tier for what it actually claims (tested against both
positive and negative controls during development).
