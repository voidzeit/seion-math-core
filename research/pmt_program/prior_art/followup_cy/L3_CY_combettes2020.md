# L3-CY: Combettes, Pesquet (2020), "Lipschitz certificates for layered network structures driven by averaged activation operators"

Prepared 2026-09-14 (PRIOR-ART-R-CY). Paraphrased.

| Field | Value |
|---|---|
| Record | P. L. Combettes, J.-C. Pesquet, SIAM J. Math. Data Sci. (2020; volume/pages not verified); DOI 10.1137/19M1272780; arXiv:1903.01014. Found by `POST_HOC` web search (search-engine result list for the CY tightness query) and checked against `pool_cy.csv` |
| Access | FULL_TEXT arXiv (PDF text): §2 (eq. (2.4), Ex. 2.1), §4 (Thm 4.2, Prop. 4.3, Remark 4.4, Prop. 4.5), §5 statements, §6 |

## Results (paraphrased)

- **Model.** $T=R_m\circ W_m\circ\cdots\circ R_1\circ W_1$, with bounded linear $W_i$ and $\alpha_i$-averaged activations $R_i$ (heterogeneous $\alpha_i$).
- **Thm 4.2.** The Lipschitz constant $\theta_m$ is a sum over subsets $J\subseteq\{1,\dots,m-1\}$ of weights
  $\prod_{j\in J}\alpha_j\prod_{j\notin J}(1-\alpha_j)$ times products of norms of partial products of the $W$'s.
- **Prop. 4.3.** Equality cases for the constant: $\theta_m=\lVert W_m\cdots W_1\rVert$ if all $R_i=\mathrm{Id}$, and $\theta_m=\prod\lVert W_i\rVert$ if all $\alpha_i=1$. There are bounds between these extremes.
- "Sharp" in the paper means improved over $\prod\lVert W_i\rVert$. No proof that $\theta_m$ is the best constant for intermediate $\alpha_i$ was found.

## Six criteria

| # | Answer | Evidence |
|---|---|---|
| C1 | NO | Real-norm expansions, not complex products |
| C2 | NO | Averagedness constants; no angles |
| C3 | NO | Exactness only in the degenerate cases of Prop. 4.3(ii)–(iii) |
| C4 | PARTIAL | Only those degenerate cases |
| C5 | NO | Depends on the order of layers through partial products $W_{j_k}\cdots W_{j_{k-1}+1}$ |
| C6 | NO | Different functional (Lipschitz constant of a layered network), no projection defects or angle caps |

**Threat 2 / 5**: a heterogeneous, layered (chain) constant for compositions of averaged operators interleaved with linear
maps. It is structurally the closest "chain of averaged maps with linear maps in between" analogue of a PMT chain, but it is
non-sharp, order-dependent, and uses a different functional. Section 6 of the paper lists DAG (non-chain) structures as future work.
