"""Gate 13.4 (``campaigns/gate13/``): real-run compression certification
over a frozen checkpoint.

Builds ``F_ref`` (the checkpoint's own trained path reasoner, uncompressed
— i.e. its projector as actually trained, normally ``proj_rank=0``) and
``F_cmp`` (the SAME weights — entity/relation embeddings, ``mu``/``U``/
``V``/``W``, router gates — with a projector ADDED post-hoc at
``--certification_proj_rank``, never independently retrained, per the
mission brief's own instruction) from ONE checkpoint, then certifies
``F_cmp``'s real query rankings against ``F_ref`` as ground truth, using
the multi-hop bound recurrence (``certified_path.py``) and the
state-to-score/ranking chain (``certification.py``'s ``certify_path_query``).

Frozen scope for this campaign (``campaigns/gate13/preregistration.md``
§2): ``path_backend=batched``, ``path_selector_mode in
{full_neighborhood, budgeted_bfs}`` — ``learned_topk`` is explicitly
rejected (checked against the checkpoint's own saved args, before any
dataset load or model construction, same fail-fast precedent as Gate
13.2b/13.3b).
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any, Dict, List

import torch

from . import reproducibility as repro
from .certification import certify_path_query, coverage_report
from .certified_bounds import GATE1_TOLERANCE
from .certified_path import propagate_certified_state_bounds
from .data import load_knowledge_graph
from .frontier_ops import build_csr_adjacency
from .reasoner import Adjacency
from .run_attribution import _rebuild_model

BOUND_FORMULA_VERSION = "gate13.4-v1"


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    p.add_argument("--checkpoint", required=True)
    p.add_argument("--train", required=True)
    p.add_argument("--valid", required=True)
    p.add_argument("--test", required=True)
    p.add_argument("--out_dir", required=True)
    p.add_argument("--certification_split", choices=["valid", "test"], default="valid")
    p.add_argument("--certification_max_queries", type=int, default=100)
    p.add_argument("--certification_proj_rank", type=int, required=True, help="F_cmp's post-hoc compression rank (must be < dim)")
    p.add_argument("--certification_seed", type=int, default=13)
    p.add_argument("--cpu", action="store_true")
    return p


def _build_ref_and_cmp(ckpt_args: Dict[str, Any], ckpt_model_state: Dict[str, Any], kg, proj_rank: int, device: torch.device, seed: int):
    ref = _rebuild_model(ckpt_args, kg).to(device)
    ref.load_state_dict(ckpt_model_state)
    ref.eval()

    cmp_args = dict(ckpt_args, path_proj_rank=proj_rank)
    # Deterministic re-execution requires this: StiefelProjector.__init__
    # draws its "raw" parameter from the ambient (unseeded-here) torch RNG
    # state, so two runs of this exact CLI command would otherwise pick a
    # DIFFERENT random compression subspace each time — silently breaking
    # reproducibility (caught during real-run testing: re-running the same
    # command gave a different certified-query count, and once a false
    # certificate, purely from this un-seeded construction).
    torch.manual_seed(seed)
    cmp = _rebuild_model(cmp_args, kg).to(device)
    cmp_sd = cmp.state_dict()
    for k in ckpt_model_state:
        if k in cmp_sd:
            cmp_sd[k] = ckpt_model_state[k]
    # keys present only in cmp (the new projector's own "raw" parameter)
    # keep their fresh (but now seeded, reproducible) random init — never
    # trained, never copied from ref.
    cmp.load_state_dict(cmp_sd)
    cmp.eval()
    return ref, cmp


def run_certification(args: argparse.Namespace) -> Dict[str, Any]:
    if args.certification_proj_rank <= 0:
        raise ValueError("--certification_proj_rank must be > 0 (0 would mean no compression at all, i.e. F_cmp == F_ref)")

    device = torch.device("cpu" if args.cpu or not torch.cuda.is_available() else "cuda")
    out_dir = Path(args.out_dir) / "certification"
    repro.ensure_dir(out_dir)

    ckpt = repro.load_checkpoint(args.checkpoint)
    ckpt_args = ckpt["args"]
    if not ckpt_args.get("enable_path"):
        raise ValueError("checkpoint was not trained with --enable_path — nothing for Gate 13.4 to certify")
    if ckpt_args.get("path_backend", "legacy") != "batched":
        raise NotImplementedError(
            "Gate 13.4 certification requires path_backend=batched (frozen scope, campaigns/gate13/preregistration.md §2) "
            f"— checkpoint was trained with path_backend={ckpt_args.get('path_backend', 'legacy')!r}"
        )
    if ckpt_args.get("path_selector_mode") == "learned_topk":
        raise NotImplementedError(
            "NOT_CERTIFIED_SELECTOR_UNSUPPORTED: Gate 13.4 does not certify learned_topk — its edge selection "
            "depends on message-derived scores, which the certified bounds here do not yet cover."
        )
    if ckpt_args["dim"] <= args.certification_proj_rank:
        raise ValueError(f"--certification_proj_rank ({args.certification_proj_rank}) must be < model dim ({ckpt_args['dim']})")
    if ckpt_args.get("path_proj_rank", 0) != 0:
        raise ValueError(
            "Gate 13.4 requires the checkpoint to have been trained WITHOUT a projector (path_proj_rank=0) so "
            "F_ref is genuinely the uncompressed reference — this checkpoint was trained with "
            f"path_proj_rank={ckpt_args.get('path_proj_rank')}"
        )

    kg = load_knowledge_graph(args.train, args.valid, args.test)
    ref, cmp = _build_ref_and_cmp(ckpt_args, ckpt["model_state"], kg, args.certification_proj_rank, device, args.certification_seed)

    legacy_adjacency = Adjacency.build(kg)
    csr = build_csr_adjacency(legacy_adjacency, kg.num_entities).to(device)

    split = kg.valid if args.certification_split == "valid" else kg.test
    sample = split[: args.certification_max_queries] if len(split) > args.certification_max_queries else split
    if not sample:
        raise ValueError(f"--certification_split {args.certification_split} has no queries in this dataset")
    h_ids = torch.tensor([t[0] for t in sample], device=device)
    r_ids = torch.tensor([t[1] for t in sample], device=device)
    t_ids = torch.tensor([t[2] for t in sample], device=device)
    query_vecs = cmp.relation(r_ids)

    # Identifies EXACTLY which (h,r,t) triples were certified, independent of
    # dataset_hashes (which only identifies the split files) and of
    # certification_max_queries (which only identifies the count) — needed to
    # tell apart two runs over the same split with different sampling.
    query_subset_hash = repro.sha256_bytes(
        json.dumps([list(t) for t in sample], sort_keys=False).encode("utf-8")
    )

    # Projector "raw" param is the ONLY randomly-initialized, never-trained
    # state in F_cmp (see _build_ref_and_cmp's manual_seed comment) — hashed
    # separately from checkpoint_sha256 (which covers F_ref's trained
    # weights only) so a silent change in the seeded compression subspace
    # is independently auditable.
    projector = cmp.path_reasoner.projector
    if projector.enabled:
        projector_state_sha256 = repro.sha256_bytes(projector.raw.detach().cpu().numpy().tobytes())
    else:
        projector_state_sha256 = None

    bounds, ledger, closure_terms = propagate_certified_state_bounds(
        cmp.path_reasoner, csr, cmp.relation.weight, h_ids, r_ids, t_ids, query_vecs, args.certification_seed, training=False,
    )
    with torch.no_grad():
        gamma = cmp.gate_g_max * torch.tanh(cmp.gamma_raw(r_ids).squeeze(-1))  # [num_queries], SIGNED
        candidates = torch.arange(kg.num_entities, device=device).unsqueeze(0).expand(len(sample), -1)
        scores_cmp = cmp.score_tail_candidates(h_ids, r_ids, candidates, csr, args.certification_seed, training=False, gold_tail_ids=t_ids)
        scores_ref = ref.score_tail_candidates(h_ids, r_ids, candidates, csr, args.certification_seed, training=False, gold_tail_ids=t_ids)

    query_certificates: List[Dict[str, Any]] = []
    bound_vs_observed: List[Dict[str, Any]] = []
    failures: List[Dict[str, Any]] = []
    results = []
    false_certificates = 0
    for qi in range(len(sample)):
        gold = int(t_ids[qi].item())
        bound = bounds.get((qi, gold))
        try:
            result = certify_path_query(qi, scores_cmp[qi], gold, bound, float(gamma[qi].item()), cmp.entity.weight, ckpt_args["dim"])
        except Exception as exc:  # recorded, never silently swallowed
            failures.append({"query_id": qi, "stage": "certify_path_query", "error": repr(exc)})
            continue
        results.append(result)

        observed_state_error = None
        observed_ratio = None
        if bound is not None:
            observed_state_error = abs(float((scores_ref[qi, gold] - scores_cmp[qi, gold]).item()))
            observed_ratio = observed_state_error / bound.value if bound.value > 0 else None
            bound_vs_observed.append({
                "query_id": qi, "bound": bound.value, "observed_score_gap": observed_state_error, "ratio": observed_ratio,
                "certified": result.certified_rank_stable,
            })

        if result.certified_rank_stable:
            ref_rank = int((scores_ref[qi] > scores_ref[qi, gold]).sum().item())
            cmp_rank = int((scores_cmp[qi] > scores_cmp[qi, gold]).sum().item())
            if ref_rank != cmp_rank:
                false_certificates += 1
        query_certificates.append({
            "query_id": qi, **result.to_dict(), "gamma_r": float(gamma[qi].item()), "observed_ratio": observed_ratio,
        })

    coverage = coverage_report(results)
    ranking_margins = [{"query_id": r.query_id, "margin": r.ranking_margin, "certified": r.certified_rank_stable} for r in results]
    node_hop_bounds = [b.to_dict() for b in ledger]
    local_bounds = [
        {"component": name, "value": bound_obj.value, "formula": bound_obj.formula, "valid": bound_obj.valid()}
        for name, bound_obj in (
            ("rho_mu", closure_terms.mu), ("rho_U", closure_terms.residual_U),
            ("rho_V", closure_terms.residual_V), ("rho_W", closure_terms.residual_W),
            ("rho_message", closure_terms.total),
        )
    ]

    for rec in query_certificates:
        repro.append_jsonl(rec, out_dir / "query_certificates.jsonl")
    for rec in node_hop_bounds:
        repro.append_jsonl(rec, out_dir / "node_hop_bounds.jsonl")
    for rec in ranking_margins:
        repro.append_jsonl(rec, out_dir / "ranking_margins.jsonl")
    for rec in local_bounds:
        repro.append_jsonl(rec, out_dir / "local_bounds.jsonl")
    for rec in failures:
        repro.append_jsonl(rec, out_dir / "certification_failures.jsonl")

    bound_vs_observed_path = out_dir / "bound_vs_observed.csv"
    with bound_vs_observed_path.open("w", encoding="utf-8") as f:
        f.write("query_id,bound,observed_score_gap,ratio,certified\n")
        for rec in bound_vs_observed:
            f.write(f"{rec['query_id']},{rec['bound']},{rec['observed_score_gap']},{rec['ratio']},{rec['certified']}\n")

    coverage_summary = {**coverage, "false_certificates": false_certificates, "certification_proj_rank": args.certification_proj_rank}
    repro.save_json(coverage_summary, out_dir / "coverage_summary.json")

    max_ratio = max((rec["ratio"] for rec in bound_vs_observed if rec["ratio"] is not None), default=None)
    commit_sha = repro.git_manifest(Path(__file__).resolve().parent).get("commit")
    manifest = {
        "model_commit": commit_sha,
        "commit_sha": commit_sha,  # exact field name required by the campaign run-record contract
        "checkpoint_path": str(args.checkpoint),
        "checkpoint_sha256": repro.sha256_file(args.checkpoint),
        "projector_state_sha256": projector_state_sha256,
        "dataset_hashes": {
            "train": repro.sha256_file(args.train), "valid": repro.sha256_file(args.valid), "test": repro.sha256_file(args.test),
        },
        "query_subset_hash": query_subset_hash,
        "reference_rank": ckpt_args.get("path_proj_rank", 0),
        "compressed_rank": args.certification_proj_rank,
        "projector_rank": args.certification_proj_rank,  # exact field name required by the campaign run-record contract
        "dim": ckpt_args["dim"],
        "path_backend": ckpt_args.get("path_backend", "legacy"),
        "selector_mode": ckpt_args.get("path_selector_mode"),
        "dtype": "float32",
        "seed": args.certification_seed,
        "projector_seed": args.certification_seed,  # exact field name required by the campaign run-record contract; the same seed gates the projector's torch.manual_seed in _build_ref_and_cmp
        "gate_g_max": cmp.gate_g_max,
        "layernorm_eps": float(cmp.path_reasoner.ln.eps),
        "gate1_tolerance": GATE1_TOLERANCE,
        "bound_formula_version": BOUND_FORMULA_VERSION,
        "numeric_tolerances": {"fp32_reconstruction": 1e-5, "gate1_tolerance": GATE1_TOLERANCE},
        "coverage": coverage_summary,
        "max_observed_over_bound_ratio": max_ratio,
    }
    repro.save_json(manifest, out_dir / "certification_manifest.json")

    assumption_checks = [c.to_dict() for c in (results[0].assumption_checks if results else [])]
    repro.save_json({"assumption_checks": assumption_checks}, out_dir / "assumption_checks.json")
    repro.save_json({"false_certificates": false_certificates, "total_certified": sum(r.certified_rank_stable for r in results)}, out_dir / "false_certificate_audit.json")

    return {
        "coverage": coverage_summary, "manifest": manifest, "num_queries": len(sample),
        "false_certificates": false_certificates,
    }


def main() -> None:
    args = build_parser().parse_args()
    result = run_certification(args)
    print(result)


if __name__ == "__main__":
    main()
