from __future__ import annotations

import numpy as np
import torch

from seion_kgr.data import build_filters
from seion_kgr.sratm_certified_compression import (
    full_rank_equivalence,
    load_train_valid_only,
)
from seion_kgr.sota.sratm import SpectralRelationAdaptiveTensorMixture


def test_train_valid_loader_does_not_require_test_file(tmp_path):
    train = tmp_path / "train.txt"
    valid = tmp_path / "valid.txt"
    train.write_text("a\tr\tb\nb\tr\tc\n", encoding="utf-8")
    valid.write_text("a\tr\tc\n", encoding="utf-8")

    kg = load_train_valid_only(train, valid)

    assert kg.test == []
    assert kg.num_entities == 3
    assert kg.num_relations_total == 2
    assert kg.tails_of_hr


def test_sratm_full_rank_factor_equivalence_on_tiny_model():
    torch.manual_seed(7)
    model = SpectralRelationAdaptiveTensorMixture(
        num_entities=6,
        num_relations=4,
        entity_dim=8,
        relation_dim=8,
        experts=2,
        active_per_relation=1,
        expert_rank=4,
        core_basis=1,
    ).eval()
    rows = np.asarray(
        [[0, 0, 1], [1, 1, 2], [2, 0, 3], [3, 1, 4]],
        dtype=np.int64,
    )

    result = full_rank_equivalence(model, rows, torch.device("cpu"), candidate_count=6)

    assert result["status"] == "PASS"
    assert result["rank_equality_fraction"] == 1.0
    assert result["max_abs_error"] < 1e-5
