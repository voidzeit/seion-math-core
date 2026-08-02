"""Gate 13.2b acceptance tests (``campaigns/gate13/``):
PASS_PATH_PRODUCTION_INTEGRATION.

Unlike ``test_reasoner_batched_parity.py`` (which compares the bare
``PathReasoner``/``BatchedPathReasoner`` reasoners directly), this file
exercises the full ``SeionKGRv26`` model — ``score_positive``/
``score_tail_candidates``, gradients, and checkpoint state — with
``path_backend="legacy"`` vs ``path_backend="batched"``, since that is
what actually matters for treating the backend as "an execution detail,
not a different architecture."
"""
from __future__ import annotations

import torch

import pytest

from seion_kgr.frontier_ops import build_csr_adjacency
from seion_kgr.losses import negative_sampling_loss
from seion_kgr.model import SeionKGRv26
from seion_kgr.reasoner import Adjacency
from seion_kgr.train import build_parser, train

TOLERANCE = 1e-4  # campaigns/gate13/preregistration.md §2 NONINFERIORITY_MARGIN


def _graph(num_relations_original: int = 2):
    """Same shape of fixture as test_reasoner_batched_parity.py's small
    graph: multi-hop chains, a node with two incoming edges in one layer
    (mean-aggregation), and a dead-end node with no outgoing edges."""
    out_edges = {
        0: [(0, 1), (1, 2)],
        1: [(0, 3)],
        2: [(1, 3)],
        3: [(0, 4), (1, 5)],
        4: [(0, 6)],
        5: [(1, 6)],
        7: [(0, 8)],
    }
    return Adjacency(out_edges), 10


def _build_pair(seed: int, enable_seion: bool, proj_rank: int, selector_mode: str, dim: int = 8, path_layers: int = 2):
    """Two models sharing identical weights (via load_state_dict), differing
    ONLY in path_backend."""
    torch.manual_seed(seed)
    legacy = SeionKGRv26(
        num_entities=10, num_relations_total=4, dim=dim, base_expert="complex",
        enable_path=True, enable_seion=enable_seion, seion_rank=4,
        path_rank=4, path_layers=path_layers, path_max_neighbors=16, path_proj_rank=proj_rank,
        path_selector_mode=selector_mode, path_backend="legacy",
    )
    batched = SeionKGRv26(
        num_entities=10, num_relations_total=4, dim=dim, base_expert="complex",
        enable_path=True, enable_seion=enable_seion, seion_rank=4,
        path_rank=4, path_layers=path_layers, path_max_neighbors=16, path_proj_rank=proj_rank,
        path_selector_mode=selector_mode, path_backend="batched",
    )
    batched.load_state_dict(legacy.state_dict())
    return legacy, batched


def _queries():
    torch.manual_seed(1)
    h = torch.tensor([0, 1, 2, 7])
    r = torch.tensor([0, 1, 0, 0])
    t = torch.tensor([1, 3, 3, 8])
    return h, r, t


# ------------------------------------------------------------------ score parity


def _run_score_parity_case(enable_seion: bool, proj_rank: int, selector_mode: str, training: bool):
    adjacency, num_nodes = _graph()
    csr = build_csr_adjacency(adjacency, num_nodes)
    legacy, batched = _build_pair(seed=0, enable_seion=enable_seion, proj_rank=proj_rank, selector_mode=selector_mode)
    h, r, t = _queries()

    pos_legacy = legacy.score_positive(h, r, t, adjacency, seed=0, training=training)
    pos_batched = batched.score_positive(h, r, t, csr, seed=0, training=training)
    assert (pos_legacy - pos_batched).abs().max().item() < TOLERANCE

    cand = torch.arange(num_nodes)
    cand_legacy = legacy.score_tail_candidates(h, r, cand, adjacency, seed=0, training=training, gold_tail_ids=t)
    cand_batched = batched.score_tail_candidates(h, r, cand, csr, seed=0, training=training, gold_tail_ids=t)
    assert (cand_legacy - cand_batched).abs().max().item() < TOLERANCE


def test_score_parity_full_neighborhood_training():
    _run_score_parity_case(enable_seion=False, proj_rank=0, selector_mode="full_neighborhood", training=True)


def test_score_parity_full_neighborhood_eval():
    _run_score_parity_case(enable_seion=False, proj_rank=0, selector_mode="full_neighborhood", training=False)


def test_score_parity_with_projector_and_seion():
    _run_score_parity_case(enable_seion=True, proj_rank=3, selector_mode="full_neighborhood", training=True)


