import numpy as np
import torch

from seion_kgr.sratm_g6_valid import _filter_block


class _KG:
    num_relations_original = 1
    tails_of_hr = {(0, 0): np.asarray([1, 3], dtype=np.int64)}
    heads_of_rt = {(0, 2): np.asarray([0], dtype=np.int64)}


def test_filter_block_restores_gold_after_filtering_known_positives():
    scores = torch.tensor([[0.1, 0.9, 0.8, 0.7]], dtype=torch.float32)
    bounds = torch.ones_like(scores)
    rows = np.asarray([[0, 0, 1]], dtype=np.int64)
    gold_scores = torch.tensor([0.9], dtype=torch.float32)
    filtered, filtered_bounds = _filter_block(scores, bounds, rows, _KG(), 0, gold_scores)
    assert torch.isclose(filtered[0, 1], torch.tensor(0.9))
    assert torch.isneginf(filtered[0, 3])
    assert torch.isclose(filtered_bounds[0, 1], torch.tensor(1.0))
    assert torch.isneginf(filtered_bounds[0, 3])
