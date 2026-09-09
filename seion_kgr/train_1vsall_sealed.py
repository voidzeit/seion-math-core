"""Exact 1-vs-all sealed training (T0 baseline: TuckER).

With FB15K-237's 14,541 entities a full softmax over the entity set costs a
[B, N] score matrix -- about 30 MB at batch 512 -- so there is no reason to
sample negatives at all. Removing sampling removes, structurally rather than by
vigilance, the entire family of decisions that produced B-0014: no ``neg_k``, no
hard-negative miner, no sampler-induced false negatives, and no filter table
anywhere near the loss.

Targets are multi-hot over TRAIN positives only, obtained from a
:class:`~seion_kgr.truth_index.TrainTruthIndex`, which cannot be constructed
from an evaluation filter. Evaluation keeps the standard filtered protocol via a
separate :class:`~seion_kgr.truth_index.EvaluationFilterIndex`.

Sealed contract: TRAIN and VALID paths only, TEST-like paths rejected at parse
time, runtime sentinel installed, no TEST read/opened/hashed.
"""

from __future__ import annotations

import argparse
import json
import platform
import sys
import time
from pathlib import Path
from typing import Any

import numpy as np
import torch
import torch.nn as nn
import torch.nn.functional as F

from .data import KnowledgeGraph
from .evaluate import evaluate
from .reproducibility import set_seed
from .sratm_certified_compression import load_train_valid_only, sha256
from .train_sratm_sealed import _forbidden_test_path, sealed_access_sentinel
from .truth_index import TrainTruthIndex, require_train_truth


class TuckER1vsAll(nn.Module):
    """Self-contained TuckER with the dropout schedule the published setup uses.

    Kept local to this module rather than reusing ``scorers.TuckERExpert`` so the
    sealed experiment cannot be perturbed by, or perturb, the shared expert.
    """

    def __init__(self, num_entities: int, num_relations: int, dim_e: int = 200,
                 dim_r: int = 200, drop_in: float = 0.3, drop_h1: float = 0.4,
                 drop_h2: float = 0.5) -> None:
        super().__init__()
        self.entity = nn.Embedding(num_entities, dim_e)
        self.relation = nn.Embedding(num_relations, dim_r)
        nn.init.xavier_normal_(self.entity.weight)
        nn.init.xavier_normal_(self.relation.weight)
        self.core = nn.Parameter(torch.empty(dim_r, dim_e, dim_e).uniform_(-1e-2, 1e-2))
        self.drop_in, self.drop_h1, self.drop_h2 = nn.Dropout(drop_in), nn.Dropout(drop_h1), nn.Dropout(drop_h2)
        self.bn_in, self.bn_h = nn.BatchNorm1d(dim_e), nn.BatchNorm1d(dim_e)
        self.bias = nn.Parameter(torch.zeros(num_entities))

    def forward(self, h_ids: torch.Tensor, r_ids: torch.Tensor) -> torch.Tensor:
        """Return ``[B, num_entities]`` logits over every candidate tail."""
        h = self.drop_in(self.bn_in(self.entity(h_ids)))
        w = torch.einsum("bd,dij->bij", self.relation(r_ids), self.core)
        hw = self.drop_h1(torch.einsum("bi,bij->bj", h, w))
        hw = self.drop_h2(self.bn_h(hw))
        return hw @ self.entity.weight.transpose(0, 1) + self.bias

    # --- adapters so the shared filtered evaluator can score this model ---
    # The evaluator passes positional `adjacency, seed` and keyword
    # `training=`, `context=`; this model uses none of them, so they are
    # accepted and ignored rather than constraining the shared signature.
    def score_positive(self, h_ids, r_ids, t_ids, *args, **kwargs):
        return self.forward(h_ids, r_ids).gather(1, t_ids.unsqueeze(1)).squeeze(1)

    def score_tail_candidates(self, h_ids, r_ids, candidate_ids, *args, **kwargs):
        logits = self.forward(h_ids, r_ids)
        if candidate_ids.ndim == 1:
            return logits.index_select(1, candidate_ids)
        return logits.gather(1, candidate_ids)


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--train", type=Path, required=True)
    p.add_argument("--valid", type=Path, required=True)
    p.add_argument("--out-dir", type=Path, required=True)
    p.add_argument("--dim-e", type=int, default=200)
    p.add_argument("--dim-r", type=int, default=200)
    p.add_argument("--batch-size", type=int, default=256)
    p.add_argument("--lr", type=float, default=5e-4)
    p.add_argument("--label-smoothing", type=float, default=0.1)
    p.add_argument("--drop-in", type=float, default=0.3)
    p.add_argument("--drop-h1", type=float, default=0.4)
    p.add_argument("--drop-h2", type=float, default=0.5)
    p.add_argument("--max-steps", type=int, default=12000)
    p.add_argument("--max-seconds", type=float, default=0.0)
    p.add_argument("--warmup-steps", type=int, default=200)
    p.add_argument("--min-lr-ratio", type=float, default=0.05)
    p.add_argument("--eval-every-seconds", type=float, default=240.0)
    p.add_argument("--eval-queries", type=int, default=2048)
    p.add_argument("--entity-block", type=int, default=4096)
    p.add_argument("--seed", type=int, default=42)
    p.add_argument("--cpu", action="store_true")
    return p


