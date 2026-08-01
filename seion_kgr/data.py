"""Reciprocal knowledge-graph loading, filters, negative sampling.

Contract §II.3.2 / §III (reciprocal closure collapses head/tail
prediction into one task). Reciprocal training triples are always added
here — v26 does not offer a non-reciprocal mode, unlike v25's
``--reciprocal_train`` flag, per contract §II's stated motivation.
"""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Mapping, Sequence, Tuple

import numpy as np
import torch
from torch.utils.data import Dataset

TripleS = Tuple[str, str, str]
TripleI = Tuple[int, int, int]


@dataclass
class KnowledgeGraph:
    num_entities: int
    num_relations_original: int
    train: np.ndarray  # [N,3] int64, includes reciprocal triples
    valid: List[TripleI]
    test: List[TripleI]
    ent2id: Dict[str, int]
    rel2id: Dict[str, int]
    tails_of_hr: Dict[Tuple[int, int], np.ndarray]
    heads_of_rt: Dict[Tuple[int, int], np.ndarray]

    @property
    def num_relations_total(self) -> int:
        return 2 * self.num_relations_original


class TripleDataset(Dataset):
    def __init__(self, triples: np.ndarray):
        if triples.ndim != 2 or triples.shape[1] != 3:
            raise ValueError(f"Expected [N,3] triples, got {triples.shape}")
        self.triples = triples.astype(np.int64, copy=False)

    def __len__(self) -> int:
        return int(self.triples.shape[0])

    def __getitem__(self, index: int):
        h, r, t = self.triples[index]
        return int(h), int(r), int(t)


def read_triples_file(path: str | Path) -> List[TripleS]:
    triples: List[TripleS] = []
    with Path(path).open("r", encoding="utf-8-sig") as f:
        for raw in f:
            line = raw.strip()
            if not line:
                continue
            parts = line.split("\t")
            if len(parts) != 3:
                parts = line.split()
            if len(parts) != 3:
                raise ValueError(f"Invalid triple line in {path}: {line!r}")
            triples.append((parts[0].strip(), parts[1].strip(), parts[2].strip()))
    return triples


def build_id_maps(*groups: Sequence[TripleS]) -> Tuple[Dict[str, int], Dict[str, int]]:
    ent2id: Dict[str, int] = {}
    rel2id: Dict[str, int] = {}
    for triples in groups:
        for h, r, t in triples:
            if h not in ent2id:
                ent2id[h] = len(ent2id)
            if t not in ent2id:
                ent2id[t] = len(ent2id)
            if r not in rel2id:
                rel2id[r] = len(rel2id)
    return ent2id, rel2id


def map_triples(triples: Sequence[TripleS], ent2id: Mapping[str, int], rel2id: Mapping[str, int]) -> List[TripleI]:
    return [(ent2id[h], rel2id[r], ent2id[t]) for h, r, t in triples]


def reciprocal_closure(triples: Sequence[TripleI], num_relations: int) -> List[TripleI]:
    """Contract §II.3.2: ``(h,r,t) <-> (t, r^{-1}, h)``, ``r^{-1}=r+num_relations``."""
    return list(triples) + [(t, r + num_relations, h) for h, r, t in triples]


def build_filters(base_triples: Sequence[TripleI], valid: Sequence[TripleI], test: Sequence[TripleI]):
    """Filters are built over the ORIGINAL (non-reciprocal) relation ids only —
    evaluation always queries with original relations; reciprocal
    relations are a training-time convenience, not an evaluation protocol
    change (matches v25's documented convention)."""
    tails: Dict[Tuple[int, int], set] = {}
    heads: Dict[Tuple[int, int], set] = {}
    for h, r, t in list(base_triples) + list(valid) + list(test):
        tails.setdefault((h, r), set()).add(t)
        heads.setdefault((r, t), set()).add(h)
    tails_np = {k: np.asarray(sorted(v), dtype=np.int64) for k, v in tails.items()}
    heads_np = {k: np.asarray(sorted(v), dtype=np.int64) for k, v in heads.items()}
    return tails_np, heads_np


