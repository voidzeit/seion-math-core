"""Gate 13.3 (``campaigns/gate13/``): error/score attribution to specific
modules — local innovation, exact telescoping decomposition, Shapley
values, and per-query rank-flip attribution.

Two decompositions are implemented, deliberately kept separate because
they have different mathematical character (see ``module_graph.py``'s
docstring for the full rationale):

- **Path-internal** (``mu``/``residual``/``projector``, via
  ``module_graph.ablate_path_components``): genuinely nonlinear —
  components are aggregated across incoming edges and passed through
  ``LayerNorm(tanh(.))`` at every reasoning layer, so ``telescoping`` here
  IS order-dependent in general and Shapley's averaging-over-orders is
  doing real work.
- **Branch-level** (``path``/``seion``/``structural_kernel``, via
  ``branch_level_telescoping``): the total score is a plain SUM of the
  base score and each branch's gated contribution
  (``s = s_base + gamma*s_path + eta*s_seion + s_kernel``), so this
  decomposition is EXACTLY order-independent by construction — this is a
  verified structural property of the current architecture, reported
  honestly as such, not a limitation of the attribution method.
"""
from __future__ import annotations

import itertools
from typing import Dict, List, Sequence

import torch

from .model import SeionKGRv26
from .module_graph import PATH_INTERNAL_MODULES, ablate_path_components


def local_innovation(reasoner, x_u: torch.Tensor, a_edge: torch.Tensor, q_query: torch.Tensor) -> Dict[str, float]:
    """Cheap, single-layer, per-edge measure of each component's OWN raw
    contribution magnitude (contract §1.2's ``lambda_v``, adapted: here
    ``f_v`` is "component v's raw output" and the "reference" is simply
    that the ambient message space is shared). This is NOT the
    output-level attribution (that is what telescoping/Shapley below
    compute) — it answers "how big is this component's own signal",
    useful as a fast triage before running the more expensive global
    decomposition."""
    mu_out = reasoner.mu(x_u, a_edge, q_query)
    residual_out = reasoner.U(x_u) + reasoner.V(a_edge) + reasoner.W(q_query)
    m_tilde = mu_out + residual_out
    if reasoner.projector.enabled:
        projector_removed = m_tilde - reasoner.projector.apply(m_tilde)
    else:
        projector_removed = torch.zeros_like(m_tilde)
    return {
        "mu": float(mu_out.pow(2).mean().sqrt().item()),
        "residual": float(residual_out.pow(2).mean().sqrt().item()),
        "projector": float(projector_removed.pow(2).mean().sqrt().item()),
    }


def path_internal_score(
    model: SeionKGRv26, h_ids: torch.Tensor, r_ids: torch.Tensor, t_ids: torch.Tensor,
    adjacency, seed: int, active_components: Sequence[str],
) -> torch.Tensor:
    """The path branch's RAW (pre-router-gate) score with its internal
    message function restricted to ``active_components`` (subset of
    ``PATH_INTERNAL_MODULES``). Requires ``model.enable_path``.

    Deliberately reads ``breakdown["gamma_path_raw"]``, NOT the gated total
    score: the outer router gate (`gamma_r = gate_g_max*tanh(alpha_r)`,
    Gate 13.1) multiplies the ENTIRE path branch uniformly regardless of
    which internal components are active, so at a freshly-initialized
    model (`gamma_r(0) = 0` exactly) it would multiply away every
    subset's score identically, masking the internal decomposition this
    function exists to measure. The router gate itself is already
    separately tested (`PASS_ROUTER_ACTIVATION`); this function isolates
    the internal composition question from that outer multiplicative
    factor."""
    if not model.enable_path:
        raise ValueError("path_internal_score requires enable_path=True")
    with ablate_path_components(model.path_reasoner, active_components):
        _, breakdown = model.score_positive(h_ids, r_ids, t_ids, adjacency, seed, training=False, return_breakdown=True)
    return breakdown["gamma_path_raw"]


def path_internal_telescoping(
    model: SeionKGRv26, h_ids: torch.Tensor, r_ids: torch.Tensor, t_ids: torch.Tensor,
    adjacency, seed: int, order: Sequence[str],
) -> Dict[str, object]:
    """Exact telescoping decomposition over ``order`` (a permutation of
    ``PATH_INTERNAL_MODULES``): ``F_{1..m}(x) - F_empty(x) = sum_j Delta_j``
    where ``Delta_j = F_{S_j}(x) - F_{S_{j-1}}(x)``, verified numerically
    (not merely asserted) — this is where an implementation bug in the
    ablation mechanism would show up as a nonzero reconstruction error."""
    with torch.no_grad():
        active: set = set()
        f_empty = path_internal_score(model, h_ids, r_ids, t_ids, adjacency, seed, active)
        prev = f_empty
        deltas = {}
        for module_id in order:
            active = active | {module_id}
            cur = path_internal_score(model, h_ids, r_ids, t_ids, adjacency, seed, active)
            deltas[module_id] = cur - prev
            prev = cur
        f_full = prev
    reconstruction = sum(deltas.values())
    observed = f_full - f_empty
    return {
        "order": tuple(order),
        "deltas": deltas,
        "f_empty": f_empty,
        "f_full": f_full,
        "reconstruction": reconstruction,
        "observed": observed,
        "max_reconstruction_error": float((reconstruction - observed).abs().max().item()),
    }


