# L3 comparison: Ceruti, Lubich, Sulz (2023), "Rank-adaptive time integration of tree tensor networks" — Appendix A, Theorem A.1

Prepared 2026-09-14. Found during the item-4 search (sharp constants for error accumulation of
projections/truncations along trees). Level-3 comparison against Theorem R (R1a–R11).
Public sources only; paraphrased.

## 1. Bibliographic record

- Authors: Gianluca Ceruti, Christian Lubich, Dominik Sulz
- Title: Rank-adaptive time integration of tree tensor networks
- Journal: SIAM J. Numer. Anal. 61 (2023), 194–222 (reference as given in arXiv:2412.00858;
  SIAM landing page not checked)
- Preprint: arXiv:2201.10291 (v1 25 Jan 2022, v2 25 Jul 2022), DOI 10.48550/arXiv.2201.10291
- Status: arXiv landing page VERIFIED. Journal reference taken from a later paper by the same group
  (Ceruti, Kusch, Lubich, Sulz, arXiv:2412.00858, which restates the bound as its Theorem 4.3).

## 2. Access level

FULL_TEXT of arXiv v2 for Appendix A (derivation of the rotate-and-cut truncation, Theorem A.1,
remark, and proof by induction over tree height). Main text only scanned for how Theorem A.1 is
used (Section 6: c = ‖C_τ̄‖(d−1)+1 in norm/energy near-conservation). Also read the restatement
(Theorem 4.3) in arXiv:2412.00858.

## 3. Their setting and assumptions

- Object: a complex tree tensor network (general, not necessarily binary trees) in orthonormal
  representation: for each subtree τ with children τ_1..τ_m, X_τ = C_τ ×_0 I ⊗_i U_{τ_i}, with
  U_{τ_i} = Mat_0(X_{τ_i}); matricizations of connection tensors and basis matrices have
  orthonormal columns (2-norm 1) below the root.
- Truncation (Algorithm 7): recursively from root to leaves, rotate by left singular vectors of
  each child-matricization of C_τ, then cut singular values whose tail is ≤ ϑ (tolerance per node).
- Error measured in the Euclidean norm of the full tensor; basis-matrix errors in the matrix 2-norm.
- Key structural facts used: connection-tensor matricizations and basis matrices remain bounded by 1
  in 2-norm after truncation (the analogue of M = 1 and contractive projections).

## 4. Their main results relevant here

- Theorem A.1 (rank truncation error): ‖X_τ̄ − X̃_τ̄‖ ≤ c ϑ with c = ‖C_τ̄‖(d_τ̄ − 1) + 1, where
  d_τ̄ is the number of vertices of the tree.
- Remark after Theorem A.1: scaling the root tolerance by ‖C_τ̄‖ gives ‖X_τ̄ − X̃_τ̄‖ ≤ d_τ̄ ϑ.
- Proof mechanism: induction over tree height establishing ‖U_τ − Ũ_τ‖_2 ≤ d_τ ϑ, using a
  telescoping sum for the difference of Kronecker products and 2-norm bounds ≤ 1 for all factors.
- The authors explicitly note that their analysis yields linear dependence on d, whereas
  Hackbusch's HOSVD-based analysis for binary trees yields square-root dependence. No sharpness
  or lower-bound claims.

## 5. Comparison table

| Claim | Implied by source? | Explanation |
|---|---|---|
| R1a | ADJACENT | Structurally the closest non-sharp analogue found: node-wise truncations along a tree, contractive (norm ≤ 1) combination maps, per-node tolerance ϑ, and a telescoping induction giving a constant linear in the number of nodes. It is the analogue of the naive telescoping bound in R (project-side observation: telescoping over the k−1 non-root internal nodes gives constant k−1 in R1a, hence C_k(η) ≤ k−1). Hypotheses differ: their per-node error is a singular-value tail of the specific orthonormal data, not a uniform operator defect on Ran P_child; combination maps are fixed tensor contractions, not general bounded multilinear maps. |
| R1b | NO | No η-dependent constant; no angle formula. |
| R2 | NO | No optimality claim or extremal example. |
| R3 | ADJACENT | The constant depends only on the number of vertices (and ‖C_root‖), for general trees — a shape-agnostic upper bound, but not a sharp one; R3 asserts invariance of the sharp constant. |
| R4 | NO | No extremizers. |
| R5 | NO | Same. |
| R10 | NO | Constant grows with d; no universal bound < 2. |
| R11 | ADJACENT | Their linear-in-nodes constant coincides in form with the η→0 limit k−1 of C_k, but they do not show it is attained or that it is the limit of a sharp constant. |

## 6. Threat score

**2 / 5** (relevant, clearly distinct).

Justification: this is a published, rigorous tree-wide truncation error bound with linear
accumulation and a telescoping proof that a referee could see as "the same idea". It does not state
or imply sharpness, the finite-η constant, tree-shape invariance of the optimum, or explicit
extremizers. It is worth citing to show that linear, shape-agnostic upper bounds are known and that
Theorem R's contribution is the exact optimal constant (strictly improving on k−1 for η > 0 where
C_k(η) < k−1, e.g. C_3(η) = √(4−3η²) < 2).

## 7. How to cite / position

Linear-in-the-number-of-nodes truncation error bounds for tree tensor networks, obtained by telescoping
with contractive factors, appear e.g. in Ceruti–Lubich–Sulz (Theorem A.1); Theorem R shows that under a
uniform local projection defect the optimal constant is C_k(η), which equals the telescoping value k−1
only in the limit η→0.

## Item-4 search record (sharp constants for accumulation along trees/chains)

Queries run (web search, 2026-09-14): "sharp constant tensor network truncation error bound tree best
possible"; "error accumulation projections tensor tree sharp bound hierarchical truncation sharp";
"HOSVD quasi-optimality sqrt(d) bound sharp attained example hierarchical Tucker sqrt(2d-3) sharp";
"Hackbusch Truncation of tensors in the hierarchical format arXiv sharp estimate"; "sharp error bound
composition of projected multilinear maps tree orthogonal projections consistency error accumulation
constant k-1"; "tree tensor network truncation error tight OR sharp bound number of nodes orthogonality
center arXiv 2023 2024"; "tensor train rounding TT-SVD error bound sqrt(d-1) sharp cannot be improved";
"error propagation nested projections multilinear operations tree best constant low-rank arithmetic
tensor"; Krämer thesis (RWTH 2020, DOI 10.18154/RWTH-2020-05412). Also scanned Semantic Scholar
citations of arXiv:2001.01191 (11 citing works; none relevant to sharp constants).

Outcome: no source found that states a sharp/best-possible constant for accumulation of projection or
truncation errors along a tree or chain of multilinear operations. Candidates not read in full and
worth a later check: Hackbusch, "Truncation of tensors in the hierarchical format", SeMA J. (2019),
MiS preprint 29/2018 (HOSVD truncation within HT format); Krämer PhD thesis (tree SVD, rounding);
Bachmayr–Nouy–Schneider, arXiv:2112.01474 (tree tensor networks for compositional functions; error
propagation through compositions). The only sharp "angle-type" constants found concern iterated
products of projections onto subspaces (see L3_reich2017_simultaneous_projections_optimal.md).
