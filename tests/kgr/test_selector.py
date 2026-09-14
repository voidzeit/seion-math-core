"""Campaign Phase B2: the learned sparse path selector.

Covers exactly the mandatory test list: permutation invariance, budget
compliance, no queried-edge leakage, gold-path preservation after
supervised warmup, deterministic top-k under a fixed tie policy,
gradients reaching selector parameters, negligible overhead when
disabled, and evaluator-semantics stability across selector modes.
"""
import time

import numpy as np
import pytest
import torch

from seion_kgr.data import tiny_kg
from seion_kgr.evaluate import evaluate
from seion_kgr.model import SeionKGRv26
from seion_kgr.reasoner import Adjacency, PathReasoner
from seion_kgr.selector import LearnedPathSelector, select_edges, supervised_priority_loss

pytestmark = pytest.mark.symbolic


# ------------------------------------------------------------------ select_edges modes


def test_full_neighborhood_keeps_everything():
    candidates = [(0, i) for i in range(10)]
    result = select_edges("full_neighborhood", candidates, budget=3)
    assert sorted(result.kept_indices) == list(range(10))


def test_budgeted_bfs_respects_exact_budget():
    candidates = [(0, i) for i in range(20)]
    rng = np.random.default_rng(1)
    result = select_edges("budgeted_bfs", candidates, budget=5, rng=rng)
    assert len(result.kept_indices) == 5
    assert len(set(result.kept_indices)) == 5  # no duplicates


def test_budgeted_bfs_below_budget_keeps_all_without_rng():
    candidates = [(0, i) for i in range(3)]
    result = select_edges("budgeted_bfs", candidates, budget=10, rng=None)
    assert sorted(result.kept_indices) == [0, 1, 2]


def test_unknown_mode_rejected():
    with pytest.raises(ValueError):
        select_edges("not_a_real_mode", [(0, 1)], budget=1)


# ------------------------------------------------------------------ learned_topk: budget, determinism, permutation invariance


def _learned_topk_setup(n=12, dim=6, rank=3, seed=0):
    torch.manual_seed(seed)
    selector = LearnedPathSelector(dim=dim, max_depth=4)
    candidates = [(i % 3, i) for i in range(n)]
    x_u = torch.randn(dim)
    relation_embed = torch.randn(3, dim)
    query_vec = torch.randn(dim)
    dst_base_embed = torch.randn(n + 5, dim)
    return selector, candidates, x_u, relation_embed, query_vec, dst_base_embed


def test_learned_topk_respects_exact_budget():
    selector, candidates, x_u, relation_embed, query_vec, dst_base_embed = _learned_topk_setup()
    result = select_edges(
        "learned_topk", candidates, budget=4, selector=selector, x_u=x_u,
        relation_embed=relation_embed, query_vec=query_vec, dst_base_embed=dst_base_embed, depth=0,
    )
    assert len(result.kept_indices) == 4
    assert len(set(result.kept_indices)) == 4


def test_learned_topk_is_deterministic_given_fixed_inputs_and_seed():
    selector, candidates, x_u, relation_embed, query_vec, dst_base_embed = _learned_topk_setup()
    kwargs = dict(
        selector=selector, x_u=x_u, relation_embed=relation_embed,
        query_vec=query_vec, dst_base_embed=dst_base_embed, depth=0,
    )
    r1 = select_edges("learned_topk", candidates, budget=4, **kwargs)
    r2 = select_edges("learned_topk", candidates, budget=4, **kwargs)
    assert r1.kept_indices == r2.kept_indices  # exact same order, no RNG involved in learned_topk itself


def test_learned_topk_tie_policy_breaks_by_original_index():
    """Force an exact tie by using a selector whose MLP output is
    constant (achieved by zeroing all weights), so every candidate has
    the same score — the tie policy must then pick the FIRST `budget`
    candidates by original index, deterministically."""
    dim = 4
    selector = LearnedPathSelector(dim=dim, max_depth=4)
    with torch.no_grad():
        for p in selector.parameters():
            p.zero_()
    candidates = [(0, i) for i in range(8)]
    x_u = torch.randn(dim)
    relation_embed = torch.randn(1, dim)
    query_vec = torch.randn(dim)
    dst_base_embed = torch.randn(8, dim)
    result = select_edges(
        "learned_topk", candidates, budget=3, selector=selector, x_u=x_u,
        relation_embed=relation_embed, query_vec=query_vec, dst_base_embed=dst_base_embed, depth=0,
    )
    assert result.kept_indices == [0, 1, 2]  # all-zero MLP output -> tie -> lowest original indices win


