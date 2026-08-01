# Scholarly status

What each document establishes, and what it does not. Support categories follow ordinary
academic usage; they are not ranked on a single scale, and no score is formed from them.

`proved` · `proved under stated assumptions` · `exact algebraic identity` ·
`rigorous numerical enclosure` · `exploratory numerical observation` · `counterexample` ·
`negative result in the tested regime` · `inconclusive` · `open problem` ·
`not independently verified`

**Independent verification is pending for every statement in this package.** No item below
may be described as independently verified.

---

## The multidimensional summary

| Statement | Conclusion | Evidence type | Scope | Independent verification |
| --- | --- | --- | --- | --- |
| Orthogonal splitting of the root error | established | exact proof | all orthogonal projectors on Hilbert spaces | pending |
| Exact local error decomposition | established | exact proof; an identity, not a bound | every internal vertex of every valid tree | pending |
| Uniform coefficients `k` and `k−1` | established as upper bounds | proof by induction | finite trees, `k ≥ 1`, uniform `M` and `ρ` | pending |
| Optimality of `k−1` at fixed `η > 0` | unresolved | upper bound proved; lower constructions do not meet it | selected low-order trees | pending |
| Optimal telescoping order | established | proof, with the exchange relation shown to be a total preorder | the declared scalar family only | pending |
| State-resolved recursion, soundness | established | proof | given block-norm bounds, which are assumed | pending |
| State-resolved recursion, cost | count of recursion steps only | assertion from two counts | excludes obtaining the block norms | pending |
| Pathwise attribution | established for the scalar recurrence | exact unrolling of an affine recurrence | attributes the **bound**, not the error | pending |
| Signed-combination triangle bound | established | proof | finite compatible combinations | pending |
| Cancellation-aware constants | unresolved | numerical search gives lower bounds only | five named combinations | pending |
| Six-term generalised Jacobi expression | inconclusive | vanished at numerical precision in all 4 000 trials and 5 reseeded checks | may be identically zero; symbolic check required | pending |
| Boundedness of kernel-defined operators | established | proof | `κ ∈ L²(X^{a+1})`, σ-finite `ν` | pending |
| Composite kernels are square-integrable | established | proof (closes an earlier gap) | as above | pending |
| Associator determines the defect kernel | established under a hypothesis | proof | additionally requires `L²(X,ν)` separable | pending |
| Associator and commutator defect | established | exact identity | any bilinear operation; no algebra axioms | pending |
| Associator as a "curvature" | a definition, not a theorem | — | no connection is introduced and none is implied | not applicable |
| Cochain descent, Hodge compatibility | established | standard proofs, cited | finite complexes; degree-zero graded operators | pending |
| Spectral truncation | established for the truncation | proof | says nothing outside the truncated space | pending |
| Induced Markov operator | conditional construction | algebra correct given the hypothesis | **hypothesis has no verified instance** | pending |
| Continuum limit, pseudodifferential class, microlocal regularity | open | none | stated as questions, not results | not applicable |
| Projector identities (numerical study) | established | identity by construction | all isometries | pending |
| Commutator approximation | unsupported | numerical comparison against the zero predictor | 15 trained checkpoints, stated objectives | pending |
| Subspace transport | not observed | principal-angle study | 3 resolutions, 1 lift per pair | pending |
| Factor persistence | not observed | principal-angle study | the same 3 resolutions; one anomaly unexplained | pending |
| Identifiability of the fitted subspace | not identified | 3 seeds, pairwise angles ≈ 89° | that objective, that configuration | pending |
| Unconstrained Procrustes on frames | vacuous | counterexample, from the study's own control | orthonormal frames of equal size | pending |
| Basis invariance of the corrected objective | established | exact algebraic identity | after summing over all columns | pending |
| Thresholded spectral projection | established under a gap assumption | perturbation theorem plus a counterexample at gap closure | finite-dimensional Hermitian matrices | pending |
| Closure defect | measured | 2 000 sampled inputs plus adversarial maximisation | no sampling model stated | pending |
| Associator constant `2` | undetermined | observed ratios 0.042–0.957 over 416 executions | that map family, `n ≤ 96` | pending |
| Generalised Jacobi ratio | undetermined | adversarial maxima 4.65–5.98 | not shown bounded | pending |
| Compressibility against a random null | modest, in one mode | single configuration, single random draw | not a null distribution | pending |
| Device throughput | CPU faster throughout | 320 executions, 4 dimensions | one machine, four experiments | pending |
| Provenance of the historical evidence | established | hashing, log parsing, lineage reconstruction | 19 historical runs | pending |
| Originality of anything in this package | **not assessed** | — | — | not performed |

