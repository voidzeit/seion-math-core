# L3 comparison: Jeong, Kong, Needell, Swartworth, Ward (NeurIPS 2023), "Nearly Optimal Bounds for Cyclic Forgetting"

Prepared 2026-09-14. Level-3 (theorem-by-theorem) comparison against Theorem R, rows R1a, R1b, R2, R3,
R5 (planar extremizer), R7 (diagonal lemma). Public sources only; paraphrased, no long quotes.

NOTE ON R-NUMBERING: this file uses the numbering of the request that produced it (R5 = planar R^2
extremizer, R7 = diagonal/equal-angle lemma). Some sibling files in this folder use a different
numbering (e.g. R4 = planar extremizer). Reconcile before merging tables.

## 1. Bibliographic record

- Authors (order on the proceedings PDF, alphabetical): Halyun Jeong, Mark Kong, Deanna Needell,
  William Swartworth, Rachel Ward. Crossref/DBLP/ML Anthology list the order Swartworth, Needell, Ward,
  Kong, Jeong (ML Anthology key `swartworth2023neurips-nearly`). Cite with the order your bib tool gives
  for DOI below and keep the title as the identifier.
- Title: Nearly Optimal Bounds for Cyclic Forgetting
- Venue: Advances in Neural Information Processing Systems 36 (NeurIPS 2023), pp. 68197–68206
- DOI: 10.52202/075280-2982; OpenReview id X25L5AjHig
- PDF: proceedings.neurips.cc/paper_files/paper/2023/file/d72ae75abaa70a3b19c5d4f436c680d1-Paper-Conference.pdf
- Status: VERIFIED (proceedings PDF read; Crossref record seen; OpenReview landing page blocked by a
  bot check, not seen). No arXiv version located.

## 2. Access level

FULL_TEXT of the main paper (10 pp.: Sections 1–5, Theorem 1, Lemma 2, Proposition 4, Lemma 5,
Theorem 6 with proof sketch, Corollary 8, Lemma 9, Section 4 on real projections). The SUPPLEMENTARY
MATERIAL (proof of Lemma 5, fullness of the spiral, real-projection statements, precise Lemma 9) was
NOT read. Some formulas in the PDF text extraction were garbled; constants below are paraphrased
conservatively.

## 3. Their setting and assumptions

- Continual linear regression with T tasks visited cyclically m times; each step is an orthogonal
  projection (block Kaczmarz). After normalization, worst-case forgetting is controlled by
  ‖A^m(I − A)‖ where A = P_T ⋯ P_1 is a product of orthogonal projections (inherited from Evron et al.,
  COLT 2022).
- Tool: numerical range W(A) plus the Crouzeix–Palencia inequality ‖p(A)‖ ≤ (1+√2) sup_{W(A)} |p|.
- Key object: the cyclic product P(v_0,…,v_{k−1}) = ⟨v_0,v_1⟩⟨v_1,v_2⟩⋯⟨v_{k−1},v_0⟩ over unit vectors
  in C^d.
- All maps are linear; projections are arbitrary (no angle/defect parameter); no trees; no multilinear maps.

## 4. Their main results relevant here

- Theorem 6: the range Σ_k of the cyclic product P over unit vectors is a FILLED SINUSOIDAL SPIRAL; it
  equals the image under z ↦ z^k of the convex hull of the k-th roots of unity. Its outer boundary is the
  k-th power of one polygon side (in polar form a spiral of index −1/k, i.e. the image of a LINE).
- Reduction step (Section 1.4 and proof of Thm 6): it suffices to take vectors in C^2 (projecting a vector
  onto the plane of its neighbours increases the factors) — a two-dimensional reduction.
- Lemma 5 (critical points): at boundary values, all consecutive inner products are equal to a common
  value (up to unimodular rephasing); the extremal tuples are powers of a quaternionic root of unity.
  This is an "equal factors at the extremum" phenomenon.
- Corollary 8: for A = P_k ⋯ P_1 (complex orthogonal projections), W(A) ⊆ Σ_{k+1}; Section 4 states the
  union of numerical ranges is the same for real projections (already in R^4).
- Lemma 9 / Lemma 2: sup over Σ_k of |z^m(1−z)| is O(k/m) with an explicit asymptotic constant, hence
  ‖A^m(I−A)‖ ≤ (absolute constant + o(1))·k/m for any product of k projections; Theorem 1: worst-case
  cyclic forgetting is O(T^2/m), dimension-free.

## 5. Comparison table

| Claim | Implied? | Explanation |
|---|---|---|
| R1a | NO | They bound numerical ranges and ‖A^m(I−A)‖ for products of projections; there is no comparison between an unprojected product A_k⋯A_1 and a projected product P_k A_k P_{k−1}⋯, and no local defect ρ with ‖(I−P)A x‖ ≤ ρ‖x‖ on Ran P. |
| R1b | NO | No constant depending on a defect ratio η; their constants are absolute (worst case over all projections, i.e. formally η = 1 with no restriction). |
| R2 | ADJACENT | Theorem 6 is an exact (sharp) extremal region for a product of k inner-product factors, with the boundary a sinusoidal spiral obtained as a k-th power image. Our extremal curve {(cos θ e^{iθ})^{n}} is also a sinusoidal spiral, r^{1/n} = cos(φ/n), but it is the n-th power image of the CIRCLE |z − 1/2| = 1/2 (index +1/n), while theirs is the image of a polygon SIDE (index −1/k). Different objects (numerical range vs. distance |1 − product|), different constraint (none vs. θ ≤ arcsin η). No formula for C_k(η) follows. |
| R3 | NO | Single cyclic product; no tree structure, no topology question. |
| R5 | ADJACENT | Their reduction of the extremal problem to C^2 (and to real R^4 for real projections) is methodologically parallel to our planar R^2 extremizer, but proves a statement about a different functional. |
| R7 | ADJACENT | Lemma 5 shows boundary points are attained when all consecutive factors coincide (equal inner products), which is the same qualitative mechanism as our diagonal lemma. Their problem has no box constraint θ_j ∈ [0, α] and maximizes over a numerical-range image rather than |1 − ∏ cos θ_j e^{iθ_j}|; the diagonal lemma is not implied. |

## 6. Threat score

**2 / 5** (closest methodological precedent found; not a priority threat).

Justification: this is the only source located that computes a SHARP extremal set for products of
projection-type factors, reduces to two complex dimensions, identifies equal-factor extremizers, and gets a
sinusoidal-spiral boundary — so a referee who knows it may ask how R7/R5 relate. But the functional
(numerical range of the product), the absence of any angle/defect constraint, and the linear single-chain
setting mean none of R1a, R1b, R2, R3, R5, R7 is implied, even for k = 2 or chains. Residual risk:
the unread supplementary material could contain a lemma on |1 − z| over the spiral; that would still lack
the η-constraint, so the score would at most rise to 3.

## 7. How to cite / position

Jeong et al. determine exactly the union of numerical ranges of products of k orthogonal projections (a
filled sinusoidal spiral, attained by equal-factor configurations in C^2); our diagonal lemma and planar
extremizer exhibit the same equal-factor mechanism for a different, angle-constrained functional
|1 − ∏ cos θ_j e^{iθ_j}|, whose extremal curve is a sinusoidal spiral of the opposite index.
