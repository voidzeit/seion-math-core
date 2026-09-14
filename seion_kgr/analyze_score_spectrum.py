"""Streaming relation-wise score-spectrum and adaptive-rank oracle analysis."""

from __future__ import annotations

import argparse
import json
import math
from pathlib import Path
from typing import Any

import numpy as np
import torch

from . import reproducibility as repro
from .data import KnowledgeGraph, load_knowledge_graph
from .score_space import (
    CandidateWhitening,
    grassmann_chordal_distance,
    prefix_lagrangian_allocation,
    spectral_waterfill,
)
from .ttn_branching import BranchingTTNK3


def parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--checkpoint", type=Path, required=True)
    p.add_argument("--train", default="data/FB15K-237/train.txt")
    p.add_argument("--valid", default="data/FB15K-237/valid.txt")
    p.add_argument("--test", default="data/FB15K-237/test.txt")
    p.add_argument("--out", type=Path, required=True)
    p.add_argument("--batch-size", type=int, default=16384)
    p.add_argument("--max-vram-gb", type=float, default=23.0)
    p.add_argument("--energy-targets", default="0.9,0.99,0.999")
    p.add_argument("--tolerances", default="0.1,0.01,0.001,0.0001")
    p.add_argument("--grassmann-rank", type=int, default=3)
    p.add_argument("--cpu", action="store_true")
    return p


def _device(args: argparse.Namespace) -> torch.device:
    if args.cpu or not torch.cuda.is_available():
        return torch.device("cpu")
    total = torch.cuda.get_device_properties(0).total_memory
    if total > args.max_vram_gb * (1024**3):
        torch.cuda.set_per_process_memory_fraction(
            min(0.98, args.max_vram_gb * (1024**3) / total), device=0
        )
    return torch.device("cuda")


def _load_model(checkpoint: Path, kg: KnowledgeGraph, device: torch.device) -> BranchingTTNK3:
    state = torch.load(checkpoint, map_location=device)
    model = BranchingTTNK3(
        kg.num_entities,
        kg.num_relations_total,
        int(state["dim"]),
        int(state["branch_dim"]),
    ).to(device)
    model.load_state_dict(state["model_state"])
    model.eval()
    model.set_mode("full")
    return model


@torch.inference_mode()
def _relation_gram(
    model: BranchingTTNK3,
    triples: np.ndarray,
    relation_id: int,
    device: torch.device,
    batch_size: int,
) -> torch.Tensor:
    rows = triples[triples[:, 1] == relation_id]
    gram = torch.zeros((model.dim, model.dim), device=device, dtype=model.root.dtype)
    for start in range(0, len(rows), batch_size):
        batch = torch.from_numpy(rows[start : start + batch_size]).to(device=device, dtype=torch.long)
        z = model.query_representation(batch[:, 0], batch[:, 1])
        gram.add_(z.T @ z)
    return (gram + gram.T) * 0.5


def _sqrt_psd(matrix: torch.Tensor) -> torch.Tensor:
    values, vectors = torch.linalg.eigh((matrix + matrix.T) * 0.5)
    values = values.clamp_min(0.0)
    return (vectors * values.sqrt().unsqueeze(0)) @ vectors.T


def _rank_for_energy(eigenvalues: list[float], target: float) -> int:
    total = max(sum(eigenvalues), 1e-30)
    cumulative = 0.0
    for rank, value in enumerate(eigenvalues, start=1):
        cumulative += value
        if cumulative / total >= target:
            return rank
    return len(eigenvalues)


def _summary(values: list[float]) -> dict[str, float]:
    if not values:
        return {"min": 0.0, "p25": 0.0, "median": 0.0, "p75": 0.0, "p90": 0.0, "max": 0.0, "mean": 0.0}
    quantiles = np.quantile(np.asarray(values, dtype=np.float64), [0.0, 0.25, 0.5, 0.75, 0.9, 1.0])
    return {
        "min": float(quantiles[0]),
        "p25": float(quantiles[1]),
        "median": float(quantiles[2]),
        "p75": float(quantiles[3]),
        "p90": float(quantiles[4]),
        "max": float(quantiles[5]),
        "mean": float(np.mean(values)),
    }


def _waterfill(
    eigenvalues: list[list[float]],
    probabilities: list[float],
    tolerance: float,
) -> tuple[list[int] | None, float | None, float | None]:
    """Compatibility wrapper over the shared exact linear-cost allocator."""

    result = spectral_waterfill(
        torch.as_tensor(eigenvalues, dtype=torch.float64),
        tolerance_squared=tolerance,
        probabilities=torch.as_tensor(probabilities, dtype=torch.float64),
        min_rank=1,
    )
    if not result["feasible"]:
        return None, None, None
    ranks = list(result["ranks"])
    expected_cost = sum(float(p) * int(rank) for p, rank in zip(probabilities, ranks))
    return ranks, expected_cost, float(result["weighted_residual"])


