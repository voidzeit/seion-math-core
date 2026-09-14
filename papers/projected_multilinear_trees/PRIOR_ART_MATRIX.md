# Prior-art matrix — Projected Multilinear Trees

Date: 2026-08-11. Search performed by an assisted bounded web search across the
equivalence axes listed below. **This is a first pass, not an adjudication.**

Per this repository's own standing policy: *absence from a bounded search is not
evidence of novelty.* The status of every claim below therefore remains
`NOVELTY_NOT_ESTABLISHED`. What this pass produces is (a) the nearest antecedent
family, and (b) a narrowed target for the definitive search.

---

## 1. Axes searched

- sharp error constants for recursive orthogonal projection after multilinear
  composition;
- hierarchical Tucker / tensor-train truncation quasi-optimality constants;
- sharpness/attainment of those constants;
- error accumulation in sequential tensor-network contraction;
- extremal constants for error propagation through bilinear maps as a function
  of perturbation magnitude.

Not yet searched, and required before adjudication: operator-space /
approximate-multiplicativity literature (Johnson, Ulam–Hyers stability for
bilinear maps); numerical multilinear algebra proceedings not indexed by general
web search; the reduced-order-modelling literature; and a citation-graph sweep
outward from the antecedents below.

---

## 2. The nearest antecedent family

**Hierarchical tensor truncation quasi-optimality.** For the TT format,
$$\|U - H_{\tilde r}(U)\| \le \sqrt{d-1}\,\inf_{V \in \mathcal{M}_{\le \tilde r}} \|U - V\|,$$
with $\sqrt{2d-3}$ for the hierarchical Tucker format (Grasedyck 2010;
Oseledets 2011). This is the closest thing found to the universal $k-1$ bound,
and a referee will raise it first.

**Why it does not imply the PMT results.** Four structural differences, each
independently sufficient:

| | TT/HT quasi-optimality | PMT |
|---|---|---|
| object | one **fixed tensor**, truncated | a **composition of maps**, each with its own budget |
| comparison | ratio to the **best rank-$r$ approximation** | ratio to the **unprojected evaluation** |
| norm | Frobenius | operator norm on the laws, with a separate closure budget |
| growth in the site count | $\sqrt{d-1}$ | $k-1$ (linear) |

The two answer different questions. TT asks *how much worse is greedy truncation
than optimal truncation*; PMT asks *how much does a per-node closure defect
$\rho$ amplify by the time it reaches the root*. Neither reduces to the other:
PMT's $\rho$ has no counterpart in the TT statement, and TT's best-approximation
denominator has no counterpart in PMT.

**What is genuinely unresolved by this pass:** whether $\sqrt{d-1}$ is known to
be *attained*. The searches surfaced the bound repeatedly but no matching lower
construction. If it is not known sharp, that is itself relevant context for how
this literature treats sharpness.

**Other families found, all further away.** Alternating-projection error bounds
(sharp for two subspaces, but iterated projection onto a subspace intersection,
not multilinear composition); tensor-network stability results bounding
worst-case amplification by the network **condition number** (a related concern,
but condition-number-driven rather than an extremal constant); recursive
matrix-multiplication norm-growth amplification factors (norm growth, not
projection defect).

---

## 3. Claim-by-claim matrix

| Claim | Nearest antecedent found | Does it imply the claim? | Status |
|---|---|---|---|
| Universal $C_T^P(\eta) \le k-1$ | TT/HT quasi-optimality $\sqrt{d-1}$, $\sqrt{2d-3}$ | **No** — different question, norm and denominator (§2) | `NOT_ESTABLISHED` |
| $C_2^P = 1$ with iff EQ1–EQ3 | none found; the argument is an elementary chain of inequalities | Likely classical *in substance* even if unstated; expect a referee to call it folklore | `LIKELY_FOLKLORE_VERIFY` |
| Gram coupling lemma | none found in this form | Simultaneous use of $K \succeq 0$ and $I-K \succeq 0$ on a 2-plane is a standard technique; the packaging may be new, the technique is not | `TECHNIQUE_STANDARD_STATEMENT_UNSEARCHED` |
| $W_3(\eta)$ exact chain constant | **none found** | — | `NOT_ESTABLISHED` |
| Branching $= W_3$ via nuclear duality | **none found** | — | `NOT_ESTABLISHED` |
| All $k=3$ trees $= W_3$ | **none found** | — | `NOT_ESTABLISHED` |
| $\lim_{\eta\downarrow0} C_T^P = k-1$ | none found | — | `NOT_ESTABLISHED` |
| Growing-support obstruction | none found | Related in spirit to lower bounds on TT ranks, unsearched | `NOT_ESTABLISHED` |
| DAG path constant $K(G)$ | path-counting in acyclic recurrences is classical | The recurrence expansion itself is standard; the multilinear $\eta\downarrow0$ identification is not | `PARTIALLY_CLASSICAL` |

---

## 4. What the search did not find, and why it matters

No result was found in which the accumulation constant is an explicit **function
of the defect ratio** with a **phase transition**, established sharp by a
matching witness. Every antecedent located is one of:

- a fixed constant independent of the perturbation size ($\sqrt{d-1}$);
- a condition-number-driven amplification bound;
- a first-order/asymptotic propagation estimate.

The distinctive content of PMT, if it survives adjudication, is therefore not the
$k-1$ bound — which is the part most likely to have an antecedent — but:

$$\boxed{\;C_3^{P}(\eta) = W_3(\eta)\ \text{exactly, with a phase transition at}\ \eta_c=\sqrt{2/3}\ \text{and a two-dimensional attaining witness.}\;}$$

This is consistent with the strategic reading already recorded: **the defensible
paper is about the exact constants, not about the framework.**

---

## 5. Required before novelty can be adjudicated

1. Settle whether $\sqrt{d-1}$ / $\sqrt{2d-3}$ are known sharp, and read
   Grasedyck 2010 and Oseledets 2011 in full rather than through search summaries.
2. Search the approximate-multiplicativity / Ulam–Hyers-stability literature for
   bilinear and multilinear maps.
3. Citation-graph sweep outward from the antecedents in §2.
4. Search the reduced-order-modelling and model-reduction literature for
   per-stage projection error accumulation.
5. Have a subject-matter reviewer confirm the four structural differences in §2
   are the ones a referee would accept.

Until all five are done, the correct manuscript language is
*"we determine the exact constant"*, never *"the first exact constant"*.

---

## Sources consulted

- Oseledets, *Tensor-Train Decomposition*, SIAM J. Sci. Comput. — <https://epubs.siam.org/doi/10.1137/090752286>
- Grasedyck, *Hierarchical singular value decomposition of tensors*, SIAM J. Matrix Anal. Appl. 31 (2010) 2029–2054 (referenced via the above)
- *On Stability of Tensor Networks and Canonical Forms* — <https://arxiv.org/pdf/2001.01191>
- *Error bounds for the method of alternating projections* — <https://link.springer.com/article/10.1007/BF02551235>
- *Towards automated generation of fast and accurate algorithms for recursive matrix multiplication* — <https://arxiv.org/pdf/2506.19405>
- *A Practical Guide to the Numerical Implementation of Tensor Networks I* — <https://www.frontiersin.org/journals/applied-mathematics-and-statistics/articles/10.3389/fams.2022.806549/full>
