"""Does SRATM carry information residual to TuckER?

The question is deliberately not "TuckER versus SRATM". T0 established a clean
TuckER baseline (VALID MRR 0.28372, exact 1-vs-all, TRAIN-only truth). What
matters for the teacher design is whether SRATM adds anything *on top of* that
baseline, because a residual that contributes nothing is a reason to stop
spending compute making SRATM competitive.

Three arms, identical in every other respect:

    A  s_T                        backbone only
    B  s_T + alpha * s~_S         one learnable scale
    C  s_T + alpha_r * s~_S       one learnable scale per relation

The backbone is loaded frozen, so any gain is attributable to the residual and
not to further backbone training. The residual is normalised query-wise,
    s~_S(h,r,t) = (s_S - mu_S(h,r)) / (sigma_S(h,r) + eps),
with mu and sigma taken over all entities for that query, so the two experts are
combined by relative position within the ranking rather than by raw scale.

Sealed contract throughout: TRAIN+VALID paths only, TRAIN-only truth in the
loss, exact 1-vs-all (no negative sampler), TEST never opened.
"""

from __future__ import annotations

import argparse
import json
import time
from pathlib import Path
from typing import Any

import numpy as np
import torch
import torch.nn as nn
import torch.nn.functional as F

from .evaluate import evaluate
from .reproducibility import set_seed
from .sota.sratm import SpectralRelationAdaptiveTensorMixture
from .sratm_certified_compression import load_train_valid_only, sha256
from .train_1vsall_sealed import TuckER1vsAll, _lr_scale
from .train_sratm_sealed import _forbidden_test_path, sealed_access_sentinel
from .truth_index import TrainTruthIndex, require_train_truth


