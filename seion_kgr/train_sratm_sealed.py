"""Train SRATM from random initialization under a fail-closed no-TEST contract.

This runner accepts only TRAIN and VALID paths.  It uses the TRAIN+VALID-only
loader, filters hard negatives against TRAIN+VALID, installs a runtime file
access sentinel, and writes provenance/checkpoint artifacts.  It is a new
experiment and never resumes or loads the historical SRATM teacher.
"""

from __future__ import annotations

import argparse
import builtins
import io
import json
import os
import platform
import sys
import time
from contextlib import contextmanager
from pathlib import Path
from typing import Any, Iterator

import numpy as np
import torch
import torch.nn.functional as F

from .data import KnowledgeGraph, train_only_filter_view
from .evaluate import evaluate
from .reproducibility import restore_rng_state, rng_state_snapshot, set_seed
from .sota.full_entity_miner import mine_full_entity_hard_negatives
from .sota.full_entity_miner_fast import mine_full_entity_hard_negatives_fast
from .sota.losses import listwise_loss, margin_distillation_loss
from .sota.momentum_encoder import MomentumEncoder
from .sota.sratm import SpectralRelationAdaptiveTensorMixture
from .sota_discovery import info_nce_loss, weighted_margin_loss
from .sratm_certified_compression import load_train_valid_only, sha256


class SealedTestAccessViolation(RuntimeError):
    """Raised when a sealed run attempts to open a test split file."""


def _forbidden_test_path(value: Any) -> bool:
    if not isinstance(value, (str, bytes, os.PathLike)):
        return False
    try:
        text = os.fspath(value)
        if isinstance(text, bytes):
            text = text.decode(errors="replace")
    except TypeError:
        return False
    basename = str(text).replace("\\", "/").rsplit("/", 1)[-1].lower()
    return basename in {"test.txt", "test.tsv", "test.json", "test.jsonl"}


