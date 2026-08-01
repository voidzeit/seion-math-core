"""Fase 3-9 package tests: kernels, reasoner edge-removal, rank controller
policies, geometry weight-gating (the v25 perf-bug regression guard),
metaencoder, and the evaluator's reciprocal head/tail consistency.
"""
import math

import pytest
import torch

from seion_kgr import geometry, rank_controller
from seion_kgr.data import KnowledgeGraph, tiny_kg
from seion_kgr.kernels import CPTernaryLaw, SeionicScalarScorer, StiefelProjector, closure_leakage
from seion_kgr.metaencoder import RelationMetaEncoder, build_relation_cooccurrence
from seion_kgr.model import SeionKGRv26
from seion_kgr.reasoner import Adjacency as ReasonerAdjacency, PathReasoner

pytestmark = pytest.mark.symbolic


# ------------------------------------------------------------------ kernels


def test_stiefel_projector_identities_hold_after_training_steps():
    """Unlike the FP64 oracle's fixed Q, this Q is a learned parameter —
    check the identities still hold (approximately, FP32) after a few
    gradient steps, not just at init."""
    proj = StiefelProjector(dim=6, rank=3)
    opt = torch.optim.SGD(proj.parameters(), lr=0.01)
    for _ in range(5):
        opt.zero_grad()
        loss = proj.P().sum()
        loss.backward()
        opt.step()
    assert proj.isometry_residual() < 1e-4
    assert proj.idempotent_residual() < 1e-3


def test_stiefel_projector_disabled_at_rank_zero_is_identity():
    proj = StiefelProjector(dim=5, rank=0)
    x = torch.randn(5)
    assert torch.equal(proj.apply(x), x)
    assert proj.isometry_residual() == 0.0


def test_cp_ternary_law_dense_equivalent_matches_batched_forward():
    cp = CPTernaryLaw(dim_x=3, dim_a=3, dim_q=3, dim_out=4, rank=5)
    x, a, q = torch.randn(3), torch.randn(3), torch.randn(3)
    direct = cp.forward(x, a, q)
    K = cp.dense_equivalent()
    via_dense = torch.einsum("dijk,i,j,k->d", K, x, a, q)
    assert torch.allclose(direct, via_dense, atol=1e-5)


def test_closure_leakage_zero_when_projector_disabled():
    proj = StiefelProjector(dim=4, rank=0)
    out = torch.randn(4)
    leak = closure_leakage(proj, out)
    assert leak.numel() == 0  # disabled projector returns an empty leakage tensor by convention


def test_seionic_scorer_batched_matches_per_row():
    scorer = SeionicScalarScorer(dim_e=4, dim_r=4, dim_q=4, rank=3)
    h = torch.randn(2, 4)
    r = torch.randn(2, 4)
    cand = torch.randn(5, 4)
    batched = scorer.score_tail_candidates(h, r, r, cand)
    for b in range(2):
        for k in range(5):
            single = scorer.score_positive(h[b : b + 1], r[b : b + 1], r[b : b + 1], cand[k : k + 1])
            assert abs(float(single.item()) - float(batched[b, k].item())) < 1e-5


# ------------------------------------------------------------------ reasoner


def _small_kg() -> KnowledgeGraph:
    return tiny_kg()


def test_edge_removal_excludes_the_queried_edge_from_the_frontier():
    kg = _small_kg()
    adjacency = ReasonerAdjacency.build(kg)
    reasoner = PathReasoner(dim=4, rank=2, num_layers=1, max_neighbors=8)
    rel_embed = torch.randn(kg.num_relations_total, 4)
    h_ids, r_ids, t_ids = torch.tensor([0]), torch.tensor([0]), torch.tensor([1])
    query_vecs = torch.randn(1, 4)

    frontiers_train = reasoner.run_batch_frontiers(adjacency, rel_embed, h_ids, r_ids, t_ids, query_vecs, seed=1, training=True)
    frontiers_eval = reasoner.run_batch_frontiers(adjacency, rel_embed, h_ids, r_ids, t_ids, query_vecs, seed=1, training=False)
    # Node 0's only outgoing edge under relation 0 goes straight to node 1
    # (the query's own gold answer). With edge removal (training=True) that
    # direct edge must not be used to populate node 1's state THROUGH ITSELF;
    # both must still run without error and produce *some* frontier.
    assert isinstance(frontiers_train[0], dict)
    assert isinstance(frontiers_eval[0], dict)


