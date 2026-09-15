# L3 comparison: Kayalar & Weinert (1988), "Error bounds for the method of alternating projections"

Prepared 2026-09-14. Level-3 comparison against Theorem R, rows R1a, R1b, R2, R3, R5 (planar
extremizer), R7 (diagonal lemma). Public sources only; paraphrased. (R-numbering follows the request
that produced this file; sibling files may number differently.)

## 1. Bibliographic record

- Authors: Selahattin Kayalar, Howard L. Weinert
- Title: Error bounds for the method of alternating projections
- Journal: Mathematics of Control, Signals, and Systems 1 (1988), no. 1, 43–59
- DOI: 10.1007/BF02551235; zbMATH Zbl 0673.65036; DBLP journals/mcss/KayalarW88
- Status: metadata VERIFIED via zbMATH Open record and Semantic Scholar API (volume/issue/pages agree).
  Springer landing page redirected to a login/authorization step and was not seen.

## 2. Access level

SECONDARY. The original is paywalled and was not read; zbMATH Open withholds its review text (license).
Statements below come from four independent open sources that restate it:
Reich–Zalas arXiv:1704.00308 (identity (3), Remark 16 citing [KW, Theorem 1]);
Bauschke–Deutsch–Hundal arXiv:0710.2387 (Theorem 1.2 and eq. (1.3));
Badea–Grivaux–Müller arXiv:1006.2047 (Section 1B);
Feshchenko arXiv:1908.00531 (Section 1.1).
The zbMATH review of Deutsch–Hundal (Zbl 0890.65053) also records a conjecture of Kayalar–Weinert that
DH later disproved. Their bound for r ≥ 3 subspaces (sharpest known in 1988, per a secondary summary) was
not seen in formula form.

## 3. Their setting and assumptions

- Closed subspaces M_1, …, M_r of a Hilbert space; orthogonal projections; M = ∩ M_i.
- Quantity: operator norm of the error (P_{M_r}⋯P_{M_1})^n − P_M of the von Neumann–Halperin method.
- Parameter: cosine c of the Friedrichs angle (angle between M_1 ⊖ M and M_2 ⊖ M).
- Linear, single fixed Hilbert space, no trees, no multilinear maps, no inserted projections in a
  product of general contractions.

## 4. Their main results relevant here (as reproduced)

- Two subspaces (sharpness of Aronszajn's inequality): for every n ≥ 1,
  ‖(P_{M_2}P_{M_1})^n − P_M‖ = c^{2n−1}. The upper bound is Aronszajn's; KW proved equality.
- [KW, Theorem 1] (as cited by Reich–Zalas, Remark 16): the product of projections onto M_i ⊖ M equals
  the product of projections onto M_i minus P_M, which reduces the error operator to a product of
  projections with trivial common intersection.
- r ≥ 3: an angle-based upper bound (improving Smith–Solmon–Wagner) and a conjecture about sharpness,
  later refuted by Deutsch–Hundal (1997). Exact form not verified here.

## 5. Comparison table

| Claim | Implied? | Explanation |
|---|---|---|
| R1a | NO | Different quantity: convergence of iterated projections to the projection onto the intersection. Not a special case of the projected-vs-unprojected product: if one takes the chain maps A_j = alternating P_{M_1}, P_{M_2} and inserted projectors P_M, the discrepancy is identically 0, and with inserted identity it is trivial. No local range-restricted defect hypothesis. |
| R1b | NO | Constant c^{2n−1} is a power of a single Friedrichs cosine; no expression of the form η^{-1} max_{θ≤arcsin η} |1 − (cos θ e^{iθ})^{k−1}|. |
| R2 | ADJACENT | Same genre: exact operator-norm constant for a product of projections, parameterized by an angle, attained. Different operator family and parameter. |
| R3 | NO | No tree structure. |
| R5 | ADJACENT | The two-subspace equality is witnessed by low-dimensional (planar) configurations at the Friedrichs angle, via the two-subspace reduction; similar in spirit to a planar extremizer, for a different functional. |
| R7 | NO | Single angle; no multi-angle extremal problem, so no diagonal (equal-angle) lemma. |

## 6. Threat score

**1 / 5** (classical background).

Justification: canonical example of a sharp, angle-based norm identity for products of projections; must be
cited as background for the "angle" mechanism, but no row of Theorem R is implied, including k = 2 and
linear chains.

## 7. How to cite / position

Sharp angle-parameterized norms for products of orthogonal projections go back to Aronszajn and
Kayalar–Weinert (‖(P_2P_1)^n − P_M‖ = c^{2n−1}); Theorem R establishes a sharp constant of a comparable
angular nature for a different problem — the discrepancy created by inserting node-wise projections into a
tree of bounded multilinear maps under a uniform local defect. (Cite as SECONDARY-verified: statement taken
from Reich–Zalas 2017 and Bauschke–Deutsch–Hundal 2009 unless the original is obtained.)
