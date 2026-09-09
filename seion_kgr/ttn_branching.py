"""Branching ``k=3`` TTN scorer for post-training projection studies.

The model has five leaves ``h_1, r_1, h_2, r_2, t``.  Two independent
bilinear laws produce branch states, optional orthogonal projectors act on
those states, and an unprojected trilinear root produces the scalar score:

    u_1 = mu_1(h_1, r_1),   u_2 = mu_2(h_2, r_2),
    s(h,r,t) = mu_3(u_1, u_2, t).

The full model is trained with ``mode='full'``.  SVD bases can then be fitted
from frozen branch activations and ``mode='projected'`` evaluates the exact
projected network in rank coordinates.  The module deliberately does not
fine-tune after projection; that separation isolates projection error.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable, Mapping

import torch
import torch.nn as nn

from seion_core.research_v5.dag_domain_certificate import (
    DAGDomainNode,
    certify_dag_domain,
    certify_dag_domain_rank_aware,
    optimal_dag_domain_ranks,
    optimal_rank_aware_dag_domain_ranks,
)


@dataclass(frozen=True)
class TTNProjectors:
    basis1: torch.Tensor
    basis2: torch.Tensor
    singular_values1: torch.Tensor
    singular_values2: torch.Tensor


class BranchingTTNK3(nn.Module):
    """A reciprocal-compatible branching TTN scorer with two truncable nodes."""

    def __init__(
        self,
        num_entities: int,
        num_relations_total: int,
        dim: int,
        branch_dim: int | None = None,
    ) -> None:
        super().__init__()
        if dim <= 1 or dim % 2:
            raise ValueError("dim must be an even integer greater than one")
        if branch_dim is None:
            branch_dim = dim
        if branch_dim <= 0:
            raise ValueError("branch_dim must be positive")
        self.dim = int(dim)
        self.leaf_dim = dim // 2
        self.branch_dim = int(branch_dim)
        self.entity = nn.Embedding(num_entities, dim)
        self.relation = nn.Embedding(num_relations_total, dim)
        self.mu1 = nn.Bilinear(self.leaf_dim, self.leaf_dim, branch_dim, bias=False)
        self.mu2 = nn.Bilinear(self.leaf_dim, self.leaf_dim, branch_dim, bias=False)
        self.root = nn.Parameter(torch.empty(branch_dim, branch_dim, dim))
        # Embedding-aware initialization: Xavier treats the vocabulary size
        # as a fan dimension for ``nn.Embedding`` and makes entity vectors
        # artificially tiny on FB15K-237.  A fixed bounded scale gives the
        # scorer useful gradients while keeping the finite-domain certificate
        # explicit after training.
        nn.init.uniform_(self.entity.weight, -0.1, 0.1)
        nn.init.uniform_(self.relation.weight, -0.1, 0.1)
        nn.init.xavier_uniform_(self.mu1.weight)
        nn.init.xavier_uniform_(self.mu2.weight)
        nn.init.xavier_uniform_(self.root)

        self.register_buffer("basis1", torch.eye(branch_dim))
        self.register_buffer("basis2", torch.eye(branch_dim))
        self.register_buffer("singular_values1", torch.zeros(branch_dim))
        self.register_buffer("singular_values2", torch.zeros(branch_dim))
        self.rank1 = branch_dim
        self.rank2 = branch_dim
        self.mode = "full"
        # Projected execution caches the transformed branch/root cores once
        # per rank assignment.  They are deliberately not persistent model
        # state: they are derived offline from frozen parameters and bases.
        self._projected_core_cache: dict[
            tuple[int, int, int, str, torch.dtype], tuple[torch.Tensor, torch.Tensor, torch.Tensor]
        ] = {}
        # Optional output-space compression. These objects are derived from
        # frozen parameters and remain outside state_dict for legacy loads.
        self.output_basis: torch.Tensor | None = None
        self.output_rank = self.dim
        self._output_entity_tables: dict[int, torch.Tensor] = {}

    def _invalidate_projected_cache(self) -> None:
        self._projected_core_cache.clear()

    def _invalidate_output_cache(self) -> None:
        self._output_entity_tables.clear()

    def _output_basis_for_rank(self) -> torch.Tensor:
        if self.output_basis is None:
            if self.output_rank != self.dim:
                raise RuntimeError("a train-only output basis is required for output_rank < dim")
            return torch.eye(self.dim, device=self.root.device, dtype=self.root.dtype)
        return self.output_basis[:, : self.output_rank]

    @torch.no_grad()
    def set_output_basis(self, basis: torch.Tensor) -> None:
        """Install a full train-only output basis for rank sweeps."""

        if basis.ndim != 2 or basis.shape[0] != self.dim or basis.shape[1] < self.dim:
            raise ValueError("output basis must have shape [dim, dim] or wider")
        self.output_basis = basis[:, : self.dim].to(
            device=self.root.device, dtype=self.root.dtype
        ).contiguous()
        self.output_rank = self.dim
        self._invalidate_output_cache()
        self._invalidate_projected_cache()

    @torch.no_grad()
    def fit_output_projector(self, entity_ids: torch.Tensor) -> tuple[torch.Tensor, torch.Tensor]:
        """Fit an output basis from entity rows observed in train only."""

        ids = torch.unique(entity_ids.to(device=self.entity.weight.device, dtype=torch.long))
        if ids.numel() == 0:
            raise ValueError("entity_ids must contain at least one entity")
        _, singular_values, vh = torch.linalg.svd(self.entity(ids), full_matrices=True)
        basis = vh.transpose(0, 1).contiguous()
        self.set_output_basis(basis)
        return basis, singular_values

    def set_output_rank(self, output_rank: int) -> None:
        if not isinstance(output_rank, int) or isinstance(output_rank, bool):
            raise ValueError("output_rank must be an integer")
        if not 1 <= output_rank <= self.dim:
            raise ValueError(f"output_rank must lie in [1, {self.dim}]")
        if output_rank < self.dim and self.output_basis is None:
            raise ValueError("fit_output_projector or set_output_basis before reducing output rank")
        self.output_rank = output_rank

    @torch.no_grad()
    def prepare_output_executor(self) -> None:
        """Transform all candidate entity rows outside the timed region."""

        if self.output_rank == self.dim and self.output_basis is None:
            return
        if self.output_rank not in self._output_entity_tables:
            self._output_entity_tables[self.output_rank] = (
                self.entity.weight.detach() @ self._output_basis_for_rank()
            )

    def output_entity_vectors(self, entity_ids: torch.Tensor) -> torch.Tensor:
        if self.output_rank == self.dim and self.output_basis is None:
            return self.entity(entity_ids)
        if self.output_rank not in self._output_entity_tables:
            self.prepare_output_executor()
        return self._output_entity_tables[self.output_rank][entity_ids]

    @torch.no_grad()
    def output_residual_bound(self) -> float:
        """Finite-domain tail residual after the train-only output projection."""

        if self.output_rank == self.dim and self.output_basis is None:
            return 0.0
        q = self._output_basis_for_rank()
        entity = self.entity.weight.detach()
        residual = entity - (entity @ q) @ q.T
        return float(torch.linalg.norm(residual, dim=-1).max().item())

    def output_certificate(
        self,
        leaf_norm_bounds: Mapping[str, float],
        rank1: int | None = None,
        rank2: int | None = None,
    ) -> dict[str, float | int]:
        """Add a certified output-projection term to the branch certificate.

        The output projection is applied to the tail leaf and the root is
        transformed to the same coordinates.  The displayed envelope is
        intentionally conservative: it uses the stored Frobenius bounds for
        both branch laws and the finite maximum residual over all entity rows.
        """

        internal = self.certificate(leaf_norm_bounds, rank1, rank2)
        residual = self.output_residual_bound()
        if residual == 0.0:
            output_error = 0.0
        else:
            nodes = self._certificate_nodes()
            branch_product = (
                nodes["branch1"].operator_bound
                * nodes["branch2"].operator_bound
                * float(leaf_norm_bounds["h1"])
                * float(leaf_norm_bounds["r1"])
                * float(leaf_norm_bounds["h2"])
                * float(leaf_norm_bounds["r2"])
            )
            output_error = nodes["root"].operator_bound * branch_product * residual
        return {
            "output_rank": int(self.output_rank),
            "tail_residual_bound": float(residual),
            "internal_error_bound": float(internal["root_bound"]),
            "output_error_bound": float(output_error),
            "total_error_bound": float(internal["root_bound"] + output_error),
        }

    @torch.no_grad()
    def _projected_cores(self) -> tuple[torch.Tensor, torch.Tensor, torch.Tensor]:
        """Return transformed cores, building them once outside inference."""

        key = (self.rank1, self.rank2, self.output_rank, str(self.root.device), self.root.dtype)
        if key not in self._projected_core_cache:
            q1 = self.basis1[:, : self.rank1]
            q2 = self.basis2[:, : self.rank2]
            qout = self._output_basis_for_rank()
            self._projected_core_cache[key] = (
                torch.einsum("ia,ijk->ajk", q1, self.mu1.weight),
                torch.einsum("ia,ijk->ajk", q2, self.mu2.weight),
                torch.einsum("ia,jb,ijd,dk->abk", q1, q2, self.root, qout),
            )
        return self._projected_core_cache[key]

    def set_mode(self, mode: str) -> None:
        if mode not in {"full", "projected"}:
            raise ValueError("mode must be 'full' or 'projected'")
        if mode == "projected" and (self.rank1 <= 0 or self.rank2 <= 0):
            raise ValueError("projected mode requires positive branch ranks")
        self.mode = mode

    @torch.no_grad()
    def fit_projectors(self, h_ids: torch.Tensor, r_ids: torch.Tensor) -> TTNProjectors:
        """Fit full square SVD bases from frozen branch activations."""

        was_training = self.training
        self.eval()
        h = self.entity(h_ids)
        r = self.relation(r_ids)
        h1, h2 = h.split(self.leaf_dim, dim=-1)
        r1, r2 = r.split(self.leaf_dim, dim=-1)
        u1 = self.mu1(h1, r1)
        u2 = self.mu2(h2, r2)
        _, s1, vh1 = torch.linalg.svd(u1, full_matrices=True)
        _, s2, vh2 = torch.linalg.svd(u2, full_matrices=True)
        q1 = vh1.transpose(0, 1).contiguous()
        q2 = vh2.transpose(0, 1).contiguous()
        self.basis1.copy_(q1)
        self.basis2.copy_(q2)
        self.singular_values1.zero_()
        self.singular_values2.zero_()
        self.singular_values1[: s1.numel()].copy_(s1)
        self.singular_values2[: s2.numel()].copy_(s2)
        self.rank1 = self.branch_dim
        self.rank2 = self.branch_dim
        self._invalidate_projected_cache()
        if was_training:
            self.train()
        return TTNProjectors(q1, q2, s1, s2)

    def set_ranks(self, rank1: int, rank2: int) -> None:
        for name, rank in (("rank1", rank1), ("rank2", rank2)):
            if not isinstance(rank, int) or isinstance(rank, bool) or not 1 <= rank <= self.branch_dim:
                raise ValueError(f"{name} must lie in [1, {self.branch_dim}]")
        self.rank1 = rank1
        self.rank2 = rank2

    @torch.no_grad()
    def project_parameter_norms(
        self,
        *,
        embedding_max_norm: float = 1.0,
        core_max_fro: float = 1.0,
        root_max_fro: float = 1.0,
    ) -> None:
        """Enforce the finite norm domain used by the certificate.

        Entity/relation rows are clipped individually; multilinear cores are
        clipped by Frobenius norm.  This makes the declared normalization an
        invariant of training rather than an estimate made from test data.
        """

        if min(embedding_max_norm, core_max_fro, root_max_fro) <= 0:
            raise ValueError("all parameter norm caps must be positive")
        self.entity.weight.renorm_(2, 0, embedding_max_norm)
        self.relation.weight.renorm_(2, 0, embedding_max_norm)
        for parameter, cap in (
            (self.mu1.weight, core_max_fro),
            (self.mu2.weight, core_max_fro),
            (self.root, root_max_fro),
        ):
            norm = parameter.norm()
            if norm > cap:
                parameter.mul_(cap / norm)
        self._invalidate_projected_cache()
        self._invalidate_output_cache()

    def _branch_states(
        self, h_ids: torch.Tensor, r_ids: torch.Tensor
    ) -> tuple[torch.Tensor, torch.Tensor, torch.Tensor]:
        h = self.entity(h_ids)
        r = self.relation(r_ids)
        h1, h2 = h.split(self.leaf_dim, dim=-1)
        r1, r2 = r.split(self.leaf_dim, dim=-1)
        return h, self.mu1(h1, r1), self.mu2(h2, r2)

    def _branch_inputs(
        self, h_ids: torch.Tensor, r_ids: torch.Tensor
    ) -> tuple[torch.Tensor, torch.Tensor, torch.Tensor, torch.Tensor]:
        h = self.entity(h_ids)
        r = self.relation(r_ids)
        h1, h2 = h.split(self.leaf_dim, dim=-1)
        r1, r2 = r.split(self.leaf_dim, dim=-1)
        return h1, r1, h2, r2

    @staticmethod
    def _transformed_bilinear_state(
        left: torch.Tensor,
        right: torch.Tensor,
        weight: torch.Tensor,
        basis: torch.Tensor,
    ) -> torch.Tensor:
        """Evaluate ``Q^T K(left,right)`` without materializing ambient output."""

        transformed = torch.einsum("ia,ijk->ajk", basis, weight)
        return torch.einsum("bi,bj,aij->ba", left, right, transformed)

    def branch_activations(self, h_ids: torch.Tensor, r_ids: torch.Tensor) -> tuple[torch.Tensor, torch.Tensor]:
        return self._branch_states(h_ids, r_ids)[1:]

    def query_representation(self, h_ids: torch.Tensor, r_ids: torch.Tensor) -> torch.Tensor:
        """Return the pre-tail query vector used by the multilinear score."""

        if self.mode == "full":
            _, u1, u2 = self._branch_states(h_ids, r_ids)
            return torch.einsum("bi,bj,ijd->bd", u1, u2, self.root)
        h1, r1, h2, r2 = self._branch_inputs(h_ids, r_ids)
        mu1, mu2, root = self._projected_cores()
        u1 = torch.einsum("bi,bj,aij->ba", h1, r1, mu1)
        u2 = torch.einsum("bi,bj,aij->ba", h2, r2, mu2)
        return torch.einsum("bi,bj,ijd->bd", u1, u2, root)

    def _score_from_states(
        self,
        u1: torch.Tensor,
        u2: torch.Tensor,
        tail: torch.Tensor,
        *,
        tail_is_batched: bool,
    ) -> torch.Tensor:
        if self.mode == "full":
            root = self.root
            interaction = torch.einsum("bi,bj,ijd->bd", u1, u2, root)
            if tail_is_batched:
                return torch.einsum("bd,bd->b", interaction, tail)
            if tail.ndim == 2:
                # Contract the two branch coordinates with the root first.
                # The previous four-way einsum could materialize an
                # O(batch * candidates * branch1 * branch2) intermediate.
                return interaction @ tail.T
            return torch.einsum("bd,bkd->bk", interaction, tail)

        # In projected mode ``u1`` and ``u2`` are already rank coordinates;
        # no ambient branch vector is formed here.  The transformed branch
        # cores are evaluated in ``score_positive``/``score_tail_candidates``.
        u1c = u1
        u2c = u2
        _, _, root = self._projected_cores()
        interaction = torch.einsum("bi,bj,ijd->bd", u1c, u2c, root)
        if tail_is_batched:
            return torch.einsum("bd,bd->b", interaction, tail)
        if tail.ndim == 2:
            return interaction @ tail.T
        return torch.einsum("bd,bkd->bk", interaction, tail)

    def score_positive(
        self,
        h_ids: torch.Tensor,
        r_ids: torch.Tensor,
        t_ids: torch.Tensor,
        *_args,
        **_kwargs,
    ) -> torch.Tensor:
        if self.mode == "full":
            _, u1, u2 = self._branch_states(h_ids, r_ids)
        else:
            h1, r1, h2, r2 = self._branch_inputs(h_ids, r_ids)
            mu1, mu2, _ = self._projected_cores()
            u1 = torch.einsum("bi,bj,aij->ba", h1, r1, mu1)
            u2 = torch.einsum("bi,bj,aij->ba", h2, r2, mu2)
        return self._score_from_states(u1, u2, self.output_entity_vectors(t_ids), tail_is_batched=True)

    def score_positive_projected_ambient(
        self,
        h_ids: torch.Tensor,
        r_ids: torch.Tensor,
        t_ids: torch.Tensor,
    ) -> torch.Tensor:
        """Reference evaluation of ``mu3(P1 u1, P2 u2, t)`` in ambient space.

        This intentionally materializes the projected branch states and is
        used only as an algebraic-equivalence oracle for the reduced-core
        implementation.  It is not used by the compressed runner.
        """

        _, u1, u2 = self._branch_states(h_ids, r_ids)
        q1 = self.basis1[:, : self.rank1]
        q2 = self.basis2[:, : self.rank2]
        u1 = u1 @ (q1 @ q1.T)
        u2 = u2 @ (q2 @ q2.T)
        interaction = torch.einsum("bi,bj,ijd->bd", u1, u2, self.root)
        if self.output_rank < self.dim or self.output_basis is not None:
            qout = self._output_basis_for_rank()
            return torch.einsum("bd,bd->b", interaction @ qout, self.entity(t_ids) @ qout)
        return torch.einsum("bd,bd->b", interaction, self.entity(t_ids))

    def score_tail_candidates(
        self,
        h_ids: torch.Tensor,
        r_ids: torch.Tensor,
        candidates_ids: torch.Tensor,
        *_args,
        **_kwargs,
    ) -> torch.Tensor:
        if self.mode == "full":
            _, u1, u2 = self._branch_states(h_ids, r_ids)
        else:
            h1, r1, h2, r2 = self._branch_inputs(h_ids, r_ids)
            mu1, mu2, _ = self._projected_cores()
            u1 = torch.einsum("bi,bj,aij->ba", h1, r1, mu1)
            u2 = torch.einsum("bi,bj,aij->ba", h2, r2, mu2)
        return self._score_from_states(
            u1, u2, self.output_entity_vectors(candidates_ids), tail_is_batched=False
        )

    def score_tail_candidates_projected_ambient(
        self,
        h_ids: torch.Tensor,
        r_ids: torch.Tensor,
        candidates_ids: torch.Tensor,
    ) -> torch.Tensor:
        """Ambient reference for the projected candidate scores."""

        _, u1, u2 = self._branch_states(h_ids, r_ids)
        q1 = self.basis1[:, : self.rank1]
        q2 = self.basis2[:, : self.rank2]
        u1 = u1 @ (q1 @ q1.T)
        u2 = u2 @ (q2 @ q2.T)
        interaction = torch.einsum("bi,bj,ijd->bd", u1, u2, self.root)
        if self.output_rank < self.dim or self.output_basis is not None:
            qout = self._output_basis_for_rank()
            return (interaction @ qout) @ (self.entity(candidates_ids) @ qout).T
        return interaction @ self.entity(candidates_ids).T

    def _certificate_cache_key(self) -> tuple:
        """Identity of every tensor `_certificate_nodes` reads.

        `data_ptr` catches rebinding (e.g. a refit basis) and `_version` catches
        in-place mutation (an optimizer step), so the cache below invalidates
        itself whenever the certificate inputs actually change.
        """
        tensors = (
            self.mu1.weight, self.mu2.weight, self.basis1, self.basis2, self.root,
        )
        return tuple((t.data_ptr(), t._version, tuple(t.shape)) for t in tensors)

    def _certificate_nodes(self) -> dict[str, DAGDomainNode]:
        # The node table depends only on frozen model tensors, never on the
        # query. The post-training sweep calls certificate() once per query per
        # rank pair, which recomputed ~128 matrix norms and as many device
        # syncs every time; on the D32 sweep that was the single largest cost.
        # Caching is exact, not approximate: same inputs, same tensors.
        key = self._certificate_cache_key()
        cached = getattr(self, "_certificate_nodes_cache", None)
        if cached is not None and cached[0] == key:
            return cached[1]

        eye = torch.eye(self.branch_dim, device=self.root.device, dtype=self.root.dtype)

        def branch_data(layer: nn.Bilinear, basis: torch.Tensor) -> tuple[float, tuple[float, ...], tuple[float, ...]]:
            flat = layer.weight.detach().reshape(self.branch_dim, -1)
            operator = float(torch.linalg.matrix_norm(flat, ord="fro").item())
            normal: list[float] = [0.0]
            projected: list[float] = [0.0]
            for rank in range(1, self.branch_dim + 1):
                q = basis[:, :rank]
                p = q @ q.T
                normal.append(float(torch.linalg.matrix_norm((eye - p) @ flat, ord="fro").item()))
                projected.append(float(torch.linalg.matrix_norm(p @ flat, ord="fro").item()))
            return operator, tuple(normal), tuple(projected)

        op1, normal1, projected1 = branch_data(self.mu1, self.basis1)
        op2, normal2, projected2 = branch_data(self.mu2, self.basis2)
        root_op = float(torch.linalg.matrix_norm(self.root.detach().reshape(-1, self.dim), ord="fro").item())
        nodes = {
            "h1": DAGDomainNode("h1"),
            "r1": DAGDomainNode("r1"),
            "h2": DAGDomainNode("h2"),
            "r2": DAGDomainNode("r2"),
            "t": DAGDomainNode("t"),
            "branch1": DAGDomainNode(
                "branch1", ("h1", "r1"), op1, normal1, projected1
            ),
            "branch2": DAGDomainNode(
                "branch2", ("h2", "r2"), op2, normal2, projected2
            ),
            "root": DAGDomainNode(
                "root", ("branch1", "branch2", "t"), root_op, (0.0, 0.0), (root_op, root_op)
            ),
        }
        self._certificate_nodes_cache = (key, nodes)
        return nodes

    def certificate(
        self,
        leaf_norm_bounds: Mapping[str, float],
        rank1: int | None = None,
        rank2: int | None = None,
        *,
        rank_aware: bool = False,
    ) -> dict[str, object]:
        nodes = self._certificate_nodes()
        ranks = {
            "branch1": self.rank1 if rank1 is None else rank1,
            "branch2": self.rank2 if rank2 is None else rank2,
            "root": 1,
        }
        if rank_aware:
            result = certify_dag_domain_rank_aware(
                nodes, "root", leaf_norm_bounds=leaf_norm_bounds, ranks=ranks
            )
            return {
                "root_bound": result.root_bound,
                "error_bounds": result.error_bounds,
                "exact_value_bounds": result.exact_value_bounds,
                "approximate_value_bounds": result.approximate_value_bounds,
                "ranks": result.ranks,
            }
        result = certify_dag_domain(
            nodes, "root", leaf_norm_bounds=leaf_norm_bounds, ranks=ranks
        )
        return {
            "root_bound": result.root_bound,
            "error_bounds": result.error_bounds,
            "value_bounds": result.value_bounds,
            "downstream_gains": result.downstream_gains,
            "rank_costs": result.rank_costs,
        }

    def optimal_certificate_ranks(
        self,
        leaf_norm_bounds: Mapping[str, float],
        budget: int,
        *,
        rank_aware: bool = False,
    ) -> tuple[dict[str, int], float]:
        nodes = self._certificate_nodes()
        if rank_aware:
            ranks, value = optimal_rank_aware_dag_domain_ranks(
                nodes, "root", leaf_norm_bounds=leaf_norm_bounds, budget=budget
            )
        else:
            ranks, value = optimal_dag_domain_ranks(
                nodes, "root", leaf_norm_bounds=leaf_norm_bounds, budget=budget
            )
        return ranks, value

    def resource_proxy(
        self,
        rank1: int | None = None,
        rank2: int | None = None,
        *,
        output_rank: int | None = None,
        candidate_count: int | None = None,
        dtype_bytes: int = 4,
    ) -> dict[str, int]:
        r1 = self.rank1 if rank1 is None else rank1
        r2 = self.rank2 if rank2 is None else rank2
        rout = self.output_rank if output_rank is None else output_rank
        if not (1 <= r1 <= self.branch_dim and 1 <= r2 <= self.branch_dim):
            raise ValueError("resource ranks must be within the branch dimension")
        if not 1 <= rout <= self.dim:
            raise ValueError("output_rank must lie within the model dimension")
        branch_units = 2 * self.branch_dim * self.leaf_dim * self.leaf_dim
        root_units = r1 * r2 * rout
        core_units = 2 * r1 * self.leaf_dim * self.leaf_dim + root_units
        candidate_units = 0 if candidate_count is None else rout * int(candidate_count)
        full_candidate_units = 0 if candidate_count is None else self.dim * int(candidate_count)
        embedding_units = (self.entity.num_embeddings + self.relation.num_embeddings) * self.dim
        output_embedding_units = 0 if rout == self.dim else self.entity.num_embeddings * rout
        basis_units = self.branch_dim * (r1 + r2)
        output_basis_units = 0 if self.output_basis is None or rout == self.dim else self.dim * rout
        return {
            "rank_budget": int(r1 + r2),
            "output_rank": int(rout),
            "full_branch_contraction_units": int(branch_units),
            "projected_score_contraction_units": int(2 * r1 * self.leaf_dim * self.leaf_dim + root_units),
            "full_score_contraction_units": int(branch_units + self.branch_dim * self.branch_dim * self.dim),
            "projected_candidate_score_units": int(core_units + candidate_units),
            "full_candidate_score_units": int(branch_units + self.branch_dim * self.branch_dim * self.dim + full_candidate_units),
            "runtime_core_storage_bytes": int(core_units * dtype_bytes),
            "offline_transformed_core_storage_bytes": int(core_units * dtype_bytes),
            "basis_storage_bytes": int(basis_units * dtype_bytes),
            "embedding_storage_bytes": int(embedding_units * dtype_bytes),
            "output_embedding_storage_bytes": int(output_embedding_units * dtype_bytes),
            "output_basis_storage_bytes": int(output_basis_units * dtype_bytes),
            "runtime_model_storage_bytes": int((embedding_units + output_embedding_units + core_units) * dtype_bytes),
            "package_storage_bytes": int((embedding_units + output_embedding_units + core_units + basis_units + output_basis_units) * dtype_bytes),
        }


def branch_leaf_norm_bounds(model: BranchingTTNK3) -> dict[str, float]:
    """Return exact stored-table norm bounds for the five TTN leaves."""

    entity = model.entity.weight.detach()
    relation = model.relation.weight.detach()
    h1, h2 = entity.split(model.leaf_dim, dim=-1)
    r1, r2 = relation.split(model.leaf_dim, dim=-1)
    return {
        "h1": float(torch.linalg.norm(h1, dim=-1).max().item()),
        "r1": float(torch.linalg.norm(r1, dim=-1).max().item()),
        "h2": float(torch.linalg.norm(h2, dim=-1).max().item()),
        "r2": float(torch.linalg.norm(r2, dim=-1).max().item()),
        "t": float(torch.linalg.norm(entity, dim=-1).max().item()),
    }


def query_leaf_norm_bounds(model: BranchingTTNK3, h_id: int, r_id: int) -> dict[str, float]:
    with torch.no_grad():
        h = model.entity.weight[h_id]
        r = model.relation.weight[r_id]
    h1, h2 = h.split(model.leaf_dim)
    r1, r2 = r.split(model.leaf_dim)
    return {
        "h1": float(torch.linalg.norm(h1).item()),
        "r1": float(torch.linalg.norm(r1).item()),
        "h2": float(torch.linalg.norm(h2).item()),
        "r2": float(torch.linalg.norm(r2).item()),
        "t": float(torch.linalg.norm(model.entity.weight.detach(), dim=-1).max().item()),
    }