---

## What changed relative to the previous version of this material

The following statements were **weakened** during the audit that preceded this package,
because the evidence did not support the earlier wording. Each change moves in the
conservative direction.

| Was | Is now | Why |
| --- | --- | --- |
| "the maximum unresolved absolute and relative gaps are 32 and 1" | "in 1 794 of 9 945 configurations (18.0 %) no positive lower bound was obtained at all" | The relative gap is `(upper − lower)/upper`, so the value 1 means the lower bound is exactly zero. Printed beside "32" it read as a small residual. |
| "directed interval calculations certify 60 small cells globally" | 309 configurations have a determined positive constant; 30 have a constant that vanishes by the theorem | Of the 60, half were the single-vertex case, where the theorem itself gives zero. |
| Jacobi combination: verdict **sharp** | verdict **undetermined**; the search did not improve on the triangle bound | A ratio of 0.994 from a finite search is not sharpness. |
| "frozen projector, train law: **exactly 0**" | `2.46 × 10⁻⁷`, the numerical floor of that run | The recorded value is not zero. |
| "all transported angles sit at 1.41–1.53 rad" | the reported angles span 1.331–1.553; the transported ones 1.407–1.472 | The stated range excluded both the smallest and the largest recorded values. |
| "96 **independent configurations**"; "416 cells" | 48 and 208 **configurations**; 96 and 416 **executions** | Each configuration was executed once per device. |
| closure defect: `STATISTICALLY_VALIDATED_PASS` | "observed over 2 000 sampled configurations" | No sampling population, statistic, uncertainty calculation or inferential procedure is specified anywhere. |
| `NOT_CERTIFIABLE_AS_DEFINED` | "the quantity evaluated at numerical precision zero in all trials; symbolic verification is required before it can be used as a nontrivial diagnostic" | The status code asserted a property of the definition; the evidence supports only a suspicion. |
| a strong match to the underspecification literature for the commutator finding | a conceptual relation, attached instead to the identifiability finding, which is the one that matches | Underspecification is about many equally good solutions; the commutator finding is about two objectives in conflict. |

No statement was **strengthened**. No statement was found to be false.

---

## Corrections applied to the mathematics

| Item | Correction |
| --- | --- |
| The theorem statement at `k = 0` | The uniform estimate is now stated for `k ≥ 1`, with the leaf case treated separately, because `M^{k−1}` is undefined at `k = 0` when `M = 0`. |
| The ordering theorem | The proof now establishes that the exchange relation is a **total preorder**, induced by a lexicographic key. Without that step an adjacent-exchange argument gives only a local minimum. |
| The closure-residual map in the companion article | Restored to the definition with inner projectors, which is the operator whose norm the hypothesis bounds, together with the one-line reason that the two agree on the relevant arguments. |
| The pathwise formula | Now states explicitly that it is the exact expansion of a valid **scalar** recurrence, in which the cross-branch interaction terms are already absorbed into the gains, and therefore attributes the bound rather than the error. |
| Composite kernels | A lemma with proof establishes that they exist and are square-integrable, with `‖κ_L‖ ≤ ‖κ‖²`. The earlier text defined an energy as their norm without establishing that the norm was finite. |
| The associator converse | The vague hypothesis "under suitable density/integrability conditions" is replaced by **separability of `L²(X,ν)`**, stated as a hypothesis and not automatic, together with a proof. |
| Cochain descent | The degree-zero hypothesis is now stated; without it the compatibility conditions do not typecheck. |
| The Stiefel gradient | The metric is now named. The formula given is the one for the embedded Euclidean metric; the canonical metric gives a different gradient. |
| The Markov operator | Presented as a conditional construction, with the three missing hypotheses displayed and an explicit statement that no verified instance is known. |

---

## Administrative conclusion

Submission is deferred. The reasons are, in order:

1. no independent review of the proofs has been performed;
2. no assessment of originality has been performed for any statement;
3. no clean-environment reproduction has been performed;
4. the exact constant in the principal result of document 01 is undetermined, already for
   two internal vertices.

None of these is a mathematical status, and none is encoded as one anywhere in the five
documents.