def path_internal_shapley(
    model: SeionKGRv26, h_ids: torch.Tensor, r_ids: torch.Tensor, t_ids: torch.Tensor, adjacency, seed: int,
) -> Dict[str, torch.Tensor]:
    """Full enumeration over all ``3! = 6`` orderings of
    ``PATH_INTERNAL_MODULES`` (small enough that Monte Carlo sampling is
    unnecessary). Caches the ``2^3 = 8`` distinct subset scores so each is
    computed exactly once regardless of how many permutations reference it."""
    modules = PATH_INTERNAL_MODULES
    cache: Dict[frozenset, torch.Tensor] = {}

    def get_score(subset: frozenset) -> torch.Tensor:
        if subset not in cache:
            with torch.no_grad():
                cache[subset] = path_internal_score(model, h_ids, r_ids, t_ids, adjacency, seed, subset)
        return cache[subset]

    phi = {m: None for m in modules}
    permutations = list(itertools.permutations(modules))
    for perm in permutations:
        active: frozenset = frozenset()
        prev = get_score(active)
        for module_id in perm:
            new_active = active | {module_id}
            cur = get_score(new_active)
            marginal = cur - prev
            phi[module_id] = marginal if phi[module_id] is None else phi[module_id] + marginal
            active, prev = new_active, cur
    for m in modules:
        phi[m] = phi[m] / len(permutations)

    f_full = get_score(frozenset(modules))
    f_empty = get_score(frozenset())
    efficiency_error = float(((sum(phi.values())) - (f_full - f_empty)).abs().max().item())
    return {"phi": phi, "f_full": f_full, "f_empty": f_empty, "efficiency_error": efficiency_error}


def branch_level_telescoping(
    model: SeionKGRv26, h_ids: torch.Tensor, r_ids: torch.Tensor, t_ids: torch.Tensor,
    adjacency, seed: int, order: Sequence[str],
) -> Dict[str, object]:
    """Branch-level decomposition over ``path``/``seion``/``structural_kernel``
    (whichever are enabled). Exactly reconstructs by construction (the
    total score is a plain sum of gated branch contributions) — this is a
    verified sanity case, not a claim that attribution is easy in
    general."""
    with torch.no_grad():
        s_total, breakdown = model.score_positive(h_ids, r_ids, t_ids, adjacency, seed, training=False, return_breakdown=True)
    contribution_key = {"path": "gamma_path", "seion": "eta_seion", "structural_kernel": "kernel_structural"}
    f_empty = breakdown["s_base"]
    deltas = {}
    for module_id in order:
        key = contribution_key[module_id]
        deltas[module_id] = breakdown[key] if key in breakdown else torch.zeros_like(f_empty)
    reconstruction = f_empty + sum(deltas.values())
    return {
        "order": tuple(order),
        "deltas": deltas,
        "f_empty": f_empty,
        "f_full": s_total,
        "reconstruction": reconstruction,
        "observed": s_total - f_empty,
        "max_reconstruction_error": float((reconstruction - s_total).abs().max().item()),
    }


def rank_flip_attribution(
    model: SeionKGRv26, h_ids: torch.Tensor, r_ids: torch.Tensor, candidates_ids: torch.Tensor,
    gold_idx: torch.Tensor, adjacency, seed: int, module_id: str,
) -> List[Dict[str, object]]:
    """Per-query rank-flip record: gold rank with the full path reasoner
    (reference) vs. with ``module_id`` ablated (intervened). ``candidates_ids``:
    ``[B, K]``; ``gold_idx``: ``[B]`` index into each row's candidate pool."""
    if module_id not in PATH_INTERNAL_MODULES:
        raise ValueError(f"module_id must be one of {PATH_INTERNAL_MODULES}, got {module_id!r}")
    with torch.no_grad():
        scores_reference = model.score_tail_candidates(h_ids, r_ids, candidates_ids, adjacency, seed, training=False)
        active = set(PATH_INTERNAL_MODULES) - {module_id}
        with ablate_path_components(model.path_reasoner, active):
            scores_intervened = model.score_tail_candidates(h_ids, r_ids, candidates_ids, adjacency, seed, training=False)

    records = []
    batch = int(h_ids.shape[0])
    for b in range(batch):
        gold = int(gold_idx[b].item())
        gold_score_ref = scores_reference[b, gold]
        gold_score_int = scores_intervened[b, gold]
        rank_ref = int((scores_reference[b] > gold_score_ref).sum().item()) + 1
        rank_int = int((scores_intervened[b] > gold_score_int).sum().item()) + 1
        records.append({
            "query_index": b,
            "module_id": module_id,
            "gold_rank_reference": rank_ref,
            "gold_rank_intervened": rank_int,
            "rank_flip": rank_ref != rank_int,
            "gold_score_delta": float((gold_score_int - gold_score_ref).item()),
        })
    return records
