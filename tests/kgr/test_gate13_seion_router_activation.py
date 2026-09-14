"""Gate 13.1 precision (``campaigns/gate13/``): PASS_SEION_ROUTER_ACTIVATION.

Mirrors ``test_gate13_router_activation.py``'s structure but for the
seionic scalar branch instead of the path branch: a FROZEN "teacher"
``SeionicScalarScorer`` (same functional form as the student's own seion
branch, independent random weights and embedding tables) generates the
gold tail for many random ``(h, r)`` queries by picking whichever
candidate its own score prefers. The student model (base ComplEx +
seionic branch) is trained on these teacher-generated labels; since the
teacher's preference is an arbitrary CP-ternary function of ``(h, r, t)``
that a bilinear ComplEx base cannot represent in general, fitting the
training data at all requires the seionic branch's gate to open.

Unlike the path test, this does NOT attempt a held-out-generalization
claim: SEION has no graph structure to exploit independently of direct
supervision (unlike the path branch, whose entities get indirect
structural signal from OTHER edges even for held-out queries), so
"generalizes to unseen heads" is not a coherent claim to test here. The
acceptance conditions are exactly the three stated in the mission brief:
nonzero gradient, gate displacement, RMS contribution ratio.
"""
from __future__ import annotations

import torch
import torch.nn as nn

from seion_kgr.kernels import SeionicScalarScorer
from seion_kgr.losses import negative_sampling_loss
from seion_kgr.model import SeionKGRv26
from seion_kgr.train import build_optimizer_param_groups

NUM_ENTITIES = 20
DIM = 16
SEION_RANK = 8
NUM_RELATIONS = 2  # no reciprocal needed: enable_path=False, path.py's reciprocal machinery is never touched
DELTA_GATE = 0.05  # frozen in campaigns/gate13/preregistration.md §2
MIN_RMS_CONTRIBUTION_RATIO = 0.05


def _build_teacher_labeled_dataset(num_queries: int = 200, candidates_per_query: int = 6, seed: int = 0):
    gen = torch.Generator().manual_seed(seed)
    teacher_entity = nn.Embedding(NUM_ENTITIES, DIM)
    teacher_relation = nn.Embedding(NUM_RELATIONS, DIM)
    teacher_seion = SeionicScalarScorer(dim_e=DIM, dim_r=DIM, dim_q=DIM, rank=SEION_RANK)
    for p in list(teacher_entity.parameters()) + list(teacher_relation.parameters()) + list(teacher_seion.parameters()):
        p.requires_grad_(False)

    h_ids = torch.randint(0, NUM_ENTITIES, (num_queries,), generator=gen)
    r_ids = torch.randint(0, NUM_RELATIONS, (num_queries,), generator=gen)
    candidates = torch.stack([
        torch.randperm(NUM_ENTITIES, generator=gen)[:candidates_per_query] for _ in range(num_queries)
    ], dim=0)  # [num_queries, candidates_per_query]

    with torch.no_grad():
        h_emb, r_emb = teacher_entity(h_ids), teacher_relation(r_ids)
        cand_emb = teacher_entity(candidates)
        teacher_scores = teacher_seion.score_tail_candidates(h_emb, r_emb, r_emb, cand_emb)  # [num_queries, K]
        gold_idx = teacher_scores.argmax(dim=-1)
        gold_tails = candidates[torch.arange(num_queries), gold_idx]
        neg_mask = torch.ones_like(candidates, dtype=torch.bool)
        neg_mask[torch.arange(num_queries), gold_idx] = False
        negatives = candidates[neg_mask].view(num_queries, candidates_per_query - 1)
    return h_ids, r_ids, gold_tails, negatives


def test_seion_router_gate_opens_and_contributes_when_seion_evidence_is_necessary():
    torch.manual_seed(0)
    h_ids, r_ids, gold_tails, negatives = _build_teacher_labeled_dataset()

    model = SeionKGRv26(
        num_entities=NUM_ENTITIES, num_relations_total=NUM_RELATIONS, dim=DIM,
        base_expert="complex", enable_path=False, enable_seion=True, seion_rank=SEION_RANK, gate_g_max=1.0,
    )
    optimizer = torch.optim.AdamW(build_optimizer_param_groups(model, lr=0.02, router_lr_multiplier=5.0))

    alpha0 = model.eta_raw(torch.arange(NUM_RELATIONS)).squeeze(-1)
    assert torch.equal(alpha0, torch.zeros_like(alpha0))

    grad_eta_norm = 0.0
    for epoch in range(200):
        optimizer.zero_grad(set_to_none=True)
        pos = model.score_positive(h_ids, r_ids, gold_tails, adjacency=None, seed=epoch, training=True)
        neg = model.score_tail_candidates(h_ids, r_ids, negatives, adjacency=None, seed=epoch, training=True, gold_tail_ids=gold_tails)
        loss = negative_sampling_loss(pos, neg, adversarial_temperature=1.0)
        loss.backward()
        grad_eta_norm = model.eta_raw.weight.grad.norm().item() if model.eta_raw.weight.grad is not None else 0.0
        optimizer.step()

    assert torch.isfinite(loss)
    assert grad_eta_norm > 0.0, "eta_raw got zero gradient — PASS_SEION_ROUTER_ACTIVATION requires |grad_alpha| > 0"

    eta = model.gate_g_max * torch.tanh(model.eta_raw(torch.arange(NUM_RELATIONS)).squeeze(-1))
    gate_displacement = eta.abs().max().item()  # eta(0) == 0 exactly
    assert gate_displacement > DELTA_GATE, (
        f"gate displacement {gate_displacement:.4f} did not exceed delta_gate={DELTA_GATE}"
    )

    with torch.no_grad():
        s_total, breakdown = model.score_positive(
            h_ids, r_ids, gold_tails, adjacency=None, seed=0, training=False, return_breakdown=True,
        )
    s_total_rms = breakdown["s_total"].pow(2).mean().sqrt().item()
    branch_rms = breakdown["eta_seion"].pow(2).mean().sqrt().item()
    rms_contribution_ratio = branch_rms / s_total_rms if s_total_rms > 0 else 0.0
    assert rms_contribution_ratio > MIN_RMS_CONTRIBUTION_RATIO, (
        f"rms_contribution_ratio {rms_contribution_ratio:.4f} did not exceed {MIN_RMS_CONTRIBUTION_RATIO}"
    )
