import torch

from seion_kgr.context import build_context_adjacency, build_context_index, build_query_context
from seion_kgr.data import KnowledgeGraph, build_filters, reciprocal_closure, tiny_kg
from seion_kgr.model import SeionKGRv26


def _single_edge_kg() -> KnowledgeGraph:
    base = [(0, 0, 1)]
    valid = [(0, 0, 1)]
    test = []
    tails, heads = build_filters(base, valid, test)
    return KnowledgeGraph(
        num_entities=3,
        num_relations_original=1,
        train=torch.tensor(reciprocal_closure(base, 1), dtype=torch.long).numpy(),
        valid=valid,
        test=test,
        ent2id={str(i): i for i in range(3)},
        rel2id={"r": 0},
        tails_of_hr=tails,
        heads_of_rt=heads,
    )


def _context(model, kg, h, r, t):
    h = torch.tensor(h, dtype=torch.long)
    r = torch.tensor(r, dtype=torch.long)
    t = torch.tensor(t, dtype=torch.long)
    return build_query_context(
        h, r, t, kg, model.entity.weight, model.relation.weight,
        max_neighbors=32, adjacency=build_context_adjacency(kg),
    )


def test_context_parity_is_exact_for_matched_inputs():
    torch.manual_seed(7)
    kg = tiny_kg()
    model = SeionKGRv26(kg.num_entities, kg.num_relations_total, 8, base_expert="tucker", enable_seion=True, gate_g_max=0.5, gate_init=0.1)
    first, _ = _context(model, kg, [0, 2], [0, 1], [1, 3])
    second, _ = _context(model, kg, [0, 2], [0, 1], [1, 3])
    assert torch.equal(first, second)


def test_vectorized_context_index_matches_reference_builder():
    torch.manual_seed(8)
    kg = tiny_kg()
    model = SeionKGRv26(kg.num_entities, kg.num_relations_total, 8, base_expert="tucker", enable_seion=True, gate_g_max=0.5, gate_init=0.1)
    h = torch.tensor([0, 2, 4])
    r = torch.tensor([0, 1, 0])
    t = torch.tensor([1, 3, 5])
    reference, _ = build_query_context(h, r, t, kg, model.entity.weight, model.relation.weight, adjacency=build_context_adjacency(kg))
    packed, _ = build_query_context(
        h, r, t, kg, model.entity.weight, model.relation.weight,
        context_index=build_context_index(kg),
    )
    assert torch.equal(reference, packed)


def test_context_excludes_query_edge_and_reciprocal_without_leakage():
    kg = _single_edge_kg()
    torch.manual_seed(9)
    model = SeionKGRv26(kg.num_entities, kg.num_relations_total, 8, base_expert="tucker", enable_seion=True, gate_g_max=0.5, gate_init=0.1)
    context, stats = _context(model, kg, [0], [0], [1])
    assert torch.equal(context, torch.zeros_like(context))
    assert stats["context_coverage"] == 0.0


def test_true_triangular_inputs_and_all_seion_factors_receive_gradient():
    torch.manual_seed(11)
    dim = 8
    model = SeionKGRv26(6, 4, dim, base_expert="tucker", enable_seion=True, gate_g_max=0.5, gate_init=0.1)
    h = torch.randn(3, dim, requires_grad=True)
    r = torch.randn(3, dim, requires_grad=True)
    c = torch.randn(3, dim, requires_grad=True)
    t = torch.randn(3, dim, requires_grad=True)
    score = (model.seion_scorer.q_seion(h, r, c) * model.seion_scorer.T(t)).sum()
    score.backward()
    for name in ("A", "B", "C", "O", "T"):
        grad = getattr(model.seion_scorer, name).weight.grad
        assert grad is not None and float(grad.norm()) > 0.0, name
    assert float(h.grad.norm()) > 0.0
    assert float(r.grad.norm()) > 0.0
    assert float(c.grad.norm()) > 0.0


def test_context_perturbation_changes_seion_score():
    torch.manual_seed(13)
    scorer = SeionKGRv26(6, 4, 8, base_expert="tucker", enable_seion=True, gate_g_max=0.5, gate_init=0.1).seion_scorer
    h, r, c, t = [torch.randn(2, 8) for _ in range(4)]
    baseline = scorer.score_positive(h, r, c, t)
    changed_h = scorer.score_positive(h + 0.25, r, c, t)
    changed_c = scorer.score_positive(h, r, c + 0.25, t)
    changed_r = scorer.score_positive(h, r + 0.25, c, t)
    assert float((baseline - changed_h).abs().max().detach()) > 0.0
    assert float((baseline - changed_c).abs().max().detach()) > 0.0
    assert float((baseline - changed_r).abs().max().detach()) > 0.0


def test_seion_and_generic_parameter_counts_are_exactly_matched():
    torch.manual_seed(17)
    kwargs = dict(num_entities=6, num_relations_total=4, dim=8, base_expert="tucker", gate_g_max=0.5, gate_init=0.1)
    seion = SeionKGRv26(enable_seion=True, **kwargs)
    generic = SeionKGRv26(enable_generic_residual=True, **kwargs)
    count_seion = sum(p.numel() for p in seion.parameters() if p.requires_grad)
    count_generic = sum(p.numel() for p in generic.parameters() if p.requires_grad)
    assert count_seion == count_generic
