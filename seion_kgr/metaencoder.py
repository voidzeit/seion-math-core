"""Fase 9: relation metaencoder for cross-graph transfer (contract §XI.4/ULTRA-style).

Builds a relation-relation graph from structural interaction (two
relations are connected if they co-occur on a shared entity, weighted by
how often) and encodes each relation as a function of that structure
rather than a free-standing embedding row — so the representation is at
least in principle transferable to a KG with a different relation
vocabulary, per contract §XI.4.

Stated honestly: this is a minimal mean-aggregation + MLP encoder, not
ULTRA's full relational message-passing construction — it is enough to
exercise the interface and test the transfer *pipeline*, not a claim of
matching ULTRA's reported transfer numbers.
"""
from __future__ import annotations

from typing import Dict, Tuple

import torch
import torch.nn as nn

from .data import KnowledgeGraph


def build_relation_cooccurrence(kg: KnowledgeGraph) -> Dict[int, Dict[int, int]]:
    """``relation -> {other_relation: shared_entity_count}``, built from
    entities that appear as a head or tail of both relations (original,
    non-reciprocal relations only — reciprocal relations are a training
    convenience, not part of the transferable relation vocabulary)."""
    entity_relations: Dict[int, set] = {}
    num_rel = kg.num_relations_original
    for h, r, t in kg.train.tolist():
        if r >= num_rel:
            continue
        entity_relations.setdefault(h, set()).add(r)
        entity_relations.setdefault(t, set()).add(r)
    adjacency: Dict[int, Dict[int, int]] = {r: {} for r in range(num_rel)}
    for _entity, rels in entity_relations.items():
        rels = list(rels)
        for i in range(len(rels)):
            for j in range(len(rels)):
                if i == j:
                    continue
                adjacency[rels[i]][rels[j]] = adjacency[rels[i]].get(rels[j], 0) + 1
    return adjacency


class RelationMetaEncoder(nn.Module):
    """``g_r = RelEncoder(structural interactions of r)`` — contract §XI.4.

    One round of degree-normalized mean aggregation over the
    co-occurrence graph, followed by an MLP, applied on top of a base
    (learnable or random-init) relation feature table.
    """

    def __init__(self, dim: int, num_layers: int = 1):
        super().__init__()
        self.num_layers = num_layers
        self.mlp = nn.Sequential(nn.Linear(dim, dim), nn.ReLU(), nn.Linear(dim, dim))

    def forward(self, base_features: torch.Tensor, adjacency: Dict[int, Dict[int, int]]) -> torch.Tensor:
        num_rel = base_features.shape[0]
        x = base_features
        for _ in range(self.num_layers):
            agg = torch.zeros_like(x)
            for r in range(num_rel):
                neighbors = adjacency.get(r, {})
                if not neighbors:
                    agg[r] = x[r]
                    continue
                total_w = sum(neighbors.values())
                acc = torch.zeros_like(x[r])
                for other, w in neighbors.items():
                    acc = acc + (w / total_w) * x[other]
                agg[r] = acc
            x = x + self.mlp(agg)  # residual, so an isolated relation keeps its base feature
        return x
