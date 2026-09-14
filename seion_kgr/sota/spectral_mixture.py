"""Relation-adaptive spectral mixture of multilinear Tucker experts."""

from __future__ import annotations

import math

import torch
import torch.nn as nn
import torch.nn.functional as F


class SpectralConditionalTensorMixture(nn.Module):
    """Sparse relation-routed Tucker mixture with differentiable bases."""

    def __init__(
        self,
        num_entities: int,
        num_relations: int,
        entity_dim: int = 256,
        relation_dim: int | None = None,
        experts: int = 8,
        active_per_relation: int = 2,
        expert_rank: int = 64,
        core_basis: int = 4,
        active_experts: torch.Tensor | None = None,
        temperature: float = 1.0,
    ) -> None:
        super().__init__()
        relation_dim = entity_dim if relation_dim is None else relation_dim
        values = (num_entities, num_relations, entity_dim, relation_dim, experts, active_per_relation, expert_rank, core_basis)
        if any(int(value) <= 0 for value in values):
            raise ValueError("all dimensions must be positive")
        if active_per_relation > experts or expert_rank > entity_dim or expert_rank > relation_dim:
            raise ValueError("active_per_relation and expert_rank exceed available dimensions")
        if temperature <= 0:
            raise ValueError("temperature must be positive")
        self.num_entities = num_entities
        self.num_relations = num_relations
        self.entity_dim = entity_dim
        self.relation_dim = relation_dim
        self.experts = experts
        self.active_per_relation = active_per_relation
        self.expert_rank = expert_rank
        self.core_basis = core_basis
        self.entity = nn.Embedding(num_entities, entity_dim)
        self.relation = nn.Embedding(num_relations, relation_dim)
        nn.init.xavier_uniform_(self.entity.weight)
        nn.init.xavier_uniform_(self.relation.weight)
        self.basis_raw = nn.Parameter(self._orthogonal_init(experts, entity_dim, expert_rank))
        self.relation_basis_raw = nn.Parameter(self._orthogonal_init(experts, relation_dim, expert_rank))
        self.core_bank = nn.Parameter(torch.empty(experts, core_basis, expert_rank, expert_rank, expert_rank))
        nn.init.normal_(self.core_bank, std=1.0 / math.sqrt(expert_rank))
        self.core_logits = nn.Parameter(torch.zeros(num_relations, active_per_relation, core_basis))
        self.routing_logits = nn.Parameter(torch.zeros(num_relations, active_per_relation))
        self.tau_raw = nn.Parameter(torch.full((num_relations,), self._inverse_softplus(temperature)))
        if active_experts is None:
            active_experts = torch.arange(active_per_relation).repeat(num_relations, 1) % experts
        if active_experts.shape != (num_relations, active_per_relation):
            raise ValueError("active_experts must have shape [num_relations, active_per_relation]")
        active_experts = active_experts.to(dtype=torch.long)
        if int(active_experts.min()) < 0 or int(active_experts.max()) >= experts:
            raise ValueError("active_experts contains an invalid expert index")
        self.register_buffer("active_experts", active_experts.clone(), persistent=True)

    @staticmethod
    def _inverse_softplus(value: float) -> float:
        return math.log(math.expm1(value)) if value < 20.0 else value

    @staticmethod
    def _orthogonal_init(count: int, rows: int, cols: int) -> torch.Tensor:
        result = torch.empty(count, rows, cols)
        for index in range(count):
            result[index] = torch.linalg.qr(torch.randn(rows, cols), mode="reduced").Q
        return result

    def orthonormal_bases(self) -> tuple[torch.Tensor, torch.Tensor]:
        return torch.linalg.qr(self.basis_raw, mode="reduced").Q, torch.linalg.qr(self.relation_basis_raw, mode="reduced").Q

    def orthonormality_error(self) -> torch.Tensor:
        bases, relation_bases = self.orthonormal_bases()
        eye = torch.eye(self.expert_rank, device=bases.device, dtype=bases.dtype)
        first = (bases.transpose(1, 2) @ bases - eye).abs().amax()
        second = (relation_bases.transpose(1, 2) @ relation_bases - eye).abs().amax()
        return torch.maximum(first, second)

    def _active(self, relation_ids: torch.Tensor) -> tuple[torch.Tensor, torch.Tensor, torch.Tensor, torch.Tensor, torch.Tensor]:
        bases, relation_bases = self.orthonormal_bases()
        active = self.active_experts[relation_ids]
        return (
            bases[active], relation_bases[active], self.core_bank[active],
            F.softmax(self.core_logits[relation_ids], dim=-1),
            F.softmax(self.routing_logits[relation_ids], dim=-1),
        )

    def _score_embeddings(self, heads: torch.Tensor, relations: torch.Tensor, tails: torch.Tensor, relation_ids: torch.Tensor) -> torch.Tensor:
        bases, relation_bases, cores, core_weights, routing_weights = self._active(relation_ids)
        h_proj = torch.einsum("bd,bmdk->bmk", heads, bases)
        r_proj = torch.einsum("bd,bmdk->bmk", relations, relation_bases)
        mixed_cores = torch.einsum("bml,bmlxyz->bmxyz", core_weights, cores)
        if tails.ndim == 2:
            t_proj = torch.einsum("bd,bmdk->bmk", tails, bases)
            expert_scores = torch.einsum("bmx,bmy,bmxyz,bmz->bm", h_proj, r_proj, mixed_cores, t_proj)
            tau = F.softplus(self.tau_raw[relation_ids]) + 1e-6
            return tau * torch.logsumexp(torch.log(routing_weights.clamp_min(1e-12)) + expert_scores / tau.unsqueeze(-1), dim=-1)
        t_proj = torch.einsum("bnd,bmdk->bnmk", tails, bases)
        expert_scores = torch.einsum("bmx,bmy,bmxyz,bnmz->bnm", h_proj, r_proj, mixed_cores, t_proj)
        tau = F.softplus(self.tau_raw[relation_ids]) + 1e-6
        return tau.unsqueeze(-1) * torch.logsumexp(torch.log(routing_weights.clamp_min(1e-12)).unsqueeze(1) + expert_scores / tau.unsqueeze(-1).unsqueeze(-1), dim=-1)

    def score_positive(self, h_ids: torch.Tensor, relation_ids: torch.Tensor, t_ids: torch.Tensor, *args, **kwargs) -> torch.Tensor:
        return self._score_embeddings(self.entity(h_ids), self.relation(relation_ids), self.entity(t_ids), relation_ids)

    def score_tail_candidates(self, h_ids: torch.Tensor, relation_ids: torch.Tensor, candidate_ids: torch.Tensor, *args, **kwargs) -> torch.Tensor:
        heads = self.entity(h_ids)
        relations = self.relation(relation_ids)
        if candidate_ids.ndim == 1:
            tails = self.entity(candidate_ids).unsqueeze(0).expand(h_ids.shape[0], -1, -1)
        elif candidate_ids.ndim == 2 and candidate_ids.shape[0] == h_ids.shape[0]:
            tails = self.entity(candidate_ids)
        else:
            raise ValueError("candidate_ids must have shape [N] or [B,N]")
        return self._score_embeddings(heads, relations, tails, relation_ids)

    def routing_probabilities(self, relation_ids: torch.Tensor) -> torch.Tensor:
        return F.softmax(self.routing_logits[relation_ids], dim=-1)

    def basis_decorrelation_penalty(self) -> torch.Tensor:
        bases, _ = self.orthonormal_bases()
        flat = bases.reshape(-1, self.expert_rank)
        gram = flat @ flat.transpose(0, 1)
        return (gram - torch.diag(torch.diagonal(gram))).pow(2).mean()
