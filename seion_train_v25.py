#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
SEION Train v25 — Reproducible Hybrid KGE Trainer
=================================================

A clean successor to the legacy v20/v21 experimental trainers.

Design goals
------------
1. One mathematically consistent score path for training and evaluation.
2. Correct, symmetric filtered head/tail ranking.
3. Three explicit and independently ablatable branches:
      - fixed structural-kernel SEION star (for example E8),
      - learned CP-Star generator,
      - bilinear baseline.
4. Filippov and associator regularizers connected to trainable embeddings
   and, when enabled, to the learned CP law.
5. Complete run provenance: source snapshot/hash, dataset hashes, kernel hash,
   environment, hardware, command, config, checkpoints and metric schema.
6. Blackwell-friendly execution without making mixed precision part of the
   scientific definition of the model.

The fixed ternary law is

    star_f(a,b,c)_d = sum_{a0,f} f[a0,f,d] a[a0]
                      * sum_{b0,c0} f[b0,c0,f] b[b0] c[c0].

The learned CP-Star law is

    star_cp(a,b,c) = s O Norm(Aa ⊙ Bb ⊙ Cc) + rho a.

The KGE score is a calibrated mixture of fixed-star distance, CP-star
Distance, and a bilinear score. All three branches use the same code path in
positive, negative, head-ranking and tail-ranking evaluation.

