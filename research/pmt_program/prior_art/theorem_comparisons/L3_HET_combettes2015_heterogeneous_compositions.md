# L3-HET comparison: Combettes & Yamada (2015), "Compositions and convex combinations of averaged nonexpansive operators"

Prepared 2026-09-14 (PRIOR-ART-R-HET). Level-3 comparison against H1, H2, H4 and H3 of
`SEARCH_PROTOCOL_HET.md`. Public sources only. Everything is paraphrased.

## 1. Bibliographic record

| Key | Record | Status |
|---|---|---|
| CY15 | P. L. Combettes, I. Yamada, "Compositions and convex combinations of averaged nonexpansive operators", J. Math. Anal. Appl. 425(1) (2015) 55–70. DOI 10.1016/j.jmaa.2014.11.044. arXiv:1407.5100. | VERIFIED. OpenAlex W1998428773 and Crossref agree on title, authors and DOI. Crossref gives issue date 2015-05; OpenAlex gives year 2014 (online first). |
| OY02 | N. Ogura, I. Yamada, Numer. Funct. Anal. Optim. 23 (2002). DOI 10.1081/NFA-120003674. | Identifier resolved (OpenAlex W2093425777). Not read; cited through CY15. |

## 2. Access level

FULL_TEXT of arXiv:1407.5100 (revised 8 Oct 2014). Read: §1, §2 (Props. 2.1–2.6, Remark 2.7). §3–§4 (algorithms) were skimmed.

## 3. Their setting

- Real Hilbert space. $T$ is α-averaged if $T=(1-\alpha)\mathrm{Id}+\alpha R$ with $R$ nonexpansive.
- The objects are compositions $T_1\cdots T_m$ of operators with **different** averagedness constants $\alpha_i$.
- The quantity is the averagedness constant of the composition. It controls step-size ranges.
- There are no orthogonal projections interleaved with multilinear maps, no defect ratio, and no error functional
  $\lVert P_rF_r-R_r\rVert$.

## 4. Relevant results (paraphrased)

- **Prop. 2.4** (m = 2, first obtained in OY02 Thm 3(b)). $T_1T_2$ is α-averaged with
  $\alpha=(\alpha_1+\alpha_2-2\alpha_1\alpha_2)/(1-\alpha_1\alpha_2)$.
- **Prop. 2.5** (m factors). $T_1\cdots T_m$ is $\varphi(\alpha_1,\dots,\alpha_m)$-averaged, where
  $\varphi=\bigl(1+(\sum_i\alpha_i/(1-\alpha_i))^{-1}\bigr)^{-1}$ (eq. 2.8). This constant is a **symmetric function of the
  heterogeneous parameters**, so it does not depend on the order of the factors.
- **Remark 2.7.** $\varphi$ is at most the max-based constant $\tilde\varphi=m\max\alpha_i/((m-1)\max\alpha_i+1)$, with equality iff all
  $\alpha_i$ are equal. It is strictly better than an older two-operator constant.
- Tightness: CY15 motivates tight constants but proves none. Tightness for m = 2 was shown later by Huang–Ryu–Yin
  (2020, Cor. 1; see `L3_HET_huang2020_two_disk_heterogeneous.md`). Tightness for m ≥ 3 is **not stated in any source read in this
  round**.

## 5. Comparison table

| Claim | Implied? | Explanation |
|---|---|---|
| H1 (heterogeneous upper bound $\Lambda_T G_{\rm box}(\eta)$) | NO (ANALOGUE) | CY15 has the same *shape* of result: a heterogeneous composite constant that improves on the constant obtained by using the worst parameter everywhere. This is the analogue of H1 against the conservative fallback (U). The model, parameter and functional are all different. |
| H2 (constant depends only on the multiset of defects) | NO (ANALOGUE, non-sharp for m ≥ 3) | $\varphi$ is symmetric in the $\alpha_i$, so order-independence of a heterogeneous composition constant is known for averaged operators. It covers chains only (no trees, arity or placement), and it is sharp only for m = 2. |
| H4 (sharpness, planar witness with independent angles) | NO | No extremal examples in CY15. For m = 2 the tightness (HRY20) uses the two-disk Minkowski product. |
| H3 (capped equal angles) | NO | No equal-parameter reduction. Remark 2.7(ii) only says that the heterogeneous and max-based constants coincide when all parameters are equal. |
| Proof device (lifted angle, π/Θ scaling) | NO | The proof is algebraic induction on Prop. 2.4. |

## 6. Threat score

**3 / 5** for H1/H2. The source has a similar result (a heterogeneous, symmetric, improvable-over-max composition constant, tight for two
factors) under materially different assumptions. **1 / 5** for H4/H3. It does not imply any H claim.

## 7. How to cite

> Heterogeneous composition constants that depend symmetrically on per-factor parameters, and improve on the constant obtained from
> the worst factor, are classical for averaged operators (Ogura–Yamada 2002; Combettes–Yamada 2015, Prop. 2.5 and Remark 2.7). Their
> tightness is known for two factors (Huang–Ryu–Yin 2020, Cor. 1). The present heterogeneous bound concerns a different functional
> (projected evaluation error in multilinear trees) and is shown to be sharp for every number of non-root nodes.

Do not write that composition constants "had only uniform versions". CY15 is a counterexample to that phrasing.
