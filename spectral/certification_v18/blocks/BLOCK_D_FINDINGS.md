# Block D (spectral snapping) — v18 findings

Legacy block D only ever snapped an already-exact projector (trivial:
eigenvalues already exactly {0,1}). v18 builds genuine near-projectors
`P_eps = P + eps*H` (H Hermitian, unit Frobenius norm) and sweeps `eps`.

Empirical sweep (n=10, rank=3, seed=0): rank recovery holds and distance
grows monotonically with `eps` up to the point the spectral gap closes
enough (gap drops from 1.0 to ~0.51 at eps=1.2), at which point snapped
rank becomes 4 instead of 3 — `gap_closing_counterexample` reproduces this
as a required, passing negative control (`test_gap_closing_counterexample_actually_fails_rank_recovery`).
This directly demonstrates the Davis-Kahan-style gap condition is
*necessary*, not just a convenient sufficient condition assumed without
test.

## Gate status

`projector_gate`: `EMPIRICAL_SCREENING_PASS` for rank recovery and distance
bound within the tested perturbation range (float64, single seed sweep +
one designed counterexample — a proper certified statistical sweep across
seeds/dimensions is listed under Phase 5 sweep execution, not claimed
here).