This file intentionally does not claim that FI, E8, CP-Star, or pathwise
quantities are universally beneficial. It makes those hypotheses testable.
"""

from __future__ import annotations

import argparse
import contextlib
import dataclasses
import datetime as dt
import hashlib
import json
import math
import os
import platform
import random
import shutil
import subprocess
import sys
import tempfile
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, Iterable, List, Mapping, Optional, Sequence, Tuple

import numpy as np
import torch
import torch.nn as nn
import torch.nn.functional as F
from torch.utils.data import DataLoader, Dataset


VERSION = "25.0.0-blackwell-repro"
RUN_SCHEMA = "seion-kge-run-v25.1"
METRICS_SCHEMA = "seion-kge-metrics-v25.1"
BRANCHES = ("fixed", "cp", "bilinear")


# =============================================================================
# Reproducibility and IO
# =============================================================================


def utc_now() -> str:
    return dt.datetime.now(dt.timezone.utc).isoformat()


def ensure_dir(path: str | Path) -> Path:
    p = Path(path)
    p.mkdir(parents=True, exist_ok=True)
    return p


def atomic_write_text(path: str | Path, text: str) -> None:
    path = Path(path)
    ensure_dir(path.parent)
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(text, encoding="utf-8")
    os.replace(tmp, path)


def save_json(obj: Any, path: str | Path) -> None:
    atomic_write_text(path, json.dumps(obj, indent=2, ensure_ascii=False, allow_nan=False))


def append_jsonl(obj: Mapping[str, Any], path: str | Path) -> None:
    path = Path(path)
    ensure_dir(path.parent)
    with path.open("a", encoding="utf-8") as f:
        f.write(json.dumps(dict(obj), ensure_ascii=False, allow_nan=False) + "\n")


def sha256_file(path: str | Path, chunk_size: int = 1 << 20) -> str:
    p = Path(path)
    h = hashlib.sha256()
    with p.open("rb") as f:
        while True:
            block = f.read(chunk_size)
            if not block:
                break
            h.update(block)
    return h.hexdigest()


def file_manifest(path: str | Path) -> Dict[str, Any]:
    p = Path(path).resolve()
    return {
        "path": str(p),
        "exists": p.is_file(),
        "size_bytes": p.stat().st_size if p.is_file() else None,
        "sha256": sha256_file(p) if p.is_file() else None,
    }


def run_command(cmd: Sequence[str], cwd: Optional[str | Path] = None, timeout: float = 5.0) -> str:
    try:
        r = subprocess.run(
            list(cmd),
            cwd=str(cwd) if cwd is not None else None,
            capture_output=True,
            text=True,
            timeout=timeout,
            check=False,
        )
        return (r.stdout or r.stderr or "").strip()[:20000]
    except Exception as exc:  # pragma: no cover - environment dependent
        return f"unavailable: {type(exc).__name__}: {exc}"


def git_manifest(cwd: str | Path) -> Dict[str, Any]:
    root = run_command(["git", "rev-parse", "--show-toplevel"], cwd=cwd)
    if not root or root.startswith("unavailable") or "fatal:" in root.lower():
        return {"available": False, "root": None, "commit": None, "dirty": None}
    commit = run_command(["git", "rev-parse", "HEAD"], cwd=root)
    status = run_command(["git", "status", "--porcelain"], cwd=root)
    return {
        "available": True,
        "root": root,
        "commit": commit,
        "dirty": bool(status.strip()),
        "status_porcelain": status,
    }


def environment_manifest() -> Dict[str, Any]:
    return {
        "created_utc": utc_now(),
        "python": sys.version,
        "python_executable": sys.executable,
        "platform": platform.platform(),
        "processor": platform.processor(),
        "numpy": np.__version__,
        "torch": torch.__version__,
        "torch_cuda": torch.version.cuda,
        "cudnn": torch.backends.cudnn.version() if torch.backends.cudnn.is_available() else None,
    }


def hardware_manifest() -> Dict[str, Any]:
    out: Dict[str, Any] = {
        "cuda_available": bool(torch.cuda.is_available()),
        "cpu_count": os.cpu_count(),
    }
    if torch.cuda.is_available():
        devices = []
        for idx in range(torch.cuda.device_count()):
            props = torch.cuda.get_device_properties(idx)
            devices.append(
                {
                    "index": idx,
                    "name": torch.cuda.get_device_name(idx),
                    "capability": list(torch.cuda.get_device_capability(idx)),
                    "total_memory_bytes": int(props.total_memory),
                    "multi_processor_count": int(props.multi_processor_count),
                }
            )
        out["cuda_devices"] = devices
        out["nvidia_smi"] = run_command(
            [
                "nvidia-smi",
                "--query-gpu=name,driver_version,memory.total,power.limit",
                "--format=csv,noheader",
            ],
            timeout=5.0,
        )
    return out


def set_seed(seed: int, deterministic: bool) -> None:
    random.seed(seed)
    np.random.seed(seed)
    torch.manual_seed(seed)
    if torch.cuda.is_available():
        torch.cuda.manual_seed_all(seed)
    if deterministic:
        torch.backends.cudnn.benchmark = False
        torch.backends.cudnn.deterministic = True
        try:
            torch.use_deterministic_algorithms(True)
        except Exception:
            pass


def get_rng_state() -> Dict[str, Any]:
    return {
        "python": random.getstate(),
        "numpy": np.random.get_state(),
        "torch": torch.get_rng_state(),
        "cuda": torch.cuda.get_rng_state_all() if torch.cuda.is_available() else None,
    }


def restore_rng_state(state: Optional[Mapping[str, Any]]) -> None:
    if not state:
        return
    random.setstate(state["python"])
    np.random.set_state(state["numpy"])
    torch.set_rng_state(state["torch"])
    if torch.cuda.is_available() and state.get("cuda") is not None:
        torch.cuda.set_rng_state_all(state["cuda"])


def autocast_context(device: torch.device, enabled: bool, dtype_name: str):
    if not enabled or device.type != "cuda":
        return contextlib.nullcontext()
    dtype = torch.bfloat16 if dtype_name == "bf16" else torch.float16
    return torch.autocast(device_type="cuda", dtype=dtype, enabled=True)


def gpu_memory_snapshot() -> Dict[str, float]:
    if not torch.cuda.is_available():
        return {}
    torch.cuda.synchronize()
    return {
        "allocated_gb": float(torch.cuda.memory_allocated() / 1024**3),
        "reserved_gb": float(torch.cuda.memory_reserved() / 1024**3),
        "max_allocated_gb": float(torch.cuda.max_memory_allocated() / 1024**3),
        "max_reserved_gb": float(torch.cuda.max_memory_reserved() / 1024**3),
    }


# =============================================================================
# Dataset
# =============================================================================


TripleS = Tuple[str, str, str]
TripleI = Tuple[int, int, int]


@dataclass
class KnowledgeGraph:
    num_entities: int
    num_relations_original: int
    num_relations_train: int
    train: np.ndarray
    valid: List[TripleI]
    test: List[TripleI]
    ent2id: Dict[str, int]
    rel2id: Dict[str, int]
    tails_of_hr: Dict[Tuple[int, int], np.ndarray]
    heads_of_rt: Dict[Tuple[int, int], np.ndarray]
    bernoulli_tail_prob: np.ndarray


class TripleDataset(Dataset):
    def __init__(self, triples: np.ndarray):
        if triples.ndim != 2 or triples.shape[1] != 3:
            raise ValueError(f"Expected [N,3] triples, got {triples.shape}")
        self.triples = triples.astype(np.int64, copy=False)

    def __len__(self) -> int:
        return int(self.triples.shape[0])

    def __getitem__(self, index: int) -> Tuple[int, int, int]:
        h, r, t = self.triples[index]
        return int(h), int(r), int(t)


def read_triples_file(path: str | Path) -> List[TripleS]:
    triples: List[TripleS] = []
    with Path(path).open("r", encoding="utf-8-sig") as f:
        for raw in f:
            line = raw.strip()
            if not line:
                continue
            if line.lower() in {"head\trelation\ttail", "head relation tail"}:
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


def add_reciprocal_training(triples: Sequence[TripleI], num_relations: int) -> List[TripleI]:
    return list(triples) + [(t, r + num_relations, h) for h, r, t in triples]


def build_filters(train: Sequence[TripleI], valid: Sequence[TripleI], test: Sequence[TripleI]):
    tails: Dict[Tuple[int, int], set[int]] = {}
    heads: Dict[Tuple[int, int], set[int]] = {}
    for h, r, t in list(train) + list(valid) + list(test):
        # Ignore reciprocal training relations when filters are built for the
        # original evaluation protocol; reciprocal triples are not passed here.
        tails.setdefault((h, r), set()).add(t)
        heads.setdefault((r, t), set()).add(h)
    tails_np = {k: np.asarray(sorted(v), dtype=np.int64) for k, v in tails.items()}
    heads_np = {k: np.asarray(sorted(v), dtype=np.int64) for k, v in heads.items()}
    return tails_np, heads_np


def build_bernoulli_probs(train: Sequence[TripleI], num_relations: int) -> np.ndarray:
    tails_per_hr: Dict[Tuple[int, int], set[int]] = {}
    heads_per_rt: Dict[Tuple[int, int], set[int]] = {}
    for h, r, t in train:
        if r >= num_relations:
            continue
        tails_per_hr.setdefault((h, r), set()).add(t)
        heads_per_rt.setdefault((r, t), set()).add(h)

    tph_num = np.zeros(num_relations, dtype=np.float64)
    tph_den = np.zeros(num_relations, dtype=np.float64)
    hpt_num = np.zeros(num_relations, dtype=np.float64)
    hpt_den = np.zeros(num_relations, dtype=np.float64)
    for (_, r), values in tails_per_hr.items():
        tph_num[r] += len(values)
        tph_den[r] += 1
    for (r, _), values in heads_per_rt.items():
        hpt_num[r] += len(values)
        hpt_den[r] += 1
    tph = tph_num / np.maximum(tph_den, 1.0)
    hpt = hpt_num / np.maximum(hpt_den, 1.0)
    return (tph / np.maximum(tph + hpt, 1e-12)).astype(np.float32)


def load_knowledge_graph(args: argparse.Namespace) -> KnowledgeGraph:
    train_raw = read_triples_file(args.train)
    valid_raw = read_triples_file(args.valid)
    test_raw = read_triples_file(args.test)
    ent2id, rel2id = build_id_maps(train_raw, valid_raw, test_raw)
    train_orig = map_triples(train_raw, ent2id, rel2id)
    valid = map_triples(valid_raw, ent2id, rel2id)
    test = map_triples(test_raw, ent2id, rel2id)
    tails, heads = build_filters(train_orig, valid, test)
    num_rel_orig = len(rel2id)
    train = add_reciprocal_training(train_orig, num_rel_orig) if args.reciprocal_train else train_orig
    return KnowledgeGraph(
        num_entities=len(ent2id),
        num_relations_original=num_rel_orig,
        num_relations_train=num_rel_orig * (2 if args.reciprocal_train else 1),
        train=np.asarray(train, dtype=np.int64),
        valid=valid,
        test=test,
        ent2id=ent2id,
        rel2id=rel2id,
        tails_of_hr=tails,
        heads_of_rt=heads,
        bernoulli_tail_prob=build_bernoulli_probs(train_orig, num_rel_orig),
    )


# =============================================================================
# Negative sampling
# =============================================================================


def _contains_sorted(values: np.ndarray, candidates: np.ndarray) -> np.ndarray:
    if values.size == 0:
        return np.zeros(candidates.shape, dtype=bool)
    idx = np.searchsorted(values, candidates)
    mask = idx < values.size
    out = np.zeros(candidates.shape, dtype=bool)
    out[mask] = values[idx[mask]] == candidates[mask]
    return out


def _sample_filtered_row(
    forbidden: np.ndarray,
    size: int,
    num_entities: int,
    rng: np.random.Generator,
    max_tries: int,
) -> np.ndarray:
    if forbidden.size >= num_entities:
        return rng.integers(0, num_entities, size=size, dtype=np.int64)
    out = np.empty(size, dtype=np.int64)
    filled = 0
    tries = 0
    while filled < size and tries < max_tries:
        need = size - filled
        candidates = rng.integers(0, num_entities, size=max(need * 2, 16), dtype=np.int64)
        candidates = candidates[~_contains_sorted(forbidden, candidates)]
        take = min(need, candidates.size)
        if take:
            out[filled : filled + take] = candidates[:take]
            filled += take
        tries += 1
    if filled < size:
        out[filled:] = rng.integers(0, num_entities, size=size - filled, dtype=np.int64)
    return out


def sample_negatives(
    h: torch.Tensor,
    r: torch.Tensor,
    t: torch.Tensor,
    kg: KnowledgeGraph,
    args: argparse.Namespace,
    rng: np.random.Generator,
    device: torch.device,
) -> Tuple[torch.Tensor, torch.Tensor]:
    batch = int(h.numel())
    k = int(args.neg_k)
    if args.neg_mode == "baseline":
        tail = torch.randint(0, kg.num_entities, (batch, k), device=device)
        head = torch.randint(0, kg.num_entities, (batch, k), device=device)
        return head, tail

    h_np = h.detach().cpu().numpy()
    r_np = r.detach().cpu().numpy()
    t_np = t.detach().cpu().numpy()
    tail_np = np.empty((batch, k), dtype=np.int64)
    head_np = np.empty((batch, k), dtype=np.int64)
    for i in range(batch):
        rr = int(r_np[i])
        # Reciprocal relations have no original filter table. Their training
        # negatives remain random, which is explicit in the manifest.
        original_rr = rr if rr < kg.num_relations_original else rr - kg.num_relations_original
        if args.neg_mode == "bernoulli":
            # We still train both branches; Bernoulli controls which branch gets
            # relation-aware filtered candidates and which remains random.
            p_tail = float(kg.bernoulli_tail_prob[original_rr])
            filter_tail = bool(rng.random() < p_tail)
        else:
            filter_tail = True

        tail_forbidden = kg.tails_of_hr.get((int(h_np[i]), original_rr), np.empty(0, dtype=np.int64))
        head_forbidden = kg.heads_of_rt.get((original_rr, int(t_np[i])), np.empty(0, dtype=np.int64))
        if args.neg_mode == "filtered" or filter_tail:
            tail_np[i] = _sample_filtered_row(tail_forbidden, k, kg.num_entities, rng, args.filtered_neg_max_tries)
        else:
            tail_np[i] = rng.integers(0, kg.num_entities, size=k, dtype=np.int64)
        if args.neg_mode == "filtered" or not filter_tail:
            head_np[i] = _sample_filtered_row(head_forbidden, k, kg.num_entities, rng, args.filtered_neg_max_tries)
        else:
            head_np[i] = rng.integers(0, kg.num_entities, size=k, dtype=np.int64)

    return (
        torch.from_numpy(head_np).to(device=device, non_blocking=True),
        torch.from_numpy(tail_np).to(device=device, non_blocking=True),
    )


# =============================================================================
# Model
# =============================================================================


def inverse_softplus(value: float) -> float:
    value = max(float(value), 1e-8)
    return math.log(math.expm1(value))


def parse_gate_init(text: str) -> Tuple[float, float, float]:
    values = {"fixed": 0.2, "cp": 0.2, "bilinear": 0.6}
    if text.strip():
        for item in text.split(","):
            name, raw = item.split("=", 1)
            name = name.strip().lower()
            if name not in values:
                raise ValueError(f"Unknown gate branch {name!r}")
            values[name] = max(float(raw), 0.0)
    total = sum(values.values())
    if total <= 0:
        raise ValueError("At least one gate weight must be positive")
    return tuple(values[name] / total for name in BRANCHES)  # type: ignore[return-value]


class SeionV25(nn.Module):
    """Fixed-kernel + learned CP-Star + bilinear KGE model."""

    def __init__(
        self,
        num_entities: int,
        num_relations: int,
        dimension: int,
        architecture: str,
        f_path: str,
        cp_rank: int,
        cp_norm: str,
        cp_residual_init: float,
        gate_per_relation: bool,
        gate_init: Tuple[float, float, float],
        context_mix_init: float,
        relation_gain: bool,
    ) -> None:
        super().__init__()
        self.D = int(dimension)
        self.architecture = architecture
        self.has_fixed = architecture in {"fixed", "hybrid"}
        self.has_cp = architecture in {"cp", "hybrid"}
        self.has_bilinear = architecture in {"bilinear", "hybrid"}
        self.gate_per_relation = bool(gate_per_relation)
        self.use_relation_gain = bool(relation_gain)

        if self.has_fixed:
            if not f_path:
                raise ValueError("--f_path is required for fixed/hybrid architecture")
            f_np = np.load(f_path)
            if f_np.shape != (self.D, self.D, self.D):
                raise ValueError(f"Expected fixed kernel {(self.D, self.D, self.D)}, got {f_np.shape}")
            self.register_buffer("f", torch.from_numpy(f_np.astype(np.float32)), persistent=True)
        else:
            self.register_buffer("f", torch.empty(0), persistent=True)

        self.ent = nn.Embedding(num_entities, self.D)
        self.rel = nn.Embedding(num_relations, self.D)
        self.rel_ctx = nn.Embedding(num_relations, self.D)
        self.rel_bilin = nn.Embedding(num_relations, self.D)
        nn.init.xavier_uniform_(self.ent.weight)
        nn.init.xavier_uniform_(self.rel.weight)
        nn.init.xavier_uniform_(self.rel_ctx.weight)
        nn.init.xavier_uniform_(self.rel_bilin.weight)

        self.ctx_mix_logits = nn.Embedding(num_relations, 1)
        with torch.no_grad():
            p = min(max(float(context_mix_init), 1e-6), 1 - 1e-6)
            self.ctx_mix_logits.weight.fill_(math.log(p / (1 - p)))

        self.rel_gain_raw = nn.Embedding(num_relations, 1)
        with torch.no_grad():
            self.rel_gain_raw.weight.fill_(inverse_softplus(1.0))

        if self.has_cp:
            if cp_rank <= 0:
                raise ValueError("--cp_rank must be positive for cp/hybrid architecture")
            self.cp_rank = int(cp_rank)
            self.cp_A = nn.Linear(self.D, self.cp_rank, bias=False)
            self.cp_B = nn.Linear(self.D, self.cp_rank, bias=False)
            self.cp_C = nn.Linear(self.D, self.cp_rank, bias=False)
            self.cp_O = nn.Linear(self.cp_rank, self.D, bias=False)
            for layer in (self.cp_A, self.cp_B, self.cp_C, self.cp_O):
                nn.init.xavier_uniform_(layer.weight)
            if cp_norm == "layernorm":
                self.cp_norm = nn.LayerNorm(self.cp_rank)
            elif cp_norm == "rms":
                self.cp_norm = RMSNorm(self.cp_rank)
            elif cp_norm == "none":
                self.cp_norm = nn.Identity()
            else:
                raise ValueError(cp_norm)
            self.cp_scale_raw = nn.Parameter(torch.tensor(inverse_softplus(1.0), dtype=torch.float32))
            residual = min(max(float(cp_residual_init), -0.999), 0.999)
            self.cp_residual_raw = nn.Parameter(torch.tensor(np.arctanh(residual), dtype=torch.float32))
        else:
            self.cp_rank = 0
            self.cp_A = self.cp_B = self.cp_C = self.cp_O = None
            self.cp_norm = nn.Identity()
            self.cp_scale_raw = None
            self.cp_residual_raw = None

        gate_logits = torch.log(torch.tensor(gate_init, dtype=torch.float32).clamp_min(1e-8))
        if self.gate_per_relation:
            self.gate_logits = nn.Embedding(num_relations, len(BRANCHES))
            with torch.no_grad():
                self.gate_logits.weight.copy_(gate_logits.unsqueeze(0).expand(num_relations, -1))
        else:
            self.gate_logits = nn.Parameter(gate_logits)

        # Independent score calibration prevents distance and bilinear branches
        # from competing only because of scale.
        self.branch_scale_raw = nn.Parameter(torch.full((3,), inverse_softplus(1.0)))
        self.branch_bias = nn.Parameter(torch.zeros(3))

        self.register_buffer("projector", torch.empty(0), persistent=True)
        self.projector_rank = 0

    def context(self, relation_ids: torch.Tensor, relation_vectors: torch.Tensor) -> torch.Tensor:
        mix = torch.sigmoid(self.ctx_mix_logits(relation_ids)).to(relation_vectors.dtype)
        return mix * self.rel_ctx(relation_ids).to(relation_vectors.dtype) + (1 - mix) * relation_vectors

    def relation_gain(self, relation_ids: torch.Tensor) -> torch.Tensor:
        if not self.use_relation_gain:
            return torch.ones(relation_ids.shape, device=relation_ids.device, dtype=self.rel.weight.dtype)
        return F.softplus(self.rel_gain_raw(relation_ids).squeeze(-1)).clamp(1e-4, 10.0)

    def branch_weights(self, relation_ids: torch.Tensor, temperature: float = 1.0) -> torch.Tensor:
        if self.architecture != "hybrid":
            weights = torch.zeros((relation_ids.numel(), 3), device=relation_ids.device, dtype=self.rel.weight.dtype)
            index = {"fixed": 0, "cp": 1, "bilinear": 2}[self.architecture]
            weights[:, index] = 1.0
            return weights
        logits = self.gate_logits(relation_ids) if self.gate_per_relation else self.gate_logits.unsqueeze(0).expand(relation_ids.numel(), -1)
        unavailable = torch.tensor(
            [not self.has_fixed, not self.has_cp, not self.has_bilinear],
            device=logits.device,
            dtype=torch.bool,
        )
        logits = logits.masked_fill(unavailable.unsqueeze(0), -1e9)
        return F.softmax(logits / max(float(temperature), 1e-6), dim=-1)

    def score_calibration(self) -> Tuple[torch.Tensor, torch.Tensor]:
        return F.softplus(self.branch_scale_raw).clamp(1e-4, 100.0), self.branch_bias

    def fixed_inner(self, b: torch.Tensor, c: torch.Tensor) -> torch.Tensor:
        if not self.has_fixed:
            raise RuntimeError("Fixed branch disabled")
        return torch.einsum("bcf,...b,...c->...f", self.f, b, c)

    def fixed_matrix(self, b: torch.Tensor, c: torch.Tensor) -> torch.Tensor:
        """Return M[...,a,d] with star(a,b,c)_d = sum_a M[a,d] a_a."""
        inner = self.fixed_inner(b, c)
        return torch.einsum("afd,...f->...ad", self.f, inner)

    def fixed_predict(self, a: torch.Tensor, b: torch.Tensor, c: torch.Tensor) -> torch.Tensor:
        matrix = self.fixed_matrix(b, c)
        return torch.einsum("...ad,...a->...d", matrix, a)

    def cp_predict(self, a: torch.Tensor, b: torch.Tensor, c: torch.Tensor) -> torch.Tensor:
        if not self.has_cp or self.cp_A is None or self.cp_B is None or self.cp_C is None or self.cp_O is None:
            raise RuntimeError("CP branch disabled")
        z = self.cp_A(a) * self.cp_B(b) * self.cp_C(c)
        z = self.cp_norm(z)
        scale = F.softplus(self.cp_scale_raw).clamp(1e-4, 100.0)
        residual = torch.tanh(self.cp_residual_raw)
        return scale * self.cp_O(z) + residual * a

    def ternary_vector(self, a: torch.Tensor, b: torch.Tensor, c: torch.Tensor, relation_ids: torch.Tensor) -> torch.Tensor:
        vectors = []
        weights = []
        gates = self.branch_weights(relation_ids)
        if self.has_fixed:
            vectors.append(self.fixed_predict(a, b, c))
            weights.append(gates[:, 0])
        if self.has_cp:
            vectors.append(self.cp_predict(a, b, c))
            weights.append(gates[:, 1])
        if not vectors:
            raise RuntimeError("No ternary branch enabled")
        weight_tensor = torch.stack(weights, dim=1)
        weight_tensor = weight_tensor / weight_tensor.sum(dim=1, keepdim=True).clamp_min(1e-12)
        out = torch.zeros_like(vectors[0])
        for index, vector in enumerate(vectors):
            out = out + weight_tensor[:, index : index + 1] * vector
        return out

    def _calibrate_components(self, raw: torch.Tensor) -> torch.Tensor:
        scale, bias = self.score_calibration()
        return raw * scale.view(*([1] * (raw.ndim - 1)), 3) + bias.view(*([1] * (raw.ndim - 1)), 3)

    def _combine(self, components: torch.Tensor, relation_ids: torch.Tensor, gate_temperature: float) -> torch.Tensor:
        calibrated = self._calibrate_components(components)
        weights = self.branch_weights(relation_ids, temperature=gate_temperature)
        while weights.ndim < calibrated.ndim:
            weights = weights.unsqueeze(1)
        return (calibrated * weights).sum(dim=-1)

    def _positive_components(self, h: torch.Tensor, r: torch.Tensor, c: torch.Tensor, t: torch.Tensor) -> torch.Tensor:
        shape = h.shape[:-1]
        zeros = torch.zeros(shape, device=h.device, dtype=h.dtype)
        fixed = -((self.fixed_predict(h, r, c) - t) ** 2).mean(dim=-1) if self.has_fixed else zeros
        cp = -((self.cp_predict(h, r, c) - t) ** 2).mean(dim=-1) if self.has_cp else zeros
        bilinear = (h * r * t).sum(dim=-1) / math.sqrt(self.D) if self.has_bilinear else zeros
        return torch.stack((fixed, cp, bilinear), dim=-1)

    def score_positive(
        self,
        h: torch.Tensor,
        relation_ids: torch.Tensor,
        t: torch.Tensor,
        gate_temperature: float = 1.0,
    ) -> torch.Tensor:
        r = self.rel(relation_ids).to(h.dtype)
        c = self.context(relation_ids, r)
        gain = self.relation_gain(relation_ids).to(h.dtype)
        components = self._positive_components(h, r, c, t)
        components[..., :2] = components[..., :2] * gain.unsqueeze(-1)
        return self._combine(components, relation_ids, gate_temperature)

    @staticmethod
    def _expand_candidates(candidates: torch.Tensor, batch: int) -> torch.Tensor:
        if candidates.ndim == 2:
            return candidates.unsqueeze(0).expand(batch, -1, -1)
        if candidates.ndim == 3 and candidates.shape[0] == batch:
            return candidates
        raise ValueError(f"Candidates must be [M,D] or [B,K,D], got {tuple(candidates.shape)}")

    def score_tail_candidates(
        self,
        h: torch.Tensor,
        relation_ids: torch.Tensor,
        candidates: torch.Tensor,
        gate_temperature: float = 1.0,
    ) -> torch.Tensor:
        batch = h.shape[0]
        cand = self._expand_candidates(candidates, batch).to(h.dtype)
        r = self.rel(relation_ids).to(h.dtype)
        c = self.context(relation_ids, r)
        gain = self.relation_gain(relation_ids).to(h.dtype)
        zeros = torch.zeros(cand.shape[:-1], device=h.device, dtype=h.dtype)

        if self.has_fixed:
            pred_fixed = self.fixed_predict(h, r, c) * gain.unsqueeze(-1)
            fixed = -((pred_fixed.unsqueeze(1) - cand) ** 2).mean(dim=-1)
        else:
            fixed = zeros
        if self.has_cp:
            pred_cp = self.cp_predict(h, r, c) * gain.unsqueeze(-1)
            cp = -((pred_cp.unsqueeze(1) - cand) ** 2).mean(dim=-1)
        else:
            cp = zeros
        bilinear = torch.einsum("bd,bkd->bk", h * r, cand) / math.sqrt(self.D) if self.has_bilinear else zeros
        components = torch.stack((fixed, cp, bilinear), dim=-1)
        return self._combine(components, relation_ids, gate_temperature)

    def score_head_candidates(
        self,
        candidates: torch.Tensor,
        relation_ids: torch.Tensor,
        t: torch.Tensor,
        gate_temperature: float = 1.0,
    ) -> torch.Tensor:
        batch = t.shape[0]
        cand = self._expand_candidates(candidates, batch).to(t.dtype)
        r = self.rel(relation_ids).to(t.dtype)
        c = self.context(relation_ids, r)
        gain = self.relation_gain(relation_ids).to(t.dtype)
        zeros = torch.zeros(cand.shape[:-1], device=t.device, dtype=t.dtype)

        if self.has_fixed:
            matrix = self.fixed_matrix(r, c)  # [B,a,d]
            pred = torch.einsum("bad,bka->bkd", matrix, cand) * gain[:, None, None]
            fixed = -((pred - t.unsqueeze(1)) ** 2).mean(dim=-1)
        else:
            fixed = zeros
        if self.has_cp:
            r_exp = r.unsqueeze(1).expand(-1, cand.shape[1], -1)
            c_exp = c.unsqueeze(1).expand_as(r_exp)
            pred_cp = self.cp_predict(cand, r_exp, c_exp) * gain[:, None, None]
            cp = -((pred_cp - t.unsqueeze(1)) ** 2).mean(dim=-1)
        else:
            cp = zeros
        bilinear = torch.einsum("bkd,bd->bk", cand, r * t) / math.sqrt(self.D) if self.has_bilinear else zeros
        components = torch.stack((fixed, cp, bilinear), dim=-1)
        return self._combine(components, relation_ids, gate_temperature)

    @torch.no_grad()
    def build_kernel_pca_projector(self, rank: int) -> None:
        if rank <= 0:
            self.projector = torch.empty(0, device=self.ent.weight.device)
            self.projector_rank = 0
            return
        if not self.has_fixed:
            raise ValueError("Kernel PCA projector requires the fixed branch")
        f64 = self.f.detach().to(device="cpu", dtype=torch.float64)
        gram = torch.einsum("acd,bcd->ab", f64, f64)
        _, vectors = torch.linalg.eigh(gram)
        q = vectors[:, -min(rank, self.D) :]
        p = (q @ q.T).to(dtype=torch.float32, device=self.ent.weight.device)
        self.projector = p
        self.projector_rank = int(q.shape[1])

    def project(self, x: torch.Tensor) -> torch.Tensor:
        if self.projector.numel() == 0:
            return x
        return torch.matmul(x, self.projector.to(dtype=x.dtype))

    @torch.no_grad()
    def renorm_embeddings(self, max_norm: float = 1.0) -> None:
        for embedding in (self.ent, self.rel, self.rel_ctx, self.rel_bilin):
            weight = embedding.weight.data
            norms = weight.norm(dim=1, keepdim=True).clamp_min(1e-12)
            weight.mul_(torch.clamp(float(max_norm) / norms, max=1.0))


class RMSNorm(nn.Module):
    def __init__(self, dimension: int, eps: float = 1e-6):
        super().__init__()
        self.weight = nn.Parameter(torch.ones(dimension))
        self.eps = eps

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        return x * torch.rsqrt(x.float().pow(2).mean(dim=-1, keepdim=True) + self.eps).to(x.dtype) * self.weight


# =============================================================================
# Regularizers
# =============================================================================


def _sample_rows(pool: torch.Tensor, count: int) -> torch.Tensor:
    idx = torch.randint(0, pool.shape[0], (count,), device=pool.device)
    return pool[idx]


def filippov_embedding_loss(
    model: SeionV25,
    pool: torch.Tensor,
    relation_ids_pool: torch.Tensor,
    samples: int,
    detach_inner: bool,
) -> torch.Tensor:
    """Relative FI defect on trainable batch-derived vectors.

    Unlike the legacy random-vector/frozen-kernel diagnostic, this loss has a
    gradient with respect to entity/relation embeddings and the CP-Star law.
    """
    if samples <= 0 or not (model.has_fixed or model.has_cp):
        return pool.new_zeros(())
    s = min(int(samples), max(1, pool.shape[0]))
    a, b, x, c, d = (_sample_rows(pool, s) for _ in range(5))
    rid = relation_ids_pool[torch.randint(0, relation_ids_pool.numel(), (s,), device=pool.device)]

    xcd = model.ternary_vector(x, c, d, rid)
    abx = model.ternary_vector(a, b, x, rid)
    abc = model.ternary_vector(a, b, c, rid)
    abd = model.ternary_vector(a, b, d, rid)
    if detach_inner:
        xcd, abx, abc, abd = (z.detach() for z in (xcd, abx, abc, abd))
    lhs = model.ternary_vector(a, b, xcd, rid)
    rhs = (
        model.ternary_vector(abx, c, d, rid)
        + model.ternary_vector(x, abc, d, rid)
        + model.ternary_vector(x, c, abd, rid)
    )
    numerator = (lhs - rhs).float().pow(2).sum(dim=-1)
    denominator = lhs.float().pow(2).sum(dim=-1) + rhs.float().pow(2).sum(dim=-1)
    return (numerator / denominator.clamp_min(1e-12)).mean()


def associator_embedding_loss(
    model: SeionV25,
    pool: torch.Tensor,
    relation_ids_pool: torch.Tensor,
    samples: int,
    detach_inner: bool,
) -> torch.Tensor:
    if samples <= 0 or not (model.has_fixed or model.has_cp):
        return pool.new_zeros(())
    s = min(int(samples), max(1, pool.shape[0]))
    x1, x2, x3, x4, x5 = (_sample_rows(pool, s) for _ in range(5))
    rid = relation_ids_pool[torch.randint(0, relation_ids_pool.numel(), (s,), device=pool.device)]
    inner_left = model.ternary_vector(x1, x2, x3, rid)
    inner_right = model.ternary_vector(x3, x4, x5, rid)
    if detach_inner:
        inner_left = inner_left.detach()
        inner_right = inner_right.detach()
    left = model.ternary_vector(inner_left, x4, x5, rid)
    right = model.ternary_vector(x1, x2, inner_right, rid)
    numerator = (left - right).float().pow(2).sum(dim=-1)
    denominator = left.float().pow(2).sum(dim=-1) + right.float().pow(2).sum(dim=-1)
    return (numerator / denominator.clamp_min(1e-12)).mean()


def closure_embedding_loss(
    model: SeionV25,
    pool: torch.Tensor,
    relation_ids_pool: torch.Tensor,
    samples: int,
) -> torch.Tensor:
    if samples <= 0 or model.projector.numel() == 0 or not (model.has_fixed or model.has_cp):
        return pool.new_zeros(())
    s = min(int(samples), max(1, pool.shape[0]))
    a, b, c = (model.project(_sample_rows(pool, s)) for _ in range(3))
    rid = relation_ids_pool[torch.randint(0, relation_ids_pool.numel(), (s,), device=pool.device)]
    y = model.ternary_vector(a, b, c, rid)
    residual = y - model.project(y)
    return (residual.float().pow(2).sum(dim=-1) / y.float().pow(2).sum(dim=-1).clamp_min(1e-12)).mean()


def cp_teacher_distillation_loss(
    model: SeionV25,
    h: torch.Tensor,
    r: torch.Tensor,
    c: torch.Tensor,
) -> torch.Tensor:
    if not (model.has_fixed and model.has_cp):
        return h.new_zeros(())
    teacher = model.fixed_predict(h, r, c).detach()
    student = model.cp_predict(h, r, c)
    mse = (student - teacher).float().pow(2).mean()
    cosine = 1.0 - F.cosine_similarity(student.float(), teacher.float(), dim=-1).mean()
    return mse + cosine


def gate_entropy_loss(model: SeionV25, relation_ids: torch.Tensor, temperature: float) -> torch.Tensor:
    if model.architecture != "hybrid":
        return relation_ids.new_zeros((), dtype=torch.float32)
    weights = model.branch_weights(relation_ids, temperature)
    entropy = -(weights * weights.clamp_min(1e-12).log()).sum(dim=-1).mean()
    return -entropy  # positive weight encourages non-collapsed gates


def effective_weight(base: float, epoch: int, warmup_epochs: int) -> float:
    if base == 0:
        return 0.0
    if warmup_epochs <= 0:
        return float(base)
    return float(base) * min(1.0, float(epoch + 1) / float(warmup_epochs))


def regularizer_gradient_audit(
    loss: torch.Tensor,
    model: SeionV25,
    retain_graph: bool = True,
) -> Dict[str, float]:
    params: List[torch.Tensor] = [model.ent.weight, model.rel.weight]
    names = ["entity", "relation"]
    if model.has_cp and model.cp_A is not None and model.cp_O is not None:
        params.extend([model.cp_A.weight, model.cp_O.weight])
        names.extend(["cp_A", "cp_O"])
    grads = torch.autograd.grad(loss, params, retain_graph=retain_graph, allow_unused=True)
    out: Dict[str, float] = {}
    for name, grad in zip(names, grads):
        out[name] = 0.0 if grad is None else float(grad.detach().float().norm().item())
    out["total"] = float(sum(out.values()))
    return out


# =============================================================================
# Loss and evaluation
# =============================================================================


def negative_sampling_loss(
    positive: torch.Tensor,
    negative: torch.Tensor,
    mode: str,
    adversarial_temperature: float,
    margin: float,
) -> torch.Tensor:
    if mode == "margin":
        return F.softplus(float(margin) - positive.unsqueeze(1) + negative).mean(dim=1)
    if mode != "logistic":
        raise ValueError(mode)
    positive_loss = F.softplus(-positive)
    if adversarial_temperature > 0:
        weights = F.softmax(negative.detach() * float(adversarial_temperature), dim=1)
        negative_loss = (weights * F.softplus(negative)).sum(dim=1)
    else:
        negative_loss = F.softplus(negative).mean(dim=1)
    return positive_loss + negative_loss


def ranks_to_metrics(ranks: torch.Tensor) -> Dict[str, float]:
    ranks = ranks.float()
    return {
        "MRR": float((1.0 / ranks).mean().item()),
        "Hits@1": float((ranks <= 1).float().mean().item()),
        "Hits@3": float((ranks <= 3).float().mean().item()),
        "Hits@10": float((ranks <= 10).float().mean().item()),
        "mean_rank": float(ranks.mean().item()),
        "count": int(ranks.numel()),
    }


def _filter_score_block(
    scores: torch.Tensor,
    filters: Mapping[Tuple[int, int], np.ndarray],
    keys: Sequence[Tuple[int, int]],
    start: int,
    end: int,
) -> None:
    rows: List[torch.Tensor] = []
    cols: List[torch.Tensor] = []
    device = scores.device
    for row, key in enumerate(keys):
        values = filters.get(key)
        if values is None or values.size == 0:
            continue
        mask = (values >= start) & (values < end)
        if mask.any():
            c = torch.from_numpy(values[mask] - start).to(device=device, dtype=torch.long)
            rows.append(torch.full((c.numel(),), row, device=device, dtype=torch.long))
            cols.append(c)
    if rows:
        scores[torch.cat(rows), torch.cat(cols)] = -torch.inf


@torch.inference_mode()
def evaluate(
    model: SeionV25,
    kg: KnowledgeGraph,
    split: str,
    device: torch.device,
    batch_size: int,
    entity_block: int,
    subset: float,
    gate_temperature: float,
    amp: bool,
    amp_dtype: str,
) -> Dict[str, Any]:
    model.eval()
    data_full = kg.valid if split == "valid" else kg.test
    if not (0 < subset <= 1.0):
        raise ValueError("eval subset must be in (0,1]")
    if subset < 1.0:
        rng = np.random.default_rng(12345 if split == "valid" else 67890)
        size = max(1, int(len(data_full) * subset))
        chosen = rng.choice(len(data_full), size=size, replace=False)
        data = [data_full[int(i)] for i in chosen]
    else:
        data = data_full

    all_entities = model.ent.weight
    head_ranks: List[torch.Tensor] = []
    tail_ranks: List[torch.Tensor] = []
    eps_tie = 1e-7

    for offset in range(0, len(data), batch_size):
        chunk = data[offset : offset + batch_size]
        h_ids_cpu = torch.tensor([x[0] for x in chunk], dtype=torch.long)
        r_ids = torch.tensor([x[1] for x in chunk], device=device, dtype=torch.long)
        t_ids_cpu = torch.tensor([x[2] for x in chunk], dtype=torch.long)
        h = model.ent(h_ids_cpu.to(device))
        t = model.ent(t_ids_cpu.to(device))

        with autocast_context(device, amp, amp_dtype):
            true_scores = model.score_positive(h, r_ids, t, gate_temperature).float().unsqueeze(1)

        ranks_tail = torch.ones(len(chunk), device=device, dtype=torch.float32)
        ranks_head = torch.ones(len(chunk), device=device, dtype=torch.float32)
        tail_keys = [(int(hh), int(rr)) for hh, rr, _ in chunk]
        head_keys = [(int(rr), int(tt)) for _, rr, tt in chunk]

        for start in range(0, kg.num_entities, entity_block):
            end = min(start + entity_block, kg.num_entities)
            candidates = all_entities[start:end]
            with autocast_context(device, amp, amp_dtype):
                tail_scores = model.score_tail_candidates(h, r_ids, candidates, gate_temperature).float()
                head_scores = model.score_head_candidates(candidates, r_ids, t, gate_temperature).float()

            _filter_score_block(tail_scores, kg.tails_of_hr, tail_keys, start, end)
            _filter_score_block(head_scores, kg.heads_of_rt, head_keys, start, end)

            tail_in_block = (t_ids_cpu >= start) & (t_ids_cpu < end)
            if tail_in_block.any():
                rows = torch.nonzero(tail_in_block, as_tuple=False).squeeze(1).to(device)
                cols = (t_ids_cpu[tail_in_block] - start).to(device)
                tail_scores[rows, cols] = true_scores[rows, 0]
            head_in_block = (h_ids_cpu >= start) & (h_ids_cpu < end)
            if head_in_block.any():
                rows = torch.nonzero(head_in_block, as_tuple=False).squeeze(1).to(device)
                cols = (h_ids_cpu[head_in_block] - start).to(device)
                head_scores[rows, cols] = true_scores[rows, 0]

            for scores, ranks in ((tail_scores, ranks_tail), (head_scores, ranks_head)):
                better = (scores > true_scores).sum(dim=1).float()
                ties = torch.isclose(scores, true_scores, atol=eps_tie, rtol=0.0).sum(dim=1).float() - 1.0
                ranks.add_(better + 0.5 * ties.clamp_min(0.0))

        tail_ranks.append(ranks_tail.cpu())
        head_ranks.append(ranks_head.cpu())

    tail = torch.cat(tail_ranks)
    head = torch.cat(head_ranks)
    combined = torch.cat((tail, head))
    return {
        "schema": METRICS_SCHEMA,
        "split": split,
        "combined": ranks_to_metrics(combined),
        "tail": ranks_to_metrics(tail),
        "head": ranks_to_metrics(head),
        "eval_subset": float(subset),
        "entity_block": int(entity_block),
    }


# =============================================================================
# Training and checkpointing
# =============================================================================


def make_scheduler(optimizer: torch.optim.Optimizer, total_steps: int, warmup_steps: int):
    def factor(step: int) -> float:
        if warmup_steps > 0 and step < warmup_steps:
            return max(1e-8, float(step + 1) / float(warmup_steps))
        progress = float(step - warmup_steps) / float(max(1, total_steps - warmup_steps))
        return 0.5 * (1.0 + math.cos(math.pi * min(max(progress, 0.0), 1.0)))

    return torch.optim.lr_scheduler.LambdaLR(optimizer, lr_lambda=factor)


def save_checkpoint(
    path: str | Path,
    model: SeionV25,
    optimizer: torch.optim.Optimizer,
    scheduler: Any,
    scaler: Optional[torch.amp.GradScaler],
    epoch: int,
    global_step: int,
    best_mrr: float,
    kg: KnowledgeGraph,
    args: argparse.Namespace,
    provenance: Mapping[str, Any],
) -> None:
    path = Path(path)
    ensure_dir(path.parent)
    tmp = path.with_suffix(path.suffix + ".tmp")
    torch.save(
        {
            "version": VERSION,
            "run_schema": RUN_SCHEMA,
            "state_dict": model.state_dict(),
            "optimizer": optimizer.state_dict(),
            "scheduler": scheduler.state_dict() if scheduler is not None else None,
            "scaler": scaler.state_dict() if scaler is not None else None,
            "epoch": int(epoch),
            "global_step": int(global_step),
            "best_mrr": float(best_mrr),
            "ent2id": kg.ent2id,
            "rel2id": kg.rel2id,
            "args": vars(args),
            "rng_state": get_rng_state(),
            "provenance": dict(provenance),
        },
        tmp,
    )
    os.replace(tmp, path)


def load_checkpoint(
    path: str | Path,
    model: SeionV25,
    optimizer: Optional[torch.optim.Optimizer] = None,
    scheduler: Any = None,
    scaler: Optional[torch.amp.GradScaler] = None,
    restore_rng: bool = False,
) -> Dict[str, Any]:
    ckpt = torch.load(path, map_location="cpu", weights_only=False)
    model.load_state_dict(ckpt["state_dict"], strict=True)
    if optimizer is not None and ckpt.get("optimizer") is not None:
        optimizer.load_state_dict(ckpt["optimizer"])
    if scheduler is not None and ckpt.get("scheduler") is not None:
        scheduler.load_state_dict(ckpt["scheduler"])
    if scaler is not None and ckpt.get("scaler") is not None:
        scaler.load_state_dict(ckpt["scaler"])
    if restore_rng:
        restore_rng_state(ckpt.get("rng_state"))
    return ckpt


def build_run_contract(args: argparse.Namespace) -> Dict[str, Any]:
    out = ensure_dir(args.out_dir)
    source = Path(__file__).resolve()
    source_snapshot = out / "source_snapshot_seion_train_v25.py"
    shutil.copy2(source, source_snapshot)
    source_info = file_manifest(source_snapshot)
    datasets = {
        "train": file_manifest(args.train),
        "valid": file_manifest(args.valid),
        "test": file_manifest(args.test),
    }
    kernel = file_manifest(args.f_path) if args.f_path else None
    git = git_manifest(source.parent)
    environment = environment_manifest()
    hardware = hardware_manifest()

    save_json(vars(args), out / "config.json")
    atomic_write_text(out / "command.txt", " ".join(sys.argv) + "\n")
    save_json(environment, out / "environment.json")
    save_json(hardware, out / "hardware.json")
    save_json(datasets, out / "dataset_manifest.json")
    save_json(kernel, out / "kernel_manifest.json")
    save_json(git, out / "git_manifest.json")
    save_json(source_info, out / "source_manifest.json")

    manifest = {
        "schema": RUN_SCHEMA,
        "version": VERSION,
        "created_utc": utc_now(),
        "status": "RUNNING",
        "command": " ".join(sys.argv),
        "source": source_info,
        "datasets": datasets,
        "kernel": kernel,
        "git": git,
        "environment_file": "environment.json",
        "hardware_file": "hardware.json",
        "scientific_warnings": [
            "A numerical regularizer is not a theorem.",
            "A fixed structural kernel is not assumed causally superior.",
            "Mixed precision can alter exact reproducibility.",
        ],
    }
    save_json(manifest, out / "run_manifest.json")
    return manifest


def apply_blackwell_defaults(args: argparse.Namespace) -> argparse.Namespace:
    if not args.blackwell_tuned:
        return args
    if args.num_workers == 0:
        args.num_workers = 4
    if args.eval_batch < 512:
        args.eval_batch = 512
    if args.entity_block_eval < 2048:
        args.entity_block_eval = 2048
    if args.batch_size < 1024:
        args.batch_size = 2048
    if args.neg_k < 128:
        args.neg_k = 256
    args.amp = True
    if args.amp_dtype == "fp16":
        # Blackwell handles bf16 well and it avoids fp16 scaler failure modes.
        args.amp_dtype = "bf16"
    return args


def train(args: argparse.Namespace) -> Dict[str, Any]:
    args = apply_blackwell_defaults(args)
    set_seed(args.seed, args.deterministic)
    device = torch.device("cpu" if args.cpu or not torch.cuda.is_available() else "cuda")
    if device.type == "cuda" and not args.deterministic:
        torch.backends.cudnn.benchmark = True
        torch.backends.cuda.matmul.allow_tf32 = bool(args.allow_tf32)
        torch.backends.cudnn.allow_tf32 = bool(args.allow_tf32)
        try:
            torch.set_float32_matmul_precision("high")
        except Exception:
            pass
        torch.cuda.reset_peak_memory_stats()

    provenance = build_run_contract(args)
    kg = load_knowledge_graph(args)
    gate_init = parse_gate_init(args.gate_init)
    model = SeionV25(
        num_entities=kg.num_entities,
        num_relations=kg.num_relations_train,
        dimension=args.D,
        architecture=args.architecture,
        f_path=args.f_path,
        cp_rank=args.cp_rank,
        cp_norm=args.cp_norm,
        cp_residual_init=args.cp_residual_init,
        gate_per_relation=args.gate_per_relation,
        gate_init=gate_init,
        context_mix_init=args.context_mix_init,
        relation_gain=args.relation_gain,
    ).to(device)
    if args.proj_rank > 0:
        model.build_kernel_pca_projector(args.proj_rank)

    dataset = TripleDataset(kg.train)
    loader = DataLoader(
        dataset,
        batch_size=args.batch_size,
        shuffle=True,
        num_workers=args.num_workers,
        pin_memory=device.type == "cuda",
        persistent_workers=args.num_workers > 0,
        drop_last=False,
        prefetch_factor=args.prefetch_factor if args.num_workers > 0 else None,
    )

    param_groups = [
        {"params": [model.ent.weight], "lr": args.lr * args.entity_lr_mult},
        {"params": [p for name, p in model.named_parameters() if name != "ent.weight"], "lr": args.lr},
    ]
    optimizer = torch.optim.AdamW(param_groups, weight_decay=args.weight_decay)
    total_steps = max(1, args.epochs * len(loader))
    warmup_steps = int(total_steps * args.warmup_fraction)
    scheduler = make_scheduler(optimizer, total_steps, warmup_steps)
    scaler: Optional[torch.amp.GradScaler]
    if device.type == "cuda" and args.amp and args.amp_dtype == "fp16":
        scaler = torch.amp.GradScaler("cuda", enabled=True)
    else:
        scaler = None

    start_epoch = 0
    global_step = 0
    best_mrr = -math.inf
    if args.resume:
        ckpt = load_checkpoint(args.resume, model, optimizer, scheduler, scaler, restore_rng=args.restore_rng)
        start_epoch = int(ckpt.get("epoch", -1)) + 1
        global_step = int(ckpt.get("global_step", 0))
        best_mrr = float(ckpt.get("best_mrr", -math.inf))

    rng = np.random.default_rng(args.seed + 100003)
    metrics_path = Path(args.out_dir) / "metrics.jsonl"
    start_time = time.time()
    no_improve = 0
    regularizer_audit: Dict[str, Any] = {}

    for epoch in range(start_epoch, args.epochs):
        model.train()
        epoch_start = time.time()
        sums: Dict[str, float] = {}
        examples = 0

        for batch_index, batch in enumerate(loader):
            h_ids, r_ids, t_ids = (x.to(device=device, non_blocking=True) for x in batch)
            head_neg_ids, tail_neg_ids = sample_negatives(h_ids, r_ids, t_ids, kg, args, rng, device)
            h = model.ent(h_ids)
            t = model.ent(t_ids)
            h_neg = model.ent(head_neg_ids)
            t_neg = model.ent(tail_neg_ids)

            optimizer.zero_grad(set_to_none=True)
            gate_temperature = max(args.gate_temperature_min, args.gate_temperature * (args.gate_temperature_decay ** epoch))
            with autocast_context(device, args.amp, args.amp_dtype):
                positive = model.score_positive(h, r_ids, t, gate_temperature)
                tail_scores = model.score_tail_candidates(h, r_ids, t_neg, gate_temperature)
                head_scores = model.score_head_candidates(h_neg, r_ids, t, gate_temperature)
                tail_loss_ex = negative_sampling_loss(
                    positive, tail_scores, args.loss_mode, args.adversarial_temperature, args.margin
                )
                head_loss_ex = negative_sampling_loss(
                    positive, head_scores, args.loss_mode, args.adversarial_temperature, args.margin
                )
                kge_loss = 0.5 * (tail_loss_ex.mean() + head_loss_ex.mean())
                total_loss = kge_loss

                r_vec = model.rel(r_ids)
                c_vec = model.context(r_ids, r_vec)
                pool = torch.cat((h, t, r_vec, c_vec), dim=0)
                relation_pool = r_ids.repeat(4)

                fi_loss = filippov_embedding_loss(
                    model, pool, relation_pool, args.fi_samples, args.fi_detach_inner
                )
                assoc_loss = associator_embedding_loss(
                    model, pool, relation_pool, args.assoc_samples, args.assoc_detach_inner
                )
                closure_loss = closure_embedding_loss(
                    model, pool, relation_pool, args.closure_samples
                )
                distill_loss = cp_teacher_distillation_loss(model, h, r_vec, c_vec)
                gate_loss = gate_entropy_loss(model, r_ids, gate_temperature)

                weights = {
                    "fi": effective_weight(args.fi_weight, epoch, args.fi_warmup_epochs),
                    "assoc": effective_weight(args.assoc_weight, epoch, args.assoc_warmup_epochs),
                    "closure": effective_weight(args.closure_weight, epoch, args.closure_warmup_epochs),
                    "distill": effective_weight(args.distill_weight, epoch, args.distill_warmup_epochs),
                    "gate_entropy": effective_weight(args.gate_entropy_weight, epoch, args.gate_warmup_epochs),
                }
                total_loss = (
                    total_loss
                    + weights["fi"] * fi_loss
                    + weights["assoc"] * assoc_loss
                    + weights["closure"] * closure_loss
                    + weights["distill"] * distill_loss
                    + weights["gate_entropy"] * gate_loss
                )

            if args.audit_regularizer_grads and not regularizer_audit and args.fi_weight > 0:
                regularizer_audit["fi"] = regularizer_gradient_audit(fi_loss, model, retain_graph=True)
                if regularizer_audit["fi"]["total"] <= args.min_regularizer_grad:
                    raise RuntimeError(
                        f"FI gradient audit failed: {regularizer_audit['fi']}. "
                        "The regularizer is disconnected from trainable parameters."
                    )

            if scaler is not None:
                scaler.scale(total_loss).backward()
                scaler.unscale_(optimizer)
                grad_norm = torch.nn.utils.clip_grad_norm_(model.parameters(), args.grad_clip)
                scaler.step(optimizer)
                scaler.update()
            else:
                total_loss.backward()
                grad_norm = torch.nn.utils.clip_grad_norm_(model.parameters(), args.grad_clip)
                optimizer.step()
            scheduler.step()
            model.renorm_embeddings(args.embedding_max_norm)
            global_step += 1

            batch_n = int(h_ids.numel())
            examples += batch_n
            values = {
                "loss": total_loss,
                "kge": kge_loss,
                "fi": fi_loss,
                "assoc": assoc_loss,
                "closure": closure_loss,
                "distill": distill_loss,
                "gate_entropy": gate_loss,
                "positive_score": positive.mean(),
                "tail_score": tail_scores.mean(),
                "head_score": head_scores.mean(),
                "grad_norm": grad_norm,
            }
            for name, value in values.items():
                sums[name] = sums.get(name, 0.0) + float(value.detach().float().item()) * batch_n

        train_metrics = {name: value / max(1, examples) for name, value in sums.items()}
        epoch_obj: Dict[str, Any] = {
            "schema": METRICS_SCHEMA,
            "type": "epoch",
            "epoch": epoch,
            "global_step": global_step,
            "train": train_metrics,
            "lr": [float(group["lr"]) for group in optimizer.param_groups],
            "wall_epoch_sec": time.time() - epoch_start,
            "wall_total_sec": time.time() - start_time,
            "gpu": gpu_memory_snapshot() if device.type == "cuda" else {},
            "gate_temperature": gate_temperature,
        }

        should_eval = (epoch + 1) % args.eval_every == 0 or epoch == args.epochs - 1
        if should_eval:
            valid = evaluate(
                model,
                kg,
                "valid",
                device,
                args.eval_batch,
                args.entity_block_eval,
                args.eval_subset,
                gate_temperature,
                args.eval_amp,
                args.amp_dtype,
            )
            epoch_obj["valid"] = valid
            current_mrr = valid["combined"]["MRR"]
            if current_mrr > best_mrr:
                best_mrr = current_mrr
                no_improve = 0
                save_checkpoint(
                    Path(args.out_dir) / "best.pt",
                    model,
                    optimizer,
                    scheduler,
                    scaler,
                    epoch,
                    global_step,
                    best_mrr,
                    kg,
                    args,
                    provenance,
                )
                epoch_obj["new_best"] = True
            else:
                no_improve += 1
                epoch_obj["new_best"] = False
        append_jsonl(epoch_obj, metrics_path)
        print(json.dumps(epoch_obj, ensure_ascii=False), flush=True)

        save_checkpoint(
            Path(args.out_dir) / "last.pt",
            model,
            optimizer,
            scheduler,
            scaler,
            epoch,
            global_step,
            best_mrr,
            kg,
            args,
            provenance,
        )
        if args.early_stop_patience > 0 and no_improve >= args.early_stop_patience:
            print(f"[EARLY-STOP] no improvement for {no_improve} evaluations", flush=True)
            break

    last_test = evaluate(
        model,
        kg,
        "test",
        device,
        args.eval_batch,
        args.entity_block_eval,
        1.0,
        args.gate_temperature_min,
        args.eval_amp,
        args.amp_dtype,
    )
    best_path = Path(args.out_dir) / "best.pt"
    best_test = None
    best_epoch = None
    if best_path.is_file():
        best_ckpt = load_checkpoint(best_path, model)
        best_epoch = int(best_ckpt.get("epoch", -1))
        best_test = evaluate(
            model,
            kg,
            "test",
            device,
            args.eval_batch,
            args.entity_block_eval,
            1.0,
            args.gate_temperature_min,
            args.eval_amp,
            args.amp_dtype,
        )

    result = {
        "schema": METRICS_SCHEMA,
        "version": VERSION,
        "status": "COMPLETED",
        "architecture": args.architecture,
        "best_valid_mrr": float(best_mrr),
        "best_epoch": best_epoch,
        "test_last": last_test,
        "test_best": best_test,
        "regularizer_gradient_audit": regularizer_audit,
        "wall_time_sec": time.time() - start_time,
        "gpu": gpu_memory_snapshot() if device.type == "cuda" else {},
        "provenance": {
            "source_sha256": provenance["source"]["sha256"],
            "git_commit": provenance["git"].get("commit"),
            "git_dirty": provenance["git"].get("dirty"),
            "dataset_sha256": {k: v["sha256"] for k, v in provenance["datasets"].items()},
            "kernel_sha256": provenance["kernel"]["sha256"] if provenance.get("kernel") else None,
        },
    }
    save_json(result, Path(args.out_dir) / "final_metrics.json")
    manifest = json.loads((Path(args.out_dir) / "run_manifest.json").read_text(encoding="utf-8"))
    manifest["status"] = "COMPLETED"
    manifest["completed_utc"] = utc_now()
    manifest["final_metrics"] = "final_metrics.json"
    save_json(manifest, Path(args.out_dir) / "run_manifest.json")
    print(json.dumps(result, indent=2, ensure_ascii=False), flush=True)
    return result


# =============================================================================
# Self-tests
# =============================================================================


def _tiny_kg() -> KnowledgeGraph:
    train = [(0, 0, 1), (1, 0, 2), (2, 1, 3), (3, 1, 4), (4, 0, 5), (5, 1, 0)]
    valid = [(0, 0, 1), (2, 1, 3)]
    test = [(1, 0, 2), (3, 1, 4)]
    tails, heads = build_filters(train, valid, test)
    return KnowledgeGraph(
        num_entities=6,
        num_relations_original=2,
        num_relations_train=2,
        train=np.asarray(train, dtype=np.int64),
        valid=valid,
        test=test,
        ent2id={str(i): i for i in range(6)},
        rel2id={str(i): i for i in range(2)},
        tails_of_hr=tails,
        heads_of_rt=heads,
        bernoulli_tail_prob=build_bernoulli_probs(train, 2),
    )


def run_self_tests() -> Dict[str, Any]:
    set_seed(7, True)
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    with tempfile.TemporaryDirectory() as tmp:
        d = 8
        f = np.random.default_rng(7).standard_normal((d, d, d)).astype(np.float32) / math.sqrt(d)
        f_path = Path(tmp) / "f.npy"
        np.save(f_path, f)
        model = SeionV25(
            num_entities=6,
            num_relations=2,
            dimension=d,
            architecture="hybrid",
            f_path=str(f_path),
            cp_rank=6,
            cp_norm="layernorm",
            cp_residual_init=0.1,
            gate_per_relation=True,
            gate_init=(0.3, 0.3, 0.4),
            context_mix_init=0.5,
            relation_gain=True,
        ).to(device)
        kg = _tiny_kg()

        h_ids = torch.tensor([0, 2], device=device)
        r_ids = torch.tensor([0, 1], device=device)
        t_ids = torch.tensor([1, 3], device=device)
        h, t = model.ent(h_ids), model.ent(t_ids)
        positive = model.score_positive(h, r_ids, t)
        head_gold = model.score_head_candidates(h.unsqueeze(1), r_ids, t).squeeze(1)
        tail_gold = model.score_tail_candidates(h, r_ids, t.unsqueeze(1)).squeeze(1)
        gold_error = max(
            float((positive - head_gold).abs().max().item()),
            float((positive - tail_gold).abs().max().item()),
        )
        if gold_error > 1e-5:
            raise AssertionError(f"Positive/head/tail score paths disagree: {gold_error}")

        eval_small = evaluate(model, kg, "test", device, 2, 2, 1.0, 1.0, False, "bf16")
        eval_full = evaluate(model, kg, "test", device, 2, 100, 1.0, 1.0, False, "bf16")
        eval_error = abs(eval_small["combined"]["MRR"] - eval_full["combined"]["MRR"])
        if eval_error > 1e-10:
            raise AssertionError(f"Blocked and full evaluation disagree: {eval_error}")

        r_vec = model.rel(r_ids)
        c_vec = model.context(r_ids, r_vec)
        pool = torch.cat((h, t, r_vec, c_vec), dim=0)
        relation_pool = r_ids.repeat(4)
        fi = filippov_embedding_loss(model, pool, relation_pool, samples=4, detach_inner=False)
        audit = regularizer_gradient_audit(fi, model, retain_graph=False)
        if audit["total"] <= 0:
            raise AssertionError(f"FI has zero trainable gradient: {audit}")

        result = {
            "status": "PASS_V25_SELF_TESTS",
            "device": str(device),
            "positive_path_max_error": gold_error,
            "blocked_eval_mrr_error": eval_error,
            "fi_gradient_audit": audit,
            "eval": eval_small,
        }
        print(json.dumps(result, indent=2), flush=True)
        return result


# =============================================================================
# CLI
# =============================================================================


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    p.add_argument("--self_test", action="store_true", help="Run evaluator and gradient invariance tests, then exit")
    p.add_argument("--train", type=str, default="")
    p.add_argument("--valid", type=str, default="")
    p.add_argument("--test", type=str, default="")
    p.add_argument("--out_dir", type=str, default="")
    p.add_argument("--D", type=int, default=248)
    p.add_argument("--f_path", type=str, default="")

    p.add_argument("--architecture", choices=["bilinear", "fixed", "cp", "hybrid"], default="hybrid")
    p.add_argument("--cp_rank", type=int, default=512)
    p.add_argument("--cp_norm", choices=["none", "layernorm", "rms"], default="layernorm")
    p.add_argument("--cp_residual_init", type=float, default=0.1)
    p.add_argument("--gate_per_relation", action="store_true")
    p.add_argument("--gate_init", type=str, default="fixed=0.15,cp=0.15,bilinear=0.70")
    p.add_argument("--gate_temperature", type=float, default=1.0)
    p.add_argument("--gate_temperature_decay", type=float, default=0.98)
    p.add_argument("--gate_temperature_min", type=float, default=0.5)
    p.add_argument("--context_mix_init", type=float, default=0.5)
    p.add_argument("--relation_gain", action="store_true")

    p.add_argument("--epochs", type=int, default=48)
    p.add_argument("--batch_size", type=int, default=2048)
    p.add_argument("--neg_k", type=int, default=256)
    p.add_argument("--neg_mode", choices=["baseline", "bernoulli", "filtered"], default="baseline")
    p.add_argument("--filtered_neg_max_tries", type=int, default=32)
    p.add_argument("--loss_mode", choices=["logistic", "margin"], default="logistic")
    p.add_argument("--adversarial_temperature", type=float, default=2.0)
    p.add_argument("--margin", type=float, default=1.0)
    p.add_argument("--lr", type=float, default=1e-3)
    p.add_argument("--entity_lr_mult", type=float, default=1.0)
    p.add_argument("--weight_decay", type=float, default=1e-5)
    p.add_argument("--warmup_fraction", type=float, default=0.05)
    p.add_argument("--grad_clip", type=float, default=1.0)
    p.add_argument("--embedding_max_norm", type=float, default=1.0)
    p.add_argument("--early_stop_patience", type=int, default=8)
    p.add_argument("--reciprocal_train", action="store_true")

    p.add_argument("--fi_weight", type=float, default=0.0)
    p.add_argument("--fi_samples", type=int, default=16)
    p.add_argument("--fi_warmup_epochs", type=int, default=5)
    p.add_argument("--fi_detach_inner", action="store_true")
    p.add_argument("--assoc_weight", type=float, default=0.0)
    p.add_argument("--assoc_samples", type=int, default=16)
    p.add_argument("--assoc_warmup_epochs", type=int, default=5)
    p.add_argument("--assoc_detach_inner", action="store_true")
    p.add_argument("--closure_weight", type=float, default=0.0)
    p.add_argument("--closure_samples", type=int, default=16)
    p.add_argument("--closure_warmup_epochs", type=int, default=5)
    p.add_argument("--proj_rank", type=int, default=0)
    p.add_argument("--distill_weight", type=float, default=0.0)
    p.add_argument("--distill_warmup_epochs", type=int, default=5)
    p.add_argument("--gate_entropy_weight", type=float, default=0.0)
    p.add_argument("--gate_warmup_epochs", type=int, default=3)
    p.add_argument("--audit_regularizer_grads", action="store_true")
    p.add_argument("--min_regularizer_grad", type=float, default=1e-12)

    p.add_argument("--eval_batch", type=int, default=512)
    p.add_argument("--entity_block_eval", type=int, default=2048)
    p.add_argument("--eval_subset", type=float, default=1.0)
    p.add_argument("--eval_every", type=int, default=1)
    p.add_argument("--eval_amp", action="store_true")

    p.add_argument("--cpu", action="store_true")
    p.add_argument("--amp", action="store_true")
    p.add_argument("--amp_dtype", choices=["fp16", "bf16"], default="bf16")
    p.add_argument("--allow_tf32", action="store_true")
    p.add_argument("--blackwell_tuned", action="store_true")
    p.add_argument("--num_workers", type=int, default=0)
    p.add_argument("--prefetch_factor", type=int, default=4)
    p.add_argument("--seed", type=int, default=42)
    p.add_argument("--deterministic", action="store_true")
    p.add_argument("--resume", type=str, default="")
    p.add_argument("--restore_rng", action="store_true")
    return p


def validate_args(args: argparse.Namespace) -> None:
    if args.self_test:
        return
    missing = [name for name in ("train", "valid", "test", "out_dir") if not getattr(args, name)]
    if missing:
        raise ValueError(f"Missing required arguments: {missing}")
    for name in ("train", "valid", "test"):
        if not Path(getattr(args, name)).is_file():
            raise FileNotFoundError(getattr(args, name))
    if args.architecture in {"fixed", "hybrid"} and not Path(args.f_path).is_file():
        raise FileNotFoundError(f"Fixed/hybrid architecture requires --f_path: {args.f_path}")
    if args.closure_weight > 0 and args.proj_rank <= 0:
        raise ValueError("--closure_weight requires --proj_rank > 0")
    if args.distill_weight > 0 and args.architecture != "hybrid":
        raise ValueError("--distill_weight requires --architecture hybrid")


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()
    validate_args(args)
    if args.self_test:
        run_self_tests()
        return
    train(args)


if __name__ == "__main__":
    main()