def test_score_parity_budgeted_bfs_when_no_node_exceeds_the_budget():
    """``budgeted_bfs`` uses DIFFERENT random-number sources per backend
    (legacy: ``numpy`` ``rng.choice``; batched: ``torch.rand`` + segment
    top-k) — the two are not expected to pick the same random SUBSET when a
    budget cut is actually active. But with ``max_neighbors=16`` and every
    node's out-degree <= 2 in this fixture, no candidate is ever actually
    cut (both backends' "keep everyone" fast path is exercised, matching
    ``full_neighborhood``), so score parity still holds exactly here — this
    deliberately does NOT test parity under an active random budget cut,
    which is out of scope (see campaigns/gate13/preregistration.md §11)."""
    _run_score_parity_case(enable_seion=False, proj_rank=0, selector_mode="budgeted_bfs", training=True)


# ------------------------------------------------------------------ queried-edge removal


def test_queried_edge_removal_identical_across_backends():
    """``(0, R0, 1)`` is itself a graph edge (``0 -R0-> 1``). Both backends'
    ``run_batch_frontiers`` unconditionally exclude the literal queried edge
    ``(h, r, t)`` (leakage prevention applies at both train AND eval time —
    only the RECIPROCAL exclusion is training-only, per ``reasoner.py``'s
    docstring), so querying with ``r=R0`` must NOT reach node 1, while
    querying the SAME head/tail with a DIFFERENT relation (``r=R1``, which
    does not match the real edge, so nothing is excluded) MUST reach it.

    This deliberately reads off ``_run_path_reasoner``'s raw reached state
    directly, NOT ``score_positive``'s total score: at a freshly
    constructed model the router gate is exactly 0 (Gate 13.1 zero init),
    which would multiply away any difference the exclusion makes to the
    total score, making a score-level comparison vacuous regardless of
    whether exclusion actually works."""
    adjacency, num_nodes = _graph()
    csr = build_csr_adjacency(adjacency, num_nodes)
    # path_layers=1: target t=1 is exactly ONE hop from h=0, so it only ever
    # appears in the FINAL frontier when reached at that single hop — with
    # path_layers=2 (the other tests' default), node 1 is merely an
    # intermediate hop expanded past at layer 2 regardless of exclusion,
    # which would make this test vacuously pass.
    legacy, batched = _build_pair(seed=2, enable_seion=False, proj_rank=0, selector_mode="full_neighborhood", path_layers=1)

    h = torch.tensor([0, 0])
    r_excluded = torch.tensor([0, 0])  # matches the real edge (0,R0,1) -> excluded
    r_not_excluded = torch.tensor([1, 1])  # does NOT match (0,R0,1) -> nothing excluded, edge still traversable
    t = torch.tensor([1, 1])
    query_ids = torch.tensor([0, 1])

    def _reached_state(model, adj, r_ids):
        query_vecs = model.relation(r_ids)
        output = model._run_path_reasoner(h, r_ids, t, adj, query_vecs, seed=0, training=True)
        return output.state_for(query_ids, t)

    with torch.no_grad():
        excluded_legacy = _reached_state(legacy, adjacency, r_excluded)
        excluded_batched = _reached_state(batched, csr, r_excluded)
        not_excluded_legacy = _reached_state(legacy, adjacency, r_not_excluded)
        not_excluded_batched = _reached_state(batched, csr, r_not_excluded)

    # Both backends must agree with each other for EACH query...
    assert (excluded_legacy - excluded_batched).abs().max().item() < TOLERANCE
    assert (not_excluded_legacy - not_excluded_batched).abs().max().item() < TOLERANCE
    # ...and excluding the literal queried edge must actually change what
    # gets reached (proof the exclusion mechanism has a real effect, not
    # just that both backends happen to agree on some value).
    assert (excluded_legacy - not_excluded_legacy).abs().max().item() > TOLERANCE, (
        "querying with r=R0 (excluded) vs r=R1 (not excluded) reached the same state — the "
        "queried-edge exclusion had no effect, so this fixture does not actually test leakage prevention"
    )


# ------------------------------------------------------------------ gradient parity


