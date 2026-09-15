# L3 comparison: Reich & Zalas (2017), "The Optimal Error Bound for the Method of Simultaneous Projections" (with the Kayalar–Weinert identity it recalls)

Prepared 2026-09-14. Found during the item-4 search as the nearest example of a SHARP, angle-based
operator-norm constant for compositions of orthogonal projections. Level-3 comparison against
Theorem R (R1a–R11). Public sources only; paraphrased.

## 1. Bibliographic record

- Authors: Simeon Reich (Technion), Rafał Zalas
- Title: The Optimal Error Bound for the Method of Simultaneous Projections
- Venue: arXiv:1704.00308 (v1 2 Apr 2017, v2 14 Sep 2017); abstract page says accepted in
  Journal of Approximation Theory (journal volume/pages not checked)
- DOI (arXiv): 10.48550/arXiv.1704.00308
- Status: arXiv landing page VERIFIED.
- Recalled classical result: Kayalar & Weinert (1988), with Aronszajn's inequality: the norm of
  (P_{M2}P_{M1})^k − P_{M1∩M2} equals cos(M1,M2)^{2k−1} (Friedrichs angle). Not independently read.

## 2. Access level

FULL_TEXT obtained (arXiv v2 PDF); read Section 1 (Theorems 1–4, identity (3), statement of
contributions) and Section 2 through Definition 7 and Theorem 8 (exact norm value). Later sections
(affine subspaces, dichotomy extensions) not read.

## 3. Their setting and assumptions

- Closed linear subspaces M_1..M_r of a real Hilbert space; orthogonal projections P_{M_i};
  M = ∩M_i.
- Operators studied: iterates T^k of the simultaneous projection T = (1/r)ΣP_{M_i}, compared with the
  alternating/cyclic product P_{M_r}…P_{M_1}.
- Quantity: the exact operator norm ‖T^k − P_M‖ (optimal error bound independent of the starting point),
  expressed through the Friedrichs number cos(M_1,…,M_r) (Def. 7).
- Everything is linear; one fixed Hilbert space; no multilinear maps, trees, or local defect hypotheses.

## 4. Their main results relevant here

- Identity (3) (Aronszajn / Kayalar–Weinert): for two subspaces, the alternating-projection error norm
  after k sweeps is exactly cos^{2k−1} of the Friedrichs angle — a sharp, angle-parameterized constant.
- Theorem 8: for every k, ‖((1/r)ΣP_{M_i})^k − P_M‖ equals an explicit expression in the Friedrichs
  number, and also equals the k-th power of cos² of the angle between two associated subspaces C, D of
  the product space H^r (Pierra's formalization).
- Example/Theorem comparisons: applying the two-subspace identity naively in the product space gives a
  weaker (non-optimal) bound.

## 5. Comparison table

| Claim | Implied by source? | Explanation |
|---|---|---|
| R1a | NO | Different quantity: convergence of iterated projections to the projection onto an intersection, not discrepancy between ideal and projected evaluation of a tree of multilinear maps. No local defect hypothesis on ranges. |
| R1b | NO | Their sharp constants are powers of a Friedrichs cosine (or an explicit function of the Friedrichs number); no expression of the form η^{-1} max_{θ≤arcsin η} |1−(cos θ e^{iθ})^{k−1}|. |
| R2 | ADJACENT | Same genre of result (exact operator-norm constant, attained, parameterized by an angle), for a different operator family. |
| R3 | NO | No tree structure. |
| R4 | ADJACENT | Sharpness is witnessed by low-dimensional subspace configurations (two lines at the Friedrichs angle), which is methodologically similar to planar extremizers in R4, but for a different problem. |
| R5 | NO | No trees. |
| R10 | NO | No analogue. |
| R11 | NO | No analogue. |

## 6. Threat score

**1 / 5** (methodological background).

Justification: provides the standard examples of sharp, angle-based operator-norm constants for products
of orthogonal projections (useful to cite for the "angle" mechanism behind C_k), but the operators,
hypotheses and quantities are different, and nothing in R1a–R11 is implied.

## 7. How to cite / position

Sharp angle-parameterized norms for products of orthogonal projections are classical (Kayalar–Weinert for
alternating projections; Reich–Zalas for simultaneous projections); Theorem R obtains a sharp constant of a
similar angular nature for a different object — projected evaluation of a tree of bounded multilinear maps
under a uniform local projection defect.