@contextmanager
def sealed_access_sentinel(log: list[dict[str, str]]) -> Iterator[None]:
    """Guard common Python file-open paths and record allowed accesses."""

    original_builtin_open = builtins.open
    original_io_open = io.open
    original_path_open = Path.open

    def guarded_open(file: Any, *args: Any, **kwargs: Any):
        if _forbidden_test_path(file):
            raise SealedTestAccessViolation(f"TEST_SPLIT_ACCESS_FORBIDDEN: {file}")
        log.append({"api": "builtins.open", "path": str(file)})
        return original_builtin_open(file, *args, **kwargs)

    def guarded_io_open(file: Any, *args: Any, **kwargs: Any):
        if _forbidden_test_path(file):
            raise SealedTestAccessViolation(f"TEST_SPLIT_ACCESS_FORBIDDEN: {file}")
        log.append({"api": "io.open", "path": str(file)})
        return original_io_open(file, *args, **kwargs)

    def guarded_path_open(self: Path, *args: Any, **kwargs: Any):
        if _forbidden_test_path(self):
            raise SealedTestAccessViolation(f"TEST_SPLIT_ACCESS_FORBIDDEN: {self}")
        log.append({"api": "Path.open", "path": str(self)})
        return original_path_open(self, *args, **kwargs)

    builtins.open = guarded_open
    io.open = guarded_io_open
    Path.open = guarded_path_open
    try:
        yield
    finally:
        builtins.open = original_builtin_open
        io.open = original_io_open
        Path.open = original_path_open


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    parser.add_argument("--train", type=Path, required=True)
    parser.add_argument("--valid", type=Path, required=True)
    parser.add_argument("--out-dir", type=Path, required=True)
    parser.add_argument("--dim", type=int, default=256)
    parser.add_argument("--relation-dim", type=int, default=256)
    parser.add_argument("--experts", type=int, default=8)
    parser.add_argument("--active-experts", type=int, default=2)
    parser.add_argument("--expert-rank", type=int, default=64)
    parser.add_argument("--core-basis", type=int, default=4)
    parser.add_argument("--batch-size", type=int, default=512)
    parser.add_argument("--candidate-block", type=int, default=2048)
    parser.add_argument("--hard-k", type=int, default=128)
    parser.add_argument("--epochs", type=int, default=100)
    parser.add_argument("--max-steps", type=int, default=1024)
    parser.add_argument("--checkpoint-every", type=int, default=64)
    parser.add_argument("--eval-every", type=int, default=256)
    parser.add_argument("--eval-queries", type=int, default=1024)
    parser.add_argument("--entity-block", type=int, default=4096)
    parser.add_argument("--lr", type=float, default=1e-3)
    parser.add_argument("--weight-decay", type=float, default=1e-6)
    parser.add_argument("--temperature", type=float, default=0.07)
    parser.add_argument("--margin", type=float, default=0.2)
    parser.add_argument("--margin-decay", type=float, default=0.03)
    parser.add_argument("--infonce-weight", type=float, default=1.0)
    parser.add_argument("--listwise-weight", type=float, default=0.25)
    parser.add_argument("--margin-weight", type=float, default=1.0)
    parser.add_argument("--distill-weight", type=float, default=0.25)
    parser.add_argument("--relation-prediction-weight", type=float, default=0.05)
    parser.add_argument("--basis-penalty", type=float, default=1e-4)
    parser.add_argument("--ema-momentum", type=float, default=0.999)
    parser.add_argument("--max-vram-gb", type=float, default=23.0)
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--cpu", action="store_true")
    parser.add_argument("--resume", type=Path, default=None)
    # --- Additive options for long sealed campaigns.  Every default reproduces
    # --- the original step-bounded, constant-LR, reference-miner behaviour.
    parser.add_argument("--max-seconds", type=float, default=0.0,
                        help="wall-clock training ceiling in seconds; 0 disables the time budget")
    parser.add_argument("--scheduler", choices=("none", "cosine"), default="none",
                        help="learning-rate schedule; 'none' keeps the constant LR of earlier runs")
    parser.add_argument("--warmup-steps", type=int, default=0,
                        help="linear LR warmup steps before the schedule takes over")
    parser.add_argument("--min-lr-ratio", type=float, default=0.1,
                        help="cosine floor as a fraction of --lr")
    parser.add_argument("--eval-every-seconds", type=float, default=0.0,
                        help="wall-clock evaluation cadence in seconds; 0 falls back to --eval-every steps")
    parser.add_argument("--fast-miner", action="store_true",
                        help="use the bit-exact desynchronized hard-negative miner")
    parser.add_argument("--mining-filter", choices=("train_valid", "train_only"), default="train_valid",
                        help=(
                            "which known-positive tables mask hard negatives during TRAINING. "
                            "'train_valid' reproduces earlier runs but leaks VALID membership into "
                            "training; 'train_only' is the non-leaking choice. Evaluation always "
                            "keeps TRAIN+VALID filters."
                        ))
    return parser


# The shared implementation now lives in data.py so every trainer uses one
# definition; re-exported here because tests and the sealed runner import it.
_train_only_filter_view = train_only_filter_view


def _lr_scale(args: argparse.Namespace, step: int, horizon: int) -> float:
    """Multiplicative LR factor for ``step`` (1-based) under the chosen schedule."""
    if args.warmup_steps > 0 and step <= args.warmup_steps:
        return step / float(args.warmup_steps)
    if args.scheduler == "none":
        return 1.0
    span = max(1, horizon - args.warmup_steps)
    progress = min(1.0, max(0.0, (step - args.warmup_steps) / span))
    return args.min_lr_ratio + (1.0 - args.min_lr_ratio) * 0.5 * (1.0 + np.cos(np.pi * progress))


def _device(args: argparse.Namespace) -> torch.device:
    if args.cpu or not torch.cuda.is_available():
        return torch.device("cpu")
    device = torch.device("cuda:0")
    total = torch.cuda.get_device_properties(device).total_memory
    fraction = min(0.95, args.max_vram_gb * 1024**3 / total)
    torch.cuda.set_per_process_memory_fraction(fraction, device=device)
    return device


def _save(path: Path, model: Any, teacher: MomentumEncoder, optimizer: Any, *, epoch: int, step: int,
          history: list[dict[str, Any]], rng: np.random.Generator, seed: int, config: dict[str, Any]) -> None:
    torch.save({
        "model": model.state_dict(),
        "teacher": teacher.encoder.state_dict(),
        "optimizer": optimizer.state_dict(),
        "epoch": epoch,
        "step": step,
        "history": history,
        "rng": rng_state_snapshot(seed, numpy_rng=rng),
        "sealed_protocol": config,
        "test_split_opened": False,
    }, path)


