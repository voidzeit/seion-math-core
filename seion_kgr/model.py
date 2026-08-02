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
"""
from __future__ import annotations

import math
from typing import Dict, List, Optional

import torch
import torch.nn as nn

from .data import KnowledgeGraph
from .kernels import SeionicScalarScorer
from .reasoner import Adjacency, PathReasoner
from .scorers import ComplExExpert, CPExpert, DistMultExpert, TuckERExpert
from .structural_kernel import KernelProvenance, StructuralKernelResidual

BASE_EXPERTS = ("complex", "distmult", "cp", "tucker")


class SeionKGRv26(nn.Module):
    def __init__(
        self,
        num_entities: int,
        num_relations_total: int,
        dim: int,
        base_expert: str = "complex",
        enable_path: bool = False,
        enable_seion: bool = False,
        seion_rank: int = 32,
        path_rank: int = 32,
        path_layers: int = 2,
        path_max_neighbors: int = 32,
        path_proj_rank: int = 0,
        path_selector_mode: str = "budgeted_bfs",
        structural_kernel: Optional[StructuralKernelResidual] = None,
        gate_g_max: float = 1.0,
    ):
        super().__init__()
        if base_expert not in BASE_EXPERTS:
            raise ValueError(f"base_expert must be one of {BASE_EXPERTS}, got {base_expert!r}")
        if base_expert == "complex" and dim % 2 != 0:
            raise ValueError("--dim must be even for the complex base expert")
        self.dim = dim
        self.base_expert_name = base_expert
        self.enable_path = enable_path
        self.enable_seion = enable_seion

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

        if enable_path:
            self.path_reasoner = PathReasoner(
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
        self.gamma_raw = nn.Embedding(num_relations_total, 1)
        self.eta_raw = nn.Embedding(num_relations_total, 1)
        nn.init.constant_(self.gamma_raw.weight, 0.0)
        nn.init.constant_(self.eta_raw.weight, 0.0)

    def _gate(self, raw: nn.Embedding, r_ids: torch.Tensor) -> torch.Tensor:
        return self.gate_g_max * torch.tanh(raw(r_ids).squeeze(-1))

    def _tail_embed(self, ids: torch.Tensor) -> torch.Tensor:
        return self.entity_tail(ids) if self.base_expert_name == "cp" else self.entity(ids)

    def score_positive(
        self,
        h_ids: torch.Tensor, r_ids: torch.Tensor, t_ids: torch.Tensor,
        adjacency: Optional[Adjacency] = None, seed: int = 0, training: bool = True,
        return_breakdown: bool = False,
    ):
        """Gate 13.1: ``return_breakdown=True`` additionally returns a dict of
        per-branch GATED contributions (``gamma * s_path``, ``eta * s_seion``)
        and raw gate values, keyed by branch name — used by
        ``gate_diagnostics.jsonl`` logging (``train.py``) and by the router
        activation acceptance test. Never changes ``s`` itself."""
        h = self.entity(h_ids)
        r = self.relation(r_ids)
        t = self._tail_embed(t_ids)
        s = self.base.score_positive(h, r, t)
        breakdown: Dict[str, torch.Tensor] = {}

        if self.enable_path and adjacency is not None:
            frontiers = self.path_reasoner.run_batch_frontiers(
                adjacency, self.relation.weight, h_ids, r_ids, t_ids, r, seed, training,
                entity_embed=self.entity.weight,
            )
            reached = torch.stack(
                [self.path_reasoner.state_for_node(f, int(t_ids[b])) for b, f in enumerate(frontiers)], dim=0,
            )
            s_path = (reached * t).sum(dim=-1) / math.sqrt(self.dim)
            gamma = self._gate(self.gamma_raw, r_ids)
            s = s + gamma * s_path
            breakdown["gamma_path"] = gamma * s_path
            breakdown["gamma_path_gate"] = gamma

        if self.enable_seion:
            seion_t = self.entity(t_ids)  # always the shared table, see score_tail_candidates note
            s_seion = self.seion_scorer.score_positive(h, r, r, seion_t)
            eta = self._gate(self.eta_raw, r_ids)
            s = s + eta * s_seion
            breakdown["eta_seion"] = eta * s_seion
            breakdown["eta_seion_gate"] = eta

        if self.enable_structural_kernel:
            kernel_t = self.entity(t_ids)  # shared table, same convention as the seionic branch
            raw = self.structural_kernel(h, r, r, r_ids)  # gate is internal to the module (near-zero init)
            s_kernel = (raw * kernel_t).sum(dim=-1) / math.sqrt(self.dim)
            s = s + s_kernel

        if return_breakdown:
            breakdown["s_total"] = s
            return s, breakdown
        return s

    def score_tail_candidates(
        self,
        h_ids: torch.Tensor, r_ids: torch.Tensor, candidates_ids: torch.Tensor,
        adjacency: Optional[Adjacency] = None, seed: int = 0, training: bool = True,
        gold_tail_ids: Optional[torch.Tensor] = None,
    ) -> torch.Tensor:
        """``candidates_ids``: ``[K]`` (shared) or ``[B,K]`` (per-row).
        ``gold_tail_ids`` is only needed to exclude the queried edge from
        the reasoner's frontier during training when candidates are
        negatives (the gold tail itself is scored via ``score_positive``)."""
        h = self.entity(h_ids)
        r = self.relation(r_ids)
        cand_emb = self._tail_embed(candidates_ids)
        s = self.base.score_tail_candidates(h, r, cand_emb)

        if self.enable_path and adjacency is not None:
            t_for_frontier = gold_tail_ids if gold_tail_ids is not None else torch.zeros_like(h_ids)
            frontiers = self.path_reasoner.run_batch_frontiers(
                adjacency, self.relation.weight, h_ids, r_ids, t_for_frontier, r, seed, training,
                entity_embed=self.entity.weight,
            )
            batch = h_ids.shape[0]
            cand_ids_2d = candidates_ids if candidates_ids.ndim == 2 else candidates_ids.unsqueeze(0).expand(batch, -1)
            states = torch.stack(
                [self.path_reasoner.states_for_candidates(frontiers[b], cand_ids_2d[b]) for b in range(batch)], dim=0,
            )  # [B,K,dim]
            cand_full = cand_emb if cand_emb.ndim == 3 else cand_emb.unsqueeze(0).expand(batch, -1, -1)
            s_path = (states * cand_full).sum(dim=-1) / math.sqrt(self.dim)
            gamma = self._gate(self.gamma_raw, r_ids).unsqueeze(-1)
            s = s + gamma * s_path

        if self.enable_seion:
            # The seionic branch always scores against entity embeddings
            # from the shared table (not the CP tail-role table) — it is
            # an independent scalar expert, not tied to CPExpert's
            # asymmetric embedding convention.
            seion_cand = self.entity(candidates_ids)
            s_seion = self.seion_scorer.score_tail_candidates(h, r, r, seion_cand)
            eta = self._gate(self.eta_raw, r_ids).unsqueeze(-1)
            s = s + eta * s_seion

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