def test_learned_topk_permutation_invariance_of_neighbor_ordering():
    """Shuffling the candidate list before scoring must select the SAME
    set of underlying (relation, dst) edges — the selector is a pure
    per-edge scoring function, not order-dependent."""
    selector, candidates, x_u, relation_embed, query_vec, dst_base_embed = _learned_topk_setup(n=10)
    result_a = select_edges(
        "learned_topk", candidates, budget=4, selector=selector, x_u=x_u,
        relation_embed=relation_embed, query_vec=query_vec, dst_base_embed=dst_base_embed, depth=0,
    )
    kept_edges_a = {candidates[i] for i in result_a.kept_indices}

    rng = np.random.default_rng(3)
    perm = rng.permutation(len(candidates))
    shuffled = [candidates[i] for i in perm]
    result_b = select_edges(
        "learned_topk", shuffled, budget=4, selector=selector, x_u=x_u,
        relation_embed=relation_embed, query_vec=query_vec, dst_base_embed=dst_base_embed, depth=0,
    )
    kept_edges_b = {shuffled[i] for i in result_b.kept_indices}
    assert kept_edges_a == kept_edges_b


def test_learned_topk_gradients_reach_selector_parameters():
    selector, candidates, x_u, relation_embed, query_vec, dst_base_embed = _learned_topk_setup()
    result = select_edges(
        "learned_topk", candidates, budget=4, selector=selector, x_u=x_u,
        relation_embed=relation_embed, query_vec=query_vec, dst_base_embed=dst_base_embed, depth=0,
    )
    loss = result.keep_weight.sum()
    loss.backward()
    total_grad = sum(float(p.grad.norm().item()) for p in selector.parameters() if p.grad is not None)
    assert total_grad > 0.0


# ------------------------------------------------------------------ oracle_or_gold_path_debug_mode + supervised warmup


def test_oracle_debug_mode_force_keeps_gold_edges():
    candidates = [(0, i) for i in range(10)]
    gold = {2, 7}
    rng = np.random.default_rng(5)
    result = select_edges("oracle_or_gold_path_debug_mode", candidates, budget=3, rng=rng, gold_edge_indices=gold)
    assert gold.issubset(set(result.kept_indices))
    assert len(result.kept_indices) == 3


def test_gold_path_preservation_after_supervised_warmup():
    """A tiny graph where node 0 has 6 outgoing edges but only edge index
    3 is 'gold' (leads toward the true answer). Before training, a
    randomly initialized selector has no reason to rank it highly; after
    a few supervised BCE steps against the gold label, it must be in the
    top-k under a tight budget."""
    torch.manual_seed(11)
    dim = 8
    selector = LearnedPathSelector(dim=dim, max_depth=4)
    n = 6
    gold_pos = 3
    x_u = torch.randn(dim)
    relation_embed = torch.randn(2, dim)
    query_vec = torch.randn(dim)
    dst_base_embed = torch.randn(n, dim)
    gold_mask = torch.zeros(n)
    gold_mask[gold_pos] = 1.0

    opt = torch.optim.Adam(selector.parameters(), lr=0.05)
    for _ in range(200):
        opt.zero_grad()
        x_u_rep = x_u.unsqueeze(0).expand(n, -1)
        a_s = relation_embed[torch.zeros(n, dtype=torch.long)]
        scores = selector.score(x_u_rep, a_s, query_vec, dst_base_embed, depth=0, accumulated_priority=torch.zeros(n))
        loss = supervised_priority_loss(scores, gold_mask)
        loss.backward()
        opt.step()

    candidates = [(0, i) for i in range(n)]
    result = select_edges(
        "learned_topk", candidates, budget=2, selector=selector, x_u=x_u,
        relation_embed=relation_embed, query_vec=query_vec, dst_base_embed=dst_base_embed, depth=0,
    )
    assert gold_pos in result.kept_indices, (
        f"gold edge index {gold_pos} not preserved after supervised warmup: kept={result.kept_indices}"
    )


