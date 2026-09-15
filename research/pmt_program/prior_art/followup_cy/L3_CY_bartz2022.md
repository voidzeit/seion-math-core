# L3-CY: Bartz, Dao, Phan (2021/2022), "Conical averagedness and convergence analysis of fixed point algorithms"

Prepared 2026-09-14 (PRIOR-ART-R-CY). Paraphrased.

| Field | Value |
|---|---|
| Record | S. Bartz, M. N. Dao, H. M. Phan, J. Global Optim. (Crossref issued 2021; volume/pages not verified); DOI 10.1007/s10898-021-01057-4; arXiv:1910.14185. In the forward sets of CY15 and OY02 |
| Access | FULL_TEXT arXiv (PDF text): §2 (Prop. 2.4, Prop. 2.5, Cor. 2.6, **Thm 2.7**, Cor. 2.8) |

## Results (paraphrased)

- **Prop. 2.5.** Composition of two conically averaged operators (constant of Ogura–Yamada form).
- **Thm 2.7 / Cor. 2.8 (m factors).** For conically $\theta_i$-averaged $T_i$ with scalars $\sigma_i$, $\prod\sigma_i=1$, under
  a sequential condition on $\theta_k$ the composition is conically $\theta$-averaged with
  $\theta=\bigl(1+(\sum_i\theta_i/(1-\theta_i))^{-1}\bigr)^{-1}$. This is the CY15 constant extended to conic parameters; it is
  averaged if $\max\theta_i<1$. Proof by induction on $m$.
- No tightness statements (the word does not occur outside the reference list).

## Six criteria

| # | Answer | Evidence |
|---|---|---|
| C1 | NO | Algebraic induction |
| C2 | NO | Conic averagedness parameters (disk radii) |
| C3 | NO | Upper bounds only |
| C4 | NO | — |
| C5 | PARTIAL | Constant symmetric; the admissibility condition (22) is sequential in $k$ |
| C6 | NO | Cap-blind (see correspondence A in `cy_numeric_check_output.txt`) |

**Threat 2 / 5** (conic extension of CY15 for $m$ factors; non-sharp).
