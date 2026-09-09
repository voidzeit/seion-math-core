"""Bounded training canary for the confirmatory TTN campaign.

This is a reversible stability gate, not a scientific training result. It
trains the full D128 scorer for a bounded number of steps, saves resumable
checkpoints, and records memory/finite-loss diagnostics before any long run.
"""

from __future__ import annotations

import argparse
import json
import random
import time
from pathlib import Path

import numpy as np
import torch
import torch.nn.functional as F

from .data import KnowledgeGraph, load_knowledge_graph, sample_negatives, train_only_filter_view
from .ttn_branching import BranchingTTNK3


def parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--train", default="data/FB15K-237/train.txt")
    p.add_argument("--valid", default="data/FB15K-237/valid.txt")
    p.add_argument("--test", default="data/FB15K-237/test.txt")
    p.add_argument("--out-dir", type=Path, required=True)
    p.add_argument("--dim", type=int, default=128)
    p.add_argument("--branch-dim", type=int, default=128)
    p.add_argument("--batch-size", type=int, default=512)
    p.add_argument("--neg-k", type=int, default=8)
    p.add_argument("--max-steps", type=int, default=64)
    p.add_argument("--checkpoint-every", type=int, default=16)
    p.add_argument("--max-vram-gb", type=float, default=4.0)
    p.add_argument("--seed", type=int, default=42)
    p.add_argument("--negative-filter", choices=("train_valid_test", "train_only"),
                   default="train_valid_test",
                   help="which known-positive tables mask TRAINING negatives (B-0014). "
                        "'train_valid_test' reproduces earlier runs but leaks held-out "
                        "membership into training; 'train_only' is the non-leaking choice. "
                        "Evaluation always keeps the full filters.")
    p.add_argument("--lr", type=float, default=1e-3)
    p.add_argument("--weight-decay", type=float, default=1e-6)
    p.add_argument("--loss-temperature", type=float, default=1000.0)
    p.add_argument("--embedding-max-norm", type=float, default=1.0)
    p.add_argument("--core-max-fro", type=float, default=1.0)
    p.add_argument("--root-max-fro", type=float, default=1.0)
    return p


def _set_seed(seed: int) -> None:
    random.seed(seed)
    np.random.seed(seed)
    torch.manual_seed(seed)
    if torch.cuda.is_available():
        torch.cuda.manual_seed_all(seed)


def _device(args: argparse.Namespace) -> torch.device:
    if not torch.cuda.is_available():
        return torch.device("cpu")
    device = torch.device("cuda:0")
    total = torch.cuda.get_device_properties(device).total_memory
    fraction = min(0.90, args.max_vram_gb * 1024**3 / total)
    if fraction <= 0:
        raise ValueError("max-vram-gb must be positive")
    torch.cuda.set_per_process_memory_fraction(fraction, device=device)
    return device


def _checkpoint(
    path: Path,
    model: BranchingTTNK3,
    optimizer: torch.optim.Optimizer,
    *,
    seed: int,
    step: int,
    history: list[dict[str, float | int]],
) -> None:
    state = {
        "model_state": {key: value.detach().cpu() for key, value in model.state_dict().items()},
        "optimizer_state": optimizer.state_dict(),
        "seed": seed,
        "step": step,
        "history": history,
        "rng_python": random.getstate(),
        "rng_numpy": np.random.get_state(),
        "rng_torch_cpu": torch.get_rng_state(),
        "rng_torch_cuda": torch.cuda.get_rng_state_all() if torch.cuda.is_available() else None,
    }
    torch.save(state, path)


def main() -> int:
    args = parser().parse_args()
    if args.dim <= 0 or args.branch_dim <= 0 or args.batch_size <= 0 or args.neg_k <= 0:
        raise ValueError("dimensions, batch-size, and neg-k must be positive")
    if args.max_steps <= 0 or args.checkpoint_every <= 0:
        raise ValueError("max-steps and checkpoint-every must be positive")

    args.out_dir.mkdir(parents=True, exist_ok=True)
    device = _device(args)
    _set_seed(args.seed)
    kg: KnowledgeGraph = load_knowledge_graph(args.train, args.valid, args.test)
    # B-0014: full filters are right for evaluation, leaking for training negatives.
    negative_kg = train_only_filter_view(kg) if args.negative_filter == "train_only" else kg
    model = BranchingTTNK3(kg.num_entities, kg.num_relations_total, args.dim, args.branch_dim).to(device)
    optimizer = torch.optim.AdamW(model.parameters(), lr=args.lr, weight_decay=args.weight_decay)
    train_tensor = torch.from_numpy(kg.train.astype(np.int64, copy=False))
    rng = np.random.default_rng(args.seed)
    history: list[dict[str, float | int]] = []
    started = time.perf_counter()
    step = 0
    order = rng.permutation(len(train_tensor))
    offset = 0
    if device.type == "cuda":
        torch.cuda.reset_peak_memory_stats(device)

    model.train()
    while step < args.max_steps:
        if offset >= len(order):
            order = rng.permutation(len(train_tensor))
            offset = 0
        indices = order[offset : offset + args.batch_size]
        offset += len(indices)
        batch = train_tensor[indices].to(device=device, non_blocking=True)
        h_ids, r_ids, t_ids = batch.T
        negatives = sample_negatives(h_ids, r_ids, t_ids, negative_kg, args.neg_k, rng, device)
        optimizer.zero_grad(set_to_none=True)
        positive = model.score_positive(h_ids, r_ids, t_ids)
        negative = model.score_tail_candidates(h_ids, r_ids, negatives)
        loss = F.softplus(args.loss_temperature * (negative - positive.unsqueeze(1))).mean()
        if not torch.isfinite(loss):
            raise RuntimeError(f"non-finite loss at step {step + 1}")
        loss.backward()
        torch.nn.utils.clip_grad_norm_(model.parameters(), 1.0)
        optimizer.step()
        model.project_parameter_norms(
            embedding_max_norm=args.embedding_max_norm,
            core_max_fro=args.core_max_fro,
            root_max_fro=args.root_max_fro,
        )
        step += 1
        record = {
            "step": step,
            "loss": float(loss.detach().cpu().item()),
            "seconds": time.perf_counter() - started,
        }
        history.append(record)
        with (args.out_dir / "training_metrics.jsonl").open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(record) + "\n")
        if step % args.checkpoint_every == 0 or step == args.max_steps:
            _checkpoint(args.out_dir / "checkpoint_last.pt", model, optimizer, seed=args.seed, step=step, history=history)

    if device.type == "cuda":
        torch.cuda.synchronize(device)
        memory = {
            "peak_allocated_bytes": int(torch.cuda.max_memory_allocated(device)),
            "peak_reserved_bytes": int(torch.cuda.max_memory_reserved(device)),
            "post_run_allocated_bytes": int(torch.cuda.memory_allocated(device)),
        }
    else:
        memory = {"peak_allocated_bytes": 0, "peak_reserved_bytes": 0, "post_run_allocated_bytes": 0}
    result = {
        "status": "TRAINING_CANARY_COMPLETE",
        "device": str(device),
        "dataset": "FB15K-237",
        "steps": step,
        "seed": args.seed,
        "config": vars(args) | {"out_dir": str(args.out_dir)},
        "elapsed_seconds": time.perf_counter() - started,
        "final_loss": history[-1]["loss"],
        "memory": memory,
        "finite_loss": True,
        "scientific_status": "stability_gate_only_not_training_quality_evidence",
    }
    (args.out_dir / "canary_result.json").write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(result, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
