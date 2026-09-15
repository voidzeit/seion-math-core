# L3-HET comparison: Ceruti, Lubich & Sulz (2023), "Rank-adaptive time integration of tree tensor networks", Appendix A

Prepared 2026-09-14 (PRIOR-ART-R-HET). This is a Level-3 comparison against H1 and H2. It complements the round-1 file
`L3_ceruti2023_ttn_rank_truncation.md`. Everything is paraphrased.

## 1. Bibliographic record

| Key | Record | Status |
|---|---|---|
| CLS23 | G. Ceruti, C. Lubich, D. Sulz, SIAM J. Numer. Anal. 61 (2023) 194–222. DOI 10.1137/22M1473790. arXiv:2201.10291. | Round 1: arXiv verified. DOI present in pool (OpenAlex record, snowball via BSU16). |

## 2. Access level

FULL_TEXT of arXiv:2201.10291v2. Read: Appendix A (Algorithm 7, criterion (A.2), Theorem A.1, the Remark, and the proof via (A.5)). Section 6 uses $c_\tau=\lVert C_\tau\rVert(d_\tau-1)+1$.

## 3. Their setting

Orthonormal tree tensor networks are truncated from the root to the leaves. At each vertex, singular values of child matricizations are cut
when their tail is ≤ ϑ (A.2). **The same tolerance ϑ is used at every vertex.** The Remark allows a modified root tolerance
ϑ/‖C‖.

## 4. Relevant results

- **Theorem A.1.** $\lVert X_{\bar\tau}-\hat X_{\bar\tau}\rVert\le c_{\bar\tau}\vartheta$ with $c_{\bar\tau}=\lVert C_{\bar\tau}\rVert(d_{\bar\tau}-1)+1$. Here $d_{\bar\tau}$ is the number of vertices.
- **Remark.** With root tolerance ϑ/‖Ĉ‖ the bound becomes $d_{\bar\tau}\vartheta$.
- **Proof.** Induction over tree height gives $\lVert U_\tau-\tilde U_\tau\rVert_2\le d_\tau\vartheta$ (A.5). It telescopes Kronecker-product differences, with all factors of norm ≤ 1.

## 5. Comparison table

| Claim | Implied? | Explanation |
|---|---|---|
| H1 | NO (ANALOGUE) | This is a telescoping, linear-in-nodes bound. The only heterogeneity is at the root. A node-dependent-tolerance version ($\sum_v\vartheta_v$) follows from the same induction, but it is **not stated**. It is not sharp and has no defect ratio. |
| H2 | NO (ANALOGUE, non-sharp) | The constant depends only on the number of vertices (and on ‖C_root‖), not on the tree shape. This is shape-independence of a non-sharp, uniform-tolerance bound. |
| H4 | NO | No extremizers. |
| H3 | NO | — |

## 6. Threat score

**2 / 5** (the same as round 1; the heterogeneous reading adds nothing stronger).

## 7. How to cite

Keep the round-1 sentence (linear, shape-agnostic telescoping bounds for TTN truncation). Add that the per-vertex tolerance is uniform
in Theorem A.1.
