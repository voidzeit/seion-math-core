"""Gate 13.3b (``campaigns/gate13/``): real-run attribution pipeline over a
frozen checkpoint.

Runs as a SEPARATE pass, never during training (unlike
``gate_diagnostics.jsonl``, which samples cheaply every eval epoch): loads
a checkpoint, reconstructs the exact model it was trained as (from the
checkpoint's own saved ``args``), and computes telescoping/Shapley/
rank-flip attribution over real queries from a real dataset split, writing
the artifact set under ``<out_dir>/attribution/``.

**Coalition semantics are frozen and versioned** (``coalition_semantics_version
= "gate13-v1"``) — the SAME definition is used everywhere in this file and
in ``attribution.py``/``module_graph.py``, never redefined per call site:

======================  ==========================================
module                  what "absent from the coalition" means
======================  ==========================================
mu, residual            output replaced with exact ZERO
projector               bypassed (IDENTITY on whatever's summed so far)
path, seion, kernel     branch's gated score contribution is ZERO
======================  ==========================================

**Raw vs effective, never conflated:** path-internal attribution is
computed on the RAW (pre-router-gate) score (see ``attribution.py``'s
``path_internal_score`` docstring for why — the gate would otherwise mask
everything at an under-trained gate). This file reports BOTH
``raw_contribution`` and ``effective_contribution = gate_value *
raw_contribution`` for every path-internal record, so a reader is never
left assuming one is the other. Branch-level records only have
``effective_contribution`` (there is no "raw" branch score independent of
its own gate to report at that granularity — the branch's OWN internal
composition, if it has one, is exactly what path-internal attribution is
for).

**``--attribution_mode {fixed_trace,end_to_end}``:** for the currently
supported selector modes (``full_neighborhood``, ``budgeted_bfs``), which
edges get explored does NOT depend on which message components are
ablated (selection uses only graph structure and a fixed RNG seed, never
message-derived scores) — so both modes provably coincide today,
verified (not merely assumed) by
``tests/kgr/test_attribution_real_run.py``. The flag exists for interface
completeness and to not silently break once ``learned_topk`` (whose edge
selection DOES depend on message-derived scores, and is therefore
genuinely mode-sensitive) is supported by a batched backend — until then,
``learned_topk`` is explicitly rejected here, matching Gate 13.2b's own
explicit-rejection precedent.
"""
from __future__ import annotations

import argparse
from pathlib import Path
from typing import Any, Dict, List

import torch

from . import reproducibility as repro
from .attribution import (
    branch_level_telescoping,
    path_internal_shapley,
    path_internal_telescoping,
    rank_flip_attribution,
)
from .data import KnowledgeGraph, load_knowledge_graph
from .frontier_ops import build_csr_adjacency
from .model import SeionKGRv26
from .module_graph import BRANCH_MODULES, PATH_INTERNAL_MODULES
from .reasoner import Adjacency
from .structural_kernel import StructuralKernelResidual, build_kernel, load_e8_info, load_e8_kernel

COALITION_SEMANTICS_VERSION = "gate13-v1"
COALITION_SEMANTICS = {
    "mu": "zero", "residual": "zero", "projector": "identity",
    "path": "zero", "seion": "zero", "structural_kernel": "zero",
}
_BRANCH_ENABLE_ATTR = {"path": "enable_path", "seion": "enable_seion", "structural_kernel": "enable_structural_kernel"}


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    p.add_argument("--checkpoint", required=True)
    p.add_argument("--train", required=True)
    p.add_argument("--valid", required=True)
    p.add_argument("--test", required=True)
    p.add_argument("--out_dir", required=True)
    p.add_argument("--attribution_split", choices=["valid", "test"], default="valid")
    p.add_argument("--attribution_mode", choices=["fixed_trace", "end_to_end"], default="end_to_end")
    p.add_argument("--attribution_max_queries", type=int, default=100)
    p.add_argument(
        "--attribution_shapley_samples", type=int, default=0,
        help="0 = full enumeration (both module sets here have <=3 members, i.e. <=6 permutations)",
    )
    p.add_argument("--attribution_seed", type=int, default=13)
    p.add_argument("--attribution_include_branches", action="store_true", default=True)
    p.add_argument("--no_attribution_include_branches", dest="attribution_include_branches", action="store_false")
    p.add_argument("--attribution_include_path_internal", action="store_true", default=True)
    p.add_argument("--no_attribution_include_path_internal", dest="attribution_include_path_internal", action="store_false")
    p.add_argument("--cpu", action="store_true")
    return p


