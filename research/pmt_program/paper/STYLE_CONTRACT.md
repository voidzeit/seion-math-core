# Style contract — Theorem R paper

```
STATUS:  FROZEN 2026-09-14 (editorial contract; changes only by explicit revision entry)
RULE:    if a new sentence does not fit this register, it probably should not enter the paper
WORDS:   "exact" → the formula;  "sharp" → the inequality;  "attained" → the extremizer
```

## 1. Scientific objective

The objective is to determine the sharp worst-case accumulation of local projection defects in
finite tree-structured multilinear computations with intermediate orthogonal projections.

More precisely, we seek the best possible projected-error constant, exhibit extremizers attaining
equality, and determine whether this constant depends on the combinatorial structure of the
underlying tree. (A characterization of *all* equality cases is not claimed; it is an open problem.)

## 2. Title

**Sharp Worst-Case Error Bounds for Tree-Structured Multilinear Computations with Orthogonal Projections**

Functional-analysis variant: *Sharp Worst-Case Error Bounds for Tree-Structured Multilinear
Computations in Real Hilbert Spaces*.

## 3. Terminology

**Use:** tree-structured multilinear computation · projected multilinear tree (PMT, only after the
definition) · bounded multilinear map · contractive multilinear map (normalized argument,
$\lVert\mu\rVert_{\rm op}\le1$) · orthogonal projection · local projection defect · normalized
local projection defect · projected output error · worst-case error · sharp bound · sharp constant ·
best possible constant · error accumulation · error amplification · internal-node count ·
combinatorial structure of the underlying tree · extremizer · equality case · planar /
two-dimensional extremizer · spherical-lift angle · multilinear angle contraction · scalar
reduction · scalar extremal problem · formalized and machine-checked in Lean 4 with Mathlib.

**Avoid:** law · universal law · leakage (in the formal development) · topology collapse ·
dimensional collapse · witness (in the mathematical exposition) · machine proved · experimentally
verified · revolutionary · fundamental · first-ever · SEIÓN (in the mathematical narrative) ·
"chains, stars and …" (a literal star has one internal node).

## 4. Abstract

> We study finite tree-structured multilinear computations in real Hilbert spaces in which every
> internal node applies a bounded multilinear map followed by an orthogonal projection. Given a
> uniform bound $M$ on the operator norms and a bound $\rho$ on the local projection defect, we
> determine the best possible constant in the worst-case estimate for the projected output error.
> For $k$ internal nodes and normalized defect $\eta=\rho/M\in(0,1]$, the sharp constant is
> $$C_k(\eta)=\frac1\eta\max_{0\le\theta\le\arcsin\eta}\bigl|1-(\cos\theta\,e^{i\theta})^{k-1}\bigr|.$$
> At fixed internal-node count and normalized local projection defect, this constant is independent
> of the combinatorial structure of the underlying tree. Equality is attained for every admissible
> tree structure by an explicit realization in a two-dimensional real Hilbert space.
> The proof introduces a spherical-lift angle on the closed unit ball. Its contraction under
> contractive multilinear maps, combined with a telescoping argument, reduces error propagation
> through the tree to a scalar extremal problem, which is solved explicitly.
> The normalized theorem, including the upper bound, admissibility of the extremizing construction,
> the matching lower bound, and equality of the corresponding suprema, has been formalized in Lean 4
> with Mathlib.

## 5. Opening of the introduction

> Hierarchical computations frequently combine multilinear operations with intermediate
> projections. While the defect introduced by a single projection is straightforward to quantify,
> the sharp accumulation of such defects through an arbitrary computation tree is less transparent.
> We determine the sharp worst-case amplification factor for a class of finite tree-structured
> multilinear computations with intermediate orthogonal projections. The resulting constant depends
> on the number of internal nodes and the normalized local projection defect, but not on the
> combinatorial structure of the underlying tree.

## 6. Definition of the object

> Throughout, a *projected multilinear tree* (PMT) is a finite rooted tree whose internal vertices
> carry bounded multilinear maps and orthogonal projections, and whose leaves carry input vectors.
> The *local projection defect* at an internal vertex is the norm of the component discarded by the
> corresponding orthogonal projection, evaluated on admissible inputs: internal-child inputs lie in
> the ranges of their associated projections, while leaf inputs are unrestricted.

## 7. Main results

> **Theorem 1.1 (Sharp worst-case projected-error bound).** For every PMT with $k$ internal nodes,
> operator-norm bound $M$, local projection defect bound $\rho$ and leaf inputs $z_\ell$,
> $$\lVert P_rF_r-R_r\rVert\le C_k(\eta)\,\rho\,M^{k-1}\prod_\ell\lVert z_\ell\rVert,\qquad \eta=\rho/M,$$
> with $C_k(\eta)$ as above. The constant $C_k(\eta)$ is best possible.

