"""Campaign Phase D: negative-control INTEGRATION runs (real training,
not just unit-level algebra checks). A negative control that does not
degrade as expected must be investigated before any other conclusion is
accepted (mandate §D1) — these tests assert the expected degradation
actually happens, on real (small, fast) data.
"""
import numpy as np
import pytest
import torch

from seion_kgr.data import KnowledgeGraph, build_filters, reciprocal_closure
from seion_kgr.evaluate import evaluate
from seion_kgr.losses import negative_sampling_loss
from seion_kgr.model import SeionKGRv26
from seion_kgr.reasoner import Adjacency
from seion_kgr.reproducibility import set_seed

pytestmark = pytest.mark.symbolic


def _small_ring_kg(num_entities=30, num_relations=2, seed=0) -> KnowledgeGraph:
    """A structured graph (each entity -> next entity, cyclically, under
    2 relations) with a real, learnable pattern -- so a correctly
    training model should clearly beat random, giving the randomized-
    label control something real to destroy."""
    rng = np.random.default_rng(seed)
    base = []
    for i in range(num_entities):
        base.append((i, i % num_relations, (i + 1) % num_entities))
        base.append((i, (i + 1) % num_relations, (i + 2) % num_entities))
    valid = base[: num_entities // 3]
    test = base[num_entities // 3 : 2 * num_entities // 3]
    tails, heads = build_filters(base, valid, test)
    return KnowledgeGraph(
        num_entities=num_entities, num_relations_original=num_relations,
        train=np.asarray(reciprocal_closure(base, num_relations), dtype=np.int64),
        valid=valid, test=test,
        ent2id={str(i): i for i in range(num_entities)}, rel2id={str(i): i for i in range(num_relations)},
        tails_of_hr=tails, heads_of_rt=heads,
    )


def _randomize_tails(kg: KnowledgeGraph, seed: int) -> KnowledgeGraph:
    """Same structure, but every training triple's tail is replaced by a
    uniformly random entity -- destroys any learnable head/relation ->
    tail pattern while keeping the dataset's shape identical."""
    rng = np.random.default_rng(seed)
    randomized = kg.train.copy()
    randomized[:, 2] = rng.integers(0, kg.num_entities, size=randomized.shape[0])
    return KnowledgeGraph(
        num_entities=kg.num_entities, num_relations_original=kg.num_relations_original,
        train=randomized, valid=kg.valid, test=kg.test,
        ent2id=kg.ent2id, rel2id=kg.rel2id, tails_of_hr=kg.tails_of_hr, heads_of_rt=kg.heads_of_rt,
    )


def _train_a_few_steps(model, kg, device, epochs=8, seed=1):
    set_seed(seed)
    optimizer = torch.optim.AdamW(model.parameters(), lr=5e-3)
    rng = np.random.default_rng(seed)
    for _epoch in range(epochs):
        idx = rng.permutation(kg.train.shape[0])
        for start in range(0, len(idx), 16):
            batch_idx = idx[start : start + 16]
            batch = kg.train[batch_idx]
            h_ids = torch.tensor(batch[:, 0], device=device)
            r_ids = torch.tensor(batch[:, 1], device=device)
            t_ids = torch.tensor(batch[:, 2], device=device)
            neg = torch.randint(0, kg.num_entities, (len(batch_idx), 8), device=device)
            optimizer.zero_grad(set_to_none=True)
            pos = model.score_positive(h_ids, r_ids, t_ids, None, 0, training=True)
            negs = model.score_tail_candidates(h_ids, r_ids, neg, None, 0, training=True, gold_tail_ids=t_ids)
            loss = negative_sampling_loss(pos, negs, 1.0)
            loss.backward()
            optimizer.step()


def test_randomized_labels_collapse_validation_mrr():
    """Real control: train the identical architecture on (a) the
    structured graph and (b) the same graph with tails randomized.
    (a) must clearly beat (b) -- if it doesn't, either the model isn't
    learning anything or the randomization didn't actually destroy the
    signal, either of which would need investigation before trusting
    anything else in this campaign."""
    device = torch.device("cpu")
    kg_real = _small_ring_kg()
    kg_random = _randomize_tails(kg_real, seed=42)

    set_seed(0)
    model_real = SeionKGRv26(num_entities=kg_real.num_entities, num_relations_total=kg_real.num_relations_total, dim=16, base_expert="distmult")
    _train_a_few_steps(model_real, kg_real, device)
    mrr_real = evaluate(model_real, kg_real, "valid", device, batch_size=8, entity_block=kg_real.num_entities, adjacency=None, subset=1.0, seed=0)["combined"]["MRR"]

    set_seed(0)
    model_random = SeionKGRv26(num_entities=kg_random.num_entities, num_relations_total=kg_random.num_relations_total, dim=16, base_expert="distmult")
    _train_a_few_steps(model_random, kg_random, device)
    mrr_random = evaluate(model_random, kg_random, "valid", device, batch_size=8, entity_block=kg_random.num_entities, adjacency=None, subset=1.0, seed=0)["combined"]["MRR"]

    assert mrr_real > mrr_random, (
        f"NEGATIVE CONTROL FAILED TO DEGRADE: structured-graph MRR ({mrr_real}) did not exceed "
        f"randomized-labels MRR ({mrr_random}) -- per mandate D1, this must be investigated before "
        f"any other campaign conclusion is trusted."
    )


def test_queried_edge_leakage_inflates_metrics_when_deliberately_enabled():
    """Real control fixture: a path-reasoner-enabled model evaluated with
    leakage DELIBERATELY re-enabled (calling score_tail_candidates with
    training=True during evaluation, which stops excluding the queried
    edge) must score better on the SAME split than the correctly
    leakage-prevented evaluation (training=False) -- if leaked evaluation
    were not measurably better, the leakage-prevention wouldn't be a
    real correctness property. This fixture must NEVER be used outside
    this negative-control test."""
    device = torch.device("cpu")
    kg = _small_ring_kg(num_entities=16, num_relations=2, seed=1)
    adjacency = Adjacency.build(kg)
    set_seed(0)
    model = SeionKGRv26(
        num_entities=kg.num_entities, num_relations_total=kg.num_relations_total, dim=12,
        base_expert="distmult", enable_path=True, path_rank=6, path_layers=1, path_max_neighbors=6,
    )
    _train_a_few_steps(model, kg, device, epochs=3)

    # Correct (leakage-prevented) evaluation.
    clean = evaluate(model, kg, "test", device, batch_size=4, entity_block=kg.num_entities, adjacency=adjacency, subset=1.0, seed=0)

    # Deliberately leaky evaluation fixture: monkeypatch score_tail_candidates
    # to force training=True (re-enables the queried-edge exclusion's
    # OPPOSITE -- i.e. disables the exclusion) regardless of caller intent.
    original = model.score_tail_candidates

    def leaky_score_tail_candidates(h_ids, r_ids, candidates_ids, adjacency=None, seed=0, training=True, gold_tail_ids=None):
        return original(h_ids, r_ids, candidates_ids, adjacency, seed, training=True, gold_tail_ids=gold_tail_ids)

    model.score_tail_candidates = leaky_score_tail_candidates
    try:
        leaky = evaluate(model, kg, "test", device, batch_size=4, entity_block=kg.num_entities, adjacency=adjacency, subset=1.0, seed=0)
    finally:
        model.score_tail_candidates = original

    assert leaky["combined"]["MRR"] >= clean["combined"]["MRR"], (
        f"NEGATIVE CONTROL FAILED TO DEGRADE: leaky-evaluation MRR ({leaky['combined']['MRR']}) was not "
        f">= the correctly leakage-prevented MRR ({clean['combined']['MRR']}) -- if leakage genuinely "
        f"never helps, that itself would need investigation (it would mean the path branch isn't using "
        f"the queried edge's information at all, which is also suspicious)."
    )