def _rebuild_model(ckpt_args: Dict[str, Any], kg: KnowledgeGraph) -> SeionKGRv26:
    """Reconstructs the exact architecture a checkpoint was trained as,
    from its own saved ``args`` — never from freshly-supplied CLI flags,
    so attribution can never silently run against a mismatched
    architecture."""
    structural_kernel = None
    if ckpt_args.get("structural_kernel_variant", "none") != "none":
        variant = ckpt_args["structural_kernel_variant"]
        needs_real_e8 = variant in ("E8_exact", "permuted_indices", "sign_shuffled")
        e8_kernel = load_e8_kernel() if needs_real_e8 else None
        e8_info = load_e8_info() if variant == "E8_exact" else None
        K, provenance = build_kernel(
            variant, e8_kernel=e8_kernel, dim=ckpt_args["structural_kernel_dim"],
            seed=ckpt_args["structural_kernel_seed"], e8_info=e8_info,
        )
        structural_kernel = StructuralKernelResidual(
            dim=ckpt_args["dim"], K=K, num_relations_total=kg.num_relations_total,
            provenance=provenance, gate_g_max=ckpt_args.get("gate_g_max", 1.0),
        )
    return SeionKGRv26(
        num_entities=kg.num_entities, num_relations_total=kg.num_relations_total, dim=ckpt_args["dim"],
        base_expert=ckpt_args["base_expert"], enable_path=ckpt_args["enable_path"], enable_seion=ckpt_args["enable_seion"],
        seion_rank=ckpt_args["seion_rank"], path_rank=ckpt_args["path_rank"], path_layers=ckpt_args["path_layers"],
        path_max_neighbors=ckpt_args["path_max_neighbors"], path_proj_rank=ckpt_args["path_proj_rank"],
        path_selector_mode=ckpt_args["path_selector_mode"], structural_kernel=structural_kernel,
        gate_g_max=ckpt_args.get("gate_g_max", 1.0), path_backend=ckpt_args.get("path_backend", "legacy"),
    )


