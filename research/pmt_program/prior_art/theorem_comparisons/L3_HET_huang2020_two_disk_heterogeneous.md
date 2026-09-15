# L3-HET comparison: heterogeneous two-factor products (Huang–Ryu–Yin 2020; Ryu–Hannah–Yin 2022; Farouki–Pottmann 2002; Bünger–Rump 2019)

Prepared 2026-09-14 (PRIOR-ART-R-HET). This is a Level-3 comparison of one cluster against H1 (scalar step), H4 and H3. It reuses the round-1
readings `L3_huang2020_tight_coefficients_srg.md`, `L3_ryu2022_scaled_relative_graph.md` and
`L3_farouki2002_minkowski_products_N_disks.md`, re-read for *heterogeneous* factors. Everything is paraphrased.

## 1. Bibliographic records

| Key | Record | Status |
|---|---|---|
| HRY20 | X. Huang, E. K. Ryu, W. Yin, J. Math. Anal. Appl. 490(1) (2020) 124211. DOI 10.1016/j.jmaa.2020.124211. arXiv:1912.01593 | Round 1 VERIFIED |
| RHY22 | E. K. Ryu, R. Hannah, W. Yin, Math. Program. 194 (2022). DOI 10.1007/s10107-021-01639-w | Round 1 VERIFIED |
| FP02 | R. T. Farouki, H. Pottmann, Reliable Computing 8(1) (2002) 43–66. DOI 10.1023/A:1014737602641 | Round 1 VERIFIED. Anchor DOI re-verified in this round (OpenAlex W422477 + Crossref). |
| BR19 | F. Bünger, S. M. Rump, "Complex disk products and Cartesian ovals", J. Geom. (2019). DOI 10.1007/s00022-019-0502-2 | Metadata only (OpenAlex). Not read. |

## 2. Access level

HRY20, RHY22, FP02: FULL_TEXT (round 1). BR19: TITLE_ONLY (the abstract is empty in OpenAlex).

## 3. What is heterogeneous in these sources

- **HRY20 Theorem 1.** It treats $\theta_1\neq\theta_2$: the SRG of $N_{\theta_1}N_{\theta_2}$ is the region inside a Cartesian oval, i.e. the exact
  Minkowski product of two *different* disks through 1. **Corollary 1** gives the tight heterogeneous averagedness coefficient
  (the Ogura–Yamada constant) by curvature matching at z = 1.
- **FP02 Prop. 4.1.** It gives the boundary of the product of N disks with *different radii* $R_k$ as (a subset of) the outer loop of an explicit
  curve. The argument uses a necessary matching condition and is heuristic.
- **RHY22 Thm 7.** The SRG of a composition is the Minkowski product of the SRGs of heterogeneous classes: "angles add, lengths multiply".
- **BR19** (title). Exact complex disk products via Cartesian ovals, presumably with rigorous heterogeneous two-disk statements. Not read.

## 4. Comparison table

| Claim | Implied? | Explanation |
|---|---|---|
| H1, scalar step $\max\lvert1-\prod_uw(\theta_u)\rvert$ over $\theta_u\le\arcsin\eta_u$ | NO | The factor sets in H1 are **arcs** $\{w(\theta):0\le\theta\le\alpha_u\}$ of the *same* circle $\lvert z-\tfrac12\rvert=\tfrac12$, truncated at different angles. The heterogeneity here is a cap on the angle. In HRY20/FP02/BR19 the heterogeneity is a disk **radius**, and the factor sets are full disks. Round 1 showed that disk-level information gives only the non-sharp value $\max(1,\cdot)$ for small caps (`L3_farouki2002_*` §5). The capped heterogeneous arc product is not treated. |
| H4 (sharpness, planar witness with independent per-node angles) | NO (ANALOGUE) | HRY20 Cor. 1 is a sharp heterogeneous constant for **two** factors and a different functional (smallest disk through 1). The planar chain with independent angles $\prod\cos\theta_je^{i\theta_j}$ itself is classical as a construction (Oikhberg 1999, Lemma 2(a), round 1). Its extremality for the projected error with heterogeneous caps was not found. |
| H2 | NO | Minkowski products are commutative, so order-independence of the product *set* is trivial. Tree/placement independence of an operator-level sharp constant is not addressed. |
| H3 (capped equal angles) | KNOWN_IN_SPECIAL_CASE only for all caps = π/2 | If every $\eta_u=1$, the caps disappear. H3 then reduces to the uniform full-arc equal-angle statement, which is FP02 §5 (heuristic) or elementary via Jensen (round-1 R7(a)). Nothing is found for unequal or sub-π/2 caps. |
| Proof device | NO (technique adjacent) | RHY22 Thm 7 plus Fact 17 is the round-1 "angles add, lengths multiply" mechanism. The uniform scaling by π/Θ when Θ > π is not found. |

## 5. Threat score

**2 / 5** overall (HRY20 is the strongest member: a sharp heterogeneous two-factor constant for a different functional). **1 / 5** for H3
beyond the known all-π/2 case. The L1 threat of 3 is lowered to 2 at adjudication because the heterogeneity parameter (disk radius) does
not map to the H1 caps.

## 6. How to cite

> Minkowski products of disks with different radii are described by Cartesian ovals (Farouki–Pottmann 2002, Prop. 4.1; rigorous for two
> factors in Huang–Ryu–Yin 2020, Thm 1, which also gives the tight heterogeneous averagedness coefficient, Cor. 1). The factor sets in
> the present heterogeneous constant are instead arcs of one circle truncated at different angles, to which disk-product boundaries do
> not apply.

Read BR19 before submission. It may contain rigorous N-disk or heterogeneous statements.
