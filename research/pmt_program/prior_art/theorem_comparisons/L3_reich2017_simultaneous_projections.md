# L3 comparison: Reich & Zalas (2017), "The optimal error bound for the method of simultaneous projections"

Prepared 2026-09-14. Level-3 comparison against Theorem R, rows R1a, R1b, R2, R3, R5 (planar
extremizer), R7 (diagonal lemma). Public sources only; paraphrased.

NOTE: a parallel comparison of the same paper exists in this folder,
`L3_reich2017_simultaneous_projections_optimal.md`, written by another session with a DIFFERENT R-numbering
(R4 = planar extremizer, R5 = equality for all tree shapes, etc.) and without the journal volume. The two
files agree in substance (threat 1). This file adds the verified journal record and the rows R5/R7 in the
numbering used here. Merge or delete one of them when consolidating.

## 1. Bibliographic record

- Authors: Simeon Reich, Rafał Zalas
- Title: The optimal error bound for the method of simultaneous projections
- Journal: Journal of Approximation Theory 223 (2017), 96–107; DOI 10.1016/j.jat.2017.08.005;
  zbMATH Zbl 1381.41013
- Preprint: arXiv:1704.00308 (v2, Sept 2017)
- Status: VERIFIED (arXiv abstract page seen; journal volume/pages confirmed via Crossref and zbMATH).

## 2. Access level

FULL_TEXT (arXiv v2 PDF, 13 pp.): Section 1 (Theorems 1–4, identity (3)), Lemma 6, Definition 7,
Theorem 8, Remarks 9, 11, Example 5/10, Fact 12, Theorem 14, Corollary 15, Remark 16, Appendix headings.

## 3. Their setting and assumptions

- Closed linear subspaces M_1, …, M_r of a real Hilbert space; M = ∩ M_i.
- Simultaneous projection operator T = (1/r) Σ P_{M_i}; error ‖T^k − P_M‖.
- Parameter: Friedrichs number cos(M_1, …, M_r) of r subspaces (Badea–Grivaux–Müller definition, Def. 7).
- Linear; no trees; no multilinear maps; no inserted projections in a product of general maps.

## 4. Their main results relevant here

- Identity (3) (Aronszajn + Kayalar–Weinert): ‖(P_{M_2}P_{M_1})^k − P_M‖ = cos(M_1,M_2)^{2k−1}.
- Lemma 6: if P_M commutes appropriately with T, then T^k − P_M = (T − P_M)^k, and for self-adjoint
  T − P_M its norm is the k-th power.
- Theorem 8 (exact norm): ‖T^k − P_M‖ = ((r−1)/r · cos(M_1,…,M_r) + 1/r)^k.
- Remark 11: for r = 2 the simultaneous rate is strictly worse than the alternating rate
  cos^{2k−1} < ((1+cos)/2)^k (when cos < 1).
- Theorem 14: dichotomy — linear convergence with the optimal rate above iff Σ M_i^⊥ is closed; otherwise
  arbitrarily slow, but super-polynomial on a dense subspace. Corollary 15: affine version.
- Remark 16: for the cyclic product, only a non-optimal bound ‖(P_{M_r}⋯P_{M_1})^k − P_M‖ ≤
  ‖P_{M_r⊖M}⋯P_{M_1⊖M}‖^k is available; the exact cyclic norm for r > 2 is described as unknown.

## 5. Comparison table

| Claim | Implied? | Explanation |
|---|---|---|
| R1a | NO | Error of averaged projections to P_M, not the discrepancy between projected and unprojected evaluation of a product/tree of maps; no range-restricted local defect. |
| R1b | NO | Sharp constant is a power of an affine function of a Friedrichs number, unrelated to η^{-1} max |1 − (cos θ e^{iθ})^{k−1}|. |
| R2 | ADJACENT | Same genre (exact operator-norm constant, attained, angle-parameterized) for a self-adjoint averaged operator; the exactness comes from self-adjointness (norm of a power = power of norm), a mechanism unavailable for the non-normal products in Theorem R. |
| R3 | NO | No tree structure. |
| R5 | NO | No planar extremizer statement; exactness is spectral, not via a 2-D configuration. |
| R7 | NO | No multi-angle extremal problem. |

## 6. Threat score

**1 / 5** (background).

Justification: provides sharp angle-type constants for projection algorithms and is the natural citation
alongside Kayalar–Weinert, but its operators, hypotheses and proof mechanism (self-adjointness) differ
from Theorem R, and no row is implied, even for k = 2 or linear chains.

## 7. How to cite / position

Exact error norms for projection methods are known in the two-subspace alternating case (Kayalar–Weinert)
and for simultaneous projections (Reich–Zalas, via self-adjointness), while the exact norm for cyclic
products of r ≥ 3 projections remains open; Theorem R concerns a different, non-self-adjoint quantity and
obtains its sharp constant through an explicit angular extremal problem.
