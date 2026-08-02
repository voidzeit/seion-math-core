"""Gate 13.1 acceptance test (``campaigns/gate13/``): PASS_ROUTER_ACTIVATION.

Builds a synthetic compositional knowledge graph where a query relation
(``R_PATH``) is TRUE iff there is a 2-hop chain ``h -R1-> m -R2-> t``, and
the ``(h, R_PATH, t)`` training triples are withheld for a subset of chains
("held-out" chains). The base bilinear expert (ComplEx) has no mechanism to
compose ``R1`` and ``R2`` — it can only fit ``R_PATH`` triples it has
actually seen — so on held-out chains it cannot do better than chance,
while the path reasoner can traverse the (always-present) ``R1``/``R2``
topology regardless of whether ``R_PATH`` was ever trained for that head.

This is deliberately NOT plugged into the real ``load_knowledge_graph``
pipeline (no reciprocal closure, no filtered negative sampling) — it is a
minimal, self-contained fixture whose only job is to force a situation
where the path branch is the SOLE source of correct signal, so the router
gate has something genuine to learn to rely on. Per the mission brief:
"No debes propagar por todo el grafo... el path reasoner debe [tener]
evidencia de que la rama contribuye".
"""
from __future__ import annotations

import torch

from seion_kgr.losses import negative_sampling_loss
from seion_kgr.model import SeionKGRv26
from seion_kgr.reasoner import Adjacency
from seion_kgr.train import build_optimizer_param_groups

R1, R2, R_PATH = 0, 1, 2
NUM_RELATIONS_ORIGINAL = 3
NUM_RELATIONS_TOTAL = 2 * NUM_RELATIONS_ORIGINAL  # matches the real reciprocal-closure convention
DELTA_GATE = 0.05  # frozen in campaigns/gate13/preregistration.md §2
MIN_RMS_CONTRIBUTION_RATIO = 0.05  # frozen in campaigns/gate13/preregistration.md §2


def _build_synthetic_compositional_kg(num_chains: int = 16, num_train_chains: int = 10):
    """Chain ``i`` uses 3 fresh entities ``(h_i, m_i, t_i)``. Returns
    ``(num_entities, adjacency, r1_triples, r2_triples, path_train_triples,
    path_test_triples)``, all as ``(h, r, t)`` int triples."""
    num_entities = 3 * num_chains
    out_edges: dict = {}
    r1_triples, r2_triples = [], []
    path_train_triples, path_test_triples = [], []
    for i in range(num_chains):
        h, m, t = 3 * i, 3 * i + 1, 3 * i + 2
        out_edges.setdefault(h, []).append((R1, m))
        out_edges.setdefault(m, []).append((R2, t))
        r1_triples.append((h, R1, m))
        r2_triples.append((m, R2, t))
        if i < num_train_chains:
            path_train_triples.append((h, R_PATH, t))
        else:
            path_test_triples.append((h, R_PATH, t))
    return num_entities, Adjacency(out_edges), r1_triples, r2_triples, path_train_triples, path_test_triples


def _to_tensors(triples):
    h = torch.tensor([tr[0] for tr in triples], dtype=torch.long)
    r = torch.tensor([tr[1] for tr in triples], dtype=torch.long)
    t = torch.tensor([tr[2] for tr in triples], dtype=torch.long)
    return h, r, t


