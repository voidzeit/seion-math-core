# L3-CY: Yang, Chen, Qiu (2026), "The θ-symmetric SRG with applications to stability of cactus dynamic networks" (+ Yang, Zhang, Chen, Qiu 2025)

Prepared 2026-09-14 (PRIOR-ART-R-CY). Rubric: `PROTOCOL_CY.md` §2. Paraphrased; one short quote.

## 1. Records

| Key | Record | Status |
|---|---|---|
| YCQ26 | X. Yang, W. Chen, L. Qiu, "The θ-Symmetric SRG with Applications to Stability of Cactus Dynamic Networks", arXiv:2608.12591 v1 (12 Aug 2026), eess.SY. No journal reference, no DOI | Found **only** through the POST_HOC Semantic Scholar citation supplement (cites RHY22 and PAT21). Not in OpenAlex forward sets. Preprint, not peer reviewed as far as known |
| YZCQ25 | X. Yang, D. Zhang, W. Chen, L. Qiu, "A Cascade of Systems and the Product of Their θ-Symmetric Scaled Relative Graphs", arXiv:2510.06583 v1 (8 Oct 2025). No DOI found | Same route (S2 citations of RHY22, PAT21) |

## 2. Access

FULL_TEXT (arXiv PDFs, text extraction; definitions double-checked on the arXiv HTML of YCQ26).
YCQ26: Lemma 2, Thm 1, Thm 4, Remark 5, **Thm 5**, Prop. 2, Cor. 4, Thm 6, Prop. 4, Prop. 5, Appendix I (proof of Thm 5).
YZCQ25: Lemmas 1–5, Prop. 1, **Thm 1**, Cor. 1–6.

## 3. Setting

Complex matrices (frequency-wise transfer matrices) and cyclic interconnections: nonsingularity of $I+A_1\cdots A_N$.
θ-symmetric (rotated) SRG ${\rm SRG}_\theta$ with a θ-arc property. In the scalar case it reduces to the scalar itself, not to a conjugate pair.
Gain and phase are coupled per factor.

## 4. Results (paraphrased)

- **YZCQ25 Thm 1.** $I+A_1\cdots A_N$ is nonsingular if $-1\notin\prod_i{\rm SRG}_{\theta_i}(\mathcal A_i)$ (Minkowski product), with $N-1$ factors
  having the θ-arc property. **Cor. 4–6:** over-approximation by annular sectors, whose products are annular sectors (gains multiply, phase
  intervals add). The choice of the rotations $\theta_i$ that maximizes the distance between $-1$ and the product is posed as an open
  optimization (eq. (13)).
- **YCQ26 Thm 5 (necessary and sufficient).** For heterogeneous uncertainty regions
  $\mathcal R[\alpha_i,\beta_i,\gamma_i]=\{re^{j(\theta+\delta)}:\ r\le\frac{\gamma}{1+\sin\Gamma}(\cos\delta+\sqrt{\sin^2\Gamma-\sin^2\delta}),\ \delta\in[-\Gamma,\Gamma]\}$
  ($\theta=(\alpha+\beta)/2$, $\Gamma=(\beta-\alpha)/2$): $I+\prod A_i$ is nonsingular for all admissible uncertain $A_i$ ($i\ne k$) iff
  $-1\notin{\rm SRG}_\theta(A_k)\prod_{i\ne k}\mathcal R[\alpha_i,\beta_i,\gamma_i]$ for some θ. These are per-factor **phase-capped** regions: the convex hull of 0 and the disc with centre $\frac{\gamma}{1+\sin\Gamma}e^{j\theta}$
  and radius $\frac{\gamma\sin\Gamma}{1+\sin\Gamma}$, which is tangent to the rays at angles $\alpha,\beta$ (our reading of the polar formula). For $\Gamma=\pi/2$ the region is the disc of diameter $\gamma$ in direction θ, e.g.
  $D(\tfrac12,\tfrac12)$ for $\gamma=1,\theta=0$. **Necessity** (Appendix I) picks points $z_i$ of the regions **independently** and realizes them by
  unitarily conjugated matrices, so that the product attains $-1$. **Prop. 2:** the same statement with sector regions, where the product is
  $\mathcal S[\sum\alpha_i,\sum\beta_i,\prod\gamma_i]$.
- **YCQ26 Remark 5.** Choosing the rotations to maximize the distance from $-1$ to the product is called "a critical open question".

## 5. Six criteria

| # | Answer | Evidence |
|---|---|---|
| C1 | **YES** | $N$-fold Minkowski products of θ-SRGs / regions (YZCQ25 Thm 1; YCQ26 Thm 5, Prop. 2). |
| C2 | **PARTIAL** | Per-factor phase intervals $[\alpha_i,\beta_i]$ (angle caps) with a coupled gain bound. The regions are cone-over-disc sets (convex hull of 0 and a disc tangent to the two rays), not arcs of the fixed circle $\lvert z-\tfrac12\rvert=\tfrac12$ capped at $\arcsin\eta_u$. For $\Gamma<\pi/2$ the boundary circle depends on the cap, so the PMT factor sets $\{w(\theta):0\le\theta\le\arcsin\eta_u\}$ are not of this form. |
| C3 | **PARTIAL** | Exact (iff) for every $N$, but for the binary question $-1\notin\prod$ with one nominal factor. No sharp value of a distance functional; the max-distance problem is declared open (Remark 5). |
| C4 | **PARTIAL** | Necessity via explicit independent realizations of region points (unitary conjugation). This is structurally like an independent-angle witness, but it realizes membership, not an extremal $\lvert1-\prod\rvert$. |
| C5 | **YES** | Products of regions commute; a cyclic permutation does not affect singularity. The cactus-network extension in the later sections is topology-dependent through the loop structure. |
| C6 | **NO** | Different sets (cone-over-disc regions vs capped arcs), a different functional (membership of $-1$ vs $\max\lvert1-\prod w(\theta_u)\rvert$), and no projected multilinear tree model. Substituting $\gamma_i=1$, $\theta=0$, $\Gamma=\pi/2$ gives full discs $D(\tfrac12,\tfrac12)$ (no caps), which only reaches the uncapped case already covered by Chaffey 2023. |

## 6. Threat

**3 / 5 for H4 (structural analogue):** an exact, every-$N$ statement over Minkowski products of heterogeneous per-factor phase-capped SRG regions,
with independent per-factor realizations. The assumptions are materially different: the functional, the region shape, and the preprint status.
**1 / 5 for H1 / H2.** No constant equal or comparable to $g_{\rm Box}$ is stated. The authors list the distance maximization as open.
YZCQ25 alone: **2 / 5** (sufficient conditions, annular-sector products).

## 7. Proposed citation (if used)

> Exact graphical criteria over Minkowski products of heterogeneous phase-bounded SRG regions have recently been obtained for the robust
> nonsingularity of cyclic interconnections (Yang–Chen–Qiu 2026, Thm 5, arXiv:2608.12591; see also Yang–Zhang–Chen–Qiu 2025). These concern
> membership of $-1$ in the product and do not compute the worst-case distance, which the authors leave open.

Manual: watch for a journal version, and check for a follow-up solving their Remark 5 (distance maximization over products of capped regions).
Such a follow-up could raise the H1/H4 threat.
