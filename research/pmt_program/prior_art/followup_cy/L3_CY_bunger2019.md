# L3-CY: Bünger, Rump (2019), "The determinant of a complex matrix and Gershgorin circles" (+ "Complex disk products and Cartesian ovals", title only)

Prepared 2026-09-14 (PRIOR-ART-R-CY). Paraphrased.

| Field | Value |
|---|---|
| Record | F. Bünger, S. M. Rump, Electron. J. Linear Algebra 35 (2019) 181–186; DOI 10.13001/1081-3810.3910 (DOI redirect → journals.uwyo.edu article 1963; publisher PDF, open access) |
| Companion | F. Bünger, S. M. Rump, "Complex disk products and Cartesian ovals", J. Geom. (2019), DOI 10.1007/s00022-019-0502-2: **TITLE_ONLY** (paywalled; the OpenAlex abstract is empty; no preprint located) |
| How found | Keyword harvest CY3 (OpenAlex, "complex disk products exact region" / "Minkowski products of complex disks Cartesian oval") |
| Access | FULL_TEXT (publisher PDF): Theorem 1, Lemma 2, Lemma 3, Corollary 4 |

## Results (paraphrased)

- **Lemma 2.** Parameterization of the outer loop of the Cartesian oval bounding $D(1,R)\cdot D(1,r)$, with no case distinction (two factors).
- **Lemma 3.** For disks **centred at 1** with $Rr=Ss$ and $R\ge S\ge s\ge r$: $D(1,S)\cdot D(1,s)\subseteq D(1,R)\cdot D(1,r)$
  (radius redistribution at fixed product enlarges the product set).
- **Theorem 1 (n factors).** If the partial sums of the ordered $|\delta_j|$ are dominated by those of the radii $r_j$, then $\prod(1+\delta_j)$
  can be written as $\prod(1+g_j)$ with $|g_j|\le r_j$. This is a membership statement for the $n$-fold Minkowski product of disks centred at 1,
  proved by induction using Lemma 3.
- **Corollary 4.** The set product of Gershgorin discs contains the determinant (complex matrices).

## Six criteria

| # | Answer | Evidence |
|---|---|---|
| C1 | YES | $n$-fold Minkowski products of complex disks. |
| C2 | NO | Disks $D(1,r_j)$ centred at 1 with heterogeneous radii; the geometry is not arcs of $\lvert z-\tfrac12\rvert=\tfrac12$, and there are no angle caps. |
| C3 | NO | Membership / majorization, not a sharp extremal constant; no max distance to a point. |
| C4 | NO | — |
| C5 | PARTIAL | Majorization is on the sorted radii, so it is permutation-invariant. |
| C6 | NO | Different sets and no distance functional. |

**Threat 1 / 5** (Minkowski products of $n\ge3$ disks, but centred disks with radius heterogeneity and a membership question).
Manual: read the J. Geom. companion before submission, as already listed in HET §6.5.