def test_router_gate_opens_and_contributes_when_path_evidence_is_necessary():
    torch.manual_seed(0)
    num_entities, adjacency, r1, r2, path_train, path_test = _build_synthetic_compositional_kg()
    all_visible_triples = r1 + r2 + path_train  # path_test's (h,R_PATH,t) triples are NEVER trained on

    model = SeionKGRv26(
        num_entities=num_entities, num_relations_total=NUM_RELATIONS_TOTAL, dim=16,
        base_expert="complex", enable_path=True, enable_seion=False,
        path_rank=8, path_layers=2, path_max_neighbors=8,
        path_selector_mode="full_neighborhood", gate_g_max=1.0,
    )
    optimizer = torch.optim.AdamW(build_optimizer_param_groups(model, lr=0.02, router_lr_multiplier=5.0))

    h_ids, r_ids, t_ids = _to_tensors(all_visible_triples)
    neg_k = 8
    gen = torch.Generator().manual_seed(1)

    # --- pre-training baseline: the gate is exactly 0 by construction ---
    alpha0 = model.gamma_raw(torch.tensor([R_PATH])).squeeze().item()
    assert alpha0 == 0.0

    for epoch in range(150):
        neg_ids = torch.randint(0, num_entities, (h_ids.shape[0], neg_k), generator=gen)
        optimizer.zero_grad(set_to_none=True)
        pos = model.score_positive(h_ids, r_ids, t_ids, adjacency, seed=epoch, training=True)
        neg = model.score_tail_candidates(h_ids, r_ids, neg_ids, adjacency, seed=epoch, training=True, gold_tail_ids=t_ids)
        loss = negative_sampling_loss(pos, neg, adversarial_temperature=1.0)
        loss.backward()
        grad_alpha_norm = model.gamma_raw.weight.grad.norm().item() if model.gamma_raw.weight.grad is not None else 0.0
        optimizer.step()

    assert torch.isfinite(loss)
    assert grad_alpha_norm > 0.0, "router param (gamma_raw) got zero gradient — PASS_ROUTER_ACTIVATION requires |grad_alpha| > 0"

    # --- gate displacement on the R_PATH relation specifically ---
    alpha_path_raw = model.gamma_raw(torch.tensor([R_PATH])).squeeze()
    gamma_path = (model.gate_g_max * torch.tanh(alpha_path_raw)).item()
    gamma_displacement = abs(gamma_path - 0.0)  # gamma_r(0) == 0 exactly
    assert gamma_displacement > DELTA_GATE, (
        f"gate displacement {gamma_displacement:.4f} did not exceed delta_gate={DELTA_GATE} "
        "on the path-necessary relation — router did not open"
    )

    # --- RMS contribution ratio of the gated path branch vs total score,
    # measured on ALL R_PATH triples (train ones the model was fit to, and
    # test ones it never saw as R_PATH triples — the gate value itself is
    # per-relation, not per-query, so either sample validates the same gamma) ---
    all_path_triples = path_train + path_test
    ph, pr, pt = _to_tensors(all_path_triples)
    with torch.no_grad():
        s_total, breakdown = model.score_positive(ph, pr, pt, adjacency, seed=0, training=False, return_breakdown=True)
    s_total_rms = breakdown["s_total"].pow(2).mean().sqrt().item()
    branch_rms = breakdown["gamma_path"].pow(2).mean().sqrt().item()
    rms_contribution_ratio = branch_rms / s_total_rms if s_total_rms > 0 else 0.0
    assert rms_contribution_ratio > MIN_RMS_CONTRIBUTION_RATIO, (
        f"rms_contribution_ratio {rms_contribution_ratio:.4f} did not exceed "
        f"{MIN_RMS_CONTRIBUTION_RATIO} on the R_PATH relation"
    )


def test_held_out_chains_generalize_better_than_a_gateless_base_only_model():
    """Bonus evidence beyond the three PASS_ROUTER_ACTIVATION conditions
    above: the trained path-enabled model should rank the true tail of a
    HELD-OUT chain (never seen as an ``R_PATH`` triple) better than a
    base-only (no path branch) model trained identically, since only the
    path branch has a mechanism to compose ``R1``/``R2`` for a head it never
    saw an ``R_PATH`` label for."""
    torch.manual_seed(0)
    num_entities, adjacency, r1, r2, path_train, path_test = _build_synthetic_compositional_kg()
    all_visible_triples = r1 + r2 + path_train
    h_ids, r_ids, t_ids = _to_tensors(all_visible_triples)
    neg_k = 8

    def _train(enable_path: bool) -> SeionKGRv26:
        torch.manual_seed(0)
        model = SeionKGRv26(
            num_entities=num_entities, num_relations_total=NUM_RELATIONS_TOTAL, dim=16,
            base_expert="complex", enable_path=enable_path, enable_seion=False,
            path_rank=8, path_layers=2, path_max_neighbors=8,
            path_selector_mode="full_neighborhood", gate_g_max=1.0,
        )
        optimizer = torch.optim.AdamW(build_optimizer_param_groups(model, lr=0.02, router_lr_multiplier=5.0))
        gen = torch.Generator().manual_seed(1)
        adj = adjacency if enable_path else None
        for epoch in range(150):
            neg_ids = torch.randint(0, num_entities, (h_ids.shape[0], neg_k), generator=gen)
            optimizer.zero_grad(set_to_none=True)
            pos = model.score_positive(h_ids, r_ids, t_ids, adj, seed=epoch, training=True)
            neg = model.score_tail_candidates(h_ids, r_ids, neg_ids, adj, seed=epoch, training=True, gold_tail_ids=t_ids)
            negative_sampling_loss(pos, neg, adversarial_temperature=1.0).backward()
            optimizer.step()
        return model

    def _mean_gold_rank(model: SeionKGRv26, adj) -> float:
        ranks = []
        with torch.no_grad():
            for h, r, t in path_test:
                cand = torch.arange(num_entities)
                scores = model.score_tail_candidates(
                    torch.tensor([h]), torch.tensor([r]), cand.unsqueeze(0), adj, seed=0, training=False,
                ).squeeze(0)
                rank = int((scores > scores[t]).sum().item()) + 1
                ranks.append(rank)
        return sum(ranks) / len(ranks)

    path_model = _train(enable_path=True)
    base_model = _train(enable_path=False)
    path_rank = _mean_gold_rank(path_model, adjacency)
    base_rank = _mean_gold_rank(base_model, None)
    assert path_rank < base_rank, (
        f"path-enabled model's mean held-out gold rank ({path_rank:.1f}) was not better than "
        f"the base-only model's ({base_rank:.1f}) — path branch provided no generalization benefit"
    )
