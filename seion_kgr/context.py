"""Deterministic query-conditioned contexts for Gate 14A.

The context is deliberately non-trainable and is built only from the training
graph.  This keeps the SEION-v2 and Generic-v2 comparison focused on the
composition law rather than on a learned context encoder.
"""
from __future__ import annotations

from dataclasses import dataclass
from hashlib import sha256
from typing import Dict, List, Tuple

import torch
import torch.nn.functional as F

from .data import KnowledgeGraph


@dataclass(frozen=True)
class TriadicContextSpec:
    direction_policy: str = "outgoing_over_reciprocal_closed_train_graph"
    target_edge_exclusion: str = "query_and_reciprocal_before_selection"
    max_neighbors: int = 32
    neighbor_selection: str = "lexicographic_relation_then_target_first"
    aggregation: str = "mean_entity_plus_relation"
    normalization: str = "layernorm_no_affine_eps_1e-5"
    dimension_policy: str = "same_as_model_dim"
    trainable: bool = False
    empty_neighborhood: str = "zero_vector"


DEFAULT_CONTEXT_SPEC = TriadicContextSpec()


@dataclass(frozen=True)
class ContextIndex:
    target_ids: torch.Tensor
    relation_ids: torch.Tensor
    valid_mask: torch.Tensor

    def to(self, device: torch.device) -> "ContextIndex":
        return ContextIndex(
            target_ids=self.target_ids.to(device),
            relation_ids=self.relation_ids.to(device),
            valid_mask=self.valid_mask.to(device),
        )


def inverse_relation(relation_id: int, num_relations_original: int) -> int:
    return relation_id + num_relations_original if relation_id < num_relations_original else relation_id - num_relations_original


def context_spec_dict(spec: TriadicContextSpec = DEFAULT_CONTEXT_SPEC) -> dict:
    return {
        "direction_policy": spec.direction_policy,
        "target_edge_exclusion": spec.target_edge_exclusion,
        "max_neighbors": spec.max_neighbors,
        "neighbor_selection": spec.neighbor_selection,
        "aggregation": spec.aggregation,
        "normalization": spec.normalization,
        "dimension_policy": spec.dimension_policy,
        "trainable": spec.trainable,
        "empty_neighborhood": spec.empty_neighborhood,
    }


def build_context_adjacency(kg: KnowledgeGraph) -> Dict[int, List[Tuple[int, int]]]:
    """Return sorted outgoing training edges, including reciprocal closure."""
    adjacency: Dict[int, List[Tuple[int, int]]] = {}
    for h, r, t in kg.train.tolist():
        adjacency.setdefault(int(h), []).append((int(r), int(t)))
    for edges in adjacency.values():
        edges.sort(key=lambda pair: (pair[0], pair[1]))
    return adjacency


def build_context_index(kg: KnowledgeGraph, max_neighbors: int = DEFAULT_CONTEXT_SPEC.max_neighbors) -> ContextIndex:
    """Pack the frozen neighbor policy into fixed-size tensors once per run."""
    if max_neighbors <= 0:
        raise ValueError("max_neighbors must be positive")
    adjacency = build_context_adjacency(kg)
    target_ids = torch.full((kg.num_entities, max_neighbors), -1, dtype=torch.long)
    relation_ids = torch.full((kg.num_entities, max_neighbors), -1, dtype=torch.long)
    valid_mask = torch.zeros((kg.num_entities, max_neighbors), dtype=torch.bool)
    for node in range(kg.num_entities):
        selected = adjacency.get(node, [])[:max_neighbors]
        if selected:
            relation_ids[node, :len(selected)] = torch.tensor([r for r, _ in selected], dtype=torch.long)
            target_ids[node, :len(selected)] = torch.tensor([t for _, t in selected], dtype=torch.long)
            valid_mask[node, :len(selected)] = True
    return ContextIndex(target_ids=target_ids, relation_ids=relation_ids, valid_mask=valid_mask)


def _normalize_context(context: torch.Tensor) -> torch.Tensor:
    if context.numel() == 0:
        return context
    return F.layer_norm(context, (context.shape[-1],), weight=None, bias=None, eps=1e-5)