# ------------------------------------------------------------------ reasoner-level: leakage, overhead, evaluator stability


def test_no_queried_edge_leakage_under_learned_topk():
    """The excluded (queried) edge must never appear as a message source
    even when the graph is small enough that it would otherwise be
    within budget and score highly (all-zero selector -> everything
    ties -> lowest-index wins, which would include the queried edge if
    leakage prevention were broken)."""
    kg = tiny_kg()
    adjacency = Adjacency.build(kg)
    dim = 4
    reasoner = PathReasoner(dim=dim, rank=2, num_layers=1, max_neighbors=8, selector_mode="learned_topk")
    with torch.no_grad():
        for p in reasoner.selector.parameters():
            p.zero_()  # tie-break by index -> would pick the queried edge first if leakage prevention failed
    rel_embed = torch.randn(kg.num_relations_total, dim)
    entity_embed = torch.randn(kg.num_entities, dim)
    h_ids, r_ids, t_ids = torch.tensor([0]), torch.tensor([0]), torch.tensor([1])
    query_vecs = torch.randn(1, dim)

    frontiers = reasoner.run_batch_frontiers(
        adjacency, rel_embed, h_ids, r_ids, t_ids, query_vecs, seed=1, training=True, entity_embed=entity_embed,
    )
    # Node 0's outgoing edges in the reciprocal-closed tiny graph are
    # (0,0,1) -- the queried triple, which must be excluded -- and
    # (0,3,5), a genuinely different edge (relation 3 is 1's reciprocal,
    # from base triple (5,1,0)) that must NOT be excluded. So the
    # leakage check is: node 1 is never reached via the direct excluded
    # edge, while node 5 legitimately can be.
    assert 1 not in frontiers[0], f"queried edge (0,0,1) leaked into the frontier: {frontiers[0]}"


def test_disabled_selector_budgeted_bfs_overhead_is_negligible():
    """budgeted_bfs (selector=None) must not be meaningfully slower than
    it was before this module existed — a smoke-level timing check, not
    a strict benchmark (CI hardware varies), so the bound is generous."""
    kg = tiny_kg()
    adjacency = Adjacency.build(kg)
    dim = 8
    reasoner = PathReasoner(dim=dim, rank=3, num_layers=2, max_neighbors=8, selector_mode="budgeted_bfs")
    assert reasoner.selector is None
    rel_embed = torch.randn(kg.num_relations_total, dim)
    h_ids, r_ids, t_ids = torch.tensor([0, 2, 4]), torch.tensor([0, 1, 0]), torch.tensor([1, 3, 5])
    query_vecs = torch.randn(3, dim)

    start = time.perf_counter()
    for _ in range(20):
        reasoner.run_batch_frontiers(adjacency, rel_embed, h_ids, r_ids, t_ids, query_vecs, seed=1, training=True)
    elapsed = time.perf_counter() - start
    assert elapsed < 5.0, f"budgeted_bfs took {elapsed:.2f}s for 20x3 tiny-graph queries — investigate overhead"


def test_learned_selector_does_not_change_evaluator_output_shape_or_keys():
    """Switching selector_mode must never silently change what evaluate()
    returns — same keys, same metric names, regardless of mode."""
    kg = tiny_kg()
    device = torch.device("cpu")
    results = {}
    for mode in ("budgeted_bfs", "learned_topk"):
        model = SeionKGRv26(
            num_entities=kg.num_entities, num_relations_total=kg.num_relations_total, dim=8,
            base_expert="distmult", enable_path=True, path_rank=3, path_layers=1,
            path_max_neighbors=4, path_selector_mode=mode,
        )
        adjacency = Adjacency.build(kg)
        results[mode] = evaluate(model, kg, "test", device, batch_size=2, entity_block=6, adjacency=adjacency, subset=1.0, seed=0)
    assert set(results["budgeted_bfs"].keys()) == set(results["learned_topk"].keys())
    for key in ("combined", "tail", "head"):
        assert set(results["budgeted_bfs"][key].keys()) == set(results["learned_topk"][key].keys())
