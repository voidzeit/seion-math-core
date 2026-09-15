# L3 comparison: Baboulin, Kaya, Mary, Robeyns (2025), "Numerical stability of tree tensor network operations, and a stable rounding algorithm"

Prepared 2026-09-14. Level-3 (theorem-by-theorem) comparison against Theorem R (R1a–R11).
Public sources only; paraphrased.

## 1. Bibliographic record

- Authors: Marc Baboulin (Univ. Paris-Saclay, LMF), Oguz Kaya (Univ. Paris-Saclay, LISN),
  Theo Mary (Sorbonne Univ., LIP6; corresponding), Matthieu Robeyns (Univ. Paris-Saclay, LISN)
- Title: Numerical stability of tree tensor network operations, and a stable rounding algorithm
- Venue/year: preprint, HAL hal-04996127 (v1), PDF dated "Version of March 18, 2025".
  Author publication page lists it as a preprint (no journal version found).
- Identifier: HAL hal-04996127; author-hosted PDF https://www.lip6.fr/Theo.Mary/doc/TTNstab.pdf
- Status: PARTIALLY VERIFIED. The HAL landing page (hal.science/hal-04996127v1) could not be viewed
  (access-control interstitial). Title/authors/HAL id verified on T. Mary's publications page and
  on the title page of the author-hosted PDF.

## 2. Access level

FULL_TEXT (author-hosted PDF, version of 18 March 2025, 24 pp.). Read completely: Section 2
(framework, Defs. 2.1–2.2, Lemmas 2.3–2.7, Theorem 2.8), Section 3 (model (3.2)–(3.3),
Theorem 3.1, Theorem 3.2), Section 4 (Corollaries 4.1–4.3), Section 5 (Algorithms 5.1–5.2,
Corollary 5.1, comparison with TT-SVD, HOSVD, Gram SVD, Krämer thesis), Section 6 experiments,
conclusion. Not verified whether the HAL version differs from the author PDF.

## 3. Their setting and assumptions

- Object: finite-dimensional real tree tensor networks (TT, Tucker, hierarchical Tucker as special
  topologies); Frobenius norm of the represented full tensor.
- Four kernels: Matricize/Tensorize (exact), Split (matrix factorization, e.g. QR or truncated SVD),
  Merge (contraction).
- Error model (finite precision / backward stability): computed Split satisfies BC = A + E with
  ‖E‖ ≤ cε‖A‖ (3.2); computed Merge satisfies Â = BC + E with ‖E‖ ≤ cε‖B‖‖C‖ (3.3).
  Truncated SVD is folded in with ε = u + τ (machine precision plus truncation threshold).
- Structural hypothesis: α-normalization (Defs. 2.1–2.2): one node carries the norm
  (‖U_j‖ ≤ α_j‖X‖), every other node is α_i-Lipschitz for contraction toward U_j. With all
  non-central nodes semi-orthogonal, α = e (all ones).
- All global statements are FIRST ORDER in ε (O(ε²) terms explicitly not tracked, Section 3.3).
- No orthogonal projectors acting on outputs of general bounded multilinear maps; nodes are
  concrete tensors and the only "maps" are contractions with norm controlled by α.

## 4. Their main results relevant here

- Lemma 2.3 / Lemma 2.4: contracting adjacent nodes multiplies α's; ‖X‖ ≤ ∏_{i≠j} α_i ‖U_j‖.
- Lemma 2.5: ‖U_i‖ ≤ α_i √r_i.
- Lemma 2.6: diagonal concatenation of semi-orthogonal nodes with ≥ 2 inner edges stays
  semi-orthogonal. Lemma 2.7: concatenation of two semi-orthogonal leaf matrices is √2-normalized.
  Theorem 2.8: the sum of two e-normalized networks is α-normalized with α = √2 at leaves, 1 elsewhere.
- Theorem 3.1 (local error): one Split or Merge on an α-normalized network changes the represented
  tensor by at most r c ε (∏ α_i) ‖X‖ (r = largest inner dimension).
- Theorem 3.2 (global error): after p operations, ‖X − X̂‖ ≤ s ε‖X‖ + O(ε²) with
  s = Σ_k c r_k ∏_i α_i^(k); simplified to p r α^n c. Linear accumulation by telescoping +
  triangle inequality.
- Corollary 4.1 (Full contraction), 4.2 (Compress, s = (n−1)cr), 4.3 (Orthogonalize,
  s = 2(n−1)cr∏α_i), Corollary 5.1 (Round: s = cr(2(n−1)∏α_i + 4(n−1) − 2ℓ)).
- The authors state explicitly that the 2^{ℓ/2} constant can be pessimistic and leave sharper
  constants to future work (end of Section 4.3). No lower bounds or extremal examples for the
  constants in Theorems 3.1–3.2.

## 5. Comparison table

| Claim | Implied by source? | Explanation |
|---|---|---|
| R1a | ADJACENT | Theorem 3.2 is an error-accumulation bound over a tree computation, but for backward errors of kernels (additive E with ‖E‖ ≤ cε‖A‖), first order only, with constants involving r, c and α-products. A projection defect could be modelled as a Split/Merge error on the full node, but their hypothesis bounds the error relative to the full node norm, not on inputs restricted to Ran P_child, and the O(ε²) remainder is uncontrolled. No exact inequality of R1a form. |
| R1b | NO | No constant depending on a defect ratio η; no angle formula. |
| R2 | NO | No optimality/sharpness claim; authors say their constant may be pessimistic. |
| R3 | NO | Constants depend on number of nodes, operations, leaves, inner dimension r. Topology-independence is only in the sense that the framework covers all trees, not that a sharp constant is shape-invariant. |
| R4 | NO | No extremal constructions for the error bounds. |
| R5 | NO | Same. |
| R10 | NO | No universal absolute constant < 2; constants grow with n and p. |
| R11 | ADJACENT | The linear growth (n−1) in Corollaries 4.1–4.2 is the same telescoping count that appears as the η→0 limit of C_k, but no limit statement for a sharp constant is made. |

## 6. Threat score

**1 / 5** (relevant background).

Justification: the paper is about finite-precision stability of tree tensor network algorithms and
the role of semi-orthogonality ("norm concentrated in one node"). Its bounds are first-order,
non-sharp by the authors' own remark, and depend on dimensions and operation counts. It neither
states nor implies any sharp constant, tree-shape invariance, or extremizer of Theorem R type. The
only overlap is the generic telescoping accumulation idea.

## 7. How to cite / position

Baboulin et al. give first-order stability bounds for sequences of local operations on tree tensor
networks whose norm is concentrated in one node, with constants that grow linearly in the number of
operations; Theorem R addresses a different question — the exact, sharp constant for the discrepancy
caused by node-wise orthogonal projections of bounded multilinear maps — and its tree-independence.
