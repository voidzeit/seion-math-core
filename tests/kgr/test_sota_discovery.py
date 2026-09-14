from __future__ import annotations

import torch
import torch.nn as nn

from seion_kgr.sota_discovery import (
    EntityVectorQueue,
    info_nce_loss,
    mine_hard_negatives,
    update_ema_,
    weighted_margin_loss,
)


def test_mine_hard_negatives_excludes_gold_and_forbidden():
    scores = torch.tensor([[0.1, 0.9, 0.8, 0.7]])
    ids = torch.tensor([10, 11, 12, 13])
    forbidden = torch.tensor([[False, False, True, False]])
    hard_ids, hard_scores = mine_hard_negatives(scores, ids, torch.tensor([11]), 2, forbidden=forbidden)
    assert hard_ids.tolist() == [[13, 10]]
    assert torch.equal(hard_scores, torch.tensor([[0.7, 0.1]]))


def test_losses_are_finite_and_reward_positive_margin():
    positive = torch.tensor([2.0, 1.5])
    negatives = torch.tensor([[0.0, -0.5], [0.2, -0.1]])
    assert torch.isfinite(info_nce_loss(positive, negatives))
    assert weighted_margin_loss(positive, negatives, margin=1.0) == 0


def test_ema_updates_parameters_and_copies_integer_buffers():
    online = nn.BatchNorm1d(2)
    target = nn.BatchNorm1d(2)
    with torch.no_grad():
        online.weight.fill_(2.0)
        target.weight.fill_(0.0)
        online.num_batches_tracked.fill_(7)
    update_ema_(target, online, momentum=0.5)
    assert torch.allclose(target.weight, torch.ones(2))
    assert int(target.num_batches_tracked.item()) == 7


def test_entity_queue_wraps_and_returns_fifo_order():
    queue = EntityVectorQueue(capacity=3, dim=2)
    queue.enqueue(torch.tensor([1, 2]), torch.tensor([[1.0, 0.0], [2.0, 0.0]]))
    queue.enqueue(torch.tensor([3, 4]), torch.tensor([[3.0, 0.0], [4.0, 0.0]]))
    ids, vectors = queue.snapshot()
    assert ids.tolist() == [2, 3, 4]
    assert vectors[:, 0].tolist() == [2.0, 3.0, 4.0]
