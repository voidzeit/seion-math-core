"""Full-entity hard-negative trainer for SpectralConditionalTensorMixture."""

from __future__ import annotations

import argparse
import json
import time
from pathlib import Path
from typing import Any

import numpy as np
import torch
import torch.nn.functional as F

from .data import KnowledgeGraph, load_knowledge_graph, tiny_kg, train_only_filter_view
from .evaluate import evaluate
from .reproducibility import restore_rng_state, rng_state_snapshot, set_seed
from .sota.full_entity_miner import mine_full_entity_hard_negatives
from .sota.losses import listwise_loss, margin_distillation_loss
from .sota.momentum_encoder import MomentumEncoder
from .sota.spectral_mixture import SpectralConditionalTensorMixture
from .sota.sratm import SpectralRelationAdaptiveTensorMixture
from .sota_discovery import info_nce_loss, weighted_margin_loss


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    p.add_argument("--train", default="")
    p.add_argument("--valid", default="")
    p.add_argument("--test", default="")
    p.add_argument("--tiny", action="store_true")
    p.add_argument("--out-dir", type=Path, default=Path("runs/SPECTRAL_MIXTURE_DISCOVERY_CANARY"))
    p.add_argument("--dim", type=int, default=256)
    p.add_argument("--relation-dim", type=int, default=256)
    p.add_argument("--experts", type=int, default=8)
    p.add_argument("--active-experts", type=int, default=2)
    p.add_argument("--expert-rank", type=int, default=64)
    p.add_argument("--core-basis", type=int, default=4)
    p.add_argument("--batch-size", type=int, default=256)
    p.add_argument("--candidate-block", type=int, default=2048)
    p.add_argument("--hard-k", type=int, default=128)
    p.add_argument("--epochs", type=int, default=1)
    p.add_argument("--max-steps", type=int, default=0)
    p.add_argument("--lr", type=float, default=1e-3)
    p.add_argument("--weight-decay", type=float, default=1e-6)
    p.add_argument("--temperature", type=float, default=0.07)
    p.add_argument("--margin", type=float, default=0.2)
    p.add_argument("--margin-decay", type=float, default=0.03)
    p.add_argument("--infonce-weight", type=float, default=1.0)
    p.add_argument("--listwise-weight", type=float, default=0.25)
    p.add_argument("--margin-weight", type=float, default=1.0)
    p.add_argument("--distill-weight", type=float, default=0.25)
    p.add_argument("--relation-prediction-weight", type=float, default=0.05)
    p.add_argument("--architecture", choices=("sratm", "spectral_mixture"), default="sratm")
    p.add_argument("--basis-penalty", type=float, default=1e-4)
    p.add_argument("--ema-momentum", type=float, default=0.999)
    p.add_argument("--eval-every", type=int, default=0)
    p.add_argument("--eval-queries", type=int, default=256)
    p.add_argument("--entity-block", type=int, default=4096)
    p.add_argument("--max-vram-gb", type=float, default=23.0)
    p.add_argument("--seed", type=int, default=42)
    p.add_argument("--negative-filter", choices=("train_valid_test", "train_only"),
                   default="train_valid_test",
                   help="which known-positive tables mask TRAINING negatives (B-0014). "
                        "'train_valid_test' reproduces the historical runs but leaks "
                        "VALID and TEST membership into training; 'train_only' is the "
                        "non-leaking choice. Evaluation always keeps the full filters.")
    p.add_argument("--cpu", action="store_true")
    p.add_argument("--resume", type=Path, default=None)
    p.add_argument("--allow-existing", action="store_true")
    return p


def _device(args: argparse.Namespace) -> torch.device:
    if args.cpu or not torch.cuda.is_available():
        return torch.device("cpu")
    device = torch.device("cuda:0")
    total = torch.cuda.get_device_properties(device).total_memory
    fraction = min(0.95, args.max_vram_gb * 1024**3 / total)
    torch.cuda.set_per_process_memory_fraction(fraction, device=device)
    return device


def _load_kg(args: argparse.Namespace) -> KnowledgeGraph:
    if args.tiny:
        return tiny_kg()
    if not (args.train and args.valid and args.test):
        raise ValueError("--train, --valid and --test are required unless --tiny is used")
    return load_knowledge_graph(args.train, args.valid, args.test)


