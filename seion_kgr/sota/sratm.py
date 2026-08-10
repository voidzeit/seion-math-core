"""Spectral Relation-Adaptive Tensor Mixture (SRATM) scorer."""

from __future__ import annotations

import math

import torch
import torch.nn as nn

from .spectral_mixture import SpectralConditionalTensorMixture


class SpectralRelationAdaptiveTensorMixture(SpectralConditionalTensorMixture):
    """Global Tucker path + spectral expert mixture + ComplEx residual.

    The spectral mixture remains the reusable base implementation.  SRATM
    adds two multilinear paths and a relation-conditioned convex fusion:

        score = alpha_r * global_tucker
              + beta_r  * spectral_mixture
              + gamma_r * complex_residual.

    Routing is static per relation, so candidate evaluation remains
    deterministic and compatible with the existing filtered evaluator.
    """

    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        dim = self.entity_dim
        relation_dim = self.relation_dim
        self.global_core = nn.Parameter(torch.empty(dim, relation_dim, dim))
        nn.init.normal_(self.global_core, std=1.0 / math.sqrt(dim))

        self.complex_entity_real = nn.Embedding(self.num_entities, dim)
        self.complex_entity_imag = nn.Embedding(self.num_entities, dim)
        self.complex_relation_real = nn.Embedding(self.num_relations, relation_dim)
        self.complex_relation_imag = nn.Embedding(self.num_relations, relation_dim)
        for embedding in (
            self.complex_entity_real,
            self.complex_entity_imag,
            self.complex_relation_real,
            self.complex_relation_imag,
        ):
            nn.init.xavier_uniform_(embedding.weight)

        self.fusion_logits = nn.Parameter(torch.zeros(self.num_relations, 3))
        self.relation_head = nn.Linear(2 * dim, self.num_relations)

    def _global_score(self, heads: torch.Tensor, relations: torch.Tensor, tails: torch.Tensor) -> torch.Tensor:
        query = torch.einsum("bd,be,def->bf", heads, relations, self.global_core)
        if tails.ndim == 2:
            return torch.einsum("bf,bf->b", query, tails)
        return torch.einsum("bf,bnf->bn", query, tails)

    def _complex_score(
        self,
        h_ids: torch.Tensor,
        relation_ids: torch.Tensor,
        candidate_ids: torch.Tensor,
        *,
        paired: bool = False,
    ) -> torch.Tensor:
        hr = self.complex_entity_real(h_ids)
        hi = self.complex_entity_imag(h_ids)
        rr = self.complex_relation_real(relation_ids)
        ri = self.complex_relation_imag(relation_ids)
        first = hr * rr - hi * ri
        second = hr * ri + hi * rr
        if paired:
            tr = self.complex_entity_real(candidate_ids)
            ti = self.complex_entity_imag(candidate_ids)
            return torch.einsum("bd,bd->b", first, tr) + torch.einsum("bd,bd->b", second, ti)
        if candidate_ids.ndim == 1:
            tr = self.complex_entity_real(candidate_ids).unsqueeze(0).expand(h_ids.shape[0], -1, -1)
            ti = self.complex_entity_imag(candidate_ids).unsqueeze(0).expand(h_ids.shape[0], -1, -1)
            return torch.einsum("bd,bnd->bn", first, tr) + torch.einsum("bd,bnd->bn", second, ti)
        tr = self.complex_entity_real(candidate_ids)
        ti = self.complex_entity_imag(candidate_ids)
        return torch.einsum("bd,bnd->bn", first, tr) + torch.einsum("bd,bnd->bn", second, ti)

    def _score_embeddings(
        self,
        heads: torch.Tensor,
        relations: torch.Tensor,
        tails: torch.Tensor,
        relation_ids: torch.Tensor,
        *,
        h_ids: torch.Tensor | None = None,
        candidate_ids: torch.Tensor | None = None,
    ) -> torch.Tensor:
        mixture = super()._score_embeddings(heads, relations, tails, relation_ids)
        global_score = self._global_score(heads, relations, tails)
        if h_ids is None or candidate_ids is None:
            raise ValueError("SRATM requires ids for the ComplEx residual")
        complex_score = self._complex_score(
            h_ids, relation_ids, candidate_ids, paired=tails.ndim == 2
        )
        weights = torch.softmax(self.fusion_logits[relation_ids], dim=-1)
        if tails.ndim == 2:
            return (
                weights[:, 0] * global_score
                + weights[:, 1] * mixture
                + weights[:, 2] * complex_score
            )
        return (
            weights[:, 0:1] * global_score
            + weights[:, 1:2] * mixture
            + weights[:, 2:3] * complex_score
        )

    def score_positive(self, h_ids: torch.Tensor, relation_ids: torch.Tensor, t_ids: torch.Tensor, *args, **kwargs) -> torch.Tensor:
        heads = self.entity(h_ids)
        relations = self.relation(relation_ids)
        tails = self.entity(t_ids)
        return self._score_embeddings(
            heads, relations, tails, relation_ids, h_ids=h_ids, candidate_ids=t_ids
        )

    def score_tail_candidates(self, h_ids: torch.Tensor, relation_ids: torch.Tensor, candidate_ids: torch.Tensor, *args, **kwargs) -> torch.Tensor:
        heads = self.entity(h_ids)
        relations = self.relation(relation_ids)
        if candidate_ids.ndim == 1:
            tails = self.entity(candidate_ids).unsqueeze(0).expand(h_ids.shape[0], -1, -1)
        elif candidate_ids.ndim == 2 and candidate_ids.shape[0] == h_ids.shape[0]:
            tails = self.entity(candidate_ids)
        else:
            raise ValueError("candidate_ids must have shape [N] or [B,N]")
        return self._score_embeddings(
            heads, relations, tails, relation_ids, h_ids=h_ids, candidate_ids=candidate_ids
        )

    def relation_logits(self, h_ids: torch.Tensor, t_ids: torch.Tensor) -> torch.Tensor:
        return self.relation_head(torch.cat((self.entity(h_ids), self.entity(t_ids)), dim=-1))

    def fusion_probabilities(self, relation_ids: torch.Tensor) -> torch.Tensor:
        return torch.softmax(self.fusion_logits[relation_ids], dim=-1)
