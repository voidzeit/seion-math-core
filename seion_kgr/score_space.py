"""Realizable score-space whitening, spectral projectors, and certificates.

The module keeps three objects separate:

* ``CandidateWhitening`` is an exact change of coordinates when no ridge is
  used and the candidate Gram support is retained.
* ``SpectralProjector`` is the Ky-Fan optimal rank projector for a supplied
  query group in the whitened coordinates.
* allocation and ranking helpers are finite numerical policies; they do not
  upgrade an empirical result to a universal theorem.

All matrix fitting is performed in a stable work dtype. Runtime projection
methods cast the small D-by-D transforms to the input dtype/device, so large
candidate matmuls can still use the selected accelerator dtype.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Sequence

import torch


def _work_dtype(dtype: torch.dtype) -> torch.dtype:
    if dtype in {torch.float16, torch.bfloat16, torch.float32}:
        return torch.float64
    return dtype


@dataclass(frozen=True)
class SpectralProjector:
    """A rank-k orthogonal projector in whitened candidate coordinates."""

    basis: torch.Tensor
    eigenvalues: torch.Tensor
    residual_energy: torch.Tensor
    support_rank: int

    @property
    def rank(self) -> int:
        return int(self.basis.shape[1])

    def matrix(self) -> torch.Tensor:
        return self.basis @ self.basis.transpose(-1, -2)


@dataclass(frozen=True)
class CandidateWhitening:
    """Exact or ridge-regularized candidate-coordinate transform.

    For an entity table ``E`` with rows as candidate vectors, the exact
    transform satisfies ``z @ E.T == (z @ sqrt) @ (E @ inv_sqrt).T`` on the
    support of ``E.T @ E``. Projectors must be contained in
    ``support_projector`` when the Gram is singular.
    """

    sqrt: torch.Tensor
    inv_sqrt: torch.Tensor
    support_projector: torch.Tensor
    eigenvalues: torch.Tensor
    support_rank: int
    ridge: float
    relative_tolerance: float

    @classmethod
    @torch.no_grad()
    def fit(
        cls,
        entity_table: torch.Tensor,
        *,
        relative_tolerance: float = 1e-10,
        ridge: float = 0.0,
    ) -> "CandidateWhitening":
        if entity_table.ndim != 2 or entity_table.shape[0] == 0:
            raise ValueError("entity_table must have shape [num_entities, dim]")
        if not entity_table.is_floating_point():
            raise TypeError("entity_table must be floating point")
        if relative_tolerance < 0 or ridge < 0:
            raise ValueError("relative_tolerance and ridge must be nonnegative")
        dtype = _work_dtype(entity_table.dtype)
        table = entity_table.to(dtype=dtype)
        gram = table.transpose(0, 1) @ table
        values, vectors = torch.linalg.eigh(gram)
        scale = float(values.abs().max().item()) if values.numel() else 0.0
        threshold = max(scale * relative_tolerance, torch.finfo(dtype).eps * max(scale, 1.0))
        positive = values > threshold
        if ridge > 0:
            effective = values.clamp_min(0) + ridge
            support = torch.ones_like(values, dtype=torch.bool)
            inv_values = effective.rsqrt()
            sqrt_values = effective.sqrt()
        else:
            effective = values.clamp_min(0)
            support = positive
            sqrt_values = torch.where(support, effective.sqrt(), torch.zeros_like(effective))
            inv_values = torch.where(support, effective.rsqrt(), torch.zeros_like(effective))
        support_matrix = (vectors * support.to(dtype)).matmul(vectors.transpose(0, 1))
        sqrt = (vectors * sqrt_values.to(dtype)).matmul(vectors.transpose(0, 1))
        inv_sqrt = (vectors * inv_values.to(dtype)).matmul(vectors.transpose(0, 1))
        return cls(
            sqrt=sqrt,
            inv_sqrt=inv_sqrt,
            support_projector=support_matrix,
            eigenvalues=effective,
            support_rank=int(support.sum().item()),
            ridge=float(ridge),
            relative_tolerance=float(relative_tolerance),
        )

    @property
    def exact(self) -> bool:
        return self.ridge == 0.0

    def _matrix_for(self, x: torch.Tensor, matrix: torch.Tensor) -> torch.Tensor:
        return matrix.to(device=x.device, dtype=x.dtype)

    def whiten_entities(self, entity_table: torch.Tensor) -> torch.Tensor:
        return entity_table @ self._matrix_for(entity_table, self.inv_sqrt)

    def whiten_queries(self, query_table: torch.Tensor) -> torch.Tensor:
        return query_table @ self._matrix_for(query_table, self.sqrt)

    def reconstruct_scores(
        self, query_table: torch.Tensor, entity_table: torch.Tensor
    ) -> torch.Tensor:
        return self.whiten_queries(query_table) @ self.whiten_entities(entity_table).transpose(0, 1)

    def max_whitened_entity_norm(self, entity_table: torch.Tensor) -> torch.Tensor:
        return self.whiten_entities(entity_table).norm(dim=-1).amax()

    @torch.no_grad()
    def relation_projector(
        self,
        query_table: torch.Tensor,
        rank: int,
    ) -> SpectralProjector:
        if query_table.ndim != 2 or query_table.shape[1] != self.sqrt.shape[0]:
            raise ValueError("query_table must have shape [num_queries, dim]")
        if not 0 <= rank <= self.support_rank:
            raise ValueError(f"rank must lie in [0, {self.support_rank}]")
        query_white = self.whiten_queries(query_table)
        work = query_white.to(dtype=self.sqrt.dtype)
        hessian = work.transpose(0, 1) @ work
        values, vectors = torch.linalg.eigh(hessian)
        order = torch.argsort(values, descending=True)
        values = values[order].clamp_min(0)
        vectors = vectors[:, order]
        support = self.support_projector.to(device=vectors.device, dtype=vectors.dtype)
        # For a full-support Gram matrix, ``vectors`` already contains the
        # ordered orthonormal eigenvectors.  Applying QR here would preserve
        # the span but destroy the eigenvalue ordering, so selecting the first
        # columns afterwards would no longer be Ky-Fan optimal.  Only the
        # singular-support branch needs a fresh support-restricted solve.
        if self.support_rank == self.sqrt.shape[0]:
            basis = vectors[:, :rank]
            selected = values[:rank]
        else:
            support_values, support_vectors = torch.linalg.eigh(support @ hessian @ support)
            support_order = torch.argsort(support_values, descending=True)
            support_values = support_values[support_order].clamp_min(0)
            support_vectors = support_vectors[:, support_order]
            basis = support_vectors[:, :rank]
            selected = support_values[:rank]
        total = values.sum()
        residual = (total - selected.sum()).clamp_min(0)
        return SpectralProjector(
            basis=basis,
            eigenvalues=selected,
            residual_energy=residual,
            support_rank=self.support_rank,
        )

    def projected_scores(
        self,
        query_table: torch.Tensor,
        entity_table: torch.Tensor,
        projector: SpectralProjector,
    ) -> torch.Tensor:
        q = self.whiten_queries(query_table)
        e = self.whiten_entities(entity_table)
        basis = projector.basis.to(device=q.device, dtype=q.dtype)
        return (q @ basis) @ (e @ basis).transpose(0, 1)

    def pointwise_error_bound(
        self,
        query_table: torch.Tensor,
        entity_table: torch.Tensor,
        projector: SpectralProjector,
    ) -> torch.Tensor:
        q = self.whiten_queries(query_table)
        e_norm = self.max_whitened_entity_norm(entity_table)
        basis = projector.basis.to(device=q.device, dtype=q.dtype)
        residual = q - (q @ basis) @ basis.transpose(0, 1)
        return residual.norm(dim=-1) * e_norm


def spectral_energy_ranks(
    eigenvalues: torch.Tensor,
    targets: Sequence[float],
    *,
    min_rank: int = 0,
) -> dict[float, int]:
    """Return the first prefix rank reaching each retained-energy target."""

    values = eigenvalues.detach().to(dtype=torch.float64).clamp_min(0)
    total = values.sum()
    result: dict[float, int] = {}
    for target in targets:
        if not 0 <= target <= 1:
            raise ValueError("energy targets must lie in [0, 1]")
        if total == 0:
            result[float(target)] = int(min_rank)
            continue
        cumulative = torch.cumsum(values, dim=0) / total
        reached = torch.nonzero(cumulative >= target, as_tuple=False)
        rank = int(reached[0].item() + 1) if reached.numel() else int(values.numel())
        result[float(target)] = max(int(min_rank), rank)
    return result


def spectral_waterfill(
    spectra: torch.Tensor,
    tolerance_squared: float,
    *,
    probabilities: torch.Tensor | None = None,
    cost_per_rank: float = 1.0,
    min_rank: int = 0,
) -> dict[str, object]:
    """Solve the linear-cost prefix allocation by marginal spectral modes.

    The rows are interpreted as prefix-mode energies in the selected basis;
    they need not be sorted when that basis is shared across relations. The
    tolerance is on the weighted squared Frobenius residual. With the same
    operational distribution used for cost and error, probabilities cancel
    from the marginal ratio; they are still retained in the diagnostics.
    """

    if spectra.ndim != 2 or spectra.shape[1] == 0:
        raise ValueError("spectra must have shape [relations, dim]")
    if tolerance_squared < 0 or cost_per_rank <= 0:
        raise ValueError("tolerance_squared must be nonnegative and cost positive")
    values = spectra.detach().to(dtype=torch.float64).clamp_min(0)
    relations, dim = values.shape
    if probabilities is None:
        probabilities = torch.full((relations,), 1.0 / relations, dtype=values.dtype)
    else:
        probabilities = probabilities.detach().to(dtype=values.dtype, device=values.device)
        if probabilities.shape != (relations,) or probabilities.sum() <= 0:
            raise ValueError("probabilities must have one positive weight per relation")
        probabilities = probabilities / probabilities.sum()
    ranks = torch.full((relations,), int(min_rank), dtype=torch.long)
    residual = (values[:, min_rank:].sum(dim=1) if min_rank else values.sum(dim=1))
    weighted_residual = float((probabilities * residual).sum().item())
    if weighted_residual > tolerance_squared:
        while weighted_residual > tolerance_squared:
            candidates = [
                (float(values[relation, int(ranks[relation].item())].item()) / cost_per_rank, relation)
                for relation in range(relations)
                if int(ranks[relation].item()) < dim
            ]
            if not candidates:
                break
            _, relation = max(candidates)
            index = int(ranks[relation].item())
            ranks[relation] += 1
            weighted_residual -= float(probabilities[relation].item() * values[relation, index].item())
    feasible = weighted_residual <= tolerance_squared + 1e-12
    return {
        "ranks": ranks.tolist(),
        "weighted_residual": max(0.0, weighted_residual),
        "cost": float(cost_per_rank * ranks.sum().item()),
        "feasible": bool(feasible),
        "probabilities": probabilities.tolist(),
    }


def prefix_allocation_dp(
    spectra: torch.Tensor,
    budget_units: int,
    *,
    probabilities: torch.Tensor | None = None,
    rank_cost_units: torch.Tensor | None = None,
    min_rank: int = 0,
) -> dict[str, object]:
    """Exact small-case prefix-knapsack allocation.

    The DP maximizes retained weighted spectral energy under an integer cost
    budget. ``rank_cost_units[r, k]`` is the total integer cost of assigning
    rank ``k`` to relation ``r`` and must be nondecreasing in ``k``. This is
    intentionally a finite optimizer for audits; large production policies
    should use water-filling or a separately profiled solver.
    """

    if spectra.ndim != 2 or budget_units < 0:
        raise ValueError("spectra must be rank-2 and budget_units nonnegative")
    values = spectra.detach().to(dtype=torch.float64).clamp_min(0)
    relations, dim = values.shape
    if min_rank < 0 or min_rank > dim:
        raise ValueError("min_rank must lie in [0, dim]")
    if probabilities is None:
        weights = torch.full((relations,), 1.0 / relations, dtype=values.dtype)
    else:
        weights = probabilities.detach().to(dtype=values.dtype, device=values.device)
        if weights.shape != (relations,) or weights.sum() <= 0:
            raise ValueError("probabilities must have one positive weight per relation")
        weights = weights / weights.sum()
    if rank_cost_units is None:
        costs = torch.arange(dim + 1, dtype=torch.long, device=values.device).expand(relations, -1)
    else:
        costs = rank_cost_units.detach().to(device=values.device, dtype=torch.long)
        if costs.shape != (relations, dim + 1):
            raise ValueError("rank_cost_units must have shape [relations, dim + 1]")
    if torch.any(costs[:, 1:] < costs[:, :-1]):
        raise ValueError("rank costs must be nondecreasing")
    if torch.any(costs[:, min_rank] > budget_units):
        raise ValueError("budget is smaller than the mandatory minimum rank cost")

    prefix = torch.cat(
        [torch.zeros((relations, 1), dtype=values.dtype), torch.cumsum(values, dim=1)], dim=1
    )
    neg_inf = float("-inf")
    dp = torch.full((relations + 1, budget_units + 1), neg_inf, dtype=values.dtype)
    dp[0, 0] = 0.0
    choices = torch.full((relations, budget_units + 1), -1, dtype=torch.long)
    previous_budget = torch.full((relations, budget_units + 1), -1, dtype=torch.long)
    for relation in range(relations):
        for used in range(budget_units + 1):
            previous = float(dp[relation, used].item())
            if previous == neg_inf:
                continue
            for rank in range(min_rank, dim + 1):
                cost = int(costs[relation, rank].item())
                next_budget = used + cost
                if next_budget > budget_units:
                    continue
                value = previous + float(weights[relation].item() * prefix[relation, rank].item())
                if value > float(dp[relation + 1, next_budget].item()):
                    dp[relation + 1, next_budget] = value
                    choices[relation, next_budget] = rank
                    previous_budget[relation, next_budget] = used
    final_budget = int(torch.argmax(dp[relations]).item())
    best_value = dp[relations, final_budget]
    if not torch.isfinite(best_value):
        return {"feasible": False, "allocation": None, "cost_units": None}
    allocation = [0] * relations
    budget = final_budget
    for relation in range(relations - 1, -1, -1):
        rank = int(choices[relation, budget].item())
        allocation[relation] = rank
        budget = int(previous_budget[relation, budget].item())
    total_energy = float((weights * values.sum(dim=1)).sum().item())
    retained = float(best_value.item())
    return {
        "feasible": True,
        "allocation": allocation,
        "cost_units": final_budget,
        "retained_energy": retained,
        "weighted_residual": max(0.0, total_energy - retained),
    }


def prefix_lagrangian_allocation(
    spectra: torch.Tensor,
    tolerance_squared: float,
    *,
    probabilities: torch.Tensor | None = None,
    min_rank: int = 1,
    iterations: int = 56,
) -> dict[str, object]:
    """Fast prefix allocation for a shared, possibly non-monotone basis.

    For each relation and Lagrange multiplier ``alpha`` this chooses the
    prefix rank maximizing ``retained_energy - alpha * rank``. A vectorized
    bisection finds the largest multiplier whose aggregate residual is still
    feasible. The result is a fast finite-policy diagnostic; exact discrete
    optimality is reserved for ``prefix_allocation_dp`` on small instances.
    """

    if spectra.ndim != 2 or spectra.shape[1] == 0:
        raise ValueError("spectra must have shape [relations, dim]")
    if tolerance_squared < 0 or min_rank < 0 or min_rank > spectra.shape[1]:
        raise ValueError("invalid tolerance or minimum rank")
    values = spectra.detach().to(dtype=torch.float64).clamp_min(0)
    relations, dim = values.shape
    if probabilities is None:
        weights = torch.full((relations,), 1.0 / relations, dtype=values.dtype, device=values.device)
    else:
        weights = probabilities.detach().to(dtype=values.dtype, device=values.device)
        if weights.shape != (relations,) or weights.sum() <= 0:
            raise ValueError("probabilities must have one positive weight per relation")
        weights = weights / weights.sum()
    ranks_axis = torch.arange(dim + 1, dtype=values.dtype, device=values.device)
    prefix = torch.cat(
        [torch.zeros((relations, 1), dtype=values.dtype, device=values.device), torch.cumsum(values, dim=1)], dim=1
    )
    total = (weights * values.sum(dim=1)).sum()

    def evaluate(alpha: float) -> tuple[torch.Tensor, torch.Tensor, torch.Tensor]:
        objective = prefix - float(alpha) * ranks_axis.unsqueeze(0)
        objective[:, :min_rank] = float("-inf")
        selected = torch.argmax(objective, dim=1)
        retained = prefix.gather(1, selected.unsqueeze(1)).squeeze(1)
        residual = (weights * (values.sum(dim=1) - retained)).sum()
        cost = (weights * selected.to(dtype=weights.dtype)).sum()
        return selected, residual, cost

    low = 0.0
    high = float(values.max().item() + 1.0)
    best: tuple[torch.Tensor, torch.Tensor, torch.Tensor] | None = None
    selected, residual, cost = evaluate(low)
    if residual <= tolerance_squared + 1e-12:
        best = (selected, residual, cost)
    for _ in range(max(8, int(iterations))):
        middle = (low + high) * 0.5
        selected, residual, cost = evaluate(middle)
        if residual <= tolerance_squared + 1e-12:
            best = (selected, residual, cost)
            low = middle
        else:
            high = middle
    if best is None:
        return {"feasible": False, "ranks": None, "weighted_residual": None, "cost": None}
    selected, residual, cost = best
    return {
        "feasible": True,
        "ranks": selected.tolist(),
        "weighted_residual": float(residual.item()),
        "cost": float(cost.item()),
        "total_energy": float(total.item()),
    }


def ranking_certificate(
    full_scores: torch.Tensor,
    compressed_scores: torch.Tensor,
    pointwise_bound: torch.Tensor | float,
    *,
    k: int = 1,
) -> dict[str, torch.Tensor | float]:
    """Evaluate deterministic top-k stability from a uniform score bound."""

    if full_scores.shape != compressed_scores.shape or full_scores.ndim != 2:
        raise ValueError("full_scores and compressed_scores must share shape [queries, candidates]")
    if not 1 <= k < full_scores.shape[1]:
        raise ValueError("k must be in [1, num_candidates-1]")
    bound = torch.as_tensor(pointwise_bound, device=full_scores.device, dtype=full_scores.dtype)
    if bound.ndim == 0:
        bound = bound.expand(full_scores.shape[0])
    if bound.shape != (full_scores.shape[0],):
        raise ValueError("pointwise_bound must be scalar or one value per query")
    top = full_scores.topk(k + 1, dim=-1).values
    margins = top[:, k - 1] - top[:, k]
    stable = margins > 2 * bound
    return {
        "boundary_margins": margins,
        "bound": bound,
        "stable": stable,
        "coverage": stable.to(dtype=torch.float32).mean(),
    }


def grassmann_chordal_distance(basis_a: torch.Tensor, basis_b: torch.Tensor) -> torch.Tensor:
    """Squared chordal distance between two orthonormal subspaces."""

    if basis_a.ndim != 2 or basis_b.ndim != 2 or basis_a.shape[0] != basis_b.shape[0]:
        raise ValueError("bases must have shape [dim, rank] with equal ambient dimension")
    rank = min(basis_a.shape[1], basis_b.shape[1])
    if rank == 0:
        return torch.zeros((), device=basis_a.device, dtype=basis_a.dtype)
    overlap = basis_a.transpose(0, 1) @ basis_b
    return torch.tensor(float(rank), device=overlap.device, dtype=overlap.dtype) - overlap.pow(2).sum()