class ResidualScorer(nn.Module):
    """Frozen TuckER backbone plus an optional query-normalised SRATM residual."""

    def __init__(self, backbone: TuckER1vsAll, num_entities: int, num_relations: int,
                 residual: str, sratm_dim: int, experts: int, active: int,
                 expert_rank: int, core_basis: int,
                 sratm_state: dict | None = None, freeze_sratm: bool = False) -> None:
        super().__init__()
        self.backbone = backbone
        for p in self.backbone.parameters():
            p.requires_grad_(False)
        self.residual = residual
        if residual == "none":
            self.sratm = None
            return
        self.sratm = SpectralRelationAdaptiveTensorMixture(
            num_entities, num_relations, entity_dim=sratm_dim, relation_dim=sratm_dim,
            experts=experts, active_per_relation=active, expert_rank=expert_rank,
            core_basis=core_basis,
        )
        # Loading an already-trained SRATM and freezing it isolates the question:
        # a poorly-trained residual would produce a null result for the wrong
        # reason. With both experts fixed, only the combination weight is fitted.
        if sratm_state is not None:
            self.sratm.load_state_dict(sratm_state)
        if freeze_sratm:
            self.sratm.eval()
            for p in self.sratm.parameters():
                p.requires_grad_(False)
        if residual == "scalar":
            self.alpha = nn.Parameter(torch.zeros(1))
        elif residual == "per_relation":
            self.alpha = nn.Parameter(torch.zeros(num_relations))
        else:
            raise ValueError(f"unknown residual mode: {residual}")

    def forward(self, h_ids: torch.Tensor, r_ids: torch.Tensor,
                all_ids: torch.Tensor) -> torch.Tensor:
        with torch.no_grad():
            base = self.backbone(h_ids, r_ids)
        if self.sratm is None:
            return base
        raw = self.sratm.score_tail_candidates(h_ids, r_ids, all_ids)
        # Query-wise standardisation: combine ranking position, not raw scale.
        mu = raw.mean(dim=1, keepdim=True)
        sigma = raw.std(dim=1, keepdim=True)
        norm = (raw - mu) / (sigma + 1e-6)
        a = self.alpha if self.residual == "scalar" else self.alpha[r_ids].unsqueeze(1)
        return base + a * norm

    # --- adapters for the shared filtered evaluator ---
    def _all(self, device) -> torch.Tensor:
        return torch.arange(self.backbone.entity.num_embeddings, device=device)

    def score_positive(self, h_ids, r_ids, t_ids, *a, **k):
        return self.forward(h_ids, r_ids, self._all(h_ids.device)).gather(
            1, t_ids.unsqueeze(1)).squeeze(1)

    def score_tail_candidates(self, h_ids, r_ids, candidate_ids, *a, **k):
        logits = self.forward(h_ids, r_ids, self._all(h_ids.device))
        return (logits.index_select(1, candidate_ids) if candidate_ids.ndim == 1
                else logits.gather(1, candidate_ids))


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--train", type=Path, required=True)
    p.add_argument("--valid", type=Path, required=True)
    p.add_argument("--backbone", type=Path, required=True)
    p.add_argument("--out-dir", type=Path, required=True)
    p.add_argument("--residual", choices=("none", "scalar", "per_relation"), required=True)
    p.add_argument("--sratm-checkpoint", type=Path, default=None,
                   help="load a trained SRATM as the residual expert")
    p.add_argument("--freeze-sratm", action="store_true",
                   help="fit only the combination weight, leaving both experts fixed")
    p.add_argument("--dim-e", type=int, default=200)
    p.add_argument("--dim-r", type=int, default=200)
    p.add_argument("--sratm-dim", type=int, default=128)
    p.add_argument("--experts", type=int, default=8)
    p.add_argument("--active-experts", type=int, default=2)
    p.add_argument("--expert-rank", type=int, default=64)
    p.add_argument("--core-basis", type=int, default=4)
    p.add_argument("--batch-size", type=int, default=256)
    p.add_argument("--lr", type=float, default=1e-3)
    p.add_argument("--label-smoothing", type=float, default=0.1)
    p.add_argument("--max-steps", type=int, default=12000)
    p.add_argument("--max-seconds", type=float, default=0.0)
    p.add_argument("--warmup-steps", type=int, default=200)
    p.add_argument("--min-lr-ratio", type=float, default=0.05)
    p.add_argument("--eval-every-seconds", type=float, default=90.0)
    p.add_argument("--eval-queries", type=int, default=2048)
    p.add_argument("--entity-block", type=int, default=4096)
    p.add_argument("--seed", type=int, default=42)
    p.add_argument("--cpu", action="store_true")
    return p


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
    best_mrr, best_step, step, stopped = -float("inf"), None, 0, None
    started = time.perf_counter()

    with sealed_access_sentinel(access_log):
        kg = load_train_valid_only(args.train, args.valid,
                                   expected_num_entities=14541,
                                   expected_num_relations_total=474)
        train_rows = [(int(h), int(r), int(t)) for h, r, t in kg.train]
        truth = require_train_truth(TrainTruthIndex.from_train(train_rows))

        backbone = TuckER1vsAll(kg.num_entities, kg.num_relations_total,
                                args.dim_e, args.dim_r).to(device)
        state = torch.load(args.backbone, map_location=device, weights_only=False)
        backbone.load_state_dict(state["model"])
        backbone.eval()

        sratm_state, sratm_sha = None, None
        if args.sratm_checkpoint is not None:
            sratm_state = torch.load(args.sratm_checkpoint, map_location=device,
                                     weights_only=False)["model"]
            sratm_sha = sha256(args.sratm_checkpoint)
        model = ResidualScorer(backbone, kg.num_entities, kg.num_relations_total,
                               args.residual, args.sratm_dim, args.experts,
                               args.active_experts, args.expert_rank,
                               args.core_basis, sratm_state, args.freeze_sratm).to(device)
        trainable = [p for p in model.parameters() if p.requires_grad]
        all_ids = torch.arange(kg.num_entities, device=device)

        queries = sorted({(int(h), int(r)) for h, r, _ in train_rows})
        query_arr = np.asarray(queries, dtype=np.int64)
        targets = [truth.train_tails(h, r) for h, r in queries]
        offs = np.zeros(len(targets) + 1, dtype=np.int64)
        np.cumsum([len(t) for t in targets], out=offs[1:])
        tvals = torch.from_numpy(np.concatenate(targets)).to(device)
        toffs = torch.from_numpy(offs).to(device)
        order = np.arange(len(queries))
        last_eval = time.perf_counter()

        def evaluate_now():
            model.eval()
            q = kg.valid[:min(args.eval_queries, len(kg.valid))]
            m = evaluate(model, kg, "valid", device, 64, args.entity_block, queries=q)
            model.train()
            return m["combined"]

        # Arm A has no trainable parameters: score the frozen backbone once.
        if not trainable:
            metrics = evaluate_now()
            history.append({"step": 0, "valid": metrics, "elapsed_seconds": 0.0})
            best_mrr, best_step, stopped = float(metrics["MRR"]), 0, "FROZEN_BACKBONE_ONLY"
        else:
            optimizer = torch.optim.Adam(trainable, lr=args.lr)
            base_lrs = [g["lr"] for g in optimizer.param_groups]
            model.train()
            while step < args.max_steps and stopped is None:
                rng.shuffle(order)
                for off in range(0, len(order), args.batch_size):
                    if step >= args.max_steps:
                        stopped = "MAX_STEPS_REACHED"; break
                    if args.max_seconds > 0 and time.perf_counter() - started >= args.max_seconds:
                        stopped = "WALL_CLOCK_BUDGET_EXHAUSTED"; break
                    idx = order[off:off + args.batch_size]
                    if len(idx) < 2:
                        continue
                    hr = torch.from_numpy(query_arr[idx]).to(device)
                    sel = torch.from_numpy(idx).to(device)
                    starts, lens = toffs[sel], toffs[sel + 1] - toffs[sel]
                    width = int(lens.max().item())
                    ar = torch.arange(width, device=device)
                    flat = (starts.unsqueeze(1) + ar).clamp(max=tvals.numel() - 1)
                    mask = ar < lens.unsqueeze(1)
                    rows = torch.arange(len(idx), device=device).unsqueeze(1).expand_as(flat)
                    label = torch.zeros(len(idx), kg.num_entities, device=device)
                    label.index_put_((rows[mask], tvals[flat][mask]),
                                     torch.ones(int(mask.sum()), device=device))
                    if args.label_smoothing > 0:
                        label = label * (1 - args.label_smoothing) + args.label_smoothing / kg.num_entities

                    for g, b in zip(optimizer.param_groups, base_lrs):
                        g["lr"] = b * _lr_scale(args, step + 1)
                    optimizer.zero_grad(set_to_none=True)
                    loss = F.binary_cross_entropy_with_logits(
                        model(hr[:, 0], hr[:, 1], all_ids), label)
                    if not torch.isfinite(loss):
                        raise FloatingPointError(f"non-finite loss at step {step}")
                    loss.backward()
                    optimizer.step()
                    step += 1

                    now = time.perf_counter()
                    if args.eval_every_seconds > 0 and now - last_eval >= args.eval_every_seconds:
                        last_eval = now
                        metrics = evaluate_now()
                        history.append({"step": step, "loss": float(loss.item()),
                                        "valid": metrics, "elapsed_seconds": now - started,
                                        "lr": optimizer.param_groups[0]["lr"]})
                        if float(metrics["MRR"]) > best_mrr:
                            best_mrr, best_step = float(metrics["MRR"]), step

    alpha = None
    if model.sratm is not None:
        a = model.alpha.detach().cpu()
        alpha = {"mode": args.residual, "mean": float(a.mean()), "abs_mean": float(a.abs().mean()),
                 "min": float(a.min()), "max": float(a.max())}

    result = {
        "status": "COMPLETE",
        "campaign": "SEALED_RESIDUAL_1VSALL",
        "arm": {"none": "A_backbone_only", "scalar": "B_global_scale",
                "per_relation": "C_per_relation_scale"}[args.residual],
        "stop_reason": stopped, "steps": step, "seed": args.seed,
        "elapsed_seconds": time.perf_counter() - started,
        "best_valid_mrr": None if best_step is None else best_mrr,
        "best_valid_step": best_step,
        "learned_alpha": alpha,
        "backbone": {"path": str(args.backbone), "sha256": sha256(args.backbone), "frozen": True},
        "residual_expert": None if args.sratm_checkpoint is None else {
            "path": str(args.sratm_checkpoint), "sha256": sratm_sha,
            "frozen": bool(args.freeze_sratm)},
        "trainable_parameter_count": sum(p.numel() for p in model.parameters() if p.requires_grad),
        "history": history,
        "config": {k: (str(v) if isinstance(v, Path) else v) for k, v in vars(args).items()},
        "negative_sampling": "NONE_EXACT_1_VS_ALL",
        "loss_truth_source": truth.provenance,
        "dataset": {"test": "NOT_READ_NOT_HASHED_NOT_OPENED"},
        "scientific_status": "EMPIRICAL_SEALED_NO_TEST_NO_SOTA_CLAIM",
    }
    (args.out_dir / "residual_result.json").write_text(
        json.dumps(result, indent=2, default=str) + "\n", encoding="utf-8")
    return result


def main() -> None:
    print(json.dumps(run(build_parser().parse_args()), indent=2, default=str))


if __name__ == "__main__":
    main()
