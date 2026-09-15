# L3-HET comparison: capped water-filling and the capped-equal-angle hypothesis H3 (Palomar–Fonollosa 2005; He et al. 2013)

Prepared 2026-09-14 (PRIOR-ART-R-HET). This is a Level-3 comparison against **H3 (OPEN)** only. Everything is paraphrased.

## 1. Bibliographic records

| Key | Record | Status |
|---|---|---|
| PF05 | D. P. Palomar, J. R. Fonollosa, "Practical algorithms for a family of waterfilling solutions", IEEE Trans. Signal Process. 53(2) (2005) 686–695. DOI 10.1109/TSP.2004.840816 | VERIFIED (OpenAlex W2102412823 + Crossref; used as snowball anchor) |
| HZZN13 | P. He, L. Zhao, S. Zhou, Z. Niu, "Water-filling: a geometric approach and its application to solve generalized radio resource allocation problems", IEEE Trans. Wireless Commun. (2013). DOI 10.1109/TWC.2013.061713.130278 | Metadata from OpenAlex. Abstract only. |

## 2. Access level

PF05: FULL_TEXT (author PDF, palomar.home.ece.ust.hk). The formulas were partly lost in text extraction, so Proposition 1, Corollary 1 and Algorithms 1–4 were read
structurally. HZZN13: ABSTRACT_ONLY.

## 3. Relevant results (paraphrased)

- **PF05 Prop. 1 / Cor. 1.** This is an exact finite algorithm for solutions of water-filling form, with one or several water levels and monotone
  constraint functions. The "maximum power" in Algorithms 3–4 is a *total* power, not a per-channel cap.
- **HZZN13 (abstract).** Geometric water-filling extends to individual **peak-power caps** (GWFPP). The optimal allocation then has the
  level-with-caps form: each item gets the common level unless its cap binds.

## 4. Comparison with H3

Recall H3: $G_{\rm box}(\eta)=\max_\tau\lvert1-\prod_uw(\min(\alpha_u,\tau))\rvert$, with $\alpha_u=\arcsin\eta_u$.

| Aspect | Status | Explanation |
|---|---|---|
| Form $\theta_u=\min(\alpha_u,\tau)$ | KNOWN as a technique (analyst derivation, not in the sources as stated) | For a *fixed* total angle $\Theta=\sum\theta_u$, maximizing the modulus $\prod\cos\theta_u$ (a separable concave objective in log form) under box caps is a capped water-filling problem. Its solution is exactly $\min(\alpha_u,\tau)$ (KKT; HZZN13-type). This gives the upper modulus branch at fixed Θ. |
| Full H3 reduction | NOT FOUND | $\lvert1-Re^{i\Theta}\rvert$ is convex in R, so at fixed Θ the maximum can sit at the **minimum** modulus. That branch is attained at vertex-type (unequal) allocations, not at water-filling. H3 also needs the Θ-optimization and the cap at Θ = π. None of this appears in the water-filling literature. |
| All caps equal to π/2 | KNOWN_IN_SPECIAL_CASE | See `L3_HET_huang2020_two_disk_heterogeneous.md`: this is round-1 R7(a) (FP02 §5 heuristic; Jensen). |

## 5. Threat score

**1 / 5** for H3 (a technique ingredient only). No threat to H1/H2/H4.

## 6. How to cite (only if H3 is proved)

> For fixed total angle, the capped-equal allocation $\theta_u=\min(\arcsin\eta_u,\tau)$ is the classical water-filling solution with
> individual caps (e.g. He et al. 2013); the reduction of $G_{\rm box}$ to this one-parameter family additionally requires controlling the
> minimum-modulus branch and the phase, which is where the argument differs.

Do not cite water-filling as evidence *for* H3. H3 remains OPEN.