> **Corollary 1.2 (Independence from tree structure).** At fixed internal-node count $k$ and
> normalized local projection defect $\eta$, the sharp worst-case projected-error constant is the
> same for every admissible tree structure — chains, balanced trees, highly branched trees, and
> irregular trees. This statement concerns the worst-case constant only; it does not imply that
> different tree structures have identical errors, approximation quality, or computational behavior
> on individual instances.

> **Theorem 1.3 (Two-dimensional extremizers).** For every admissible tree structure there exists a
> realization in a two-dimensional real Hilbert space that attains equality in Theorem 1.1. Thus the
> worst-case value over all dimensions is already attained in dimension two.

## 8. Proof strategy

> The key geometric quantity is a spherical-lift angle on the closed unit ball. After normalizing
> the operator norm, this angle is contractive under multilinear maps. Replacing the inputs one
> coordinate at a time and applying the spherical triangle inequality yields a multilinear
> angle-contraction estimate. The resulting nodewise bound induces a multiplicative scalar recursion.
> Iteration over the tree reduces the Hilbert-space error problem to a scalar extremal problem. A
> diagonal extremization argument then identifies the sharp constant, and an explicit
> two-dimensional construction attains equality. The contraction property parallels known
> monotonicity properties of generalized fidelity.

## 9. Positioning relative to tensor approximation

> The present result is not a quasi-optimality estimate relative to a best low-rank approximation.
> It is a sharp worst-case stability estimate for an admissible class of tree-structured
> multilinear computations with intermediate orthogonal projections. The theorem optimizes the
> global projected error under local operator-norm and projection-defect constraints rather than
> comparing a truncation algorithm with a best approximation of prescribed rank.

## 10. Formal verification

> The normalized theorem and its supporting lemmas have been formalized in Lean 4 with Mathlib. The
> formal development includes the multilinear angle-contraction estimate, nodewise propagation, the
> global upper bound, admissibility of the two-dimensional extremizing construction, the matching
> lower bound, and equality of the associated suprema. The Lean development machine-checks the
> formal definitions and statements; the correspondence between the formal model and the
> mathematical admissible class, together with the scaling and common-ambient-space reductions used
> to recover the general formulation, is documented separately. The development contains no `sorry`
> declarations or project-specific axioms; the axioms reported for the main theorems are
> `propext`, `Classical.choice` and `Quot.sound`, recorded in the reproducibility package.

Verified 2026-09-14 by `lake env lean AxiomsCheck.lean` (see `../lean/BUILD_LOG.md`).

## 11. Practical limitation

> The estimate is sharp in the worst case. It need not provide a sharp relative-error estimate for
> an individual computation, because the output norm may be much smaller than the natural scale
> $M^k\prod_\ell\lVert z_\ell\rVert$. Indeed, no universal relative-error estimate can hold without
> additional lower control on the output amplitude. Instance-dependent relative estimates therefore
> require additional information on amplitude propagation.

## 12. Novelty language

Until the prior-art review (`../prior_art/`) is complete: **no affirmative novelty claim.**

If the systematic review finds no equivalent result:

> To the best of our knowledge, existing analyses do not identify the exact worst-case constant for
> this class of tree-structured multilinear computations under local projection-defect constraints.
> The distinguishing feature is the simultaneous combination of an explicit best constant,
> independence from arbitrary tree structure at fixed internal-node count, and an extremizer
> attaining equality for every admissible tree structure.

## 13. Two-sentence thesis

> We determine the sharp worst-case projected-error constant for finite tree-structured multilinear
> computations with intermediate orthogonal projections in real Hilbert spaces and show that, at
> fixed internal-node count and normalized local projection defect, it is independent of the
> combinatorial structure of the underlying tree. Equality is attained by an explicit
> two-dimensional extremizer, and the normalized theorem has been formalized and machine-checked in
> Lean 4 with Mathlib.

## Revision log

| Date | Change |
|---|---|
| 2026-09-14 | Frozen from author draft with corrections: `(\cos\theta\,e^{i\theta})` typo fixed; "contractive" in proof strategy; "stars" removed; auditable axiom sentence; "sharp worst-case amplification factor"; objective says "exhibit extremizers" (no full equality-case characterization); Thm 1.3 consequence rephrased ("worst-case value … attained in dimension two"). |
| open | Attainment of the maximum over θ (compactness) is argued on paper; the Lean statement is equality of suprema. Formalize `IsCompact.exists_isMaxOn` step before using "attained" in the formal-verification paragraph. |
| 2026-09-14 (later) | The item above is resolved on branch `research/heterogeneous-theorem-r`, which is not yet merged: `theorem_R_max_attained`, `gBox_attained` and `heterogeneous_max_attained` are machine-checked. "Attained" may enter §10 once that branch is merged. |
| 2026-09-14 (later) | Revision **R1 PROPOSED** (below): heterogeneous architecture. It is not adopted. Adoption requires (a) merge of the heterogeneous Lean branch, (b) the PRIOR-ART-R-HET verdict, and (c) an explicit author decision. Until then §§4–13 above remain the contract. |

