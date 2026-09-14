"""Gate 13.1 precision (``campaigns/gate13/``): PASS_STRUCTURAL_KERNEL_ROUTER_ACTIVATION.

Same teacher-student construction as
``test_gate13_seion_router_activation.py``, for the structural-kernel
branch instead. Teacher and student share the SAME frozen kernel tensor
``K`` (as they must — ``K`` is a non-trainable buffer, provenance-fixed at
construction; only the adapters ``Ux``/``Ua``/``Uq``/``W`` and the gate are
ever trained), but the teacher's own adapters and gate are independently
(randomly, then frozen) initialized, and its gate is manually opened
(``epsilon_raw`` is 0 at construction, same as the student — a fresh
teacher would emit an all-zero signal, so it must be perturbed away from 0
to have any preference to teach) so it has an actual candidate preference
to teach the student.
"""
from __future__ import annotations

import torch
import torch.nn as nn

from seion_kgr.losses import negative_sampling_loss
from seion_kgr.model import SeionKGRv26
from seion_kgr.structural_kernel import StructuralKernelResidual, build_kernel
from seion_kgr.train import build_optimizer_param_groups

NUM_ENTITIES = 20
DIM = 16
KERNEL_DIM = 6
NUM_RELATIONS = 2
DELTA_GATE = 0.05
MIN_RMS_CONTRIBUTION_RATIO = 0.05


def _build_teacher_labeled_dataset(num_queries: int = 200, candidates_per_query: int = 6, seed: int = 0):
    gen = torch.Generator().manual_seed(seed)
    K, provenance = build_kernel("random_scale_matched", dim=KERNEL_DIM, seed=seed)

    teacher_entity = nn.Embedding(NUM_ENTITIES, DIM)
    teacher_relation = nn.Embedding(NUM_RELATIONS, DIM)
    teacher_kernel = StructuralKernelResidual(dim=DIM, K=K, num_relations_total=NUM_RELATIONS, provenance=provenance, gate_g_max=1.0)
    nn.init.uniform_(teacher_kernel.epsilon_raw.weight, -2.0, 2.0)  # manually OPEN the teacher's gate (0 at construction, same as the student)
    for p in list(teacher_entity.parameters()) + list(teacher_relation.parameters()) + list(teacher_kernel.parameters()):
        p.requires_grad_(False)

    h_ids = torch.randint(0, NUM_ENTITIES, (num_queries,), generator=gen)
    r_ids = torch.randint(0, NUM_RELATIONS, (num_queries,), generator=gen)
    candidates = torch.stack([
        torch.randperm(NUM_ENTITIES, generator=gen)[:candidates_per_query] for _ in range(num_queries)
    ], dim=0)

    with torch.no_grad():
        h_emb, r_emb = teacher_entity(h_ids), teacher_relation(r_ids)
        cand_emb = teacher_entity(candidates)  # [num_queries, K, dim]
        teacher_vec = teacher_kernel(h_emb, r_emb, r_emb, r_ids)  # [num_queries, dim], already gated
        teacher_scores = torch.einsum("bd,bkd->bk", teacher_vec, cand_emb)
        gold_idx = teacher_scores.argmax(dim=-1)
        gold_tails = candidates[torch.arange(num_queries), gold_idx]
        neg_mask = torch.ones_like(candidates, dtype=torch.bool)
        neg_mask[torch.arange(num_queries), gold_idx] = False
        negatives = candidates[neg_mask].view(num_queries, candidates_per_query - 1)
    return h_ids, r_ids, gold_tails, negatives, K, provenance


def test_structural_kernel_router_gate_opens_and_contributes_when_kernel_evidence_is_necessary():
    torch.manual_seed(0)
    h_ids, r_ids, gold_tails, negatives, K, provenance = _build_teacher_labeled_dataset()

    student_kernel = StructuralKernelResidual(dim=DIM, K=K, num_relations_total=NUM_RELATIONS, provenance=provenance, gate_g_max=1.0)
    model = SeionKGRv26(
        num_entities=NUM_ENTITIES, num_relations_total=NUM_RELATIONS, dim=DIM,
        base_expert="complex", enable_path=False, enable_seion=False,
        structural_kernel=student_kernel, gate_g_max=1.0,
    )
    optimizer = torch.optim.AdamW(build_optimizer_param_groups(model, lr=0.02, router_lr_multiplier=5.0))

    alpha0 = model.structural_kernel.epsilon_raw(torch.arange(NUM_RELATIONS)).squeeze(-1)
    assert torch.equal(alpha0, torch.zeros_like(alpha0))

    grad_eps_norm = 0.0
    for epoch in range(200):
        optimizer.zero_grad(set_to_none=True)
        pos = model.score_positive(h_ids, r_ids, gold_tails, adjacency=None, seed=epoch, training=True)
        neg = model.score_tail_candidates(h_ids, r_ids, negatives, adjacency=None, seed=epoch, training=True, gold_tail_ids=gold_tails)
        loss = negative_sampling_loss(pos, neg, adversarial_temperature=1.0)
        loss.backward()
        grad_eps_norm = model.structural_kernel.epsilon_raw.weight.grad.norm().item() if model.structural_kernel.epsilon_raw.weight.grad is not None else 0.0
        optimizer.step()

    assert torch.isfinite(loss)
    assert grad_eps_norm > 0.0, "epsilon_raw got zero gradient — PASS_STRUCTURAL_KERNEL_ROUTER_ACTIVATION requires |grad_alpha| > 0"

    eps = model.structural_kernel.gate_g_max * torch.tanh(model.structural_kernel.epsilon_raw(torch.arange(NUM_RELATIONS)).squeeze(-1))
    gate_displacement = eps.abs().max().item()
    assert gate_displacement > DELTA_GATE, (
        f"gate displacement {gate_displacement:.4f} did not exceed delta_gate={DELTA_GATE}"
    )

    with torch.no_grad():
        s_total, breakdown = model.score_positive(
            h_ids, r_ids, gold_tails, adjacency=None, seed=0, training=False, return_breakdown=True,
        )
    s_total_rms = breakdown["s_total"].pow(2).mean().sqrt().item()
    branch_rms = breakdown["kernel_structural"].pow(2).mean().sqrt().item()
    rms_contribution_ratio = branch_rms / s_total_rms if s_total_rms > 0 else 0.0
    assert rms_contribution_ratio > MIN_RMS_CONTRIBUTION_RATIO, (
        f"rms_contribution_ratio {rms_contribution_ratio:.4f} did not exceed {MIN_RMS_CONTRIBUTION_RATIO}"
    )
