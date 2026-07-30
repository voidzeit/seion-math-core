from __future__ import annotations

from spectral.certification_v18.blocks.block_d_snapping import gap_closing_counterexample, snapping_report


def test_exact_projector_snaps_perfectly():
    r = snapping_report(n=10, rank=3, eps=0.0, seed=0)
    assert r.rank_recovered
    assert r.dist_rel < 1e-8


def test_small_perturbation_still_recovers_rank_within_bound():
    r = snapping_report(n=10, rank=3, eps=0.05, seed=0)
    assert r.rank_recovered
    assert r.dist_rel < 0.1


def test_distance_grows_monotonically_with_perturbation_size():
    rows = [snapping_report(n=10, rank=3, eps=eps, seed=0) for eps in (0.0, 0.1, 0.3, 0.5, 0.7)]
    dists = [r.dist_rel for r in rows]
    assert all(dists[i] <= dists[i + 1] + 1e-9 for i in range(len(dists) - 1))


def test_gap_closing_counterexample_actually_fails_rank_recovery():
    """Required negative control: the gap condition is NECESSARY, not just
    a convenient sufficient condition — demonstrate a case where it's
    violated and rank recovery genuinely fails."""
    c = gap_closing_counterexample()
    assert not c.rank_recovered, "the counterexample must actually misrecover rank, or it proves nothing"
    assert c.spectral_gap < 1.0, "the perturbation must have measurably closed the gap"
