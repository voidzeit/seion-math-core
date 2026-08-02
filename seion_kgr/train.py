"""Fase 3 (+4/5/6/7/8 behind flags): training loop, CLI, manifest writing.

The forward direction ``(h,r,?)`` and the backward/head direction are
BOTH trained as tail-scoring calls — the backward call uses
``(t, r^{-1}, ?)`` with gold ``h`` — never a separately implemented
head-scoring path (contract §II.3.2). Backward-direction negatives are
unfiltered/random because ``kg.tails_of_hr`` has no entries for
reciprocal relation ids — this mirrors a documented v25 limitation
(``seion_train_v25.py``'s ``sample_negatives`` comment), not a new bug.
"""
from __future__ import annotations

import argparse
import json
import math
import sys
import time
from pathlib import Path
from typing import Any, Dict

import numpy as np
import torch

from . import geometry, projection, rank_controller, reproducibility as repro
from .data import KnowledgeGraph, TripleDataset, load_knowledge_graph, sample_negatives, tiny_kg
from .evaluate import evaluate
from .losses import n3_regularizer, negative_sampling_loss
from .model import SeionKGRv26
from .rank_controller import ModuleDiagnostics
from .reasoner import Adjacency


def _inverse_relation(r: int, num_rel_orig: int) -> int:
    return r + num_rel_orig if r < num_rel_orig else r - num_rel_orig


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    p.add_argument("--self_test", action="store_true")
    p.add_argument("--train", type=str, default="")
    p.add_argument("--valid", type=str, default="")
    p.add_argument("--test", type=str, default="")
    p.add_argument("--out_dir", type=str, default="")
    p.add_argument("--dim", type=int, default=64)
    p.add_argument("--base_expert", choices=["complex", "distmult", "cp", "tucker"], default="complex")
    p.add_argument("--enable_path", action="store_true")
    p.add_argument("--path_rank", type=int, default=32)
    p.add_argument("--path_layers", type=int, default=2)
    p.add_argument("--path_max_neighbors", type=int, default=32)
    p.add_argument("--path_proj_rank", type=int, default=0)
    p.add_argument(
        "--path_selector_mode",
        choices=["full_neighborhood", "budgeted_bfs", "learned_topk"],
        default="budgeted_bfs",
        help="oracle_or_gold_path_debug_mode is intentionally not CLI-exposed: synthetic-fixture-only",
    )
    p.add_argument("--enable_seion", action="store_true")
    p.add_argument("--seion_rank", type=int, default=32)

    p.add_argument("--epochs", type=int, default=3)
    p.add_argument("--batch_size", type=int, default=256)
    p.add_argument("--neg_k", type=int, default=32)
    p.add_argument("--adversarial_temperature", type=float, default=1.0)
    p.add_argument("--n3_weight", type=float, default=1e-3)
    p.add_argument("--lr", type=float, default=1e-3)
    p.add_argument("--weight_decay", type=float, default=0.0)
    p.add_argument("--grad_clip", type=float, default=1.0)

    p.add_argument("--fi_weight", type=float, default=0.0)
    p.add_argument("--fi_samples", type=int, default=8)
    p.add_argument("--fi_warmup_epochs", type=int, default=2)
    p.add_argument("--assoc_weight", type=float, default=0.0)
    p.add_argument("--assoc_samples", type=int, default=8)
    p.add_argument("--assoc_warmup_epochs", type=int, default=2)

    p.add_argument("--eval_every", type=int, default=1)
    p.add_argument("--eval_batch", type=int, default=64)
    p.add_argument("--entity_block_eval", type=int, default=2048)
    p.add_argument("--eval_subset", type=float, default=1.0)
    p.add_argument("--eval_max_queries", type=int, default=0, help="0 = no cap; smoke runs should set this")

    p.add_argument("--cpu", action="store_true")
    p.add_argument("--seed", type=int, default=42)
    p.add_argument("--resume", type=str, default="", help="path to a last.pt/best.pt checkpoint to resume from")
    return p


