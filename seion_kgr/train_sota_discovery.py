"""Accuracy-first KGE discovery runner.

This runner is intentionally separate from ``train.py`` and from the frozen
certified protocol.  It is a bounded discovery implementation for structural
KGE models: dynamic hard negatives are mined from a candidate pool scored by
an EMA teacher, then the online model is trained with InfoNCE and weighted
top-k margin losses.  Text and external knowledge are not implicit inputs.

The runner is safe to use for short CPU/tiny canaries.  Long GPU campaigns
remain subject to the repository's dump/driver safety gate.
"""

from __future__ import annotations

import argparse
import copy
import json
import random
import time
from pathlib import Path
from typing import Any

import numpy as np
import torch
import torch.nn.functional as F

from .data import KnowledgeGraph, load_knowledge_graph, sample_negatives, tiny_kg
from .evaluate import evaluate
from .model import BASE_EXPERTS, SeionKGRv26
from .reproducibility import restore_rng_state, rng_state_snapshot, set_seed
from .sota_discovery import info_nce_loss, mine_hard_negatives, update_ema_, weighted_margin_loss


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    p.add_argument("--train", default="")
    p.add_argument("--valid", default="")
    p.add_argument("--test", default="")
    p.add_argument("--out-dir", type=Path, default=Path("runs/KGE_SOTA_DISCOVERY_CANARY"))
    p.add_argument("--dim", type=int, default=128)
    p.add_argument("--base-expert", choices=BASE_EXPERTS, default="tucker")
    p.add_argument("--batch-size", type=int, default=256)
    p.add_argument("--epochs", type=int, default=1)
    p.add_argument("--max-steps", type=int, default=0, help="0 means no explicit step cap")
    p.add_argument("--candidate-pool", type=int, default=1024)
    p.add_argument("--hard-k", type=int, default=64)
    p.add_argument("--temperature", type=float, default=0.07)
    p.add_argument("--margin", type=float, default=0.2)
    p.add_argument("--margin-decay", type=float, default=0.03)
    p.add_argument("--infonce-weight", type=float, default=1.0)
    p.add_argument("--margin-weight", type=float, default=1.0)
    p.add_argument("--distill-weight", type=float, default=0.0)
    p.add_argument("--ema-momentum", type=float, default=0.999)
    p.add_argument("--lr", type=float, default=1e-3)
    p.add_argument("--weight-decay", type=float, default=1e-6)
    p.add_argument("--eval-every", type=int, default=0, help="steps; 0 disables validation during training")
    p.add_argument("--eval-queries", type=int, default=256)
    p.add_argument("--entity-block", type=int, default=4096)
    p.add_argument("--seed", type=int, default=42)
    p.add_argument("--cpu", action="store_true")
    p.add_argument("--resume", type=Path, default=None)
    p.add_argument("--allow-existing", action="store_true")
    p.add_argument("--tiny", action="store_true", help="use the built-in tiny graph for a safe canary")
    return p


def _device(args: argparse.Namespace) -> torch.device:
    return torch.device("cpu" if args.cpu or not torch.cuda.is_available() else "cuda")


def _load_kg(args: argparse.Namespace) -> KnowledgeGraph:
    if args.tiny:
        return tiny_kg()
    if not (args.train and args.valid and args.test):
        raise ValueError("--train, --valid and --test are required unless --tiny is used")
    return load_knowledge_graph(args.train, args.valid, args.test)


def _batch_tensor(kg: KnowledgeGraph, order: np.ndarray, offset: int, batch_size: int, device: torch.device) -> torch.Tensor:
    indices = order[offset : offset + batch_size]
    return torch.from_numpy(kg.train[indices]).to(device=device, dtype=torch.long, non_blocking=True)


@torch.no_grad()
def _mine(
    teacher: SeionKGRv26,
    h: torch.Tensor,
    r: torch.Tensor,
    t: torch.Tensor,
    kg: KnowledgeGraph,
    pool_size: int,
    hard_k: int,
    rng: np.random.Generator,
    device: torch.device,
) -> tuple[torch.Tensor, torch.Tensor]:
    pool = sample_negatives(h, r, t, kg, pool_size, rng, device)
    teacher.eval()
    pool_scores = teacher.score_tail_candidates(h, r, pool, training=False)
    return mine_hard_negatives(pool_scores, pool, t, hard_k)


def _save_checkpoint(
    path: Path,
    model: SeionKGRv26,
    teacher: SeionKGRv26,
    optimizer: torch.optim.Optimizer,
    epoch: int,
    step: int,
    history: list[dict[str, Any]],
    rng: np.random.Generator,
) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    torch.save(
        {
            "model": model.state_dict(),
            "teacher": teacher.state_dict(),
            "optimizer": optimizer.state_dict(),
            "epoch": epoch,
            "step": step,
            "history": history,
            "rng": rng_state_snapshot(0, numpy_rng=rng),
        },
        path,
    )


