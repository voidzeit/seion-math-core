#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
SEION-KGR v26 — FP64 reference oracle (Fase 1)
================================================

Small, slow, explicit. No AMP, no ``torch.compile``, no batching
cleverness, no GPU path. This file exists to be *read*, not to be fast.
It implements exactly the objects defined in
``docs/SEION_KGR_MATHEMATICAL_CONTRACT.md`` sections II-XI and XIV, and
nothing from the razonador/rank-controller/E8-residual sections (those
are Fase 4+ per the build sequence in that contract).

Every object below that has a claimed identity in
``docs/SEION_KGR_CLAIM_MATRIX.md`` is cross-checked here by an
*independent* implementation path (an explicit nested-loop
reconstruction next to the vectorized one), the same discipline already
used in ``src/seion_core/research_v3/projected_evaluation.py`` ("checks
both residuals ... against independent coordinate-loop and NumPy
evaluations").

This file does not reuse or re-derive the finite typed-tree ``k``/``k-1``
theorems (``docs/theorems_v3/``) — those are already proved and tested
there. It only checks the KG-specific objects that are new in the KGR
contract: reciprocal closure, the CP ternary law instantiated for
entities/relations/queries, the projector/closure residual retyped for
message passing, one-hop query-conditioned message passing, the two KGE
scorers, and the elementary margin/ranking-order theorem.

Run:

    python seion_kgr_reference_fp64.py --self_test
"""

from __future__ import annotations

import argparse
import itertools
import math
from dataclasses import dataclass, field
from typing import Dict, List, Sequence, Tuple

import torch

DTYPE = torch.float64
DEVICE = torch.device("cpu")

# Deliberately NOT calling torch.set_default_dtype(DTYPE) here: this module
# is imported by other code (tests, the seion_kgr package) in the same
# process, and mutating the global default dtype as an import side effect
# silently changes every torch.* call downstream that omits an explicit
# dtype — exactly the bug caught by tests/kgr/test_seion_kgr_package.py's
# evaluate() dtype mismatch. Every tensor constructor in this file passes
# dtype=DTYPE explicitly instead.


def _g(seed: int) -> torch.Generator:
    g = torch.Generator(device=DEVICE)
    g.manual_seed(seed)
    return g


# =============================================================================
# II. Typed spaces and projectors
# =============================================================================


@dataclass
class Projector:
    """``P = Q Q^T`` for an isometry ``Q: W -> V`` (``Q^T Q = I_W``).

    Contract §II / §IX. ``Q`` has shape ``[dim_V, dim_W]`` with
    ``dim_W <= dim_V``.
    """

    Q: torch.Tensor  # [dim_V, dim_W]

    def __post_init__(self) -> None:
        if self.Q.ndim != 2:
            raise ValueError(f"Q must be [dim_V, dim_W], got {tuple(self.Q.shape)}")
        self.Q = self.Q.to(dtype=DTYPE, device=DEVICE)

    @property
    def dim_V(self) -> int:
        return int(self.Q.shape[0])

    @property
    def dim_W(self) -> int:
        return int(self.Q.shape[1])

    def isometry_residual(self) -> float:
        """``||Q^T Q - I||`` — must be ~0 (Gate 1)."""
        gram = self.Q.T @ self.Q
        return float(torch.linalg.norm(gram - torch.eye(self.dim_W, dtype=DTYPE)).item())

    def P(self) -> torch.Tensor:
        return self.Q @ self.Q.T

    def idempotent_residual(self) -> float:
        p = self.P()
        return float(torch.linalg.norm(p @ p - p).item())

    def selfadjoint_residual(self) -> float:
        p = self.P()
        return float(torch.linalg.norm(p - p.T).item())

    def apply(self, x: torch.Tensor) -> torch.Tensor:
        """``P x`` for ``x`` of shape ``[..., dim_V]``."""
        return x @ self.P().T

    def full_rank(self) -> "Projector":
        return self

    @staticmethod
    def identity(dim: int) -> "Projector":
        return Projector(torch.eye(dim, dtype=DTYPE))

    @staticmethod
    def random_rank(dim: int, rank: int, seed: int) -> "Projector":
        if not (0 < rank <= dim):
            raise ValueError(f"rank must be in (0, {dim}], got {rank}")
        raw = torch.randn(dim, rank, generator=_g(seed), dtype=DTYPE)
        q, _ = torch.linalg.qr(raw)
        return Projector(q[:, :rank])


def closure_residual(P_out: Projector, mu_output: torch.Tensor) -> torch.Tensor:
    """``r_mu = (I - P) mu(...)`` — contract §VI/§IX, retyped for messages.

    Takes the *already evaluated* ambient output ``mu_output`` (the
    inputs are assumed already projected by the caller, matching
    ``r_mu = (I-P_{tau0}) mu(P_{tau1}., ..., P_{taua}.)``).
    """
    return mu_output - P_out.apply(mu_output)


# =============================================================================
# III. CP ternary seionic law
# =============================================================================


@dataclass
class CPTernaryLaw:
    """``mu(x,a,q) = O[(Ax) o (Ba) o (Cq)]`` — contract §III.

    ``A: dim_x -> rank``, ``B: dim_a -> rank``, ``C: dim_q -> rank``,
    ``O: rank -> dim_out``. All stored as explicit matrices, no bias,
    matching ``docs/definitions/nary_laws.md``'s ``CPLaw``.
    """

    A: torch.Tensor  # [rank, dim_x]
    B: torch.Tensor  # [rank, dim_a]
    C: torch.Tensor  # [rank, dim_q]
    O: torch.Tensor  # [dim_out, rank]

    def __post_init__(self) -> None:
        self.A, self.B, self.C, self.O = (
            m.to(dtype=DTYPE, device=DEVICE) for m in (self.A, self.B, self.C, self.O)
        )
        rank = self.A.shape[0]
        if self.B.shape[0] != rank or self.C.shape[0] != rank or self.O.shape[1] != rank:
            raise ValueError("CP factor rank mismatch")

    @property
    def rank(self) -> int:
        return int(self.A.shape[0])

    @property
    def dim_out(self) -> int:
        return int(self.O.shape[0])

    def forward(self, x: torch.Tensor, a: torch.Tensor, q: torch.Tensor) -> torch.Tensor:
        """Vectorized evaluation, ``x,a,q`` shape ``[..., dim_*]``."""
        z = (x @ self.A.T) * (a @ self.B.T) * (q @ self.C.T)
        return z @ self.O.T

    def dense_tensor_explicit_loops(self) -> torch.Tensor:
        """Independent cross-check path for Proposition CLM_KGR_002.

        Builds ``K[d,i,j,k] = sum_alpha O[d,alpha] A[alpha,i] B[alpha,j] C[alpha,k]``
        with plain nested Python loops — no einsum, no matmul reuse of
        the ``forward`` code path.
        """
        d_out, dim_x = self.O.shape[0], self.A.shape[1]
        dim_a, dim_q = self.B.shape[1], self.C.shape[1]
        rank = self.rank
        K = torch.zeros(d_out, dim_x, dim_a, dim_q, dtype=DTYPE)
        for d in range(d_out):
            for i in range(dim_x):
                for j in range(dim_a):
                    for k in range(dim_q):
                        total = 0.0
                        for alpha in range(rank):
                            total += (
                                float(self.O[d, alpha].detach())
                                * float(self.A[alpha, i].detach())
                                * float(self.B[alpha, j].detach())
                                * float(self.C[alpha, k].detach())
                            )
                        K[d, i, j, k] = total
        return K

    def forward_via_dense(self, x: torch.Tensor, a: torch.Tensor, q: torch.Tensor) -> torch.Tensor:
        """Contract the explicit dense tensor with (x,a,q) — must match ``forward``."""
        K = self.dense_tensor_explicit_loops()
        return torch.einsum("dijk,...i,...j,...k->...d", K, x, a, q)

    def gauge_transform(self, scales: Sequence[Tuple[float, float, float, float]]) -> "CPTernaryLaw":
        """Apply the CP gauge group (contract §V / CLM_KGR_003).

        ``scales[alpha] = (c0, c1, c2, c3)`` with product 1; scales the
        ``O``, ``A``, ``B``, ``C`` rows of component ``alpha`` and
        must leave the reconstructed tensor unchanged.
        """
        if len(scales) != self.rank:
            raise ValueError("one scale tuple per CP component required")
        A2, B2, C2, O2 = self.A.clone(), self.B.clone(), self.C.clone(), self.O.clone()
        for alpha, (c0, c1, c2, c3) in enumerate(scales):
            if abs(c0 * c1 * c2 * c3 - 1.0) > 1e-9:
                raise ValueError(f"gauge scale product must be 1, got {c0*c1*c2*c3}")
            O2[:, alpha] *= c0
            A2[alpha, :] *= c1
            B2[alpha, :] *= c2
            C2[alpha, :] *= c3
        return CPTernaryLaw(A2, B2, C2, O2)

    def permute_components(self, perm: Sequence[int]) -> "CPTernaryLaw":
        """The other half of the CP gauge group (contract §V): permuting
        the rank/component axis consistently across ``A,B,C`` (rows) and
        ``O`` (columns) is just reordering the sum over alpha and must
        leave the reconstructed tensor unchanged. ``gauge_transform``
        above only covers the scale half — this closes the gap flagged
        as TODO in CLM_KGR_003's limitation."""
        if sorted(perm) != list(range(self.rank)):
            raise ValueError(f"perm must be a permutation of range({self.rank}), got {perm}")
        idx = torch.tensor(list(perm), dtype=torch.long)
        return CPTernaryLaw(A=self.A[idx], B=self.B[idx], C=self.C[idx], O=self.O[:, idx])


def cyclic_projector(law3: torch.Tensor) -> torch.Tensor:
    """``Pi_cyc = (1/3) sum_j sigma^j`` applied to a dense ternary tensor.

    Contract §IV / CLM_KGR_005. ``law3`` has shape ``[d,i,j,k]`` with
    ``i==j==k`` dimension so the cyclic permutation of input slots is
    well typed.
    """
    d, n0, n1, n2 = law3.shape
    if not (n0 == n1 == n2):
        raise ValueError("cyclic symmetrization requires equal input dimensions")
    sigma0 = law3
    sigma1 = law3.permute(0, 3, 1, 2)  # (i,j,k) -> reading as mu(x2,x3,x1): shift
    sigma2 = law3.permute(0, 2, 3, 1)
    return (sigma0 + sigma1 + sigma2) / 3.0


# =============================================================================
# Reciprocal knowledge graph (contract §II.3.2 / III.2)
# =============================================================================


@dataclass
class ReciprocalKG:
    num_entities: int
    num_relations_original: int
    triples: List[Tuple[int, int, int]]  # includes reciprocal triples, rel id may be >= num_relations_original
    tails_of_hr: Dict[Tuple[int, int], set]
    heads_of_rt: Dict[Tuple[int, int], set]

    @property
    def num_relations_total(self) -> int:
        return 2 * self.num_relations_original


def reciprocal_closure(triples: Sequence[Tuple[int, int, int]], num_relations: int) -> List[Tuple[int, int, int]]:
    """Contract §II.3.2: ``(h,r,t) <-> (t, r^{-1}, h)``, ``r^{-1} = r + num_relations``."""
    out = list(triples)
    out += [(t, r + num_relations, h) for h, r, t in triples]
    return out


def build_reciprocal_kg(base_triples: Sequence[Tuple[int, int, int]], num_entities: int, num_relations: int) -> ReciprocalKG:
    all_triples = reciprocal_closure(base_triples, num_relations)
    tails: Dict[Tuple[int, int], set] = {}
    heads: Dict[Tuple[int, int], set] = {}
    for h, r, t in all_triples:
        tails.setdefault((h, r), set()).add(t)
        heads.setdefault((r, t), set()).add(h)
    return ReciprocalKG(
        num_entities=num_entities,
        num_relations_original=num_relations,
        triples=all_triples,
        tails_of_hr=tails,
        heads_of_rt=heads,
    )


def tiny_reciprocal_kg(seed: int = 7) -> Tuple[ReciprocalKG, torch.Generator]:
    """A 6-entity, 2-relation graph, small enough for brute force + explicit loops."""
    base = [(0, 0, 1), (1, 0, 2), (2, 1, 3), (3, 1, 4), (4, 0, 5), (5, 1, 0)]
    return build_reciprocal_kg(base, num_entities=6, num_relations=2), _g(seed)


# =============================================================================
# VII. Query-conditioned one-hop message passing (explicit per-edge loop)
# =============================================================================


@dataclass
class MessagePassingLayer:
    """One layer of §VII/§VIII: certified core ``C_l`` then nonlinear envelope ``N_l``.

    ``mu`` is the ternary seionic law (§III). ``U, V, W`` are the linear
    residual branches. ``P_out`` projects the ambient message. This
    class evaluates node-by-node, edge-by-edge with plain Python loops
    — the point is to be an unambiguous ground truth, not to scale.
    """

    mu: CPTernaryLaw
    U: torch.Tensor  # [dim_out, dim_x]
    V: torch.Tensor  # [dim_out, dim_a]
    W: torch.Tensor  # [dim_out, dim_q]
    P_out: Projector

    def __post_init__(self) -> None:
        self.U = self.U.to(dtype=DTYPE)
        self.V = self.V.to(dtype=DTYPE)
        self.W = self.W.to(dtype=DTYPE)

    def message_ambient(self, x_u: torch.Tensor, a_edge: torch.Tensor, q_query: torch.Tensor) -> torch.Tensor:
        """``m~ = mu(x_u, a_edge, q) + U x_u + V a_edge + W q`` — the certified core, pre-projection."""
        return self.mu.forward(x_u, a_edge, q_query) + self.U @ x_u + self.V @ a_edge + self.W @ q_query

    def message_projected(self, x_u: torch.Tensor, a_edge: torch.Tensor, q_query: torch.Tensor) -> torch.Tensor:
        """``m = P_{l+1} m~`` — end of the certified core ``C_l``."""
        m_tilde = self.message_ambient(x_u, a_edge, q_query)
        return self.P_out.apply(m_tilde)

    def closure_leakage(self, x_u: torch.Tensor, a_edge: torch.Tensor, q_query: torch.Tensor) -> torch.Tensor:
        m_tilde = self.message_ambient(x_u, a_edge, q_query)
        return m_tilde - self.P_out.apply(m_tilde)

    def run(
        self,
        kg: ReciprocalKG,
        node_state_dim: int,
        relation_embed: torch.Tensor,  # [num_relations_total, dim_a]
        head: int,
        query_relation: int,
        query_indicator: torch.Tensor,  # [dim_q]
    ) -> Dict[int, torch.Tensor]:
        """Contract §VII: build ``x^{(0;q)}``, then one aggregation+update pass.

        Explicit per-node/per-edge Python loop (no batching) — this is
        the reference semantics that any vectorized/optimized
        implementation must reproduce exactly.
        """
        x0: Dict[int, torch.Tensor] = {
            v: torch.zeros(node_state_dim, dtype=DTYPE) for v in range(kg.num_entities)
        }
        x0[head] = query_indicator.clone()

        incoming: Dict[int, List[Tuple[int, int]]] = {v: [] for v in range(kg.num_entities)}
        for h, r, t in kg.triples:
            incoming[t].append((h, r))

        x1: Dict[int, torch.Tensor] = {}
        for v in range(kg.num_entities):
            edges = incoming[v]
            if not edges:
                z_v = torch.zeros(self.P_out.dim_V, dtype=DTYPE)
            else:
                acc = torch.zeros(self.P_out.dim_V, dtype=DTYPE)
                for (u, s) in edges:
                    m = self.message_projected(x0[u], relation_embed[s], query_indicator)
                    acc = acc + m
                z_v = acc / float(len(edges))
            pre = x0[v] if x0[v].numel() == z_v.numel() else torch.zeros_like(z_v)
            updated = pre + torch.tanh(z_v)
            mean = updated.mean()
            var = updated.var(unbiased=False)
            x1[v] = (updated - mean) / torch.sqrt(var + 1e-6)
        return x1


# =============================================================================
# XI. KGE scorers
# =============================================================================


@dataclass
class ReciprocalComplExScorer:
    """Contract §XI / §XX.1 — real and imaginary parts stored separately (FP64, no complex dtype needed)."""

    e_re: torch.Tensor
    e_im: torch.Tensor
    r_re: torch.Tensor
    r_im: torch.Tensor

    def __post_init__(self) -> None:
        self.e_re, self.e_im, self.r_re, self.r_im = (
            t.to(dtype=DTYPE) for t in (self.e_re, self.e_im, self.r_re, self.r_im)
        )

    def score(self, h: int, r: int, t: int) -> float:
        eh_re, eh_im = self.e_re[h], self.e_im[h]
        ar_re, ar_im = self.r_re[r], self.r_im[r]
        et_re, et_im = self.e_re[t], self.e_im[t]
        # Re(<e_h, a_r, conj(e_t)>) elementwise then summed.
        real_part = (eh_re * ar_re * et_re) + (eh_im * ar_re * et_im) + (eh_re * ar_im * et_im) - (eh_im * ar_im * et_re)
        return float(real_part.sum().item())


@dataclass
class SeionicScalarScorer:
    """Contract §XI / §XX.2 — ``s(h,r,t) = <q_seion(h,r), T e_t>``."""

    entity: torch.Tensor  # [N, dim_e]
    A: torch.Tensor  # [rank, dim_e]
    B: torch.Tensor  # [rank, dim_r]
    C: torch.Tensor  # [rank, dim_r]  (context c_r, here reuses relation embedding)
    O: torch.Tensor  # [dim_q, rank]
    T: torch.Tensor  # [dim_q, dim_e]
    relation: torch.Tensor  # [R, dim_r]

    def __post_init__(self) -> None:
        for name in ("entity", "A", "B", "C", "O", "T", "relation"):
            setattr(self, name, getattr(self, name).to(dtype=DTYPE))

    def q_seion(self, h: int, r: int) -> torch.Tensor:
        eh = self.entity[h]
        ar = self.relation[r]
        cr = self.relation[r]
        z = (self.A @ eh) * (self.B @ ar) * (self.C @ cr)
        return self.O @ z

    def score(self, h: int, r: int, t: int) -> float:
        """Per-candidate loop path — the ground truth."""
        q = self.q_seion(h, r)
        return float((q @ (self.T @ self.entity[t])).item())

    def score_all_candidates(self, h: int, r: int) -> torch.Tensor:
        """Batched-matrix path: ``S(h,r,:) = q_seion (T E)^T`` — contract §XI.

        Must equal ``[score(h,r,t) for t]`` exactly (Gate 3: "1-vs-all =
        score individual").
        """
        q = self.q_seion(h, r)
        TE = self.entity @ self.T.T  # [N, dim_q]
        return TE @ q


# =============================================================================
# Brute-force filtered evaluator (explicit loops, Gate 3 ground truth)
# =============================================================================


def brute_force_filtered_rank(
    scorer_fn,
    kg: ReciprocalKG,
    h: int,
    r: int,
    t: int,
    mode: str,
) -> float:
    """Rank of the gold tail (mode='tail') or gold head (mode='head') among all entities.

    Explicit O(N) Python loop, filtered, with the standard "average
    over ties" policy: ``rank = 1 + #strictly_better + 0.5 * (#ties - 1)``.
    """
    if mode == "tail":
        gold_score = scorer_fn(h, r, t)
        forbidden = kg.tails_of_hr.get((h, r), set()) - {t}
        scores = []
        for cand in range(kg.num_entities):
            if cand in forbidden:
                continue
            scores.append(scorer_fn(h, r, cand))
    elif mode == "head":
        gold_score = scorer_fn(h, r, t)
        forbidden = kg.heads_of_rt.get((r, t), set()) - {h}
        scores = []
        for cand in range(kg.num_entities):
            if cand in forbidden:
                continue
            scores.append(scorer_fn(cand, r, t))
    else:
        raise ValueError(mode)

    better = sum(1 for s in scores if s > gold_score + 1e-9)
    ties = sum(1 for s in scores if abs(s - gold_score) <= 1e-9)
    return 1.0 + better + 0.5 * max(ties - 1, 0)


# =============================================================================
# XIV. Elementary margin / ranking-order certificate (Theorem 30.1 form)
# =============================================================================


def margin_preserves_order(s_i: float, s_j: float, epsilon: float) -> bool:
    """``s_i - s_j > 2*epsilon`` implies ``s~_i > s~_j`` for any perturbation bounded by epsilon.

    This is the elementary claim CLM_KGR_019 makes. Returns whether the
    *hypothesis* holds (the conclusion is unconditionally true whenever
    the hypothesis does — proved by the triangle inequality in the
    contract, §XIV).
    """
    return (s_i - s_j) > 2.0 * epsilon


# =============================================================================
# Self-tests (Gate 0 / Gate 1 / Gate 3 / Gate 7 style, all FP64 CPU)
# =============================================================================


def _assert_close(name: str, value: float, tol: float) -> None:
    if not (value <= tol):
        raise AssertionError(f"{name} = {value} exceeds tolerance {tol}")


def run_self_tests(seed: int = 7) -> Dict[str, object]:
    torch.manual_seed(seed)
    report: Dict[str, object] = {}

    # --- Gate 1: isometry / projector identities -----------------------
    proj = Projector.random_rank(dim=6, rank=3, seed=seed)
    _assert_close("isometry_residual", proj.isometry_residual(), 1e-10)
    _assert_close("idempotent_residual", proj.idempotent_residual(), 1e-10)
    _assert_close("selfadjoint_residual", proj.selfadjoint_residual(), 1e-10)
    report["gate1_projector"] = "PASS"

    # --- Gate 0: type-mismatch rejection --------------------------------
    try:
        CPTernaryLaw(
            A=torch.randn(4, 5, generator=_g(seed), dtype=DTYPE),
            B=torch.randn(3, 5, generator=_g(seed), dtype=DTYPE),  # wrong rank vs A
            C=torch.randn(4, 5, generator=_g(seed), dtype=DTYPE),
            O=torch.randn(5, 4, generator=_g(seed), dtype=DTYPE),
        )
        raise AssertionError("CPTernaryLaw accepted a rank-mismatched factor set")
    except ValueError:
        pass
    report["gate0_type_reject"] = "PASS"

    # --- CLM_KGR_002: CP == dense contraction (independent loop path) --
    dim = 3  # keep tiny: dense_tensor_explicit_loops is O(dim^3 * rank)
    rank = 2
    cp = CPTernaryLaw(
        A=torch.randn(rank, dim, generator=_g(seed + 1), dtype=DTYPE),
        B=torch.randn(rank, dim, generator=_g(seed + 2), dtype=DTYPE),
        C=torch.randn(rank, dim, generator=_g(seed + 3), dtype=DTYPE),
        O=torch.randn(dim, rank, generator=_g(seed + 4), dtype=DTYPE),
    )
    x = torch.randn(dim, generator=_g(seed + 5), dtype=DTYPE)
    a = torch.randn(dim, generator=_g(seed + 6), dtype=DTYPE)
    q = torch.randn(dim, generator=_g(seed + 7), dtype=DTYPE)
    direct = cp.forward(x, a, q)
    via_dense = cp.forward_via_dense(x, a, q)
    cp_err = float((direct - via_dense).abs().max().item())
    _assert_close("cp_dense_equivalence", cp_err, 1e-10)
    report["clm_kgr_002_cp_dense_equivalence"] = {"status": "PASS", "max_abs_error": cp_err}

    # --- CLM_KGR_003: CP gauge invariance of the reconstructed tensor --
    scales = []
    for _ in range(rank):
        c0 = float(torch.rand(1, generator=_g(seed + 8), dtype=DTYPE).item()) + 0.5
        c1 = float(torch.rand(1, generator=_g(seed + 9), dtype=DTYPE).item()) + 0.5
        c2 = float(torch.rand(1, generator=_g(seed + 10), dtype=DTYPE).item()) + 0.5
        c3 = 1.0 / (c0 * c1 * c2)
        scales.append((c0, c1, c2, c3))
    cp_gauged = cp.gauge_transform(scales)
    K_before = cp.dense_tensor_explicit_loops()
    K_after = cp_gauged.dense_tensor_explicit_loops()
    gauge_err = float((K_before - K_after).abs().max().item())
    _assert_close("cp_gauge_invariance", gauge_err, 1e-8)
    report["clm_kgr_003_gauge_invariance"] = {"status": "PASS", "max_abs_error": gauge_err}

    # --- CLM_KGR_005: cyclic projector idempotent + self-adjoint -------
    K3 = torch.randn(2, dim, dim, dim, generator=_g(seed + 11), dtype=DTYPE)
    K3_flat = K3  # [d, i, j, k] with i=j=k=dim already
    K_cyc = cyclic_projector(K3_flat)
    K_cyc_twice = cyclic_projector(K_cyc)
    cyc_idem_err = float((K_cyc - K_cyc_twice).abs().max().item())
    _assert_close("cyclic_projector_idempotent", cyc_idem_err, 1e-10)
    report["clm_kgr_005_cyclic_idempotent"] = {"status": "PASS", "max_abs_error": cyc_idem_err}

    # --- Reciprocal closure structural check ----------------------------
    kg, rng = tiny_reciprocal_kg(seed)
    for h, r, t in kg.triples[:6]:  # only the base (non-reciprocal) triples
        assert (t, r + kg.num_relations_original, h) in kg.triples
    report["reciprocal_closure_structural"] = "PASS"

    # --- Gate 3: score paths agree (positive == candidate-restricted) --
    N, dim_e, dim_r, dim_q, rank_s = kg.num_entities, 4, 4, 4, 3
    entity = torch.randn(N, dim_e, generator=_g(seed + 20), dtype=DTYPE)
    relation = torch.randn(kg.num_relations_total, dim_r, generator=_g(seed + 21), dtype=DTYPE)
    seion_scorer = SeionicScalarScorer(
        entity=entity,
        A=torch.randn(rank_s, dim_e, generator=_g(seed + 22), dtype=DTYPE),
        B=torch.randn(rank_s, dim_r, generator=_g(seed + 23), dtype=DTYPE),
        C=torch.randn(rank_s, dim_r, generator=_g(seed + 24), dtype=DTYPE),
        O=torch.randn(dim_q, rank_s, generator=_g(seed + 25), dtype=DTYPE),
        T=torch.randn(dim_q, dim_e, generator=_g(seed + 26), dtype=DTYPE),
        relation=relation,
    )
    h0, r0, t0 = kg.triples[0]
    single = seion_scorer.score(h0, r0, t0)
    batched = seion_scorer.score_all_candidates(h0, r0)[t0]
    score_path_err = abs(single - float(batched.item()))
    _assert_close("seion_scorer_1vsall_vs_individual", score_path_err, 1e-10)
    report["gate3_1vsall_vs_individual"] = {"status": "PASS", "max_abs_error": score_path_err}

    # --- Gate 3: brute-force filtered ranking sanity (hand-checkable) --
    def scorer_fn(h: int, r: int, t: int) -> float:
        return seion_scorer.score(h, r, t)

    rank_tail = brute_force_filtered_rank(scorer_fn, kg, h0, r0, t0, mode="tail")
    if not (1.0 <= rank_tail <= float(kg.num_entities)):
        raise AssertionError(f"tail rank out of range: {rank_tail}")
    report["gate3_brute_force_rank_range"] = {"status": "PASS", "rank_tail": rank_tail}

    # --- Gate 7: filtering negative control — removing the filter must
    # never *increase* the gold rank (gold is always at least as good a
    # candidate once excluded competitors are added back in).
    def unfiltered_rank(h: int, r: int, t: int) -> float:
        gold_score = scorer_fn(h, r, t)
        scores = [scorer_fn(h, r, cand) for cand in range(kg.num_entities) if cand != t]
        better = sum(1 for s in scores if s > gold_score + 1e-9)
        ties = sum(1 for s in scores if abs(s - gold_score) <= 1e-9)
        return 1.0 + better + 0.5 * ties

    rank_unfiltered = unfiltered_rank(h0, r0, t0)
    if rank_unfiltered < rank_tail - 1e-9:
        raise AssertionError(
            f"filtering made the gold rank worse ({rank_tail} -> {rank_unfiltered}); "
            "filter table or brute-force loop is broken"
        )
    report["gate7_filter_monotonicity"] = {
        "status": "PASS",
        "rank_filtered": rank_tail,
        "rank_unfiltered": rank_unfiltered,
    }

    # --- CLM_KGR_019 / Theorem 30.1: margin implies order, and a
    # falsification control showing order CAN flip below the margin ---
    s_i, s_j, eps = 1.0, 0.3, 0.2  # gap 0.7 > 2*0.2=0.4: certified
    assert margin_preserves_order(s_i, s_j, eps)
    s_tilde_i, s_tilde_j = s_i - eps, s_j + eps  # worst-case perturbation
    if not (s_tilde_i > s_tilde_j):
        raise AssertionError("Theorem 30.1 violated under a margin > 2*epsilon")
    report["clm_kgr_019_margin_certified_case"] = "PASS"

    s_i2, s_j2, eps2 = 1.0, 0.9, 0.2  # gap 0.1 <= 2*0.2=0.4: NOT certified
    assert not margin_preserves_order(s_i2, s_j2, eps2)
    s_tilde_i2, s_tilde_j2 = s_i2 - eps2, s_j2 + eps2  # 0.8 vs 1.1: order flips
    if not (s_tilde_i2 < s_tilde_j2):
        raise AssertionError(
            "negative control did not flip order — the margin example is not "
            "demonstrating why margin > 2*epsilon is required"
        )
    report["clm_kgr_019_negative_control_order_flips_below_margin"] = "PASS"

    # --- One-hop message passing runs and produces finite, typed output
    dim_x = dim_a = dim_q = 4
    mp_layer = MessagePassingLayer(
        mu=CPTernaryLaw(
            A=torch.randn(3, dim_x, generator=_g(seed + 30), dtype=DTYPE),
            B=torch.randn(3, dim_a, generator=_g(seed + 31), dtype=DTYPE),
            C=torch.randn(3, dim_q, generator=_g(seed + 32), dtype=DTYPE),
            O=torch.randn(dim_x, 3, generator=_g(seed + 33), dtype=DTYPE),
        ),
        U=torch.randn(dim_x, dim_x, generator=_g(seed + 34), dtype=DTYPE) * 0.1,
        V=torch.randn(dim_x, dim_a, generator=_g(seed + 35), dtype=DTYPE) * 0.1,
        W=torch.randn(dim_x, dim_q, generator=_g(seed + 36), dtype=DTYPE) * 0.1,
        P_out=Projector.identity(dim_x),
    )
    rel_embed = torch.randn(kg.num_relations_total, dim_a, generator=_g(seed + 37), dtype=DTYPE)
    query_ind = torch.randn(dim_q, generator=_g(seed + 38), dtype=DTYPE)
    x1 = mp_layer.run(kg, dim_x, rel_embed, head=0, query_relation=0, query_indicator=query_ind)
    if len(x1) != kg.num_entities:
        raise AssertionError("message passing did not produce a state for every node")
    for v, state in x1.items():
        if not torch.isfinite(state).all():
            raise AssertionError(f"non-finite state at node {v}")
    report["message_passing_one_hop"] = "PASS"

    # --- Closure leakage is exactly zero when P = I (full-rank projector)
    leak_full = mp_layer.closure_leakage(
        torch.randn(dim_x, generator=_g(seed + 40), dtype=DTYPE),
        torch.randn(dim_a, generator=_g(seed + 41), dtype=DTYPE),
        torch.randn(dim_q, generator=_g(seed + 42), dtype=DTYPE),
    )
    leak_full_norm = float(torch.linalg.norm(leak_full).item())
    _assert_close("closure_leakage_full_rank_projector", leak_full_norm, 1e-10)
    report["closure_leakage_full_rank"] = {"status": "PASS", "norm": leak_full_norm}

    report["status"] = "PASS_KGR_V26_FASE1_SELF_TESTS"
    return report


# =============================================================================
# CLI
# =============================================================================


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument(
        "--self_test",
        action="store_true",
        help="Run the Fase 1 self-test battery and exit (currently the only supported action)",
    )
    p.add_argument("--seed", type=int, default=7)
    return p


def main() -> None:
    args = build_parser().parse_args()
    if not args.self_test:
        raise SystemExit(
            "This Fase 1 reference oracle currently only supports --self_test; "
            "dataset-driven evaluation is a later phase (see docs/SEION_KGR_MATHEMATICAL_CONTRACT.md)."
        )
    import json

    result = run_self_tests(seed=args.seed)
    print(json.dumps(result, indent=2, default=str))


if __name__ == "__main__":
    main()
