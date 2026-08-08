"""Contract §XI/§XX: SeionKGRv26 — base expert + path branch + seionic
branch + optional structural-kernel (E8/control) residual, combined by
per-relation residual gates initialized at exactly zero (contract §XX.4:
"el modelo empieza como el baseline fuerte").

Campaign Phase B3 update: the structural-kernel branch (E8 or one of its
matched controls, `structural_kernel.py`) is now implemented, closing
the CLM_KGR_018 gap the canonical commit deliberately left open. It
remains OFF by default (`enable_structural_kernel=False`) and, when
enabled, still starts near-zero via its own internal per-relation gate
— it never becomes the default predictor. Its own module docstring
carries the CLM_KGR_018-compliant warning: no causal claim is licensed
by this wiring alone, only by the matched-control comparison it makes
possible.

Gate 13.1 update (router activation, `campaigns/gate13/`): the router
gates were previously `sigmoid(gamma_raw)` with `gamma_raw` initialized to
`-4.0` (`sigmoid(-4) ~= 0.018`, `sigmoid'(-4) ~= 0.0177`) — a 40-epoch run
showed the gate stays at its initialization under that parameterization,
starving the path/seion branches of gradient signal. The gate is now
`gamma_r = gate_g_max * tanh(alpha_r)` with `alpha_r` (still stored in the
`gamma_raw`/`eta_raw` embeddings) zero-initialized: `gamma_r(0) = 0`
exactly (same "starts as the baseline" property) but
`d(gamma_r)/d(alpha_r)(0) = gate_g_max`, i.e. a `gate_g_max`-sized gradient
at init rather than `~0.0177`.

Gate 13.2b update (production integration, `campaigns/gate13/`):
`path_backend` selects which reasoner implementation the path branch
uses — `"legacy"` (default, `reasoner.PathReasoner`, unchanged behavior)
or `"batched"` (`reasoner_batched.BatchedPathReasoner`, CSR + vectorized
frontier expansion, Gate 13.2). Both expose identical submodule names
(`mu`, `U`, `V`, `W`, `projector`, `ln`, `unreached_state`), so a
checkpoint trained with one backend loads directly into a model
constructed with the other — `path_backend` is an execution detail, not a
different architecture. Score computation always reads off a
`PathReasonerOutput` (`path_reasoner_output.py`), so this file has exactly
ONE readout implementation regardless of which backend produced it.

Signed-gate declaration (post-Gate-13.2b precision, `campaigns/gate13/`):
`gamma_r = gate_g_max * tanh(alpha_r)` ranges over `(-gate_g_max,
gate_g_max)`, NOT `(0, 1)` like the old `sigmoid`. **The Gate 13 routers
are signed residual gates, not convex-mixing weights** — a trained
`gamma_r < 0` is not a failure mode, it means the branch learned to
SUBTRACT a residual correction from the base score for that relation, not
to blend the two additively. Any downstream reporting (attribution,
diagnostics) must track `signed` and `absolute` contributions separately
(see `compute_gate_diagnostics` in `train.py`) — reducing a gate to "how
much did it contribute" without a sign is a category error for this
architecture.
"""
from __future__ import annotations

import math
from typing import Dict, Optional, Union

import torch
import torch.nn as nn

from .data import KnowledgeGraph
from .frontier_ops import CSRAdjacency
from .kernels import GenericLowRankResidualScorer, SeionicScalarScorer
from .path_reasoner_output import PathReasonerOutput
from .reasoner import Adjacency, PathReasoner
from .reasoner_batched import BatchedPathReasoner
from .scorers import ComplExExpert, CPExpert, DistMultExpert, TuckERExpert
from .structural_kernel import KernelProvenance, StructuralKernelResidual

BASE_EXPERTS = ("complex", "distmult", "cp", "tucker")
PATH_BACKENDS = ("legacy", "batched")
STANDALONE_MODES = ("residual", "warm_started_decoder", "end_to_end")


