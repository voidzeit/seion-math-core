# L3 comparison: Feshchenko (2019), "On the optimal error bound for the first step in the method of cyclic alternating projections"

Prepared 2026-09-14. Found in the item-6 search (sharp constants for norms of products of projections).
Level-3 comparison against Theorem R, rows R1a, R1b, R2, R3, R5 (planar extremizer), R7 (diagonal lemma).
Public sources only; paraphrased.

## 1. Bibliographic record

- Author: Ivan Feshchenko
- Title: On the optimal error bound for the first step in the method of cyclic alternating projections
- Venue: arXiv:1908.00531 [math.FA], v1 1 Aug 2019 (zbMATH indexes it as a preprint; no journal version
  found in Crossref/zbMATH searches)
- Status: VERIFIED (arXiv abstract page seen).

## 2. Access level

FULL_TEXT (arXiv v1): Section 1 (Propositions 1.1, 1.2), Section 2 (Theorems 2.1–2.7, Lemma 2.1,
Proposition 2.1, Corollary 2.1), proof headings of Section 3.

## 3. Their setting and assumptions

- n closed subspaces of a complex Hilbert space, H_0 their intersection.
- f_n(c) = sup ‖P_n⋯P_1 − P_0‖ over all systems with (BGM) Friedrichs number ≤ c.
- Global parameter (one Friedrichs number for the whole system), not local per-step angles; linear chain;
  no trees, no multilinear maps.

## 4. Their main results relevant here

- Proposition 1.2 / Theorem 2.1: f_n(c) equals the maximum of |a_12 a_23 ⋯ a_{n−1,n}| over Hermitian n×n
  matrices with unit diagonal and 0 ≤ A ≤ (1 + (n−1)c) I (a Gram-matrix extremal problem for a product of
  consecutive inner products).
- Lemma 2.1: optimal matrices can be taken real, with nonnegative superdiagonal and a centro-symmetry.
- Theorem 2.2: exact f_3(c) = 4c² on [0, 1/4] and c on [1/4, 1], with explicit optimal matrices.
- Theorem 2.3: for c ≤ 1/(n−1)², f_n(c) = (n−1)^{n−1} c^{n−1} with an explicit extremal matrix.
- Theorems 2.4–2.7: f_n^{1/(n−1)} concave; functional equation; upper bound
  f_n(c) ≤ 1 − a_n(1−c) + b_n(1−c)², matched below up to O((1−c)²), with a_n = 2(n−1) sin²(π/(2n)).

## 5. Comparison table

| Claim | Implied? | Explanation |
|---|---|---|
| R1a | NO | Norm of one sweep of cyclic projections minus P_0, not the projected-vs-unprojected discrepancy; hypothesis is a global Friedrichs number, not a per-node range-restricted defect. |
| R1b | NO | Constants are of a different form (polynomial/trigonometric in c and n); no η^{-1} max |1 − (cos θ e^{iθ})^{k−1}|. |
| R2 | ADJACENT | Genuine best-constant problem for products of projections, solved exactly for n = 3 and for small c; same genre as determining C_k(η), different quantity and parameter. |
| R3 | NO | No trees. |
| R5 | NO | Extremizers are n×n Gram matrices, not planar configurations. |
| R7 | ADJACENT | The objective is a product of consecutive inner-product factors, as in our scalar problem, and Remark 2.1 shows uniqueness of the optimal superdiagonal by an AM–GM averaging argument; but the optimal superdiagonal is not shown to be constant in general, and the constraint is spectral, not a box on angles. |

## 6. Threat score

**1 / 5**.

Justification: a sharp-constant study for products of projections that should be cited to show awareness of
the "best constant" literature; it does not imply any row of Theorem R.

## 7. How to cite / position

Best constants for a single sweep of cyclic projections in terms of the global Friedrichs number are known
only partially (Feshchenko 2019: exact for three subspaces and for small c); Theorem R instead fixes a local
per-node defect and obtains the exact constant for every k and every tree shape.
