# L3-CY: Lee, Yi, Ryu (2025), "Convergence analyses of Davis–Yin splitting via scaled relative graphs"

Prepared 2026-09-14 (PRIOR-ART-R-CY). Paraphrased.

## 1. Record

| Field | Value | Status |
|---|---|---|
| Venue | SIAM J. Optim. (2025); DOI 10.1137/23M1621320; arXiv:2207.04015 (v3, 21 Apr 2024) | co-citation set $S_2$ (cites HRY20, RHY22, OY02); DOI check in `l3_dois_cy.json` |
| Companion | S. Yi, E. K. Ryu, "... II: convex optimization problems", Optimization (2025), DOI 10.1080/02331934.2025.2544700, arXiv:2211.15604 | forward set of RHY22/OY02; title+abstract only (same machinery, contraction factors for DYS on convex problems) |
| Access | FULL_TEXT arXiv v3 (PDF text): §1–§2 (Thm 2.1, Cor. 2.2–2.3, Thm 2.6 "SRG product theorem", Cor. 2.7), statements of Thms 3.1–3.3 and 4.1 | |

## 2. Results (paraphrased)

- **Thm 2.1 / Cor. 2.2.** For the three-operator DYS map, the set of values $|G-s|$ (distances from a real point $s$) equals the
  set of $|{\rm DYS}(z_A,z_B,z_C)-s|$ over $z_A,z_B,z_C$ in the respective SRGs, under arc properties. Hence the tight
  contraction factor is a **maximum modulus of a three-variable complex polynomial over product sets** (disks).
- **Thms 3.1–3.3.** Contraction factors obtained by bounding that maximum modulus, described as the best known. They are
  compared numerically against PEP tight factors; they are not claimed tight in general.
- **Thm 4.1.** Tight averagedness coefficient of DYS under strong monotonicity / Lipschitz assumptions.
- The introduction recalls HRY20's tightness for the composition of **two** averaged operators; it does not mention $m\ge3$ compositions.

## 3. Six criteria

| # | Answer | Evidence |
|---|---|---|
| C1 | **PARTIAL** | Max modulus of a polynomial $1-z_A-z_B+(2-\alpha z_C)z_Az_B$ over SRG sets. It is not a pure product, but it is the same "max of $\lvert p(z)-s\rvert$ over sets" technique. |
| C2 | **NO** | Sets are full disks and half-planes (monotone / cocoercive / Lipschitz classes), not angle-capped arcs. |
| C3 | **NO** | Three operators in a fixed algebraic form; tight only where stated (Thm 4.1), not for a family indexed by $m$. |
| C4 | **PARTIAL** | Tightness via SRG-fullness for specific results; no general extremizers for Thms 3.1–3.3. |
| C5 | **PARTIAL** | Symmetric in $z_A,z_B$ only. |
| C6 | **NO** | Different map (DYS, not a composition chain), different sets. |

## 4. Threat

**2 / 5** (shared technique: tight operator constants from the maximum distance to a point over images of products of SRG sets).