class SeionKGRv26(nn.Module):
    def __init__(
        self,
        num_entities: int,
        num_relations_total: int,
        dim: int,
        base_expert: str = "complex",
        enable_path: bool = False,
        enable_seion: bool = False,
        enable_generic_residual: bool = False,
        seion_rank: int = 32,
        path_rank: int = 32,
        path_layers: int = 2,
        path_max_neighbors: int = 32,
        path_proj_rank: int = 0,
        path_selector_mode: str = "budgeted_bfs",
        structural_kernel: Optional[StructuralKernelResidual] = None,
        gate_g_max: float = 1.0,
        gate_init: float = 0.0,
        path_backend: str = "legacy",
        standalone_mode: str = "residual",
    ):
        super().__init__()
        if base_expert not in BASE_EXPERTS:
            raise ValueError(f"base_expert must be one of {BASE_EXPERTS}, got {base_expert!r}")
        if path_backend not in PATH_BACKENDS:
            raise ValueError(f"path_backend must be one of {PATH_BACKENDS}, got {path_backend!r}")
        if standalone_mode not in STANDALONE_MODES:
            raise ValueError(f"standalone_mode must be one of {STANDALONE_MODES}, got {standalone_mode!r}")
        if base_expert == "complex" and dim % 2 != 0:
            raise ValueError("--dim must be even for the complex base expert")
        self.dim = dim
        self.base_expert_name = base_expert
        self.enable_path = enable_path
        self.enable_seion = enable_seion
        self.enable_generic_residual = enable_generic_residual
        if enable_seion and enable_generic_residual:
            raise ValueError("enable_seion and enable_generic_residual are mutually exclusive controls")
        self.standalone_mode = standalone_mode
        self.use_base_scorer = standalone_mode == "residual"

        self.entity = nn.Embedding(num_entities, dim)
        self.relation = nn.Embedding(num_relations_total, dim)
        nn.init.xavier_uniform_(self.entity.weight)
        nn.init.xavier_uniform_(self.relation.weight)

        if base_expert == "complex":
            self.base = ComplExExpert()
        elif base_expert == "distmult":
            self.base = DistMultExpert()
        elif base_expert == "tucker":
            self.base = TuckERExpert(dim, dim)
        else:
            self.base = CPExpert()
            self.entity_tail = nn.Embedding(num_entities, dim)
            nn.init.xavier_uniform_(self.entity_tail.weight)

        if not self.use_base_scorer:
            for parameter in self.base.parameters():
                parameter.requires_grad_(False)

        self.path_backend = path_backend
        if enable_path:
            reasoner_cls = PathReasoner if path_backend == "legacy" else BatchedPathReasoner
            self.path_reasoner = reasoner_cls(
                dim=dim, rank=path_rank, num_layers=path_layers,
                max_neighbors=path_max_neighbors, proj_rank=path_proj_rank,
                selector_mode=path_selector_mode,
            )
        else:
            self.path_reasoner = None

        if enable_seion:
            self.seion_scorer = SeionicScalarScorer(dim_e=dim, dim_r=dim, dim_q=dim, rank=seion_rank)
        else:
            self.seion_scorer = None
        if enable_generic_residual:
            self.generic_residual_scorer = GenericLowRankResidualScorer(dim_e=dim, dim_r=dim, dim_q=dim, rank=seion_rank)
        else:
            self.generic_residual_scorer = None

        # Caller-constructed: loading a specific kernel variant (E8_exact
        # needs a file, the controls need a seed/shape) is a policy
        # decision that belongs in train.py, not hidden inside the model.
        self.structural_kernel = structural_kernel
        self.enable_structural_kernel = structural_kernel is not None

        # Zero-init residual router (contract §XX.4; Gate 13.1 reparameterization —
        # see module docstring). ``gamma_raw``/``eta_raw`` store the PRE-ACTIVATION
        # alpha_r, not a pre-sigmoid logit, despite the unchanged attribute names
        # (kept so checkpoints/optimizer-group lookups by name stay stable).
        self.gate_g_max = gate_g_max
        if abs(gate_init) >= gate_g_max:
            raise ValueError("gate_init must satisfy abs(gate_init) < gate_g_max")
        self.gate_init = gate_init
        self.gamma_raw = nn.Embedding(num_relations_total, 1)
        self.eta_raw = nn.Embedding(num_relations_total, 1)
        raw_init = math.atanh(gate_init / gate_g_max) if gate_init != 0.0 else 0.0
        nn.init.constant_(self.gamma_raw.weight, raw_init)
        nn.init.constant_(self.eta_raw.weight, raw_init)

        self.path_score_norm = None
        self.seion_query_norm = None
        self.seion_target_norm = None
        self.path_scale_raw = None
        self.seion_scale_raw = None
        if standalone_mode != "residual":
            if enable_path:
                self.path_score_norm = nn.LayerNorm(dim)
                self.path_scale_raw = nn.Embedding(num_relations_total, 1)
                nn.init.constant_(self.path_scale_raw.weight, math.log(math.expm1(1.0)))
            if enable_seion:
                self.seion_query_norm = nn.LayerNorm(dim)
                self.seion_target_norm = nn.LayerNorm(dim)
                self.seion_scale_raw = nn.Embedding(num_relations_total, 1)
                nn.init.constant_(self.seion_scale_raw.weight, math.log(math.expm1(1.0)))

    def _gate(self, raw: nn.Embedding, r_ids: torch.Tensor) -> torch.Tensor:
        return self.gate_g_max * torch.tanh(raw(r_ids).squeeze(-1))

    def _tail_embed(self, ids: torch.Tensor) -> torch.Tensor:
        return self.entity_tail(ids) if self.base_expert_name == "cp" else self.entity(ids)

    @staticmethod
    def _positive_scale(raw: nn.Embedding, r_ids: torch.Tensor) -> torch.Tensor:
        return torch.nn.functional.softplus(raw(r_ids).squeeze(-1)) + 1e-6

    def _run_path_reasoner(
        self,
        h_ids: torch.Tensor, r_ids: torch.Tensor, t_ids: torch.Tensor,
        adjacency: Union[Adjacency, CSRAdjacency], query_vecs: torch.Tensor, seed: int, training: bool,
    ) -> PathReasonerOutput:
        """Gate 13.2b: the ONE call site that dispatches to whichever
        reasoner backend is active and returns a backend-agnostic
        ``PathReasonerOutput`` — callers (``score_positive``,
        ``score_tail_candidates``) never branch on backend themselves.
        ``adjacency`` must already be the type the active backend expects
        (``Adjacency`` for ``"legacy"``, ``CSRAdjacency`` for
        ``"batched"``) — the caller (``train.py``) builds the matching one
        once per run, per ``args.path_backend``."""
        num_nodes = self.entity.num_embeddings
        if self.path_backend == "legacy":
            frontiers = self.path_reasoner.run_batch_frontiers(
                adjacency, self.relation.weight, h_ids, r_ids, t_ids, query_vecs, seed, training,
                entity_embed=self.entity.weight,
            )
            return PathReasonerOutput.from_legacy_frontiers(frontiers, num_nodes, self.path_reasoner.unreached_state)
        frontier = self.path_reasoner.run_batch_frontiers(
            adjacency, self.relation.weight, h_ids, r_ids, t_ids, query_vecs, seed, training,
        )
        return PathReasonerOutput.from_batched_frontier(frontier, num_nodes, self.path_reasoner.unreached_state)

    def score_positive(
        self,
        h_ids: torch.Tensor, r_ids: torch.Tensor, t_ids: torch.Tensor,
        adjacency: Optional[Adjacency] = None, seed: int = 0, training: bool = True,
        return_breakdown: bool = False, context: Optional[torch.Tensor] = None,
    ):
        """Gate 13.1: ``return_breakdown=True`` additionally returns a dict of
        per-branch GATED contributions (``gamma * s_path``, ``eta * s_seion``)
        and raw gate values, keyed by branch name — used by
        ``gate_diagnostics.jsonl`` logging (``train.py``) and by the router
        activation acceptance test. Never changes ``s`` itself."""
        h = self.entity(h_ids)
        r = self.relation(r_ids)
        t = self._tail_embed(t_ids)
        s = self.base.score_positive(h, r, t) if self.use_base_scorer else torch.zeros(h.shape[0], device=h.device)
        breakdown: Dict[str, torch.Tensor] = {"s_base": s}

        if self.enable_path and adjacency is not None:
            output = self._run_path_reasoner(h_ids, r_ids, t_ids, adjacency, r, seed, training)
            query_ids = torch.arange(h_ids.shape[0], device=h_ids.device)
            reached = output.state_for(query_ids, t_ids)
            path_vec = self.path_score_norm(reached) if self.path_score_norm is not None else reached
            path_target = self.path_score_norm(t) if self.path_score_norm is not None else t
            s_path = (path_vec * path_target).sum(dim=-1) / math.sqrt(self.dim)
            gamma = self._positive_scale(self.path_scale_raw, r_ids) if self.path_scale_raw is not None else self._gate(self.gamma_raw, r_ids)
            s = s + gamma * s_path
            breakdown["gamma_path"] = gamma * s_path
            breakdown["gamma_path_gate"] = gamma
            breakdown["gamma_path_raw"] = s_path  # PRE-gate branch score (signed-gate diagnostics)

        if self.enable_seion:
            seion_t = self.entity(t_ids)  # always the shared table, see score_tail_candidates note
            seion_context = r if context is None else context
            if self.seion_query_norm is not None:
                s_seion = (self.seion_query_norm(self.seion_scorer.q_seion(h, r, seion_context)) * self.seion_target_norm(self.seion_scorer.T(seion_t))).sum(dim=-1) / math.sqrt(self.dim)
            else:
                s_seion = self.seion_scorer.score_positive(h, r, seion_context, seion_t)
            eta = self._positive_scale(self.seion_scale_raw, r_ids) if self.seion_scale_raw is not None else self._gate(self.eta_raw, r_ids)
            s = s + eta * s_seion
            breakdown["eta_seion"] = eta * s_seion
            breakdown["eta_seion_gate"] = eta
            breakdown["eta_seion_raw"] = s_seion  # PRE-gate branch score

        if self.enable_generic_residual:
            generic_t = self.entity(t_ids)
            generic_context = r if context is None else context
            s_generic = self.generic_residual_scorer.score_positive(h, r, generic_context, generic_t)
            eta = self._gate(self.eta_raw, r_ids)
            s = s + eta * s_generic
            breakdown["eta_generic"] = eta * s_generic
            breakdown["eta_generic_gate"] = eta
            breakdown["eta_generic_raw"] = s_generic

        if self.enable_structural_kernel:
            kernel_t = self.entity(t_ids)  # shared table, same convention as the seionic branch
            gated_vec, kernel_breakdown = self.structural_kernel(h, r, r, r_ids, return_breakdown=True)
            s_kernel = (gated_vec * kernel_t).sum(dim=-1) / math.sqrt(self.dim)
            s_kernel_raw = (kernel_breakdown["raw_branch_output"] * kernel_t).sum(dim=-1) / math.sqrt(self.dim)
            s = s + s_kernel
            breakdown["kernel_structural"] = s_kernel
            breakdown["kernel_structural_gate"] = kernel_breakdown["gate"]
            breakdown["kernel_structural_raw"] = s_kernel_raw

        if return_breakdown:
            breakdown["s_total"] = s
            return s, breakdown
        return s

    def score_tail_candidates(
        self,
        h_ids: torch.Tensor, r_ids: torch.Tensor, candidates_ids: torch.Tensor,
        adjacency: Optional[Adjacency] = None, seed: int = 0, training: bool = True,
        gold_tail_ids: Optional[torch.Tensor] = None,
        context: Optional[torch.Tensor] = None,
    ) -> torch.Tensor:
        """``candidates_ids``: ``[K]`` (shared) or ``[B,K]`` (per-row).
        ``gold_tail_ids`` is only needed to exclude the queried edge from
        the reasoner's frontier during training when candidates are
        negatives (the gold tail itself is scored via ``score_positive``)."""
        h = self.entity(h_ids)
        r = self.relation(r_ids)
        cand_emb = self._tail_embed(candidates_ids)
        s = self.base.score_tail_candidates(h, r, cand_emb) if self.use_base_scorer else torch.zeros(h.shape[0], cand_emb.shape[-2], device=h.device)

        if self.enable_path and adjacency is not None:
            t_for_frontier = gold_tail_ids if gold_tail_ids is not None else torch.zeros_like(h_ids)
            output = self._run_path_reasoner(h_ids, r_ids, t_for_frontier, adjacency, r, seed, training)
            batch = h_ids.shape[0]
            cand_ids_2d = candidates_ids if candidates_ids.ndim == 2 else candidates_ids.unsqueeze(0).expand(batch, -1)
            query_ids = torch.arange(batch, device=h_ids.device)
            states = output.states_for_candidates(query_ids, cand_ids_2d)  # [B,K,dim]
            cand_full = cand_emb if cand_emb.ndim == 3 else cand_emb.unsqueeze(0).expand(batch, -1, -1)
            path_states = self.path_score_norm(states) if self.path_score_norm is not None else states
            path_cand = self.path_score_norm(cand_full) if self.path_score_norm is not None else cand_full
            s_path = (path_states * path_cand).sum(dim=-1) / math.sqrt(self.dim)
            gamma = (self._positive_scale(self.path_scale_raw, r_ids) if self.path_scale_raw is not None else self._gate(self.gamma_raw, r_ids)).unsqueeze(-1)
            s = s + gamma * s_path

        if self.enable_seion:
            # The seionic branch always scores against entity embeddings
            # from the shared table (not the CP tail-role table) — it is
            # an independent scalar expert, not tied to CPExpert's
            # asymmetric embedding convention.
            seion_cand = self.entity(candidates_ids)
            seion_context = r if context is None else context
            if self.seion_query_norm is not None:
                q = self.seion_query_norm(self.seion_scorer.q_seion(h, r, seion_context))
                target = self.seion_target_norm(self.seion_scorer.T(seion_cand))
                s_seion = (torch.einsum("bd,bkd->bk", q, target) if target.ndim == 3 else q @ target.T) / math.sqrt(self.dim)
            else:
                s_seion = self.seion_scorer.score_tail_candidates(h, r, seion_context, seion_cand)
            eta = (self._positive_scale(self.seion_scale_raw, r_ids) if self.seion_scale_raw is not None else self._gate(self.eta_raw, r_ids)).unsqueeze(-1)
            s = s + eta * s_seion

        if self.enable_generic_residual:
            generic_cand = self.entity(candidates_ids)
            generic_context = r if context is None else context
            s_generic = self.generic_residual_scorer.score_tail_candidates(h, r, generic_context, generic_cand)
            eta = self._gate(self.eta_raw, r_ids).unsqueeze(-1)
            s = s + eta * s_generic

        if self.enable_structural_kernel:
            # Same efficient pattern as the seionic branch: run the
            # kernel ONCE per query row -> [B,dim], then a single dot
            # product against candidates -> [B,K]. Never materializes a
            # [B,K,kernel_dim] intermediate.
            kernel_cand = self.entity(candidates_ids)
            raw = self.structural_kernel(h, r, r, r_ids)  # [B, dim]
            kernel_cand_full = kernel_cand if kernel_cand.ndim == 3 else kernel_cand.unsqueeze(0).expand(h.shape[0], -1, -1)
            s_kernel = torch.einsum("bd,bkd->bk", raw, kernel_cand_full) / math.sqrt(self.dim)
            s = s + s_kernel
        return s