def load_knowledge_graph(train_path: str, valid_path: str, test_path: str) -> KnowledgeGraph:
    train_raw = read_triples_file(train_path)
    valid_raw = read_triples_file(valid_path)
    test_raw = read_triples_file(test_path)
    ent2id, rel2id = build_id_maps(train_raw, valid_raw, test_raw)
    train_orig = map_triples(train_raw, ent2id, rel2id)
    valid = map_triples(valid_raw, ent2id, rel2id)
    test = map_triples(test_raw, ent2id, rel2id)
    tails, heads = build_filters(train_orig, valid, test)
    num_rel_orig = len(rel2id)
    train_full = reciprocal_closure(train_orig, num_rel_orig)
    return KnowledgeGraph(
        num_entities=len(ent2id),
        num_relations_original=num_rel_orig,
        train=np.asarray(train_full, dtype=np.int64),
        valid=valid,
        test=test,
        ent2id=ent2id,
        rel2id=rel2id,
        tails_of_hr=tails,
        heads_of_rt=heads,
    )


def tiny_kg() -> KnowledgeGraph:
    """Small synthetic graph for smoke tests, mirrors the Fase 1 oracle's tiny graph."""
    base = [(0, 0, 1), (1, 0, 2), (2, 1, 3), (3, 1, 4), (4, 0, 5), (5, 1, 0)]
    valid = [(0, 0, 1), (2, 1, 3)]
    test = [(1, 0, 2), (3, 1, 4)]
    tails, heads = build_filters(base, valid, test)
    return KnowledgeGraph(
        num_entities=6,
        num_relations_original=2,
        train=np.asarray(reciprocal_closure(base, 2), dtype=np.int64),
        valid=valid,
        test=test,
        ent2id={str(i): i for i in range(6)},
        rel2id={str(i): i for i in range(2)},
        tails_of_hr=tails,
        heads_of_rt=heads,
    )


def _contains_sorted(values: np.ndarray, candidates: np.ndarray) -> np.ndarray:
    if values.size == 0:
        return np.zeros(candidates.shape, dtype=bool)
    idx = np.searchsorted(values, candidates)
    mask = idx < values.size
    out = np.zeros(candidates.shape, dtype=bool)
    out[mask] = values[idx[mask]] == candidates[mask]
    return out


def sample_negatives(
    h: torch.Tensor, r: torch.Tensor, t: torch.Tensor, kg: KnowledgeGraph, neg_k: int,
    rng: np.random.Generator, device: torch.device,
) -> torch.Tensor:
    """Filtered tail negatives for the given (h,r,t) batch (contract-agnostic
    utility, reused for both tail and — via the reciprocal relation — head
    negatives by the caller)."""
    batch = int(h.numel())
    h_np, r_np, t_np = h.cpu().numpy(), r.cpu().numpy(), t.cpu().numpy()
    out = np.empty((batch, neg_k), dtype=np.int64)
    for i in range(batch):
        forbidden = kg.tails_of_hr.get((int(h_np[i]), int(r_np[i])), np.empty(0, dtype=np.int64))
        if forbidden.size >= kg.num_entities:
            out[i] = rng.integers(0, kg.num_entities, size=neg_k, dtype=np.int64)
            continue
        filled = 0
        tries = 0
        row = np.empty(neg_k, dtype=np.int64)
        while filled < neg_k and tries < 16:
            need = neg_k - filled
            cand = rng.integers(0, kg.num_entities, size=max(need * 2, 16), dtype=np.int64)
            cand = cand[~_contains_sorted(forbidden, cand)]
            take = min(need, cand.size)
            if take:
                row[filled : filled + take] = cand[:take]
                filled += take
            tries += 1
        if filled < neg_k:
            row[filled:] = rng.integers(0, kg.num_entities, size=neg_k - filled, dtype=np.int64)
        out[i] = row
    return torch.from_numpy(out).to(device=device, non_blocking=True)