def test_gradient_parity_across_backends():
    """Backward pass on a real negative-sampling loss, comparing gradients
    module-by-module. Uses ``full_neighborhood`` (tie-free, no budget-cut
    randomness) so any divergence is a genuine implementation bug, not RNG
    source mismatch (see ``test_score_parity_budgeted_bfs_when_no_node_exceeds_the_budget``'s
    docstring for why an active random cut is out of scope for parity)."""
    adjacency, num_nodes = _graph()
    csr = build_csr_adjacency(adjacency, num_nodes)
    legacy, batched = _build_pair(seed=3, enable_seion=True, proj_rank=3, selector_mode="full_neighborhood")
    h, r, t = _queries()
    neg = torch.tensor([[2, 4, 6], [0, 2, 5], [0, 1, 6], [0, 1, 2]])

    def _step(model, adj):
        pos = model.score_positive(h, r, t, adj, seed=0, training=True)
        negs = model.score_tail_candidates(h, r, neg, adj, seed=0, training=True, gold_tail_ids=t)
        loss = negative_sampling_loss(pos, negs, adversarial_temperature=1.0)
        loss.backward()
        return loss

    loss_legacy = _step(legacy, adjacency)
    loss_batched = _step(batched, csr)
    assert abs(float(loss_legacy.item()) - float(loss_batched.item())) < TOLERANCE

    checked = 0
    for name, p_legacy in legacy.named_parameters():
        p_batched = dict(batched.named_parameters())[name]
        if p_legacy.grad is None and p_batched.grad is None:
            continue
        assert p_legacy.grad is not None and p_batched.grad is not None, name
        g_legacy, g_batched = p_legacy.grad.flatten(), p_batched.grad.flatten()
        max_abs_err = (g_legacy - g_batched).abs().max().item()
        assert max_abs_err < TOLERANCE, f"{name}: max abs grad error {max_abs_err}"
        norm_product = g_legacy.norm() * g_batched.norm()
        if norm_product > 1e-12:
            cosine = torch.dot(g_legacy, g_batched) / norm_product
            assert cosine.item() > 0.999, f"{name}: cosine similarity {cosine.item()}"
        checked += 1
    assert checked > 5, "too few parameters had gradients to be a meaningful parity check"


# ------------------------------------------------------------------ checkpoint cross-backend load


def test_checkpoint_trained_with_legacy_loads_into_batched_and_matches():
    """The user-facing promise of Gate 13.2b: ``path_backend`` is an
    execution detail. Train (a few real optimizer steps) with the legacy
    backend, save its state_dict, load it into a freshly constructed
    batched-backend model, and confirm identical scores — not just
    identical architecture."""
    adjacency, num_nodes = _graph()
    csr = build_csr_adjacency(adjacency, num_nodes)
    torch.manual_seed(4)
    legacy = SeionKGRv26(
        num_entities=10, num_relations_total=4, dim=8, base_expert="complex",
        enable_path=True, enable_seion=False, path_rank=4, path_layers=2,
        path_max_neighbors=16, path_selector_mode="full_neighborhood", path_backend="legacy",
    )
    optimizer = torch.optim.AdamW(legacy.parameters(), lr=0.05)
    h, r, t = _queries()
    neg = torch.tensor([[2, 4, 6], [0, 2, 5], [0, 1, 6], [0, 1, 2]])
    for _ in range(10):
        optimizer.zero_grad(set_to_none=True)
        pos = legacy.score_positive(h, r, t, adjacency, seed=0, training=True)
        negs = legacy.score_tail_candidates(h, r, neg, adjacency, seed=0, training=True, gold_tail_ids=t)
        negative_sampling_loss(pos, negs, adversarial_temperature=1.0).backward()
        optimizer.step()

    batched = SeionKGRv26(
        num_entities=10, num_relations_total=4, dim=8, base_expert="complex",
        enable_path=True, enable_seion=False, path_rank=4, path_layers=2,
        path_max_neighbors=16, path_selector_mode="full_neighborhood", path_backend="batched",
    )
    batched.load_state_dict(legacy.state_dict())  # the actual "checkpoint cross-backend load" being tested

    with torch.no_grad():
        pos_legacy = legacy.score_positive(h, r, t, adjacency, seed=0, training=False)
        pos_batched = batched.score_positive(h, r, t, csr, seed=0, training=False)
    assert (pos_legacy - pos_batched).abs().max().item() < TOLERANCE


# ------------------------------------------------------------------ explicit rejection, not silent fallback


def test_batched_backend_with_learned_topk_is_explicitly_rejected(tmp_path):
    """``learned_topk`` is not vectorized (Gate 13.2's documented scope
    cut). Combining it with ``--path_backend batched`` must fail loudly and
    immediately — not silently fall back to a different selector mode or to
    the legacy backend, and not waste time loading a dataset first."""
    args = build_parser().parse_args([
        "--train", "dummy_train.txt", "--valid", "dummy_valid.txt", "--test", "dummy_test.txt",
        "--out_dir", str(tmp_path), "--enable_path",
        "--path_backend", "batched", "--path_selector_mode", "learned_topk",
    ])
    with pytest.raises(NotImplementedError, match="learned_topk"):
        train(args)  # must raise before ever touching --train/--valid/--test (which don't even exist on disk)