def _module_diagnostics(model: SeionKGRv26, args: argparse.Namespace, last_batch_grad_norms: Dict[str, float]) -> list:
    """Contract §XXVII feature vector `phi_v`, computed per named
    rank-bearing module. `pathwise_score` and `gradient_sensitivity` are
    honest simplifications (see module docstrings for what a full
    implementation would need) — this is diagnostic logging, not a
    mechanism that resizes the model at runtime."""
    diagnostics = []
    if model.enable_path:
        O = model.path_reasoner.mu.O.weight.detach()
        s = torch.linalg.svdvals(O)
        energy = s.pow(2)
        half = max(1, energy.numel() // 2)
        uncaptured = float(1.0 - energy[:half].sum() / energy.sum().clamp_min(1e-12))
        leak = 0.0
        if model.path_reasoner.projector.enabled:
            sample = torch.randn(16, model.dim)
            leak = projection.measure_closure_leakage_sample(model.path_reasoner.projector, sample)["mean_ratio"]
        grad_sens = last_batch_grad_norms.get("path_reasoner", 0.0)
        diagnostics.append(ModuleDiagnostics(
            name="path_reasoner", closure_leakage=leak, singular_energy_uncaptured=uncaptured,
            gradient_sensitivity=grad_sens, pathwise_score=leak, current_rank=args.path_rank, max_rank=args.dim,
        ))
    if model.enable_seion:
        O = model.seion_scorer.O.weight.detach()
        s = torch.linalg.svdvals(O)
        energy = s.pow(2)
        half = max(1, energy.numel() // 2)
        uncaptured = float(1.0 - energy[:half].sum() / energy.sum().clamp_min(1e-12))
        grad_sens = last_batch_grad_norms.get("seion_scorer", 0.0)
        diagnostics.append(ModuleDiagnostics(
            name="seion_scorer", closure_leakage=0.0, singular_energy_uncaptured=uncaptured,
            gradient_sensitivity=grad_sens, pathwise_score=uncaptured, current_rank=args.seion_rank, max_rank=args.dim,
        ))
    return diagnostics


def train(args: argparse.Namespace) -> Dict[str, Any]:
    repro.set_seed(args.seed)
    device = torch.device("cpu" if args.cpu or not torch.cuda.is_available() else "cuda")

    if args.out_dir:
        repro.build_run_contract(
            args.out_dir, sys.argv, {"train": args.train, "valid": args.valid, "test": args.test},
        )

    kg = load_knowledge_graph(args.train, args.valid, args.test)
    model = SeionKGRv26(
        num_entities=kg.num_entities, num_relations_total=kg.num_relations_total, dim=args.dim,
        base_expert=args.base_expert, enable_path=args.enable_path, enable_seion=args.enable_seion,
        seion_rank=args.seion_rank, path_rank=args.path_rank, path_layers=args.path_layers,
        path_max_neighbors=args.path_max_neighbors, path_proj_rank=args.path_proj_rank,
        path_selector_mode=args.path_selector_mode,
    ).to(device)
    adjacency = Adjacency.build(kg) if args.enable_path else None

    dataset = TripleDataset(kg.train)
    loader = torch.utils.data.DataLoader(dataset, batch_size=args.batch_size, shuffle=True, drop_last=False)
    optimizer = torch.optim.AdamW(model.parameters(), lr=args.lr, weight_decay=args.weight_decay)
    rng = np.random.default_rng(args.seed + 1)
    gen = torch.Generator(device=device)
    gen.manual_seed(args.seed + 2)

    metrics_path = Path(args.out_dir) / "metrics.jsonl" if args.out_dir else None
    rank_history_path = Path(args.out_dir) / "rank_history.jsonl" if args.out_dir else None
    error_attribution_path = Path(args.out_dir) / "error_attribution.jsonl" if args.out_dir else None
    start = time.time()
    history: list[Dict[str, Any]] = []

    start_epoch = 0
    global_step = 0
    best_mrr = -math.inf
    if args.resume:
        ckpt = repro.load_checkpoint(args.resume)
        model.load_state_dict(ckpt["model_state"])
        optimizer.load_state_dict(ckpt["optimizer_state"])
        start_epoch = int(ckpt["epoch"]) + 1
        global_step = int(ckpt["global_step"])
        best_mrr = float(ckpt["best_mrr"])
        print(f"[resume] loaded {args.resume}: start_epoch={start_epoch} best_mrr={best_mrr}", file=sys.stderr)

    for epoch in range(start_epoch, args.epochs):
        model.train()
        epoch_start = time.time()
        sums: Dict[str, float] = {}
        n = 0
        for h_ids, r_ids, t_ids in loader:
            h_ids, r_ids, t_ids = h_ids.to(device), r_ids.to(device), t_ids.to(device)
            r_inv_ids = torch.tensor(
                [_inverse_relation(int(r), kg.num_relations_original) for r in r_ids.tolist()], device=device,
            )
            tail_negs = sample_negatives(h_ids, r_ids, t_ids, kg, args.neg_k, rng, device)
            head_negs = sample_negatives(t_ids, r_inv_ids, h_ids, kg, args.neg_k, rng, device)  # unfiltered, see docstring

            optimizer.zero_grad(set_to_none=True)
            pos_fwd = model.score_positive(h_ids, r_ids, t_ids, adjacency, args.seed, training=True)
            neg_fwd = model.score_tail_candidates(h_ids, r_ids, tail_negs, adjacency, args.seed, training=True, gold_tail_ids=t_ids)
            pos_bwd = model.score_positive(t_ids, r_inv_ids, h_ids, adjacency, args.seed, training=True)
            neg_bwd = model.score_tail_candidates(t_ids, r_inv_ids, head_negs, adjacency, args.seed, training=True, gold_tail_ids=h_ids)

            loss_fwd = negative_sampling_loss(pos_fwd, neg_fwd, args.adversarial_temperature)
            loss_bwd = negative_sampling_loss(pos_bwd, neg_bwd, args.adversarial_temperature)
            kge_loss = 0.5 * (loss_fwd + loss_bwd)

            n3 = n3_regularizer(model.entity(h_ids), model.relation(r_ids), model.entity(t_ids)) if args.n3_weight > 0 else torch.zeros((), device=device)
            total = kge_loss + args.n3_weight * n3

            weights = geometry.geometric_curriculum_weights(
                epoch, args.assoc_weight, args.assoc_warmup_epochs, args.fi_weight, args.fi_warmup_epochs, 0.0, 1,
            )
            fi_loss = torch.zeros((), device=device)
            assoc_loss = torch.zeros((), device=device)
            if args.enable_seion and (weights["fi"] > 0 or weights["assoc"] > 0):
                # q_seion(x,a,q) -> vector of the same dim is a genuine
                # ternary map, so it can serve as the recursive `ternary_fn`
                # both diagnostics need (contract §V/§VII source note).
                ternary_fn = model.seion_scorer.q_seion
                pool = torch.cat([model.entity(h_ids), model.entity(t_ids), model.relation(r_ids)], dim=0)
                fi_loss = geometry.filippov_energy(ternary_fn, pool, args.fi_samples, weights["fi"], gen)
                assoc_loss = geometry.associator_energy(ternary_fn, pool, args.assoc_samples, weights["assoc"], gen)
                total = total + weights["fi"] * fi_loss + weights["assoc"] * assoc_loss

            total.backward()
            grad_norm = torch.nn.utils.clip_grad_norm_(model.parameters(), args.grad_clip)
            last_batch_grad_norms: Dict[str, float] = {}
            if args.enable_path:
                last_batch_grad_norms["path_reasoner"] = float(
                    sum(p.grad.norm().item() for p in model.path_reasoner.parameters() if p.grad is not None)
                )
            if args.enable_seion:
                last_batch_grad_norms["seion_scorer"] = float(
                    sum(p.grad.norm().item() for p in model.seion_scorer.parameters() if p.grad is not None)
                )
            optimizer.step()
            global_step += 1

            batch_n = int(h_ids.numel())
            n += batch_n
            for name, value in (("loss", total), ("kge", kge_loss), ("n3", n3), ("fi", fi_loss), ("assoc", assoc_loss), ("grad_norm", grad_norm)):
                sums[name] = sums.get(name, 0.0) + float(value.detach().item()) * batch_n

        epoch_metrics = {name: v / max(n, 1) for name, v in sums.items()}
        record: Dict[str, Any] = {"epoch": epoch, "train": epoch_metrics, "wall_sec": time.time() - epoch_start}

        is_eval_epoch = (epoch + 1) % args.eval_every == 0 or epoch == args.epochs - 1
        if is_eval_epoch:
            eval_subset = args.eval_subset
            if args.eval_max_queries > 0:
                eval_subset = min(eval_subset, args.eval_max_queries / max(len(kg.valid), 1))
            valid = evaluate(model, kg, "valid", device, args.eval_batch, args.entity_block_eval, adjacency, eval_subset, args.seed)
            record["valid"] = valid
            current_mrr = valid["combined"]["MRR"]
            record["new_best"] = current_mrr > best_mrr
            if current_mrr > best_mrr:
                best_mrr = current_mrr

            diagnostics = _module_diagnostics(model, args, last_batch_grad_norms)
            if diagnostics and rank_history_path is not None:
                comparison = rank_controller.compare_policies(
                    diagnostics, budget=sum(d.current_rank for d in diagnostics),
                    objective_fn=lambda alloc: sum(
                        d.closure_leakage * max(d.current_rank - alloc[d.name], 0) for d in diagnostics
                    ),
                    seed=args.seed,
                )
                repro.append_jsonl({"epoch": epoch, "diagnostics": [d.__dict__ for d in diagnostics], "policy_comparison": comparison}, rank_history_path)

            if args.enable_path and model.path_reasoner.projector.enabled and error_attribution_path is not None:
                sample = torch.randn(16, args.dim)
                leak = projection.measure_closure_leakage_sample(model.path_reasoner.projector, sample)
                repro.append_jsonl({"epoch": epoch, "closure_leakage": leak}, error_attribution_path)

        if args.out_dir:
            rng_state = repro.rng_state_snapshot(args.seed, rng)
            args_dict = {k: v for k, v in vars(args).items()}
            repro.save_checkpoint(Path(args.out_dir) / "last.pt", model.state_dict(), optimizer.state_dict(), epoch, global_step, best_mrr, args_dict, rng_state)
            if is_eval_epoch and record.get("new_best"):
                repro.save_checkpoint(Path(args.out_dir) / "best.pt", model.state_dict(), optimizer.state_dict(), epoch, global_step, best_mrr, args_dict, rng_state)

        history.append(record)
        if metrics_path is not None:
            repro.append_jsonl(record, metrics_path)
        print(json.dumps(record, default=str), flush=True)

    test_subset = args.eval_subset
    if args.eval_max_queries > 0:
        test_subset = min(test_subset, args.eval_max_queries / max(len(kg.test), 1))
    test_metrics = evaluate(model, kg, "test", device, args.eval_batch, args.entity_block_eval, adjacency, test_subset, args.seed)
    result = {
        "status": "COMPLETED",
        "base_expert": args.base_expert,
        "enable_path": args.enable_path,
        "enable_seion": args.enable_seion,
        "test": test_metrics,
        "wall_sec": time.time() - start,
    }
    if args.out_dir:
        if args.enable_path:
            audit = projection.audit_projectors({"path_reasoner": model.path_reasoner.projector})
            repro.save_json(audit, Path(args.out_dir) / "projection_audit.json")
        repro.mark_completed(args.out_dir, result)
    print(json.dumps(result, indent=2, default=str), flush=True)
    return result


def run_self_test() -> Dict[str, Any]:
    """End-to-end smoke test on the tiny synthetic graph — every base
    expert x {path off/on} x {seion off/on}, one epoch, asserting finite
    loss and nonzero gradients. This is NOT Gate 12 (no seeds, no
    dataset); it only proves the pipeline executes correctly."""
    device = torch.device("cpu")
    kg = tiny_kg()
    results = {}
    for base in ("complex", "distmult", "cp", "tucker"):
        for enable_path in (False, True):
            for enable_seion in (False, True):
                repro.set_seed(3)
                model = SeionKGRv26(
                    num_entities=kg.num_entities, num_relations_total=kg.num_relations_total, dim=8,
                    base_expert=base, enable_path=enable_path, enable_seion=enable_seion,
                    seion_rank=3, path_rank=3, path_layers=1, path_max_neighbors=4,
                ).to(device)
                adjacency = Adjacency.build(kg) if enable_path else None
                h = torch.tensor([0, 2])
                r = torch.tensor([0, 1])
                t = torch.tensor([1, 3])
                pos = model.score_positive(h, r, t, adjacency, seed=1, training=True)
                cand = torch.arange(kg.num_entities)
                scores = model.score_tail_candidates(h, r, cand, adjacency, seed=1, training=True, gold_tail_ids=t)
                if not torch.isfinite(pos).all() or not torch.isfinite(scores).all():
                    raise AssertionError(f"non-finite scores for base={base} path={enable_path} seion={enable_seion}")
                # positive score must equal the candidate score at the gold column
                gold_col = scores[torch.arange(2), t]
                err = float((pos - gold_col).abs().max().item())
                if err > 1e-4:
                    raise AssertionError(
                        f"positive/candidate score paths disagree (base={base}, path={enable_path}, "
                        f"seion={enable_seion}): {err}"
                    )
                loss = negative_sampling_loss(pos, scores[:, :4], 1.0)
                loss.backward()
                grad_total = sum(float(p.grad.norm().item()) for p in model.parameters() if p.grad is not None)
                if grad_total <= 0:
                    raise AssertionError(f"zero total gradient for base={base} path={enable_path} seion={enable_seion}")
                key = f"{base}_path{int(enable_path)}_seion{int(enable_seion)}"
                results[key] = {"status": "PASS", "score_path_max_error": err, "grad_total": grad_total}
    results["status"] = "PASS_SEION_KGR_V26_SELF_TESTS"
    return results


def main() -> None:
    args = build_parser().parse_args()
    if args.self_test:
        print(json.dumps(run_self_test(), indent=2, default=str))
        return
    missing = [n for n in ("train", "valid", "test", "out_dir") if not getattr(args, n)]
    if missing:
        raise ValueError(f"Missing required arguments: {missing}")
    train(args)


if __name__ == "__main__":
    main()
