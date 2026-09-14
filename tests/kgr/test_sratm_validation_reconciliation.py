import torch

from seion_kgr.sratm_validation_reconciliation import _rank_from_scores


def test_rank_helper_distinguishes_strict_and_half_tie_policy():
    scores = torch.tensor([[1.0, 1.0, 0.5]])
    gold = torch.tensor([0])
    assert _rank_from_scores(scores, gold, half_ties=False).item() == 1.0
    assert _rank_from_scores(scores, gold, half_ties=True).item() == 1.5
