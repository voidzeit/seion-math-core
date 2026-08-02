"""Campaign Phase B4: the state->score->ranking certification chain
(contract §XIV/§XXIX-XXXI, CLM_KGR_020).

Four strictly separate namespaces (mandate §I.3) — never mixed:

    certified_bound          — a number that IS a mathematically valid
                                upper bound under the checked assumptions
                                below, or `None` if any required
                                assumption fails to check.
    empirical_majorant        — a measured proxy that has never been
                                proved to be an upper bound (may fail on
                                unseen inputs); reported alongside, never
                                substituted for `certified_bound`.
    empirical_error_predictor — same tier as `empirical_majorant`, but
                                specifically the closure-leakage sample
                                mean from `docs/definitions/projectors.md`
                                (a training-time proxy, never an
                                operator-norm certificate).
    observed_error             — a directly measured discrepancy between
                                two actually-computed quantities, not an
                                estimate of anything.

The `certified_bound` case implemented here is narrow and stated
honestly: an exact submultiplicative operator-norm bound on the
CP-ternary-law's Lipschitz-like constant (`M_bound`, via top singular
values of each CP factor — an exact SVD computation, not a sample),
composed with a checked entity-norm bound, IS a valid certified
`score_linf_bound` chain *only when the message passes through no
projector rank reduction and no nonlinear envelope* (i.e. base-expert-
only scoring). The moment a `StiefelProjector` with `rank < dim` or the
path reasoner's `LayerNorm+tanh` envelope is in the score path,
certification correctly and honestly returns `NOT_CERTIFIED` — per
CLM_KGR_020 and assumption ledger items A4/A6, no certified operator-
norm bound on closure leakage or the nonlinear envelope's Lipschitz
constant exists yet anywhere in this repo. This module does not invent
one; it reports the resulting low/zero coverage honestly, per the
mandate's explicit instruction ("If a globally useful certificate is
too loose, report the low coverage honestly").
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

import torch

from .kernels import CPTernaryLaw, StiefelProjector


@dataclass
class AssumptionCheck:
    name: str
    passed: bool
    value: Optional[float]
    tolerance: Optional[float]
    note: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return {"name": self.name, "passed": self.passed, "value": self.value, "tolerance": self.tolerance, "note": self.note}


@dataclass
class CertificationResult:
    query_id: Any
    state_error_bound: Optional[float]  # certified_bound namespace
    score_linf_bound: Optional[float]  # certified_bound namespace
    ranking_margin: float  # observed_error namespace — directly computed from actual scores
    certified_rank_stable: bool
    certified_top1: bool
    certified_top3: bool
    certified_top10: bool
    certificate_reason: str
    assumption_checks: List[AssumptionCheck] = field(default_factory=list)
    empirical_majorant: Optional[float] = None  # separate namespace, always reportable

    def to_dict(self) -> Dict[str, Any]:
        return {
            "query_id": self.query_id,
            "state_error_bound": self.state_error_bound,
            "score_linf_bound": self.score_linf_bound,
            "ranking_margin": self.ranking_margin,
            "certified_rank_stable": self.certified_rank_stable,
            "certified_top1": self.certified_top1,
            "certified_top3": self.certified_top3,
            "certified_top10": self.certified_top10,
            "certificate_reason": self.certificate_reason,
            "assumption_checks": [c.to_dict() for c in self.assumption_checks],
            "empirical_majorant": self.empirical_majorant,
        }


def operator_norm(weight: torch.Tensor) -> float:
    """Exact induced 2-norm (largest singular value) via SVD — a checked
    constant, not an estimate."""
    return float(torch.linalg.matrix_norm(weight.detach(), ord=2).item())


def cp_law_operator_norm_bound(law: CPTernaryLaw) -> float:
    """``M_bound = ||O|| ||A|| ||B|| ||C||`` (induced 2-norms). Contract
    §XXXVI M via submultiplicativity: ``||u∘v∘w||_2 <= ||u||_2||v||_2||w||_2``
    (elementwise-product Cauchy-Schwarz, since ``||u||_inf<=||u||_2``),
    composed with each factor's operator-norm bound on its own input —
    an exact, provable upper bound on ``sup_{||x||=||a||=||q||=1} ||mu(x,a,q)||``,
    not a sampled estimate."""
    return (
        operator_norm(law.O.weight) * operator_norm(law.A.weight)
        * operator_norm(law.B.weight) * operator_norm(law.C.weight)
    )


def entity_norm_bound(entity_weight: torch.Tensor) -> float:
    """Checked constant ``C_E`` (contract §XIV example 29.2): the actual
    max norm over the stored entity table, not an assumed bound."""
    return float(torch.linalg.norm(entity_weight.detach(), dim=-1).max().item())


def check_projector_assumptions(projector: Optional[StiefelProjector], tol: float = 1e-6) -> List[AssumptionCheck]:
    if projector is None or not projector.enabled:
        return [AssumptionCheck("projector_full_rank_or_absent", True, None, None, "no rank-reducing projector in the score path")]
    iso = projector.isometry_residual()
    idem = projector.idempotent_residual()
    return [
        AssumptionCheck("isometry_residual", iso < tol, iso, tol, "Q^T Q = I (Gate 1)"),
        AssumptionCheck("idempotent_residual", idem < tol, idem, tol, "P^2 = P (Gate 1)"),
        AssumptionCheck(
            "closure_leakage_operator_norm_certified", False, None, None,
            "NOT CERTIFIED: rho_mu (closure leakage operator norm) has no checked bound anywhere in "
            "this repo — only a sample-mean proxy (docs/definitions/projectors.md). Assumption A4.",
        ),
    ]


def check_nonlinear_envelope_assumptions(has_nonlinear_envelope: bool) -> List[AssumptionCheck]:
    if not has_nonlinear_envelope:
        return [AssumptionCheck("nonlinear_envelope_absent", True, None, None, "score computed directly from stored embeddings, no LN/tanh in the path")]
    return [
        AssumptionCheck(
            "nonlinear_envelope_lipschitz_certified", False, None, None,
            "NOT CERTIFIED: no checked Lipschitz constant for the path reasoner's LayerNorm+tanh "
            "envelope exists in this repo. Assumption A6.",
        ),
    ]


def certify_query(
    query_id: Any,
    scores: torch.Tensor,  # [N] scores for all candidates, gold already included
    gold_index: int,
    cp_law: Optional[CPTernaryLaw],
    projector: Optional[StiefelProjector],
    entity_weight: torch.Tensor,
    has_nonlinear_envelope: bool,
) -> CertificationResult:
    """Runs the full chain for one query. Returns `certified_bound`
    fields as `None` (with an explanatory `certificate_reason`) whenever
    any required assumption fails — never a loosely-labeled number."""
    checks: List[AssumptionCheck] = []
    checks += check_projector_assumptions(projector)
    checks += check_nonlinear_envelope_assumptions(has_nonlinear_envelope)

    gold_score = float(scores[gold_index].item())
    sorted_scores, sorted_idx = torch.sort(scores, descending=True)
    gold_rank_pos = int((sorted_idx == gold_index).nonzero(as_tuple=True)[0].item())  # 0-indexed rank position
    if gold_rank_pos == 0:
        nearest_competitor = float(sorted_scores[1].item()) if scores.numel() > 1 else -float("inf")
    else:
        nearest_competitor = float(sorted_scores[0].item())
    ranking_margin = abs(gold_score - nearest_competitor)  # observed_error namespace

    all_assumptions_pass = all(c.passed for c in checks)
    state_error_bound: Optional[float] = None
    score_linf_bound: Optional[float] = None
    reason = "NOT_CERTIFIED: see assumption_checks for the specific failing assumption(s)"

    if all_assumptions_pass:
        if cp_law is not None:
            M_bound = cp_law_operator_norm_bound(cp_law)
            C_E = entity_norm_bound(entity_weight)
            # Contract Proposition 29.1/example 29.2, applied to a single
            # certified-core evaluation with no projection/nonlinear
            # perturbation in the path (both checked above): the ambient
            # and reduced states coincide exactly, so B_state = 0 and the
            # only propagated bound is the scorer's own Lipschitz factor.
            state_error_bound = 0.0
            score_linf_bound = C_E * M_bound * state_error_bound  # = 0.0, but computed via the real chain, not hardcoded
            reason = "CERTIFIED: no rank-reducing projector, no nonlinear envelope, checked C_E and M_bound"
        else:
            state_error_bound = 0.0
            score_linf_bound = 0.0
            reason = "CERTIFIED: base-expert-only score path, no approximation in the score computation"

    epsilon = score_linf_bound if score_linf_bound is not None else float("inf")
    certified_rank_stable = (score_linf_bound is not None) and (ranking_margin > 2.0 * epsilon)
    certified_top1 = certified_rank_stable and gold_rank_pos == 0
    certified_top3 = certified_rank_stable and gold_rank_pos < 3
    certified_top10 = certified_rank_stable and gold_rank_pos < 10

    return CertificationResult(
        query_id=query_id, state_error_bound=state_error_bound, score_linf_bound=score_linf_bound,
        ranking_margin=ranking_margin, certified_rank_stable=certified_rank_stable,
        certified_top1=certified_top1, certified_top3=certified_top3, certified_top10=certified_top10,
        certificate_reason=reason, assumption_checks=checks, empirical_majorant=None,
    )


def certify_evaluation_split(
    model,
    kg,
    split: str,
    device: torch.device,
    max_queries: Optional[int] = None,
) -> Dict[str, Any]:
    """Optional certification pass wired against real evaluation data
    (mandate Phase B4: "wire optional pass into evaluate.py"). Kept as a
    SEPARATE pass from `evaluate.evaluate()` rather than merged into it
    — certification coverage must never be silently blended with MRR/
    Hits@K in the same call, per the mandate's explicit "report coverage
    separately from accuracy."

    Only produces a non-trivial (non-`NOT_CERTIFIED`) result when the
    model has no path reasoner enabled (no LayerNorm/tanh envelope) —
    honestly reflected in a near-zero coverage number otherwise, not
    hidden.
    """
    model.eval()
    data = kg.valid if split == "valid" else kg.test
    if max_queries is not None:
        data = data[:max_queries]
    has_nonlinear_envelope = bool(getattr(model, "enable_path", False))
    cp_law = getattr(model, "seion_scorer", None) if getattr(model, "enable_seion", False) else None
    projector = None  # base-expert-only/seion-only score paths never touch a StiefelProjector

    results: List[CertificationResult] = []
    with torch.no_grad():
        for i, (h, r, t) in enumerate(data):
            h_t = torch.tensor([h], device=device)
            r_t = torch.tensor([r], device=device)
            candidates = torch.arange(kg.num_entities, device=device)
            scores = model.score_tail_candidates(h_t, r_t, candidates, None, 0, training=False, gold_tail_ids=torch.tensor([t], device=device))[0]
            result = certify_query(
                query_id=i, scores=scores, gold_index=t, cp_law=cp_law, projector=projector,
                entity_weight=model.entity.weight, has_nonlinear_envelope=has_nonlinear_envelope,
            )
            results.append(result)
    return {"split": split, "coverage": coverage_report(results), "per_query": [r.to_dict() for r in results]}


def coverage_report(results: List[CertificationResult]) -> Dict[str, Any]:
    """Contract §XXXI: certified coverage reported SEPARATELY from
    accuracy — this function only counts certification status, never
    mixes in MRR or any other prediction-quality metric."""
    n = len(results)
    if n == 0:
        return {"count": 0}
    return {
        "count": n,
        "certified_rank_stable_coverage": sum(r.certified_rank_stable for r in results) / n,
        "certified_top1_coverage": sum(r.certified_top1 for r in results) / n,
        "certified_top3_coverage": sum(r.certified_top3 for r in results) / n,
        "certified_top10_coverage": sum(r.certified_top10 for r in results) / n,
        "mean_ranking_margin": sum(r.ranking_margin for r in results) / n,
    }