def run(args: argparse.Namespace) -> dict[str, Any]:
    if args.dim <= 0 or args.batch_size <= 0 or args.epochs <= 0:
        raise ValueError("dim, batch-size and epochs must be positive")
    if args.candidate_pool <= 1 or args.hard_k <= 0 or args.hard_k >= args.candidate_pool:
        raise ValueError("candidate-pool must exceed hard-k and both must be positive")
    if args.distill_weight < 0 or args.infonce_weight < 0 or args.margin_weight < 0:
        raise ValueError("loss weights must be non-negative")
    if args.out_dir.exists() and any(args.out_dir.iterdir()) and not args.allow_existing and args.resume is None:
        raise FileExistsError(f"output directory is not empty: {args.out_dir}")
    args.out_dir.mkdir(parents=True, exist_ok=True)
    set_seed(args.seed)
    rng = np.random.default_rng(args.seed)
    device = _device(args)
    kg = _load_kg(args)
    model = SeionKGRv26(kg.num_entities, kg.num_relations_total, args.dim, base_expert=args.base_expert).to(device)
    teacher = copy.deepcopy(model).to(device)
    for parameter in teacher.parameters():
        parameter.requires_grad_(False)
    teacher.eval()
    optimizer = torch.optim.AdamW(model.parameters(), lr=args.lr, weight_decay=args.weight_decay)
    history: list[dict[str, Any]] = []
    start_epoch = 1
    global_step = 0

    if args.resume is not None:
        checkpoint = torch.load(args.resume, map_location=device, weights_only=False)
        model.load_state_dict(checkpoint["model"])
        teacher.load_state_dict(checkpoint["teacher"])
        optimizer.load_state_dict(checkpoint["optimizer"])
        start_epoch = int(checkpoint["epoch"]) + 1
        global_step = int(checkpoint["step"])
        history = list(checkpoint.get("history", []))
        if "rng" in checkpoint:
            restore_rng_state(checkpoint["rng"], numpy_rng=rng)

    train_order = np.arange(len(kg.train), dtype=np.int64)
    for epoch in range(start_epoch, args.epochs + 1):
        model.train()
        teacher.eval()
        rng.shuffle(train_order)
        epoch_losses: list[float] = []
        started = time.perf_counter()
        for offset in range(0, len(train_order), args.batch_size):
            if args.max_steps and global_step >= args.max_steps:
                break
            batch = _batch_tensor(kg, train_order, offset, args.batch_size, device)
            h, r, t = batch.T
            hard_ids, _ = _mine(teacher, h, r, t, kg, args.candidate_pool, args.hard_k, rng, device)
            optimizer.zero_grad(set_to_none=True)
            positive = model.score_positive(h, r, t, training=True)
            negatives = model.score_tail_candidates(h, r, hard_ids, training=True, gold_tail_ids=t)
            loss_nce = info_nce_loss(positive, negatives, args.temperature)
            loss_margin = weighted_margin_loss(positive, negatives, args.margin, decay=args.margin_decay)
            loss = args.infonce_weight * loss_nce + args.margin_weight * loss_margin
            if args.distill_weight > 0:
                with torch.no_grad():
                    teacher_positive = teacher.score_positive(h, r, t, training=False)
                    teacher_negative = teacher.score_tail_candidates(h, r, hard_ids, training=False)
                loss = loss + args.distill_weight * (
                    F.mse_loss(positive, teacher_positive) + F.mse_loss(negatives, teacher_negative)
                )
            if not torch.isfinite(loss):
                raise FloatingPointError(f"non-finite loss at step {global_step}")
            loss.backward()
            torch.nn.utils.clip_grad_norm_(model.parameters(), 1.0)
            optimizer.step()
            update_ema_(teacher, model, args.ema_momentum)
            global_step += 1
            epoch_losses.append(float(loss.detach().item()))
            if args.eval_every and global_step % args.eval_every == 0 and kg.valid:
                valid_queries = kg.valid[: min(len(kg.valid), args.eval_queries)]
                metrics = evaluate(model, kg, "valid", device, args.batch_size, args.entity_block, queries=valid_queries)
                history.append({"epoch": epoch, "step": global_step, "loss": float(loss.item()), "valid": metrics["combined"]})
            if global_step % max(1, min(1000, len(train_order) // max(1, args.batch_size))) == 0:
                _save_checkpoint(args.out_dir / "checkpoint_last.pt", model, teacher, optimizer, epoch, global_step, history, rng)
        history.append({
            "epoch": epoch,
            "step": global_step,
            "loss": float(np.mean(epoch_losses)) if epoch_losses else None,
            "seconds": time.perf_counter() - started,
            "steps": len(epoch_losses),
        })
        _save_checkpoint(args.out_dir / "checkpoint_last.pt", model, teacher, optimizer, epoch, global_step, history, rng)
        if args.max_steps and global_step >= args.max_steps:
            break

    result = {
        "status": "COMPLETE",
        "dataset": "tiny" if args.tiny else "external",
        "device": str(device),
        "seed": args.seed,
        "dim": args.dim,
        "base_expert": args.base_expert,
        "global_step": global_step,
        "history": history,
        "num_entities": kg.num_entities,
        "num_relations_original": kg.num_relations_original,
    }
    (args.out_dir / "discovery_result.json").write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    return result


def main() -> None:
    args = build_parser().parse_args()
    run(args)


if __name__ == "__main__":
    main()
