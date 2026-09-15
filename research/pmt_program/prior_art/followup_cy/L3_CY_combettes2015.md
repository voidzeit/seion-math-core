# L3-CY: Combettes, Yamada (2015), Prop. 2.5 / Remark 2.7 — the constant, the six criteria, and a numerical comparison with $g_{\rm Box}$

Prepared 2026-09-14 (PRIOR-ART-R-CY). Complements `../theorem_comparisons/L3_HET_combettes2015_heterogeneous_compositions.md`
(which stays authoritative for H1/H2 wording). Paraphrased; one short quote.

## 1. Record and access

CY15 = P. L. Combettes, I. Yamada, J. Math. Anal. Appl. 425(1) (2015) 55–70, DOI 10.1016/j.jmaa.2014.11.044, arXiv:1407.5100.
The DOI was re-verified in this follow-up (`anchors_cy.json`: OpenAlex W1998428773 journal + W2950378366 arXiv preprint; Crossref
title/author/year match; the arXiv DataCite DOI 10.48550/arxiv.1407.5100 returns HTTP 404 at Crossref, as expected). FULL_TEXT arXiv v2:
§2 (Prop. 2.4, 2.5 with proof, Remark 2.7).

## 2. The constant (explicit)

For $T_i$ $\alpha_i$-averaged, $\alpha_i\in(0,1)$, $i=1,\dots,m$, the composition $T_1\cdots T_m$ is $\varphi$-averaged with

$$\varphi(\alpha_1,\dots,\alpha_m)=\Bigl(1+\Bigl(\sum_{i=1}^m\frac{\alpha_i}{1-\alpha_i}\Bigr)^{-1}\Bigr)^{-1},\qquad\text{equivalently}\qquad
\frac{\varphi}{1-\varphi}=\sum_{i=1}^m\frac{\alpha_i}{1-\alpha_i}.$$

In SRG language (RHY22), $\alpha$-averagedness means that the SRG lies in the disk $D(1-\alpha,\alpha)$, which passes through 1.
A point $c$ lies in $D(1-\alpha,\alpha)$ iff $\alpha\ge|1-c|^2/(2(1-\mathrm{Re}\,c))$ (elementary; checked in the script).
Remark 2.7 compares $\varphi$ with the max-based constant $m\max\alpha_i/((m-1)\max\alpha_i+1)$ (equal iff all $\alpha_i$ coincide).
Tightness: CY15 motivates tight constants ("It is therefore important that they be tight") but proves none. HRY20 Cor. 1 proves $m=2$.

*Heuristic observation (ours, not from the source; not a proof).* Under $z\mapsto\log z$ at $z=1$, the circle $\partial D(1-\alpha,\alpha)$
has radius of curvature $\alpha/(1-\alpha)$. For convex sets tangent at a common point with a common normal, radii of curvature
add under Minkowski sums. So additivity of $\alpha/(1-\alpha)$ is exactly second-order contact at $z=1$ of
$\prod_iD(1-\alpha_i,\alpha_i)$ with $D(1-\varphi,\varphi)$. This suggests that $\varphi$ is tight for **every** $m$ in the planar
normal (complex-scalar) model. Check (T) in `cy_numeric_check_output.txt` agrees: for $m=3,4$ the supremum of the minimal
averagedness over products of boundary points approaches $\varphi$ from below near $z=1$ (e.g. $0.749993$ vs $\varphi=0.75$),
and $\varphi$ is never exceeded. **No source found in this follow-up states this for $m\ge3$** (see the report).

## 3. Six criteria (CY15 Prop. 2.5 read against $g_{\rm Box}$)

| # | Answer | Evidence |
|---|---|---|
| C1 | **NO** (in the source) / YES in SRG reformulation | Proved by algebraic induction on Prop. 2.4; the SRG product form is later (RHY22 Thm 7, HRY20). |
| C2 | **NO** | $\alpha_i$ is a disk radius. Every point $w(\theta)$, $\theta\in(0,\pi/2]$, has minimal averagedness exactly $1/2$, so no $\alpha<1/2$ disk contains any arc point other than 1. Averagedness cannot see the caps $\arcsin\eta_u$. |
| C3 | **NO** (source) | Sharp for $m=2$ only via HRY20; $m\ge3$ tightness not stated (heuristically true in the scalar model, §2). |
| C4 | **NO** | No extremizer. |
| C5 | **YES** | $\varphi$ is symmetric in the $\alpha_i$. Chains only; no trees. |
| C6 | **NO** | Correspondence (A), containment with $\alpha_u=1/2$: gives the valid but cap-blind bound $g_{\rm Box}\le2\varphi=2m/(m+1)$, attained only for $m=1,\eta=1$ (e.g. $g_{\rm Box}(1,1,1)=9/7\approx1.2857<1.5$; $g_{\rm Box}(0.05^3)\approx0.1497\ll1.5$). Correspondence (B), $\alpha_u=\eta_u/2$: $2\varphi(\eta/2)$ is **not** a bound. It is below $g_{\rm Box}$ in 8 of 14 test vectors (e.g. $(0.3,0.3,0.3)$: $0.692<0.833$), equal for the two $m=1$ vectors, and above in the remaining 4 (e.g. $(1,1,1)$: $1.5>1.286$). The only agreement is to first order for small $\eta$ (both $\approx\sum\eta_u$). Check (D): even the exact $\max\lvert1-z\rvert$ over $\prod D(1-\alpha_i,\alpha_i)$ is strictly below $2\varphi$ (e.g. $1.2857$ vs $1.5$), so a sharp averagedness constant does not yield a sharp distance-from-1 constant. |

## 4. Threat

Unchanged from HET: **3 / 5** for H1/H2 as an analogue (heterogeneous, symmetric composition constant), **1 / 5** for H4/H3.
The numerical comparison shows that CY15 is **unrelated** to $g_{\rm Box}$ beyond (a) a cap-blind valid upper bound and
(b) first-order agreement for small defects under a non-rigorous correspondence. Heuristic check only.