## Revision R1 — PROPOSED (not in force)

Rationale: the heterogeneous statement contains the uniform one as a special case. It is also
machine-checked (H1, H2, H4, attainment, and the scaled form with `M_v > 0`), so the paper can lead
with it. H3 (capped equal angles) is open and must not appear as a result.

**R1-§7 Main results.**

> **Theorem 1.1 (Sharp heterogeneous projected-error bound).** Let $T$ be a PMT. For every internal
> vertex $v$ let $M_v>0$ bound the operator norm of $\mu_v$ and let $\rho_v\ge0$ bound its local
> projection defect; put $\eta_v=\rho_v/M_v$. Then
> $$\lVert P_rF_r-R_r\rVert\le G_{\rm box}(\boldsymbol\eta)\prod_{v}M_v\prod_\ell\lVert z_\ell\rVert,\qquad
> G_{\rm box}(\boldsymbol\eta)=\max_{0\le\theta_v\le\arcsin\eta_v}\Bigl|1-\prod_{v\ne r}\cos\theta_v\,e^{i\theta_v}\Bigr|,$$
> where the product and the maximum run over the non-root internal vertices. The constant
> $G_{\rm box}(\boldsymbol\eta)$ is best possible for every tree structure and every assignment of
> normalized local projection defects.

> **Corollary 1.2 (Independence from tree structure and defect placement).** The sharp constant
> depends only on the multiset $\{\eta_v : v \text{ non-root internal}\}$. It does not depend on the
> combinatorial structure of the underlying tree, on the arities, on the root defect, or on which
> vertex carries which defect. This concerns the worst-case constant only.

> **Corollary 1.3 (Uniform defects).** If $\eta_v=\eta\in(0,1]$ for every non-root internal vertex and
> $M_v=M$, then $G_{\rm box}(\eta,\dots,\eta)=\eta\,C_k(\eta)$ with
> $C_k(\eta)=\eta^{-1}\max_{0\le\theta\le\arcsin\eta}|1-(\cos\theta\,e^{i\theta})^{k-1}|$. This
> recovers the bound $C_k(\eta)\,\rho\,M^{k-1}\prod_\ell\lVert z_\ell\rVert$.

> **Theorem 1.4 (Two-dimensional extremizers).** For every tree structure and every defect assignment
> there is a realization in a two-dimensional real Hilbert space attaining equality in Theorem 1.1.

**R1-§8 Proof strategy, added sentence.**

> In the heterogeneous setting the scalar reduction yields one angle per internal vertex, constrained
> only by its own defect. When the total angle exceeds $\pi$, a uniform rescaling of all angles
> reduces to the boundary case. No equal-angle reduction is needed for the sharp constant, and the
> diagonal extremization enters only in Corollary 1.3.

**R1-§10 Formal verification, replacement sentence** (only after merge).

> The formal development includes the heterogeneous upper bound, the extremizing construction with
> independent vertex angles, the equality of suprema, invariance under permutation of defects,
> attainment of the maxima, the scaling reduction for positive operator-norm bounds, and the
> recovery of the uniform constant.

**R1 novelty and positioning (internal candidate; subject to §12 and PRIOR-ART-R-HET).**

Banned: "previous work considers only uniform local errors". Combettes–Yamada 2015, Grasedyck 2010
and Bachmayr–Nouy–Schneider 2021 contradict it. Candidate sentence:

> Existing analyses include heterogeneous and tree-independent error estimates in related settings.
> The distinguishing feature of the present result is the determination of the exact sharp
> worst-case constant for nodewise projection defects, together with its invariance under
> placement and an explicit extremizing construction attaining equality.

Comparison sentence. The inequality is machine-checked as `gBox_le_sum`. The first-order agreement is
argued on paper only (`w(θ) = 1 + iθ + O(θ²)`):

> The sharp constant never exceeds the additive telescoping bound $\sum_v \eta_v$ and agrees with
> it to first order in the defects.

**R1-§10 addendum** (after merge). The common-ambient-space reduction and the unit-ball forms of
the norm and closure conditions are also formalized (`CommonSpace.lean`, `SpecLemmas.lean`). The
definition correspondence is documented in `../lean/SPEC_AUDIT.md`.

**R1 limitation (must accompany any use).**

> Evaluating $G_{\rm box}$ is a finite-dimensional maximization over a box. Whether the maximum is
> always attained on the capped equal-angle curve $\theta_v=\min(\arcsin\eta_v,\tau)$ is left open;
> that curve is known to give a lower bound for $G_{\rm box}$.