def _save(path: Path, model, teacher, optimizer, *, epoch: int, step: int, history: list[dict[str, Any]], rng: np.random.Generator, seed: int) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    torch.save({
        "model": model.state_dict(),
        "teacher": teacher.encoder.state_dict(),
        "optimizer": optimizer.state_dict(),
        "epoch": epoch,
        "step": step,
        "history": history,
        "rng": rng_state_snapshot(seed, numpy_rng=rng),
    }, path)


def _move_optimizer_state(optimizer: torch.optim.Optimizer, device: torch.device) -> None:
    for state in optimizer.state.values():
        for key, value in list(state.items()):
            if torch.is_tensor(value):
                state[key] = value.to(device=device)


def run(args: argparse.Namespace) -> dict[str, Any]:
    if args.out_dir.exists() and any(args.out_dir.iterdir()) and args.resume is None and not args.allow_existing:
        raise FileExistsError(f"output directory is not empty: {args.out_dir}")
    if args.max_vram_gb <= 0 or args.batch_size <= 0 or args.candidate_block <= 0 or args.hard_k <= 0:
        raise ValueError("resource and batch parameters must be positive")
    args.out_dir.mkdir(parents=True, exist_ok=True)
    set_seed(args.seed)
    rng = np.random.default_rng(args.seed)
    device = _device(args)
    kg = _load_kg(args)
    # B-0014: this trainer requires --test and folds VALID+TEST into the filter
    # tables. Those tables are right for evaluation and leaking for training
    # negatives; only the miner gets the TRAIN-only view.
    negative_kg = train_only_filter_view(kg) if args.negative_filter == "train_only" else kg
    model_cls = SpectralRelationAdaptiveTensorMixture if args.architecture == "sratm" else SpectralConditionalTensorMixture
    model = model_cls(
        kg.num_entities, kg.num_relations_total, entity_dim=args.dim, relation_dim=args.relation_dim,
        experts=args.experts, active_per_relation=args.active_experts,
        expert_rank=args.expert_rank, core_basis=args.core_basis,
    ).to(device)
    teacher = MomentumEncoder(model, momentum=args.ema_momentum).to(device)
    optimizer = torch.optim.AdamW(model.parameters(), lr=args.lr, weight_decay=args.weight_decay)
    history: list[dict[str, Any]] = []
    best_valid_mrr = -float("inf")
    best_valid_step: int | None = None
    start_epoch, step = 1, 0
    if args.resume is not None:
        state = torch.load(args.resume, map_location=device, weights_only=False)
        model.load_state_dict(state["model"])
        teacher.encoder.load_state_dict(state["teacher"])
        optimizer.load_state_dict(state["optimizer"])
        _move_optimizer_state(optimizer, device)
        start_epoch, step = int(state["epoch"]) + 1, int(state["step"])
        history = list(state.get("history", []))
        prior_valid = [
            float(item["valid"]["MRR"])
            for item in history
            if isinstance(item, dict) and isinstance(item.get("valid"), dict) and "MRR" in item["valid"]
        ]
        if prior_valid:
            best_valid_mrr = max(prior_valid)
            best_valid_step = next(
                int(item["step"])
                for item in history
                if isinstance(item, dict) and isinstance(item.get("valid"), dict)
                and float(item["valid"].get("MRR", -float("inf"))) == best_valid_mrr
            )
        restore_rng_state(state["rng"], numpy_rng=rng)

    train_order = np.arange(len(kg.train), dtype=np.int64)
    for epoch in range(start_epoch, args.epochs + 1):
        rng.shuffle(train_order)
        model.train()
        epoch_losses: list[float] = []
        started = time.perf_counter()
        for offset in range(0, len(train_order), args.batch_size):
            if args.max_steps and step >= args.max_steps:
                break
            batch = torch.from_numpy(kg.train[train_order[offset : offset + args.batch_size]]).to(device=device, dtype=torch.long, non_blocking=True)
            h, r, t = batch.T
            hard_ids, _ = mine_full_entity_hard_negatives(
                teacher.encoder, h, r, t, negative_kg, candidate_block=args.candidate_block, hard_k=args.hard_k,
            )
            optimizer.zero_grad(set_to_none=True)
            positive = model.score_positive(h, r, t)
            negatives = model.score_tail_candidates(h, r, hard_ids)
            loss = (
                args.infonce_weight * info_nce_loss(positive, negatives, args.temperature)
                + args.listwise_weight * listwise_loss(positive, negatives, args.temperature)
                + args.margin_weight * weighted_margin_loss(positive, negatives, args.margin, decay=args.margin_decay)
                + args.basis_penalty * model.basis_decorrelation_penalty()
            )
            if args.relation_prediction_weight > 0 and hasattr(model, "relation_logits"):
                relation_logits = model.relation_logits(h, t)
                loss = loss + args.relation_prediction_weight * F.cross_entropy(relation_logits, r)
            if args.distill_weight > 0:
                with torch.no_grad():
                    teacher_positive = teacher.encoder.score_positive(h, r, t)
                    teacher_negative = teacher.encoder.score_tail_candidates(h, r, hard_ids)
                loss = loss + args.distill_weight * margin_distillation_loss(teacher_positive, teacher_negative, positive, negatives)
            if not torch.isfinite(loss):
                raise FloatingPointError(f"non-finite loss at step {step}")
            loss.backward()
            torch.nn.utils.clip_grad_norm_(model.parameters(), 1.0)
            optimizer.step()
            teacher.update(model)
            step += 1
            epoch_losses.append(float(loss.detach().item()))
            if args.eval_every and step % args.eval_every == 0 and kg.valid:
                queries = kg.valid[: min(args.eval_queries, len(kg.valid))]
                metrics = evaluate(model, kg, "valid", device, min(args.batch_size, 64), args.entity_block, queries=queries)
                history.append({"epoch": epoch, "step": step, "loss": float(loss.item()), "valid": metrics["combined"]})
                current_mrr = float(metrics["combined"]["MRR"])
                if current_mrr > best_valid_mrr:
                    best_valid_mrr = current_mrr
                    best_valid_step = step
                    _save(
                        args.out_dir / "checkpoint_best.pt",
                        model,
                        teacher,
                        optimizer,
                        epoch=epoch,
                        step=step,
                        history=history,
                        rng=rng,
                        seed=args.seed,
                    )
            if step % max(1, min(100, len(train_order) // max(1, args.batch_size))) == 0:
                _save(args.out_dir / "checkpoint_last.pt", model, teacher, optimizer, epoch=epoch, step=step, history=history, rng=rng, seed=args.seed)
        history.append({"epoch": epoch, "step": step, "loss": float(np.mean(epoch_losses)) if epoch_losses else None, "seconds": time.perf_counter() - started, "steps": len(epoch_losses)})
        _save(args.out_dir / "checkpoint_last.pt", model, teacher, optimizer, epoch=epoch, step=step, history=history, rng=rng, seed=args.seed)
        if args.max_steps and step >= args.max_steps:
            break

    if device.type == "cuda":
        torch.cuda.synchronize(device)
        memory = {"peak_allocated_bytes": int(torch.cuda.max_memory_allocated(device)), "peak_reserved_bytes": int(torch.cuda.max_memory_reserved(device)), "post_run_allocated_bytes": int(torch.cuda.memory_allocated(device))}
    else:
        memory = {"peak_allocated_bytes": 0, "peak_reserved_bytes": 0, "post_run_allocated_bytes": 0}
    config = {key: (str(value) if isinstance(value, Path) else value) for key, value in vars(args).items()}
    result = {
        "status": "COMPLETE",
        "device": str(device),
        "dataset": "tiny" if args.tiny else "external",
        "seed": args.seed,
        "steps": step,
        "best_valid_mrr": None if best_valid_step is None else best_valid_mrr,
        "best_valid_step": best_valid_step,
        "config": config,
        "history": history,
        "memory": memory,
        "architecture": args.architecture,
        "scientific_status": "discovery_training_only_no_SOTA_or_certificate_claim",
    }
    (args.out_dir / "discovery_result.json").write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    return result


def main() -> None:
    run(build_parser().parse_args())


if __name__ == "__main__":
    main()
