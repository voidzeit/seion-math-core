import numpy as np

from seion_core.projectors.snapping import snapping_counterexample_without_gap, spectral_snap


def test_spectral_snapping_has_idempotent_output_with_gap():
    near = np.diag([0.1, 0.9, 0.2])
    projector, report = spectral_snap(near)
    assert report["gap_condition_satisfied"]
    assert report["rank_after_snapping"] == 1
    assert projector.diagnostics()["idempotence_error"] < 1e-12


def test_no_gap_counterexample_is_registered():
    assert snapping_counterexample_without_gap()["rank_flip"] is True

