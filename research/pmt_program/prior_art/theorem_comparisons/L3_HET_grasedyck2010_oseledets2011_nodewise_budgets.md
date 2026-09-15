# L3-HET comparison: node-wise truncation budgets in HT/TT (Grasedyck 2010; Oseledets 2011; Hackbusch 2012/2018)

Prepared 2026-09-14 (PRIOR-ART-R-HET). This is a Level-3 comparison of one cluster against H1, H2 and H4. The primary source is
Grasedyck (2010), read in full in round 1 (`L3_grasedyck2010_hsvd.md`). Oseledets (2011) and Hackbusch (monograph Thm 11.58) are
secondary members, known through Hackbusch's MiS preprint 29/2018. Everything is paraphrased.

## 1. Bibliographic records

| Key | Record | Status |
|---|---|---|
| G10 | L. Grasedyck, "Hierarchical singular value decomposition of tensors", SIAM J. Matrix Anal. Appl. 31(4) (2010) 2029–2054. DOI 10.1137/090764189 | Round 1: MPI MiS preprint landing page verified; SIAM page not opened (HTTP 403). |
| O11 | I. V. Oseledets, "Tensor-train decomposition", SIAM J. Sci. Comput. 33(5) (2011) 2295–2317. DOI 10.1137/090752286 | OpenAlex W1993482030 resolved. Full text not read (paywall). |
| H12 | W. Hackbusch, *Tensor Spaces and Numerical Tensor Calculus*, Springer 2012. DOI 10.1007/978-3-642-28027-6 | Not read directly. Thm 11.58 is quoted in Hackbusch, MiS preprint 29/2018, eq. (4.13) (read). |

## 2. Access level

G10: FULL_TEXT (MiS preprint, round 1). O11: SECONDARY. H12: SECONDARY. The theorem numbers of O11 (commonly "Thm 2.2 / Cor. 2.4") are
**not verified**.

## 3. Their setting

- One fixed tensor $A$ in a finite-dimensional Euclidean space, with a dimension tree (G10, H12) or a chain of unfoldings (O11).
- There is one orthogonal projection $\pi_t$ per node, acting on the same ambient space. The error is $\lVert A-\prod_t\pi_tA\rVert$.
- Node-wise errors are data-dependent singular-value tails $\varepsilon_t=\lVert A-\pi_tA\rVert$. They are **heterogeneous by nature**.

## 4. Relevant results (paraphrased)

- **G10 Lemma 3.10.** For any order of the node projections, $\lVert A-\prod_t\pi_tA\rVert^2\le\sum_t\lVert A-\pi_tA\rVert^2$. The proof is
  Pythagoras plus $\lVert\pi_t\rVert\le1$.
- **G10 Thm 3.11 / Remark 3.12.** With SVD frames the error is at most $(\sum_t\text{tail}_t^2)^{1/2}\le\sqrt{2d-3}\,\lVert A-A_{\rm best}\rVert$. The
  author states that the estimate is not optimal.
- **G10 Thm 3.18.** Uniform node tolerances $\varepsilon/\sqrt{2d-3}$ guarantee total error ≤ ε (a uniform allocation of a heterogeneous budget).
- **O11 (secondary).** TT-SVD: $\lVert A-B\rVert\le(\sum_k\varepsilon_k^2)^{1/2}$ with per-unfolding errors $\varepsilon_k$. The standard tolerance
  allocation is $\varepsilon/\sqrt{d-1}$ per core.
- **H12 Thm 11.58 (secondary).** HOSVD truncation in HT format: the error is at most the square root of the sum over all vertices of
  the discarded tails.

## 5. Comparison table

| Claim | Implied? | Explanation |
|---|---|---|
| H1 | NO (CLOSE, non-sharp) | These are the canonical **heterogeneous node-wise error budgets** for tree/chain truncation. They are root-sum-square, data-dependent and not sharp. They concern products of projections on one tensor, not projections interleaved with bounded multilinear maps under a uniform-in-input defect. There is no $M_v$ and no $\eta_v$. (Analyst remark, not in the sources: the naive telescoping analogue in the PMT model gives $E\le\Lambda_T\sum_u\eta_u$, because $\lvert1-\cos\theta e^{i\theta}\rvert=\sin\theta$. $G_{\rm box}(\eta)\le\sum_u\eta_u$ is therefore the additive benchmark that H1 sharpens.) |
| H2 | NO (CLOSE, non-sharp) | G10 Lemma 3.10 holds "in any order", and the bound depends only on the multiset of node errors. This is a non-sharp order/placement independence for a heterogeneous budget. H2 asserts the independence for the **sharp** constant and for general topology and arity. |
| H4 | NO | There are no extremal tensors; G10 Remark 3.12 says the estimate is not optimal. |
| H3 | NO | Only uniform allocation (ε/√(#nodes)). There is no capped-equal structure. |
| Proof device | NO | Pythagoras, not angles. |

## 6. Threat score

**3 / 5** for H1/H2 (a similar heterogeneous, placement-independent bound under materially different assumptions). **0–1 / 5** for H4/H3.

## 7. How to cite

> Node-wise heterogeneous truncation budgets for hierarchical and tensor-train formats are classical: the error of the product of
> node-wise projections is bounded by the root-sum-square of node-wise errors, independently of the order of the projections
> (Grasedyck 2010, Lemma 3.10 and Thm 3.11; Oseledets 2011; Hackbusch 2012, Thm 11.58). These bounds are not sharp and concern
> projections of a single tensor; the present result concerns projections interleaved with bounded multilinear maps, where the
> accumulation is linear to first order and the sharp heterogeneous constant is $G_{\rm box}(\eta)$.

Verify the published theorem numbering of G10 and O11 before quoting numbers.
