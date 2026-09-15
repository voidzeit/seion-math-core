# L3-CY: Bauschke, Bendit, Moursi (2023), "How averaged is the composition of two linear projections?"

Prepared 2026-09-14 (PRIOR-ART-R-CY). Rubric: `PROTOCOL_CY.md` §2. Paraphrased; one short quote.

## 1. Record

| Field | Value | Status |
|---|---|---|
| Authors / title | H. H. Bauschke, T. Bendit, W. M. Moursi, "How averaged is the composition of two linear projections?" | |
| Venue | Numer. Funct. Anal. Optim. 44(15–16) (2023) 1652–1668; DOI 10.1080/01630563.2023.2270308; arXiv:2303.13738 | DOI check in `l3_dois_cy.json` |
| How found | `POST_HOC` web search for the tightness of the Ogura–Yamada / Combettes–Yamada constant (logged in `PROTOCOL_CY.md` §9); cross-checked against the frozen pool (`pool_cy.csv`) | outside the frozen forward/keyword procedure unless it appears in `pool_cy.csv` |

## 2. Access

FULL_TEXT, arXiv:2303.13738 v1 (PDF text extraction): §1 (Fact 1.3), §2, §3 (Theorem 3.2, Corollary 3.3, Remark 3.4,
Example 3.5, Remark 3.7).

## 3. Setting

Real Hilbert space; modulus of averagedness $k(T)$ (the smallest $\alpha$ with $T$ α-averaged); compositions
$P_VP_U$ and $P_V((1-\lambda)\mathrm{Id}+\lambda R_U)$ of (relaxed) projections onto closed linear subspaces.

## 4. Relevant results (paraphrased)

- **Theorem 3.2 / Corollary 3.3.** $k(P_VP_U)=(1+c_F)/(2+c_F)$, where $c_F$ is the cosine of the Friedrichs angle
  between $U$ and $V$. This is an exact, angle-dependent averagedness modulus for **two** projections.
- **Remark 3.4.** With $c_F=1$ (possible only in infinite dimension) the Ogura–Yamada bound is attained; in finite dimension
  it is strictly improved. Quote: "This shows that the Ogura–Yamada bound is optimal!"
- **Remark 3.7.** The two-relaxed-projection case is left open; the authors conjecture sharpness of Ogura–Yamada there.
- Nothing about $m\ge3$ factors.

## 5. Six criteria

| # | Answer | Evidence |
|---|---|---|
| C1 complex / Minkowski product | **NO** | Exact modulus computed via the linear (2×2 block) structure, not as a complex product. |
| C2 angular caps | **PARTIAL** | One angle per **pair** (Friedrichs angle), which enters as $c_F$; it is not a per-factor cap along $\lvert z-\tfrac12\rvert=\tfrac12$. |
| C3 exact for every $m$ | **NO** | Exact for $m=2$ only; nothing for $m\ge3$. |
| C4 extremizer | **YES (m = 2)** | Exact formula; optimality of Ogura–Yamada via $c_F=1$ subspaces. |
| C5 order independence | **YES (m = 2)** | Formula symmetric ($c_F(U,V)=c_F(V,U)$). |
| C6 specializes to $g_{\rm Box}$ | **NO** | Different functional (averagedness modulus, not $\max\lvert1-\prod w\rvert$); one angle per pair, not per-node defect caps; $m=2$. |

## 6. Threat

**2 / 5** (closest averagedness analogue involving projections and angles; sharp only for two factors; different functional).
It answers a sharpness question for $m=2$ in a projection setting. It does **not** answer the priority question for $m\ge3$.

## 7. Proposed citation

> For two projections the averagedness modulus is known exactly in terms of the Friedrichs angle, $k(P_VP_U)=(1+c_F)/(2+c_F)$
> (Bauschke–Bendit–Moursi 2023, Cor. 3.3), which also shows optimality of the two-factor Ogura–Yamada bound (Remark 3.4).