def _lr_scale(args: argparse.Namespace, step: int) -> float:
    if args.warmup_steps > 0 and step <= args.warmup_steps:
        return step / float(args.warmup_steps)
    span = max(1, args.max_steps - args.warmup_steps)
    progress = min(1.0, max(0.0, (step - args.warmup_steps) / span))
    return args.min_lr_ratio + (1.0 - args.min_lr_ratio) * 0.5 * (1.0 + np.cos(np.pi * progress))


def run(args: argparse.Namespace) -> dict[str, Any]:
    if _forbidden_test_path(args.train) or _forbidden_test_path(args.valid):
        raise ValueError("sealed runner accepts TRAIN and VALID only")
    if args.out_dir.exists() and any(args.out_dir.iterdir()):
        raise FileExistsError(f"output directory is not empty: {args.out_dir}")
    args.out_dir.mkdir(parents=True, exist_ok=True)

    access_log: list[dict[str, str]] = []
    set_seed(args.seed)
    rng = np.random.default_rng(args.seed)
    device = torch.device("cpu" if args.cpu or not torch.cuda.is_available() else "cuda:0")
    history: list[dict[str, Any]] = []
    best_mrr, best_step, step = -float("inf"), None, 0
    started = time.perf_counter()

    with sealed_access_sentinel(access_log):
        kg: KnowledgeGraph = load_train_valid_only(
            args.train, args.valid, expected_num_entities=14541, expected_num_relations_total=474,
        )
        if kg.test:
            raise RuntimeError("sealed loader returned non-empty test data")

        # The ONLY truth table the loss may see. Built from TRAIN rows alone;
        # by construction it cannot be derived from an evaluation filter.
        train_rows = [(int(h), int(r), int(t)) for h, r, t in kg.train]
        truth = require_train_truth(TrainTruthIndex.from_train(train_rows))

        model = TuckER1vsAll(
            kg.num_entities, kg.num_relations_total, args.dim_e, args.dim_r,
            args.drop_in, args.drop_h1, args.drop_h2,
        ).to(device)
        optimizer = torch.optim.Adam(model.parameters(), lr=args.lr)
        base_lrs = [g["lr"] for g in optimizer.param_groups]

        # Deduplicate to (h, r) queries: 1-vs-all trains one query at a time,
        # not one triple at a time, so repeated heads are not over-weighted.
        queries = sorted({(int(h), int(r)) for h, r, _ in train_rows})
        query_arr = np.asarray(queries, dtype=np.int64)
        targets = [truth.train_tails(h, r) for h, r in queries]
        order = np.arange(len(queries))
        # Flatten the multi-hot targets into a CSR pair once, on the host, so the
        # per-step label matrix is a single vectorized scatter instead of one
        # Python iteration (and one host->device copy) per row in the batch.
        tgt_offsets = np.zeros(len(targets) + 1, dtype=np.int64)
        np.cumsum([len(t) for t in targets], out=tgt_offsets[1:])
        tgt_values = torch.from_numpy(
            np.concatenate(targets) if targets else np.zeros(0, dtype=np.int64)
        ).to(device)
        tgt_offsets_t = torch.from_numpy(tgt_offsets).to(device)
        last_eval, stopped = time.perf_counter(), None

        model.train()
        while step < args.max_steps and stopped is None:
            rng.shuffle(order)
            for off in range(0, len(order), args.batch_size):
                if step >= args.max_steps:
                    stopped = "MAX_STEPS_REACHED"; break
                if args.max_seconds > 0 and time.perf_counter() - started >= args.max_seconds:
                    stopped = "WALL_CLOCK_BUDGET_EXHAUSTED"; break
                idx = order[off:off + args.batch_size]
                if len(idx) < 2:      # BatchNorm needs >1 row
                    continue
                hr = torch.from_numpy(query_arr[idx]).to(device)
                sel = torch.from_numpy(idx).to(device)
                starts, lengths = tgt_offsets_t[sel], tgt_offsets_t[sel + 1] - tgt_offsets_t[sel]
                width = int(lengths.max().item())
                ar = torch.arange(width, device=device)
                flat = (starts.unsqueeze(1) + ar).clamp(max=max(tgt_values.numel() - 1, 0))
                mask = ar < lengths.unsqueeze(1)
                rows = torch.arange(len(idx), device=device).unsqueeze(1).expand_as(flat)
                label = torch.zeros(len(idx), kg.num_entities, device=device)
                label.index_put_((rows[mask], tgt_values[flat][mask]),
                                 torch.ones(int(mask.sum()), device=device))
                if args.label_smoothing > 0:
                    label = label * (1.0 - args.label_smoothing) + args.label_smoothing / kg.num_entities

                for g, base in zip(optimizer.param_groups, base_lrs):
                    g["lr"] = base * _lr_scale(args, step + 1)
                optimizer.zero_grad(set_to_none=True)
                loss = F.binary_cross_entropy_with_logits(model(hr[:, 0], hr[:, 1]), label)
                if not torch.isfinite(loss):
                    raise FloatingPointError(f"non-finite loss at step {step}")
                loss.backward()
                optimizer.step()
                step += 1

                now = time.perf_counter()
                if args.eval_every_seconds > 0 and now - last_eval >= args.eval_every_seconds:
                    last_eval = now
                    model.eval()
                    q = kg.valid[:min(args.eval_queries, len(kg.valid))]
                    m = evaluate(model, kg, "valid", device, 64, args.entity_block, queries=q)
                    rec = {"step": step, "loss": float(loss.item()), "valid": m["combined"],
                           "elapsed_seconds": now - started, "lr": optimizer.param_groups[0]["lr"]}
                    history.append(rec)
                    if float(m["combined"]["MRR"]) > best_mrr:
                        best_mrr, best_step = float(m["combined"]["MRR"]), step
                        torch.save({"model": model.state_dict(), "step": step,
                                    "config": vars(args), "test_split_opened": False},
                                   args.out_dir / "checkpoint_best.pt")
                    model.train()

    result = {
        "status": "COMPLETE",
        "campaign": "SEALED_1VSALL_T0_TUCKER",
        "stop_reason": stopped or "QUERIES_EXHAUSTED",
        "device": str(device), "steps": step,
        "elapsed_seconds": time.perf_counter() - started,
        "best_valid_mrr": None if best_step is None else best_mrr,
        "best_valid_step": best_step,
        "history": history,
        "config": {k: (str(v) if isinstance(v, Path) else v) for k, v in vars(args).items()},
        "train_queries": len(queries),
        "negative_sampling": "NONE_EXACT_1_VS_ALL",
        "loss_truth_source": truth.provenance,
        "dataset": {"train_sha256": sha256(args.train), "valid_sha256": sha256(args.valid),
                    "test": "NOT_READ_NOT_HASHED_NOT_OPENED",
                    "num_entities": int(kg.num_entities)},
        "no_leakage": {"test_split_opened": False, "test_split_read": False,
                       "test_split_hashed": False, "runtime_forbidden_accesses": 0,
                       "loss_sees_only": truth.provenance,
                       "b0014_structurally_impossible": "no negative sampler and no filter table in the loss"},
        "environment": {"python": sys.version, "torch": torch.__version__,
                        "platform": platform.platform()},
        "scientific_status": "EMPIRICAL_SEALED_TRAINING_NO_TEST_NO_SOTA_CLAIM",
    }
    (args.out_dir / "training_result.json").write_text(
        json.dumps(result, indent=2, default=str) + "\n", encoding="utf-8")
    return result


def main() -> None:
    print(json.dumps(run(build_parser().parse_args()), indent=2, default=str))


if __name__ == "__main__":
    main()
