# L3-CY: Chaffey, Forni, Sepulchre (2023), "Graphical Nonlinear System Analysis"

Prepared 2026-09-14 (PRIOR-ART-R-CY). Rubric: `PROTOCOL_CY.md` §2. Paraphrased; one short quote.

## 1. Record

| Field | Value | Status |
|---|---|---|
| Authors / title | T. Chaffey, F. Forni, R. Sepulchre, "Graphical Nonlinear System Analysis" | |
| Venue | IEEE Trans. Automat. Control (2023; volume/pages not verified); DOI 10.1109/TAC.2023.3234016; arXiv:2107.11272 | OpenAlex W-record in forward sets of HRY20, RHY22, PAT21 (co-citation set $S_2$); DOI check in `l3_dois_cy.json` |
| How found | Co-citation set $S_2$ (cites HRY20 and RHY22) | frozen procedure §3.3 |
| Prior rounds | Round 1 `PRIOR_ART_MATRIX.csv`: threat 1, title-level only ("graphical nonlinear system analysis") | **re-scored here** |

## 2. Access

FULL_TEXT, arXiv:2107.11272 (PDF text extraction). Read: SRG definitions and interconnection rules
(Propositions on sums/products, chord and arc properties), §"cascades" with **Theorem 5**, its proof, Figs. 8–10.
Published numbering not checked (paywalled); theorem numbers below refer to the arXiv version.

## 3. Setting

Input–output systems on $L_2$; SRGs of nonlinear operators; series interconnection ⇒ SRG ⊆ product of SRGs
(equality under an arc property, as in Ryu–Hannah–Yin). Subsystem $i$ is output-strict incrementally positive with
parameter $\gamma_i$; its SRG is the disc with centre $\gamma_i/2$ and radius $\gamma_i/2$, i.e. $\gamma_i\,D(\tfrac12,\tfrac12)$.

## 4. Relevant result (paraphrased)

**Theorem 5 (arXiv numbering).** For a cascade of $n$ such systems, the SRG is the product of the $n$ discs, and
its boundary is parameterized by $z(\theta)=\gamma_1\cdots\gamma_n\cos^n(\theta/n)e^{-j\theta}$, $-\pi<\theta<\pi$
(the conjugate orientation is immaterial). Proof: boundary points of disc $i$ are $\gamma_i\cos(\varphi_i)e^{-j\varphi_i}$,
$|\varphi_i|<\pi/2$; the product of such points is $\prod\gamma_i\prod\cos\varphi_i\,e^{-j\sum\varphi_i}$, and
$\prod\cos\varphi_i\le\cos^n(\sum\varphi_i/n)$ by Jensen (convexity of $-\ln\cos$), so equal angles give the outer
boundary. The authors state that for $n>2$ this SRG is new; they use it for an incremental $L_2$-gain bound (minimal
distance from $-1$ of the inverse SRG), a shortage-of-passivity value, and a generalized secant condition.
Quote: "For n > 2, this SRG is a novel result."

## 5. Six criteria

| # | Answer | Evidence |
|---|---|---|
| C1 complex / Minkowski product | **YES** | Thm 5: SRG of the cascade = Minkowski product of $n$ discs; factors written as $\cos\varphi_i e^{-j\varphi_i}$, exactly $w(\varphi_i)$ up to conjugation and scaling. |
| C2 angular caps $\theta_u\le\arcsin\eta_u$ | **PARTIAL (no caps)** | The per-factor angle is the same angle as in $w$, but it ranges over the full interval $(-\pi/2,\pi/2)$. Heterogeneity is a scale $\gamma_i$, which factors out of the product. There are no per-factor angle caps. |
| C3 exact for every $m$ | **YES for the region** | The region is exact for all $n$ (Thm 5). No sharp constant for $\max\lvert1-z\rvert$ is stated. |
| C4 extremizer | **YES (boundary)** | Equal angles $\varphi_i=\theta/n$ realize the boundary. Operators realizing each disc boundary point are implicit via SRG-fullness, not built explicitly. |
| C5 order independence | **YES (trivial)** | Product of sets is commutative; heterogeneity only in scale. No tree/placement statement. |
| C6 specializes to $g_{\rm Box}$ | **ONLY for all $\eta_u=1$** | With $\gamma_i=1$ and no caps, $\max_{z\in{\rm SRG}}\lvert1-z\rvert=\max_\theta\lvert1-\cos^n(\theta/n)e^{-j\theta}\rvert$, which is the uniform all-$\pi/2$ value $g_{\rm Box}(1,\dots,1)$ (e.g. $n=2$: $2/\sqrt3$; $n=3$: $9/7$, cf. `cy_numeric_check_output.txt`). This last maximization is **not** carried out in the paper. For $\eta_u<1$ the arcs are strict sub-arcs; Jensen with equal angles is then infeasible when caps differ, so Thm 5 does not give $g_{\rm Box}$. That is exactly the open H3 question and the H1/H4 content. |

## 6. Threat

**3 / 5** for the scalar step of H1/H4 and for round-1 R7(a) (uniform, all caps $\pi/2$). It is a peer-reviewed,
rigorous statement of the exact $n$-fold product of discs $D(\tfrac12,\tfrac12)$ with the $\prod\cos\varphi_ie^{i\varphi_i}$
parametrization and the equal-angle (Jensen) boundary. **1 / 5** for H2 (placement). **2 / 5** for H3: equal angles are
the uncapped case of the capped-equal-angle ansatz, and the capped case is not treated. It does not imply H1/H4 for
heterogeneous caps, and it contains no operator-level statement about projected multilinear trees.

## 7. Proposed citation

> The Minkowski product of $n$ discs $D(\tfrac12,\tfrac12)$, i.e. the scaled relative graph of a cascade of output-strict
> incrementally positive systems, has the boundary $\cos^n(\theta/n)e^{i\theta}$, obtained from $\prod_i\cos\varphi_ie^{i\varphi_i}$ by
> Jensen's inequality (Chaffey–Forni–Sepulchre 2023, Thm 5 in arXiv:2107.11272). The uniform constant with all defects equal to 1 is
> the largest distance from 1 on that region. With per-node caps $\theta_u\le\arcsin\eta_u<\pi/2$ the factor sets are proper arcs,
> and the equal-angle description no longer applies.

Action: check the published TAC numbering (paywalled) and whether Chaffey's PhD thesis (Cambridge; year not verified) extends
Thm 5 to angle-restricted classes (manual).