def main() -> None:
    args = parser().parse_args()
    if args.batch_size <= 0 or args.max_vram_gb <= 0:
        raise ValueError("batch-size and max-vram-gb must be positive")
    device = _device(args)
    kg = load_knowledge_graph(args.train, args.valid, args.test)
    model = _load_model(args.checkpoint, kg, device)
    forward_train = kg.train[kg.train[:, 1] < kg.num_relations_original]
    relation_counts = np.bincount(
        forward_train[:, 1], minlength=kg.num_relations_original
    ).astype(np.float64)
    probabilities = (relation_counts / max(float(relation_counts.sum()), 1.0)).tolist()

    entity = model.entity.weight.detach()
    whitening = CandidateWhitening.fit(entity)
    sqrt_entity = whitening.sqrt.to(device=device, dtype=entity.dtype)
    relation_records: list[dict[str, Any]] = []
    spectra: list[list[float]] = []
    score_grams: list[torch.Tensor] = []
    global_hessian = torch.zeros((model.dim, model.dim), device=device, dtype=model.root.dtype)
    grassmann_bases: list[torch.Tensor] = []
    projector_bases: list[torch.Tensor] = []
    if args.grassmann_rank <= 0 or args.grassmann_rank > model.dim:
        raise ValueError("grassmann-rank must lie in [1, dim]")
    for relation_id in range(kg.num_relations_original):
        gram_query = _relation_gram(model, forward_train, relation_id, device, args.batch_size)
        score_gram = sqrt_entity @ gram_query @ sqrt_entity
        score_gram = (score_gram + score_gram.T) * 0.5
        global_hessian.add_(score_gram, alpha=float(probabilities[relation_id]))
        score_grams.append(score_gram.detach().cpu().to(dtype=torch.float64))
        eigenvalues, eigenvectors = torch.linalg.eigh((score_gram + score_gram.T) * 0.5)
        order = torch.argsort(eigenvalues, descending=True)
        eigenvalues = eigenvalues[order].clamp_min(0.0)
        eigenvectors = eigenvectors[:, order]
        values = [float(value) for value in eigenvalues.detach().cpu()]
        spectra.append(values)
        projector_bases.append(eigenvectors.detach().cpu().to(dtype=torch.float32))
        grassmann_bases.append(eigenvectors[:, : args.grassmann_rank].detach().cpu())
        score_energy = max(sum(values), 1e-30)
        probabilities_spectrum = np.asarray(values, dtype=np.float64) / score_energy
        effective_rank = float(np.exp(-(probabilities_spectrum * np.log(np.maximum(probabilities_spectrum, 1e-30))).sum()))
        relation_records.append({
            "relation_id": relation_id,
            "relation_name": next((name for name, idx in kg.rel2id.items() if idx == relation_id), str(relation_id)),
            "train_frequency": int(relation_counts[relation_id]),
            "probability": probabilities[relation_id],
            "score_eigenvalues": values,
            "score_energy": float(sum(values)),
            "effective_rank": effective_rank,
            "rank_at_energy": {
                str(target): _rank_for_energy(values, target)
                for target in (float(value) for value in args.energy_targets.split(","))
            },
        })

    grassmann_distances = torch.zeros(
        (kg.num_relations_original, kg.num_relations_original), dtype=torch.float64
    )
    for left in range(kg.num_relations_original):
        for right in range(left + 1, kg.num_relations_original):
            distance = grassmann_chordal_distance(grassmann_bases[left], grassmann_bases[right])
            grassmann_distances[left, right] = distance
            grassmann_distances[right, left] = distance
    upper = grassmann_distances[torch.triu_indices(kg.num_relations_original, kg.num_relations_original, 1).unbind()]
    grassmann_summary = _summary([float(value) for value in upper.tolist()])

    global_values, global_vectors = torch.linalg.eigh((global_hessian + global_hessian.T) * 0.5)
    global_order = torch.argsort(global_values, descending=True)
    global_values = global_values[global_order].clamp_min(0.0)
    global_basis = global_vectors[:, global_order].detach().cpu().to(dtype=torch.float64)
    shared_spectra: list[list[float]] = []
    for record, score_gram in zip(relation_records, score_grams):
        shared_modes = torch.diagonal(global_basis.T @ score_gram @ global_basis).clamp_min(0.0)
        shared_values = [float(value) for value in shared_modes.tolist()]
        shared_spectra.append(shared_values)
        shared_energy = max(sum(shared_values), 1e-30)
        shared_probabilities = np.asarray(shared_values, dtype=np.float64) / shared_energy
        record["shared_basis_effective_rank"] = float(
            np.exp(-(shared_probabilities * np.log(np.maximum(shared_probabilities, 1e-30))).sum())
        )
        record["shared_basis_rank_at_energy"] = {
            str(target): _rank_for_energy(shared_values, target)
            for target in (float(value) for value in args.energy_targets.split(","))
        }

    tolerances = [float(value) for value in args.tolerances.split(",")]
    allocation_summary = []
    shared_allocation_summary = []
    uniform_spectra = [
        sum(p * sum(values[rank:]) for p, values in zip(probabilities, spectra))
        for rank in range(model.dim + 1)
    ]
    for tolerance in tolerances:
        uniform_rank = next(
            (rank for rank, error in enumerate(uniform_spectra) if error <= tolerance),
            None,
        )
        ranks, spectral_cost, spectral_error = _waterfill(spectra, probabilities, tolerance)
        uniform_cost = None if uniform_rank is None else float(uniform_rank)
        allocation_summary.append({
            "tolerance": tolerance,
            "uniform_rank": uniform_rank,
            "uniform_average_rank": uniform_cost,
            "uniform_weighted_score_residual": None if uniform_rank is None else uniform_spectra[uniform_rank],
            "spectral_ranks": ranks,
            "spectral_average_rank": spectral_cost,
            "spectral_weighted_score_residual": spectral_error,
            "G_spectral": None if uniform_cost is None or spectral_cost is None else uniform_cost / spectral_cost,
            "spectral_rank_quantiles": None if ranks is None else _summary([float(rank) for rank in ranks]),
        })
        shared_uniform_spectra = [
            sum(p * sum(values[rank:]) for p, values in zip(probabilities, shared_spectra))
            for rank in range(model.dim + 1)
        ]
        shared_uniform_rank = next(
            (rank for rank, error in enumerate(shared_uniform_spectra) if error <= tolerance),
            None,
        )
        shared_result = prefix_lagrangian_allocation(
            torch.as_tensor(shared_spectra, dtype=torch.float64),
            tolerance_squared=tolerance,
            probabilities=torch.as_tensor(probabilities, dtype=torch.float64),
            min_rank=1,
        )
        shared_ranks = shared_result["ranks"] if shared_result["feasible"] else None
        shared_cost = shared_result["cost"] if shared_result["feasible"] else None
        shared_error = shared_result["weighted_residual"] if shared_result["feasible"] else None
        shared_uniform_cost = None if shared_uniform_rank is None else float(shared_uniform_rank)
        shared_allocation_summary.append({
            "tolerance": tolerance,
            "uniform_rank": shared_uniform_rank,
            "uniform_average_rank": shared_uniform_cost,
            "uniform_weighted_score_residual": None if shared_uniform_rank is None else shared_uniform_spectra[shared_uniform_rank],
            "shared_spectral_ranks": shared_ranks,
            "shared_spectral_average_rank": shared_cost,
            "shared_spectral_weighted_score_residual": shared_error,
            "G_shared_spectral": None if shared_uniform_cost is None or shared_cost is None else shared_uniform_cost / shared_cost,
        })

    peak_allocated = int(torch.cuda.max_memory_allocated(device)) if device.type == "cuda" else None
    peak_reserved = int(torch.cuda.max_memory_reserved(device)) if device.type == "cuda" else None
    output = {
        "status": "SCORE_SPACE_RELATION_SPECTRUM_COMPLETE",
        "device": str(device),
        "checkpoint": str(args.checkpoint),
        "dataset": "FB15K-237",
        "relation_scope": "original_forward_train_triples_only",
        "num_entities": kg.num_entities,
        "num_relations_original": kg.num_relations_original,
        "dim": model.dim,
        "batch_size": args.batch_size,
        "max_vram_gb": args.max_vram_gb,
        "peak_allocated_bytes": peak_allocated,
        "peak_reserved_bytes": peak_reserved,
        "gram_definition": "H_rho = G_E^(1/2) G_Zrho G_E^(1/2), eigenvalues=squared score singular values",
        "candidate_whitening": {
            "exact": whitening.exact,
            "ridge": whitening.ridge,
            "support_rank": whitening.support_rank,
            "projector_realizable": True,
        },
        "projector_cache": str(args.out.with_suffix(".projectors.pt")),
        "relation_records": relation_records,
        "effective_rank_summary": _summary([record["effective_rank"] for record in relation_records]),
        "shared_basis_effective_rank_summary": _summary([record["shared_basis_effective_rank"] for record in relation_records]),
        "global_score_eigenvalues": [float(value) for value in global_values.detach().cpu().tolist()],
        "shared_basis": global_basis.tolist(),
        "grassmann_rank": args.grassmann_rank,
        "grassmann_distance_summary": grassmann_summary,
        "grassmann_distance_matrix": grassmann_distances.tolist(),
        "allocation_summary": allocation_summary,
        "shared_allocation_summary": shared_allocation_summary,
        "limitations": [
            "The score spectrum is an exact Frobenius oracle for the sampled train query rows and all stored entity embeddings, not a ranking certificate.",
            "Spectral allocations are diagnostic opportunity bounds; they are not yet an executable certified allocator.",
            "Relation-specific routing and cross-relation parameter sharing remain future architecture work.",
        ],
    }
    args.out.parent.mkdir(parents=True, exist_ok=True)
    torch.save(
        {
            "relation_bases": torch.stack(projector_bases),
            "global_basis": global_basis.to(dtype=torch.float32),
            "relation_ids": torch.arange(kg.num_relations_original, dtype=torch.long),
        },
        args.out.with_suffix(".projectors.pt"),
    )
    repro.save_json(output, args.out)
    print(json.dumps({"out": str(args.out), "device": str(device), "relations": len(relation_records)}, sort_keys=True))


if __name__ == "__main__":
    main()