def build_query_context(
    h_ids: torch.Tensor,
    r_ids: torch.Tensor,
    gold_t_ids: torch.Tensor,
    kg: KnowledgeGraph,
    entity_weight: torch.Tensor,
    relation_weight: torch.Tensor,
    max_neighbors: int = DEFAULT_CONTEXT_SPEC.max_neighbors,
    adjacency: Dict[int, List[Tuple[int, int]]] | None = None,
    context_index: ContextIndex | None = None,
) -> tuple[torch.Tensor, dict]:
    """Build ``c_(h,r)`` for a batch, excluding the query edge and inverse.

    The graph traversal is deterministic and has no trainable parameters.
    Embeddings remain differentiable so the context can train the shared
    representation, while both matched models receive the same construction.
    """
    if h_ids.ndim != 1 or r_ids.ndim != 1 or gold_t_ids.ndim != 1:
        raise ValueError("h_ids, r_ids and gold_t_ids must be rank-1 tensors")
    if not (h_ids.numel() == r_ids.numel() == gold_t_ids.numel()):
        raise ValueError("query tensors must have equal length")
    if max_neighbors <= 0:
        raise ValueError("max_neighbors must be positive")
    if context_index is not None:
        if context_index.target_ids.shape[1] != max_neighbors:
            raise ValueError("context_index max_neighbors does not match the requested budget")
        index_device = h_ids.device
        target_ids = context_index.target_ids.to(index_device)[h_ids]
        relation_ids = context_index.relation_ids.to(index_device)[h_ids]
        valid_mask = context_index.valid_mask.to(index_device)[h_ids]
        inverse = torch.where(r_ids < kg.num_relations_original, r_ids + kg.num_relations_original, r_ids - kg.num_relations_original)
        query_excluded = valid_mask & (relation_ids == r_ids[:, None]) & (target_ids == gold_t_ids[:, None])
        reciprocal_excluded = (
            valid_mask & (h_ids == gold_t_ids)[:, None]
            & (relation_ids == inverse[:, None]) & (target_ids == h_ids[:, None])
        )
        selected_mask = valid_mask & ~query_excluded & ~reciprocal_excluded
        safe_targets = target_ids.clamp_min(0)
        safe_relations = relation_ids.clamp_min(0)
        context_values = entity_weight[safe_targets] + relation_weight[safe_relations]
        context_values = context_values * selected_mask.unsqueeze(-1)
        counts = selected_mask.sum(dim=1)
        context = context_values.sum(dim=1) / counts.clamp_min(1).unsqueeze(-1)
        context = context * (counts > 0).unsqueeze(-1)
        context = _normalize_context(context)
        stats = {
            "context_rms": float(context.detach().float().pow(2).mean().sqrt().item()) if context.numel() else 0.0,
            "context_variance": float(context.detach().float().var(unbiased=False).item()) if context.numel() else 0.0,
            "context_zero_fraction": float((context.detach() == 0).float().mean().item()) if context.numel() else 1.0,
            "context_coverage": float((counts > 0).float().mean().item()) if counts.numel() else 0.0,
            "mean_candidate_neighbors": float(valid_mask.sum(dim=1).float().mean().item()) if valid_mask.numel() else 0.0,
            "mean_selected_neighbors": float(counts.float().mean().item()) if counts.numel() else 0.0,
            "max_neighbors": int(max_neighbors),
            "spec": context_spec_dict(),
        }
        return context, stats

    adjacency = adjacency or build_context_adjacency(kg)
    rows: list[torch.Tensor] = []
    used_counts: list[int] = []
    candidate_counts: list[int] = []
    for h, r, t in zip(h_ids.detach().cpu().tolist(), r_ids.detach().cpu().tolist(), gold_t_ids.detach().cpu().tolist()):
        inverse = inverse_relation(int(r), kg.num_relations_original)
        excluded = {(int(h), int(r), int(t)), (int(t), inverse, int(h))}
        candidates = [
            (edge_r, edge_t)
            for edge_r, edge_t in adjacency.get(int(h), [])
            if (int(h), edge_r, edge_t) not in excluded
        ]
        candidates.sort(key=lambda pair: (pair[0], pair[1]))
        selected = candidates[:max_neighbors]
        candidate_counts.append(len(candidates))
        used_counts.append(len(selected))
        if not selected:
            rows.append(entity_weight.new_zeros(entity_weight.shape[-1]))
            continue
        rel = torch.tensor([x[0] for x in selected], device=relation_weight.device, dtype=torch.long)
        ent = torch.tensor([x[1] for x in selected], device=entity_weight.device, dtype=torch.long)
        rows.append((entity_weight.index_select(0, ent) + relation_weight.index_select(0, rel)).mean(dim=0))
    context = torch.stack(rows, dim=0) if rows else entity_weight.new_zeros((0, entity_weight.shape[-1]))
    context = _normalize_context(context)
    used = torch.tensor(used_counts, dtype=torch.float32)
    stats = {
        "context_rms": float(context.detach().float().pow(2).mean().sqrt().item()) if context.numel() else 0.0,
        "context_variance": float(context.detach().float().var(unbiased=False).item()) if context.numel() else 0.0,
        "context_zero_fraction": float((context.detach() == 0).float().mean().item()) if context.numel() else 1.0,
        "context_coverage": float((used > 0).float().mean().item()) if used.numel() else 0.0,
        "mean_candidate_neighbors": float(sum(candidate_counts) / max(len(candidate_counts), 1)),
        "mean_selected_neighbors": float(used.mean().item()) if used.numel() else 0.0,
        "max_neighbors": int(max_neighbors),
        "spec": context_spec_dict(),
    }
    return context, stats


def tensor_sha256(tensor: torch.Tensor) -> str:
    data = tensor.detach().cpu().contiguous().numpy().tobytes()
    return sha256(data).hexdigest()