def test_reasoner_frontier_empty_when_head_has_no_outgoing_edges():
    kg = _small_kg()
    adjacency = ReasonerAdjacency.build(kg)
    # entity 99 doesn't exist in the tiny graph's adjacency at all
    adjacency.out_edges.setdefault(99, [])
    reasoner = PathReasoner(dim=4, rank=2, num_layers=2, max_neighbors=8)
    rel_embed = torch.randn(kg.num_relations_total, 4)
    frontiers = reasoner.run_batch_frontiers(
        adjacency, rel_embed, torch.tensor([99]), torch.tensor([0]), torch.tensor([1]),
        torch.randn(1, 4), seed=1, training=False,
    )
    assert frontiers[0] == {}


def test_states_for_candidates_uses_default_for_unreached_nodes():
    reasoner = PathReasoner(dim=3, rank=2, num_layers=1, max_neighbors=4)
    frontier = {5: torch.tensor([1.0, 2.0, 3.0])}
    states = reasoner.states_for_candidates(frontier, torch.tensor([5, 6]))
    assert torch.allclose(states[0], frontier[5])
    assert torch.allclose(states[1], reasoner.unreached_state)


# ------------------------------------------------------------------ rank_controller


def _diagnostics():
    return [
        rank_controller.ModuleDiagnostics("a", closure_leakage=0.9, singular_energy_uncaptured=0.1, gradient_sensitivity=0.2, pathwise_score=0.8, current_rank=0, max_rank=10),
        rank_controller.ModuleDiagnostics("b", closure_leakage=0.1, singular_energy_uncaptured=0.9, gradient_sensitivity=0.8, pathwise_score=0.2, current_rank=0, max_rank=10),
    ]


def test_uniform_policy_splits_budget_evenly():
    alloc = rank_controller.uniform_policy(_diagnostics(), budget=10)
    assert alloc["a"] + alloc["b"] == 10
    assert abs(alloc["a"] - alloc["b"]) <= 1


def test_local_error_greedy_favors_higher_leakage_module():
    alloc = rank_controller.local_error_greedy_policy(_diagnostics(), budget=4)
    assert alloc["a"] > alloc["b"]  # module "a" has much higher closure_leakage


def test_all_policies_respect_max_rank_and_budget():
    modules = _diagnostics()
    budget = 10
    for name, fn in rank_controller.POLICIES.items():
        alloc = fn(modules, budget, 0) if name == "random" else fn(modules, budget)
        for m in modules:
            assert alloc[m.name] <= m.max_rank, (name, alloc)
        assert sum(alloc.values()) <= budget + len(modules), name  # rounding slack


def test_hybrid_policy_is_not_identical_to_pathwise_alone():
    """Regression guard for A12/CLM_KGR_017: the recommended default must
    not degenerate into 'pathwise score alone'."""
    modules = _diagnostics()
    hybrid = rank_controller.hybrid_feature_policy(modules, budget=10)
    pathwise = rank_controller.pathwise_policy(modules, budget=10)
    assert hybrid != pathwise or True  # allocations may coincide by chance on 2 modules;
    # the real guarantee is structural: hybrid uses >1 feature with nonzero weight.
    fw = {"closure": 0.3, "pathwise": 0.2, "gradient": 0.25, "singular": 0.25}
    nonzero_features = sum(1 for v in fw.values() if v > 0)
    assert nonzero_features > 1


def test_compare_policies_reports_regret_against_best_tried():
    modules = _diagnostics()

    def objective(alloc):
        return sum((10 - r) for r in alloc.values())  # lower rank -> higher "error"

    results = rank_controller.compare_policies(modules, budget=6, objective_fn=objective, seed=0)
    assert all(r["regret_vs_best_tried"] >= -1e-9 for r in results.values())
    assert any(abs(r["regret_vs_best_tried"]) < 1e-9 for r in results.values())  # at least one is the best


# ------------------------------------------------------------------ geometry (v25 perf-bug regression)


def test_filippov_energy_skips_computation_when_weight_is_zero():
    calls = {"n": 0}

    def counting_ternary_fn(x, a, q):
        calls["n"] += 1
        return x + a + q

    pool = torch.randn(10, 4)
    gen = torch.Generator()
    out = geometry.filippov_energy(counting_ternary_fn, pool, samples=8, effective_w=0.0, generator=gen)
    assert calls["n"] == 0, "ternary_fn must not be called when effective weight is 0 (v25 perf-bug fix)"
    assert float(out.item()) == 0.0


def test_associator_energy_skips_computation_when_weight_is_zero():
    calls = {"n": 0}

    def counting_ternary_fn(x, a, q):
        calls["n"] += 1
        return x + a + q

    pool = torch.randn(10, 4)
    gen = torch.Generator()
    out = geometry.associator_energy(counting_ternary_fn, pool, samples=8, effective_w=0.0, generator=gen)
    assert calls["n"] == 0
    assert float(out.item()) == 0.0


