# L3 comparison: Grasedyck (2010), "Hierarchical Singular Value Decomposition of Tensors"

Prepared 2026-09-14. Level-3 comparison against Theorem R (R1a–R11), restricted (as requested) to the
truncation error bounds (√(2d−3) quasi-optimality) and the lemmas on products of projections.
Public sources only; paraphrased.

## 1. Bibliographic record

- Author: Lars Grasedyck (then MPI for Mathematics in the Sciences, Leipzig)
- Title: Hierarchical Singular Value Decomposition of Tensors
- Journal: SIAM J. Matrix Anal. Appl. 31(4) (2010), 2029–2054. DOI 10.1137/090764189
- Preprint: MPI MiS Preprint 27/2009 (received 26.06.2009; revised version March 2010)
- Status: Preprint landing page VERIFIED (MPI MiS repository page seen; it states the journal
  reference and DOI). SIAM landing page NOT verified (HTTP 403).

## 2. Access level

FULL_TEXT of the MiS preprint, revised version (March 2010), obtained from the MPI MiS public
preprint server. Read closely: Sections 1–3 (Tucker truncation Lemma 2.6, dimension trees,
Lemma 3.2, Defs. 3.4–3.6, Lemma 3.8, Def. 3.9, Lemma 3.10, Theorem 3.11, Remark 3.12,
Example 3.14, Lemma 3.15, Def. 3.17, Theorem 3.18, Algorithms 1–2, Theorem 3.22) and skimmed
Section 4 headings. The published SIAM version was not seen; theorem numbering there may differ
by a small offset — check before citing numbers.

## 3. Their setting and assumptions

- Object: a single full tensor A ∈ R^{n_1×…×n_d} (finite dimensional, Euclidean/Frobenius norm)
  and a binary dimension tree T_I with 2d−1 nodes (d leaves, d−1 interior nodes).
- For each node t, an orthogonal frame U_t and the orthogonal frame projection π_t acting on the
  ambient space R^I (in matricized form U_tU_t^T applied to A^(t)). All π_t act on the SAME space;
  they are orthogonal projections but need not commute.
- Truncation: A_H = ∏_t π_t A (in some order), with U_t = dominant left singular vectors of A^(t)
  (root-to-leaves, Def. 3.17) or of the partially truncated tensor (leaves-to-root, Def. 3.20).
- Error quantities are data-dependent: per-node discarded singular value tails Σ_{i>k_t} σ_{t,i}²,
  compared with the best H-Tucker approximation error.
- No bounded multilinear maps with a norm parameter M; the "combination" of subtrees is the
  (isometric) tensor product structure of R^I itself.

## 4. Their main results relevant here

- Lemma 3.8 (successive truncation): for orthogonal projections π_t, π_s,
  ‖A − π_tπ_sA‖² ≤ ‖A − π_tA‖² + ‖A − π_sA‖². Proof via orthogonality of (I−π_t)A and π_t(·)
  (Pythagoras) plus ‖π_t‖ ≤ 1.
- Lemma 3.10: for any order of the projections over all tree nodes,
  ‖A − ∏_t π_tA‖² ≤ Σ_t ‖A − π_tA‖².
- Theorem 3.11 (hierarchical truncation error): with SVD-based frames,
  ‖A − ∏π_tA‖ ≤ (Σ_t Σ_{i>k_t} σ_{t,i}²)^{1/2} ≤ √(2d−2)‖A − A_best‖.
- Remark 3.12: the estimate is stated to be NOT optimal; merging the two root children gives
  √(2d−3) (coinciding with the SVD for d=2 and the Tucker/HOSVD √d estimate for d=3).
- Theorem 3.18: characterization of hierarchical approximability (node-wise tails ≤ ε/√(2d−3)
  guarantee ‖A − A_H‖ ≤ ε; conversely each node tail ≤ best error).
- Lemma 3.15: product of level-wise projections lands in H-Tucker with the prescribed ranks.
- Theorem 3.22 (leaves-to-root truncation): error ≤ (2+√2)√d ‖A − A_best‖ for complete binary trees.
- Example 3.14 illustrates that coarse projections can increase finer ranks (a structural, not
  extremal-error, example).
- No lower bounds / extremal tensors showing that √(2d−3) is attained.

## 5. Comparison table

| Claim | Implied by source? | Explanation |
|---|---|---|
| R1a | ADJACENT | Lemma 3.10 is an error-accumulation inequality for a product of orthogonal projections indexed by tree nodes, with square-root-of-sum accumulation. Differences: (i) all projections act on one ambient space and on one fixed tensor A, whereas in R each P_v acts on the output of a general bounded multilinear map μ_v (norm ≤ M) applied to already-projected inputs; (ii) the per-node error in Grasedyck is the data-dependent tail ‖A − π_tA‖, not a uniform defect ρ over inputs in Ran P_child; (iii) comparison target is the unprojected A (or A_best), not P_rF_r. Choosing μ_v = tensor product (M = 1) with elementary-tensor leaves gives only a rank-one special configuration, and even then the hypotheses do not match. No R1a-form statement follows. |
| R1b | NO | No constant in terms of a defect ratio; Remark 3.12 explicitly says the √(2d−2) estimate is not optimal. |
| R2 | NO | No sharpness claims or lower-bound constructions. |
| R3 | ADJACENT | Lemma 3.10's bound depends only on the number of projections, not the order or tree layout, so it is "shape-agnostic" — but it is a non-sharp upper bound in a different setting (binary dimension trees only for the √(2d−3) statements). R3 is a statement about a sharp constant being shape-invariant; not implied. |
| R4 | NO | No extremizers. |
| R5 | NO | Same. |
| R10 | NO | No universal absolute bound; √(2d−3) grows with d. |
| R11 | NO | Accumulation here is √(number of nodes) (Pythagorean), versus the linear limit k−1 of C_k in R11. (Project-side remark, not from the source: the linear count in R reflects that general μ_v can rotate projection residuals back into the retained range, which the orthogonal tensor-product structure used by Grasedyck prevents; this contrast has not been verified as a theorem.) |

## 6. Threat score

**1 / 5** (background).

Justification: the HSVD paper is the canonical reference for quasi-optimal hierarchical truncation
and for the Pythagorean "sum of squared node errors" lemma, but it concerns products of orthogonal
projections on one tensor space with data-dependent errors, gives non-sharp constants (the author
says so), provides no extremizers, and exhibits square-root rather than linear accumulation. None of
R1a–R11 is implied.

## 7. How to cite / position

Grasedyck's hierarchical SVD bounds the error of a product of node-wise orthogonal projections acting on
one fixed tensor by the root-sum-square of node-wise truncation errors (giving the non-sharp factor
√(2d−3)); Theorem R concerns projections interleaved with general bounded multilinear maps under a
uniform local defect, where the sharp constant is identified and grows linearly (k−1) in the small-defect limit.