def _move_optimizer_state(optimizer: Any, device: torch.device) -> None:
    for state in optimizer.state.values():
        for key, value in list(state.items()):
            if torch.is_tensor(value):
                state[key] = value.to(device=device)


def _config(args: argparse.Namespace) -> dict[str, Any]:
    return {key: (str(value) if isinstance(value, Path) else value) for key, value in vars(args).items()}


def run(args: argparse.Namespace) -> dict[str, Any]:
    if _forbidden_test_path(args.train) or _forbidden_test_path(args.valid):
        raise ValueError("sealed runner accepts TRAIN and VALID only; TEST-like path rejected")
    if args.resume is not None and _forbidden_test_path(args.resume):
        raise ValueError("sealed runner cannot resume from a TEST-like path")
    if args.out_dir.exists() and any(args.out_dir.iterdir()) and args.resume is None:
        raise FileExistsError(f"output directory is not empty: {args.out_dir}")
    if args.max_steps <= 0 or args.batch_size <= 0 or args.checkpoint_every <= 0:
        raise ValueError("max_steps, batch_size, and checkpoint_every must be positive")
    args.out_dir.mkdir(parents=True, exist_ok=True)
    config = _config(args)
    config.update({
        "campaign": "SRATM_SEALED_TRAINING_V1",
        "loader": "TRAIN_PLUS_VALID_ONLY",
        "filters": "TRAIN_PLUS_VALID_ONLY",
        "test_split_opened": False,
        "test_split_read": False,
        "test_split_hashed": False,
        "student_distillation": False,
        "starting_weights": "random_initialization" if args.resume is None else "sealed_checkpoint_resume",
    })
    initialization_path = args.out_dir / "initialization_provenance.json"
    if not initialization_path.exists():
        initialization_path.write_text(json.dumps({
            "campaign": "SRATM_SEALED_TRAINING_V1",
            "initialization": "random_initialization" if args.resume is None else "preexisting_sealed_checkpoint_resume",
            "resume_path": None if args.resume is None else str(args.resume),
            "historical_teacher_loaded": False,
            "test_split_opened": False,
            "test_split_read": False,
            "test_split_hashed": False,
            "note": "Written before model construction so an interrupted run retains initialization provenance.",
        }, indent=2) + "\n", encoding="utf-8")
    initialization_provenance = json.loads(initialization_path.read_text(encoding="utf-8"))
    access_log: list[dict[str, str]] = []
    set_seed(args.seed)
    rng = np.random.default_rng(args.seed)
    device = _device(args)
    history: list[dict[str, Any]] = []
    best_valid_mrr = -float("inf")
    best_valid_step: int | None = None
    step = 0
    start_epoch = 1
    started = time.perf_counter()

    with sealed_access_sentinel(access_log):
        kg: KnowledgeGraph = load_train_valid_only(
            args.train, args.valid, expected_num_entities=14541, expected_num_relations_total=474,
        )
        if kg.test:
            raise RuntimeError("sealed loader returned non-empty test data")
        model = SpectralRelationAdaptiveTensorMixture(
            kg.num_entities, kg.num_relations_total, entity_dim=args.dim,
            relation_dim=args.relation_dim, experts=args.experts,
            active_per_relation=args.active_experts, expert_rank=args.expert_rank,
            core_basis=args.core_basis,
        ).to(device)
        teacher = MomentumEncoder(model, momentum=args.ema_momentum).to(device)
        optimizer = torch.optim.AdamW(model.parameters(), lr=args.lr, weight_decay=args.weight_decay)
        if args.resume is not None:
            state = torch.load(args.resume, map_location=device, weights_only=False)
            model.load_state_dict(state["model"])
            teacher.encoder.load_state_dict(state["teacher"])
            optimizer.load_state_dict(state["optimizer"])
            _move_optimizer_state(optimizer, device)
            start_epoch, step = int(state["epoch"]) + 1, int(state["step"])
            history = list(state.get("history", []))
            restore_rng_state(state["rng"], numpy_rng=rng)

        miner = (
            mine_full_entity_hard_negatives_fast if args.fast_miner else mine_full_entity_hard_negatives
        )
        # Evaluation keeps kg (TRAIN+VALID filters, the standard filtered
        # protocol); mining may be restricted to TRAIN-only to avoid leaking
        # VALID membership into the training signal.
        mining_kg = _train_only_filter_view(kg) if args.mining_filter == "train_only" else kg
        base_lrs = [group["lr"] for group in optimizer.param_groups]
        time_budget_exhausted = False
        last_eval_at = time.perf_counter()

        train_order = np.arange(len(kg.train), dtype=np.int64)
        for epoch in range(start_epoch, args.epochs + 1):
            rng.shuffle(train_order)
            model.train()
            epoch_losses: list[float] = []
            epoch_started = time.perf_counter()
            for offset in range(0, len(train_order), args.batch_size):
                if step >= args.max_steps:
                    break
                if args.max_seconds > 0 and (time.perf_counter() - started) >= args.max_seconds:
                    time_budget_exhausted = True
                    break
                batch = torch.from_numpy(kg.train[train_order[offset:offset + args.batch_size]]).to(
                    device=device, dtype=torch.long, non_blocking=True,
                )
                h, r, t = batch.T
                hard_ids, _ = miner(
                    teacher.encoder, h, r, t, mining_kg,
                    candidate_block=args.candidate_block, hard_k=args.hard_k,
                )
                scale = _lr_scale(args, step + 1, args.max_steps)
                for group, base_lr in zip(optimizer.param_groups, base_lrs):
                    group["lr"] = base_lr * scale
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
                    loss = loss + args.relation_prediction_weight * F.cross_entropy(model.relation_logits(h, t), r)
                if args.distill_weight > 0:
                    with torch.no_grad():
                        teacher_positive = teacher.encoder.score_positive(h, r, t)
                        teacher_negative = teacher.encoder.score_tail_candidates(h, r, hard_ids)
                    loss = loss + args.distill_weight * margin_distillation_loss(
                        teacher_positive, teacher_negative, positive, negatives,
                    )
                if not torch.isfinite(loss):
                    raise FloatingPointError(f"non-finite loss at sealed step {step}")
                loss.backward()
                torch.nn.utils.clip_grad_norm_(model.parameters(), 1.0)
                optimizer.step()
                teacher.update(model)
                step += 1
                epoch_losses.append(float(loss.detach().item()))
                now = time.perf_counter()
                if args.eval_every_seconds > 0:
                    due = (now - last_eval_at) >= args.eval_every_seconds
                else:
                    due = bool(args.eval_every) and step % args.eval_every == 0
                if due:
                    last_eval_at = now
                    queries = kg.valid[:min(args.eval_queries, len(kg.valid))]
                    metrics = evaluate(model, kg, "valid", device, min(args.batch_size, 64), args.entity_block, queries=queries)
                    record = {
                        "epoch": epoch, "step": step, "loss": float(loss.item()),
                        "valid": metrics["combined"],
                        "elapsed_seconds": now - started,
                        "lr": optimizer.param_groups[0]["lr"],
                    }
                    history.append(record)
                    model.train()
                    current_mrr = float(metrics["combined"]["MRR"])
                    if current_mrr > best_valid_mrr:
                        best_valid_mrr, best_valid_step = current_mrr, step
                        _save(args.out_dir / "checkpoint_best.pt", model, teacher, optimizer, epoch=epoch, step=step, history=history, rng=rng, seed=args.seed, config=config)
                if step % args.checkpoint_every == 0:
                    _save(args.out_dir / "checkpoint_last.pt", model, teacher, optimizer, epoch=epoch, step=step, history=history, rng=rng, seed=args.seed, config=config)
            history.append({"epoch": epoch, "step": step, "loss": float(np.mean(epoch_losses)) if epoch_losses else None, "seconds": time.perf_counter() - epoch_started, "steps": len(epoch_losses)})
            _save(args.out_dir / "checkpoint_last.pt", model, teacher, optimizer, epoch=epoch, step=step, history=history, rng=rng, seed=args.seed, config=config)
            if step >= args.max_steps or time_budget_exhausted:
                break

        if device.type == "cuda":
            torch.cuda.synchronize(device)
            memory = {
                "peak_allocated_bytes": int(torch.cuda.max_memory_allocated(device)),
                "peak_reserved_bytes": int(torch.cuda.max_memory_reserved(device)),
                "post_run_allocated_bytes": int(torch.cuda.memory_allocated(device)),
            }
        else:
            memory = {"peak_allocated_bytes": 0, "peak_reserved_bytes": 0, "post_run_allocated_bytes": 0}

    elapsed = time.perf_counter() - started
    result = {
        "status": "COMPLETE",
        "campaign": "SRATM_SEALED_TRAINING_V1",
        "device": str(device),
        "seed": args.seed,
        "steps": step,
        "elapsed_seconds": elapsed,
        "examples_per_second": float((step * args.batch_size) / max(elapsed, 1e-9)),
        "best_valid_mrr": None if best_valid_step is None else best_valid_mrr,
        "best_valid_step": best_valid_step,
        "stop_reason": (
            "WALL_CLOCK_BUDGET_EXHAUSTED" if time_budget_exhausted
            else "MAX_STEPS_REACHED" if step >= args.max_steps
            else "EPOCHS_EXHAUSTED"
        ),
        "schedule": {
            "scheduler": args.scheduler,
            "warmup_steps": args.warmup_steps,
            "min_lr_ratio": args.min_lr_ratio,
            "final_lr": optimizer.param_groups[0]["lr"],
            "horizon_steps": args.max_steps,
        },
        "miner": "fast_desynchronized_bit_exact" if args.fast_miner else "reference",
        "mining_filter": {
            "mode": args.mining_filter,
            "training_negatives_masked_by": (
                "TRAIN_ONLY" if args.mining_filter == "train_only" else "TRAIN_PLUS_VALID"
            ),
            "evaluation_filters": "TRAIN_PLUS_VALID",
            "valid_membership_leaks_into_training": args.mining_filter != "train_only",
        },
        "history": history,
        "memory": memory,
        "config": config,
        "dataset": {
            "train_sha256": sha256(args.train),
            "valid_sha256": sha256(args.valid),
            "test": "NOT_READ_NOT_HASHED_NOT_OPENED",
            "num_entities": int(kg.num_entities),
            "num_relations_total": int(kg.num_relations_total),
            "train_rows_with_reciprocals": int(len(kg.train)),
            "valid_rows": int(len(kg.valid)),
        },
        "no_leakage": {
            "test_split_opened": False,
            "test_split_read": False,
            "test_split_hashed": False,
            "runtime_forbidden_accesses": 0,
            "runtime_access_log_count": len(access_log),
            "runtime_access_log": access_log,
            "loader": "load_train_valid_only",
            "filter_source": "TRAIN_PLUS_VALID_ONLY",
            "starting_weights": config["starting_weights"],
            "initialization_provenance": initialization_provenance,
        },
        "scientific_status": "EMPIRICAL_SEALED_TRAINING_NO_TEST_NO_SOTA_CLAIM",
    }
    (args.out_dir / "sealed_training_result.json").write_text(json.dumps(result, indent=2, default=str) + "\n", encoding="utf-8")
    (args.out_dir / "config.json").write_text(json.dumps(config, indent=2, default=str) + "\n", encoding="utf-8")
    (args.out_dir / "no_leakage_runtime.json").write_text(json.dumps(result["no_leakage"], indent=2, default=str) + "\n", encoding="utf-8")
    (args.out_dir / "manifest.json").write_text(json.dumps({
        "campaign": result["campaign"],
        "status": result["status"],
        "command": " ".join([sys.executable, "-m", "seion_kgr.train_sratm_sealed", *sys.argv[1:]]),
        "git_head": _git_head(),
        "test_split_opened": False,
        "test_split_read": False,
        "test_split_hashed": False,
        "artifacts": sorted(path.name for path in args.out_dir.iterdir() if path.is_file()),
    }, indent=2) + "\n", encoding="utf-8")
    return result


def _git_head() -> str:
    import subprocess

    return subprocess.run(["git", "rev-parse", "HEAD"], capture_output=True, text=True, check=False).stdout.strip()


def main() -> None:
    print(json.dumps(run(build_parser().parse_args()), indent=2, default=str))


if __name__ == "__main__":
    main()