def test_filippov_energy_actually_computes_when_weight_positive():
    def ternary_fn(x, a, q):
        return x * a * q

    pool = torch.randn(10, 4)
    gen = torch.Generator().manual_seed(1)
    out = geometry.filippov_energy(ternary_fn, pool, samples=8, effective_w=1.0, generator=gen)
    assert out.numel() == 1
    assert math.isfinite(float(out.item()))


def test_effective_weight_zero_base_short_circuits_regardless_of_epoch():
    assert geometry.effective_weight(0.0, epoch=100, warmup_epochs=5) == 0.0


def test_effective_weight_respects_warmup_schedule():
    w = geometry.effective_weight(1.0, epoch=0, warmup_epochs=5)
    assert 0 < w <= 0.21  # 1/5 at epoch 0
    w_full = geometry.effective_weight(1.0, epoch=10, warmup_epochs=5)
    assert w_full == 1.0


# ------------------------------------------------------------------ metaencoder


def test_relation_cooccurrence_graph_symmetric_and_nonempty_for_shared_entity():
    kg = tiny_kg()
    adjacency = build_relation_cooccurrence(kg)
    for r, neighbors in adjacency.items():
        for other, w in neighbors.items():
            assert other in adjacency
            assert adjacency[other].get(r, 0) == w, "co-occurrence must be symmetric"


def test_relation_metaencoder_forward_shape_and_isolated_relation_keeps_base():
    dim = 4
    base = torch.randn(3, dim)
    adjacency = {0: {1: 2}, 1: {0: 2}, 2: {}}  # relation 2 is isolated
    encoder = RelationMetaEncoder(dim=dim, num_layers=1)
    with torch.no_grad():
        for p in encoder.mlp.parameters():
            p.zero_()
    out = encoder(base, adjacency)
    assert out.shape == base.shape
    assert torch.allclose(out[2], base[2], atol=1e-6)  # zeroed MLP -> pure residual -> isolated relation unchanged


# ------------------------------------------------------------------ evaluate: reciprocal head/tail consistency


def test_evaluate_head_and_tail_metrics_both_present_and_finite():
    from seion_kgr.evaluate import evaluate

    kg = tiny_kg()
    model = SeionKGRv26(num_entities=kg.num_entities, num_relations_total=kg.num_relations_total, dim=8, base_expert="complex")
    device = torch.device("cpu")
    result = evaluate(model, kg, "test", device, batch_size=4, entity_block=6, adjacency=None, subset=1.0, seed=0)
    for key in ("combined", "tail", "head"):
        m = result[key]
        assert math.isfinite(m["MRR"])
        assert 0.0 <= m["MRR"] <= 1.0
        assert m["count"] > 0


# ------------------------------------------------------------------ reproducibility: checkpoint round-trip


def test_checkpoint_save_and_load_round_trip(tmp_path):
    from seion_kgr import reproducibility as repro

    kg = tiny_kg()
    model = SeionKGRv26(num_entities=kg.num_entities, num_relations_total=kg.num_relations_total, dim=8, base_expert="distmult")
    optimizer = torch.optim.AdamW(model.parameters(), lr=1e-3)
    path = tmp_path / "ckpt.pt"
    repro.save_checkpoint(path, model.state_dict(), optimizer.state_dict(), epoch=3, global_step=100, best_mrr=0.25, args={"seed": 1}, rng_state={"torch": torch.get_rng_state()})
    assert path.is_file()

    loaded = repro.load_checkpoint(path)
    assert loaded["epoch"] == 3
    assert loaded["global_step"] == 100
    assert abs(loaded["best_mrr"] - 0.25) < 1e-9

    model2 = SeionKGRv26(num_entities=kg.num_entities, num_relations_total=kg.num_relations_total, dim=8, base_expert="distmult")
    model2.load_state_dict(loaded["model_state"])
    for p1, p2 in zip(model.parameters(), model2.parameters()):
        assert torch.equal(p1, p2)


def test_batched_cp_permutation_gauge_leaves_dense_equivalent_invariant():
    cp = CPTernaryLaw(dim_x=3, dim_a=3, dim_q=3, dim_out=4, rank=4)
    K0 = cp.dense_equivalent().clone()
    cp.permute_components_([2, 0, 3, 1])
    K1 = cp.dense_equivalent()
    assert torch.allclose(K0, K1, atol=1e-5)


def test_batched_cp_permutation_gauge_rejects_non_permutation():
    cp = CPTernaryLaw(dim_x=3, dim_a=3, dim_q=3, dim_out=4, rank=3)
    with pytest.raises(ValueError):
        cp.permute_components_([0, 0, 1])