def run_attribution(args: argparse.Namespace) -> Dict[str, Any]:
    if not args.attribution_include_branches and not args.attribution_include_path_internal:
        raise ValueError("at least one of --attribution_include_branches/--attribution_include_path_internal must be set")

    device = torch.device("cpu" if args.cpu or not torch.cuda.is_available() else "cuda")
    out_dir = Path(args.out_dir) / "attribution"
    repro.ensure_dir(out_dir)

    ckpt = repro.load_checkpoint(args.checkpoint)
    ckpt_args = ckpt["args"]
    # Explicit rejection BEFORE any dataset load or model construction (same
    # fail-fast precedent as Gate 13.2b's train.py guard) — checked directly
    # against the checkpoint's own saved args, not after reconstructing the
    # model (whose BatchedPathReasoner would raise its own less specific
    # ValueError first otherwise).
    if ckpt_args.get("enable_path") and ckpt_args.get("path_selector_mode") == "learned_topk":
        raise NotImplementedError(
            "Gate 13.3b attribution does not yet support learned_topk — fixed_trace and end_to_end "
            "genuinely differ there (edge selection depends on message-derived scores), unlike the "
            "currently-supported selector modes. See this module's docstring."
        )

    kg = load_knowledge_graph(args.train, args.valid, args.test)
    model = _rebuild_model(ckpt_args, kg).to(device)
    model.load_state_dict(ckpt["model_state"])
    model.eval()

    path_backend = ckpt_args.get("path_backend", "legacy")
    adjacency = None
    if model.enable_path:
        legacy_adjacency = Adjacency.build(kg)
        adjacency = legacy_adjacency if path_backend == "legacy" else build_csr_adjacency(legacy_adjacency, kg.num_entities).to(device)

    split = kg.valid if args.attribution_split == "valid" else kg.test
    sample = split[: args.attribution_max_queries] if len(split) > args.attribution_max_queries else split
    if not sample:
        raise ValueError(f"--attribution_split {args.attribution_split} has no queries in this dataset")
    h_ids = torch.tensor([t[0] for t in sample], device=device)
    r_ids = torch.tensor([t[1] for t in sample], device=device)
    t_ids = torch.tensor([t[2] for t in sample], device=device)

    module_error_records: List[Dict[str, Any]] = []
    shapley_records: List[Dict[str, Any]] = []
    rank_flip_records: List[Dict[str, Any]] = []
    module_interactions: Dict[str, Any] = {}
    failures: List[Dict[str, Any]] = []
    path_internal_included = bool(model.enable_path and args.attribution_include_path_internal)
    enabled_branches: List[str] = []

    if path_internal_included:
        try:
            order = PATH_INTERNAL_MODULES
            tel_forward = path_internal_telescoping(model, h_ids, r_ids, t_ids, adjacency, args.attribution_seed, order)
            tel_backward = path_internal_telescoping(model, h_ids, r_ids, t_ids, adjacency, args.attribution_seed, tuple(reversed(order)))
            shap = path_internal_shapley(model, h_ids, r_ids, t_ids, adjacency, args.attribution_seed)

            with torch.no_grad():
                gamma_path = model.gate_g_max * torch.tanh(model.gamma_raw(r_ids).squeeze(-1))  # [num_queries]
            for qi in range(len(sample)):
                gate_value = float(gamma_path[qi].item())
                for module_id in PATH_INTERNAL_MODULES:
                    raw_delta = float(shap["phi"][module_id][qi].item())
                    module_error_records.append({
                        "query_id": qi, "module_id": f"path.{module_id}",
                        "raw_contribution": raw_delta,
                        "effective_contribution": raw_delta * gate_value,
                        "gate_value": gate_value,
                    })
            for module_id in PATH_INTERNAL_MODULES:
                shapley_records.append({
                    "module_id": f"path.{module_id}",
                    "mean_raw_phi": float(shap["phi"][module_id].mean().item()),
                    "mean_effective_phi": float((shap["phi"][module_id] * gamma_path).mean().item()),
                })
            module_interactions["path_internal"] = {
                "order_forward": list(tel_forward["order"]), "max_reconstruction_error_forward": tel_forward["max_reconstruction_error"],
                "order_backward": list(tel_backward["order"]), "max_reconstruction_error_backward": tel_backward["max_reconstruction_error"],
                "shapley_efficiency_error": shap["efficiency_error"],
            }

            candidates = torch.arange(kg.num_entities, device=device).unsqueeze(0).expand(len(sample), -1)
            for module_id in PATH_INTERNAL_MODULES:
                rank_flip_records.extend(
                    rank_flip_attribution(model, h_ids, r_ids, candidates, t_ids, adjacency, args.attribution_seed, module_id)
                )
        except Exception as exc:  # recorded, never silently swallowed
            failures.append({"stage": "path_internal", "error": repr(exc)})

    if args.attribution_include_branches and any(getattr(model, _BRANCH_ENABLE_ATTR[b]) for b in BRANCH_MODULES):
        try:
            enabled_branches = [b for b in BRANCH_MODULES if getattr(model, _BRANCH_ENABLE_ATTR[b])]
            branch_tel = branch_level_telescoping(model, h_ids, r_ids, t_ids, adjacency, args.attribution_seed, enabled_branches)
            module_interactions["branch_level"] = {
                "order": list(branch_tel["order"]), "max_reconstruction_error": branch_tel["max_reconstruction_error"],
            }
            for module_id in enabled_branches:
                delta = branch_tel["deltas"][module_id]
                for qi in range(len(sample)):
                    module_error_records.append({
                        "query_id": qi, "module_id": module_id,
                        "raw_contribution": None,  # no "raw" concept independent of the branch's own gate at this granularity
                        "effective_contribution": float(delta[qi].item()),
                        "gate_value": None,
                    })
        except Exception as exc:
            failures.append({"stage": "branch_level", "error": repr(exc)})

    for rec in module_error_records:
        repro.append_jsonl(rec, out_dir / "module_error_attribution.jsonl")
    for rec in shapley_records:
        repro.append_jsonl(rec, out_dir / "shapley_attribution.jsonl")
    for rec in rank_flip_records:
        repro.append_jsonl(rec, out_dir / "rank_flip_attribution.jsonl")
    for rec in failures:
        repro.append_jsonl(rec, out_dir / "attribution_failures.jsonl")
    repro.save_json(module_interactions, out_dir / "module_interactions.json")

    summary = {
        "num_queries": len(sample),
        "attribution_split": args.attribution_split,
        "attribution_mode": args.attribution_mode,
        "modules_included": {
            "path_internal": list(PATH_INTERNAL_MODULES) if path_internal_included else [],
            "branch_level": enabled_branches,
        },
        "num_failures": len(failures),
    }
    repro.save_json(summary, out_dir / "attribution_summary.json")

    manifest = {
        "model_commit": repro.git_manifest(Path(__file__).resolve().parent).get("commit"),
        "checkpoint_path": str(args.checkpoint),
        "checkpoint_sha256": repro.sha256_file(args.checkpoint),
        "dataset_hashes": {
            "train": repro.sha256_file(args.train), "valid": repro.sha256_file(args.valid), "test": repro.sha256_file(args.test),
        },
        "path_backend": path_backend,
        "selector_mode": ckpt_args.get("path_selector_mode"),
        "attribution_mode": args.attribution_mode,
        "coalition_semantics_version": COALITION_SEMANTICS_VERSION,
        "coalition_semantics": COALITION_SEMANTICS,
        "shapley_samples": args.attribution_shapley_samples or "full_enumeration",
        "seed": args.attribution_seed,
        "modules": summary["modules_included"],
        "numeric_tolerances": {"fp32_reconstruction": 1e-5},
    }
    repro.save_json(manifest, out_dir / "attribution_manifest.json")
    return {"summary": summary, "manifest": manifest, "module_interactions": module_interactions, "num_failures": len(failures)}


def main() -> None:
    args = build_parser().parse_args()
    result = run_attribution(args)
    print(result)


if __name__ == "__main__":
    main()
