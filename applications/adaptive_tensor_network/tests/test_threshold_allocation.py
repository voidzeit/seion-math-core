from __future__ import annotations

import sys
from pathlib import Path

import numpy as np


APP = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(APP / "src"))
sys.path.insert(0, str(APP / "experiments"))

from allocation import (  # noqa: E402
    threshold_adaptive_allocation,
    threshold_ranks_from_spectra,
    threshold_static_allocation,
)
from run_horizon_aware_allocation import BUNDLE, FIT_BATCH, Instance  # noqa: E402


def test_threshold_ranks_obey_common_cutoff_and_exact_budget() -> None:
    spectra = {
        "a": np.array([5.0, 3.0, 1.0, 0.25]),
        "b": np.array([4.0, 2.0, 0.5, 0.1]),
    }
    ranks, tau = threshold_ranks_from_spectra(
        spectra,
        5,
        minimum_ranks={"a": 1, "b": 1},
        maximum_ranks={"a": 4, "b": 4},
    )
    assert sum(ranks.values()) == 5
    for node_id, rank in ranks.items():
        assert float(np.sum(spectra[node_id][rank:] ** 2)) <= tau
        if rank > 1:
            assert float(np.sum(spectra[node_id][rank - 1 :] ** 2)) > tau


def test_static_threshold_is_deterministic_and_uses_exact_increment_budget() -> None:
    instance = Instance(8, 0)
    minimum = {node: instance.base[node] for node in instance.allocatable}
    budget = sum(minimum.values()) + 18
    first, tau_first = threshold_static_allocation(
        instance.net,
        budget,
        node_ids=instance.allocatable,
        minimum_ranks=minimum,
    )
    second, tau_second = threshold_static_allocation(
        instance.net,
        budget,
        node_ids=instance.allocatable,
        minimum_ranks=minimum,
    )
    assert first == second
    assert tau_first == tau_second
    assert sum(first.values()) == budget
    assert all(first[node] >= minimum[node] for node in instance.allocatable)


def test_adaptive_threshold_adds_exact_bundle_without_refitting_projectors() -> None:
    seed = 0
    instance = Instance(8, seed)
    ranks = dict(instance.base)
    fit_batch = instance.net.sample_leaf_batch(FIT_BATCH, seed=seed * 1000 + 1)
    bases_before = {
        node: instance.net.projectors[node].basis.copy() for node in instance.allocatable
    }
    current_values = instance.net.reduced_forward(fit_batch, ranks)
    minimum = {node: ranks[node] for node in instance.allocatable}
    selected, _ = threshold_adaptive_allocation(
        instance.net,
        sum(minimum.values()) + BUNDLE,
        node_ids=instance.allocatable,
        minimum_ranks=minimum,
        current_values=current_values,
    )
    assert sum(selected.values()) == sum(minimum.values()) + BUNDLE
    assert all(selected[node] >= minimum[node] for node in instance.allocatable)
    for node in instance.allocatable:
        np.testing.assert_array_equal(instance.net.projectors[node].basis, bases_before[node])
