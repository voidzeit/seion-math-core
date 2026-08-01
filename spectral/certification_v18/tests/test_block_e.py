from __future__ import annotations

import pytest

from spectral.certification_v18.blocks.block_e_interscale import interscale_experiment


def test_requires_at_least_three_resolutions():
    with pytest.raises(ValueError, match="at least three"):
        interscale_experiment(resolutions=[12, 18], steps=10)


def test_experiment_runs_and_reports_all_pairwise_comparisons():
    result = interscale_experiment(resolutions=[10, 14, 18], rank=3, cp_rank=3, steps=60)
    assert len(result["comparisons"]) == 3  # 3 choose 2
    assert result["held_out_resolution"] == 18
    for c in result["comparisons"]:
        fwd = c["forward"]
        assert 0.0 <= fwd.trained_transport_max_angle <= 3.2
        assert 0.0 <= fwd.random_baseline_max_angle <= 3.2
