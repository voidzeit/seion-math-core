# L3-CY: Huang, Ryu, Yin (2020), "Tight coefficients of averaged operators via scaled relative graph" — re-read for $m\ge3$

Prepared 2026-09-14 (PRIOR-ART-R-CY). Complements `../theorem_comparisons/L3_HET_huang2020_two_disk_heterogeneous.md`. Paraphrased.

| Field | Value |
|---|---|
| Record | J. Math. Anal. Appl. 490(1) (2020) 124211; DOI 10.1016/j.jmaa.2020.124211; arXiv:1912.01593 (v3, 27 Apr 2020). Re-verified (`anchors_cy.json`: OpenAlex W3024233472; Crossref match). A separate OpenAlex record of the arXiv version (DOI 10.48550/arxiv.1912.01593) exists; the exact-title search did not return it, so its citations are not in the forward set (it appears as a citing work of CY15/OY02) |
| Access | FULL_TEXT arXiv v3 (PDF text): abstract, §1, §3 (Thm 1, Cor. 1, proof of Thm 1), §4 (Fact 3, Cor. 2), references |

## What it says about $m\ge3$

- §3 treats only $N_{\alpha_1}N_{\alpha_2}$. **Thm 1** gives the exact region (Cartesian oval) of ${\rm Disk}(\alpha_1){\rm Disk}(\alpha_2)$.
  **Cor. 1** gives the Ogura–Yamada coefficient and its tightness ("cannot be reduced without further assumptions").
- §4: the tight averagedness coefficient of **Davis–Yin three-operator splitting** (Cor. 2). This is three operators, but the map is not a
  composition chain and the result is not an $m$-indexed family.
- No statement, remark or open problem about compositions of $m\ge3$ averaged operators, or about products of three or more disks,
  was found in the text (searched: "three", "m operators", "composition", "tight"). The proof of Thm 2 / Cor. 2 uses the image set
  $\{1-z_2+z_1(2z_2-1-\alpha z_3z_2)\}$ with $z_1,z_2\in{\rm Disk}(1/2)$ and $z_3$ in a scaled ${\rm Disk}(1/2)$, a three-variable polynomial
  image and not a pure $m$-fold product, and only to prove containment of a disk.

## Six criteria

| # | Answer | Evidence |
|---|---|---|
| C1 | YES | SRG of the composition = Minkowski product of two disks (Thm 1). |
| C2 | NO | Disk radii $\alpha_i$; no caps. |
| C3 | NO | $m=2$. |
| C4 | YES ($m=2$) | Tightness via SRG-fullness. |
| C5 | YES ($m=2$) | Symmetric. |
| C6 | NO | Different functional (smallest disk through 1), $m=2$, full disks. |

**Threat 2 / 5** (unchanged).
