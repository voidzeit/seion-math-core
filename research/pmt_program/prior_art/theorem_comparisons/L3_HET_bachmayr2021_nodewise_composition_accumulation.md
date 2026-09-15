# L3-HET comparison: Bachmayr, Nouy & Schneider (2021), "Approximation by tree tensor networks in high dimensions: Sobolev and compositional functions"

Prepared 2026-09-14 (PRIOR-ART-R-HET). This is a Level-3 comparison against H1, H2 and H4. Round 1 read this source at Level 2 (threat 3, R1a).
Public sources only. Everything is paraphrased.

## 1. Bibliographic record

| Key | Record | Status |
|---|---|---|
| BNS21 | M. Bachmayr, A. Nouy, R. Schneider, "Approximation by tree tensor networks in high dimensions: Sobolev and compositional functions", arXiv:2112.01474 (v1, 2 Dec 2021), dedicated to R. DeVore. | Title and authors VERIFIED on the arXiv PDF first page (this resolves the round-1 "VERIFY title" flag). Journal version not checked (`NO_DOI` for the preprint; MR Lookup / Crossref needed). |

## 2. Access level

FULL_TEXT of arXiv v1. Read §4: the compositional class, eqs. (12)–(13), Lemma 4.4, Prop. 4.7 and Lemma 4.9 with proof.

## 3. Their setting

- The functions are compositions $f=C((f_\alpha)_{\alpha\in I(T)})$ along a dimension tree, with Sobolev-bounded constituents (class $\mathcal F^T_{s,B}$).
- There is one approximation operator $Q^\alpha_{N_\alpha}$ per node. It is nonexpansive in $L^\infty$ (12) and has rate $(\min N)^{-s}$ (13), with
  **node-dependent** resolutions $N_\alpha$.
- The approximations are nested level by level: $\tilde f_\ell=(\bigotimes_\alpha Q^\alpha_{N_\alpha})(\tilde f_{\ell-1}\circ(f_\alpha))$.

## 4. Relevant results (paraphrased)

- **Lemma 4.4.** For compositions of length ℓ, $\lVert h\rVert_{W^{s,\infty}}\le C(B,s,\ell)$, where the constant grows with ℓ (e.g. $B_1^{\ell-1}$ for s = 1).
- **Prop. 4.7.** The squared tree-tensor approximation error is at most $\sum_{\alpha}(M\,C(B,s,\mathrm{level}(\alpha)))^2 r_\alpha^{-2s}$ (node-wise, level-weighted).
- **Lemma 4.9.** $\lVert f-\tilde f\rVert_{L^\infty}\le\sum_{\alpha\in I(T)}Q_{\#S(\alpha)}\,C(B,s,\mathrm{level}(\alpha))\,(\min N_\alpha)^{-s}$.
  The proof telescopes over levels, uses the triangle inequality inside a level, and uses nonexpansiveness of the $Q$'s.

## 5. Comparison table

| Claim | Implied? | Explanation |
|---|---|---|
| H1 | NO (CLOSE, additive) | This is a genuine **heterogeneous node-wise accumulation bound along a tree of compositions**: each node has its own local error $(\min N_\alpha)^{-s}$, and the total is their weighted sum. It is additive (first-order type), not sharp, in $L^\infty$ for nonlinear compositions, and it carries depth-growing weights. There are no orthogonal projections after bounded multilinear maps and no defect ratio $\eta_v$. |
| H2 | NO (contrast) | The weights $C(B,s,\mathrm{level}(\alpha))$ depend on **where** a node sits (its level), so the bound is placement-dependent. H2 asserts the opposite for the sharp constant in the PMT model. |
| H4 | NO | There are no lower bounds or extremal examples. |
| H3 | NO | — |
| Proof device | NO | Triangle inequality and nonexpansiveness. No angles. |

## 6. Threat score

**3 / 5** for H1 (a similar heterogeneous tree accumulation result under materially different assumptions). **1 / 5** for H2 (contrast)
and H4.

## 7. How to cite

> Additive, node-wise accumulation bounds along trees of compositions, with level-dependent weights, appear in approximation theory
> for tree tensor networks (Bachmayr–Nouy–Schneider 2021, Lemma 4.9 and Prop. 4.7). In contrast, for projected multilinear trees the
> sharp heterogeneous constant is placement-independent.

Obtain the journal version (if any) and check the lemma numbering before citing.
