from __future__ import annotations

import torch
import torch.nn as nn

from seion_kgr.sota.ensemble import normalize_relation_scores, weighted_score_ensemble
from seion_kgr.sota.hard_negative_miner import mine_filtered_hard_negatives
from seion_kgr.sota.losses import listwise_loss, margin_distillation_loss
from seion_kgr.sota.momentum_encoder import MomentumEncoder
from seion_kgr.sota.query_gate import QueryGate
from seion_kgr.sota.retriever import recall_at_k, union_topk
from seion_kgr.sota.splits import SplitContract


def test_split_contract_rejects_test_leakage():
    contract = SplitContract.from_iterables(["a", "b"], ["a"], ["v"], ["t"])
    contract.assert_discovery_ids(["a", "v"])
    try:
        contract.assert_discovery_ids(["t"])
    except ValueError:
        pass
    else:
        raise AssertionError("test leakage was not rejected")


def test_retriever_union_is_deterministic_and_recall_is_exact():
    first = torch.tensor([[0.9, 0.1, 0.2, 0.3]])
    second = torch.tensor([[0.2, 0.8, 0.7, 0.1]])
    candidates = union_topk([first, second], 2)
    assert candidates.tolist() == [[0, 1, 2, 3]]
    assert recall_at_k(candidates, torch.tensor([2])) == 1.0


def test_filtered_miner_excludes_known_positives():
    scores = torch.tensor([[0.1, 0.9, 0.8, 0.7]])
    ids = torch.tensor([0, 1, 2, 3])
    mask = torch.tensor([[False, False, True, False]])
    hard, _ = mine_filtered_hard_negatives(scores, ids, torch.tensor([1]), mask, 2)
    assert hard.tolist() == [[3, 0]]


def test_gate_is_convex_and_momentum_has_no_gradient():
    gate = QueryGate(3, 2, hidden_dim=4)
    weights = gate(torch.ones(5, 3))
    assert torch.allclose(weights.sum(dim=1), torch.ones(5))
    online = nn.Linear(3, 2)
    teacher = MomentumEncoder(online, momentum=0.9)
    assert all(parameter.grad is None for parameter in teacher.parameters())
    teacher.update(online)


def test_ensemble_and_distillation_losses_are_finite():
    scores = torch.tensor([[[1.0, 2.0], [2.0, 1.0]], [[0.0, 1.0], [1.0, 0.0]]])
    relation = torch.tensor([0, 1])
    normalized = normalize_relation_scores(scores, relation)
    result = weighted_score_ensemble(normalized, torch.tensor([1.0, 2.0]))
    assert result.shape == (2, 2)
    assert torch.isfinite(listwise_loss(torch.tensor([1.0, 2.0]), torch.tensor([[0.0, -1.0], [0.5, 0.1]])))
    assert margin_distillation_loss(
        torch.tensor([1.0]), torch.tensor([[0.0, -1.0]]),
        torch.tensor([0.9], requires_grad=True), torch.tensor([[-0.1, -0.9]], requires_grad=True),
    ).isfinite()
