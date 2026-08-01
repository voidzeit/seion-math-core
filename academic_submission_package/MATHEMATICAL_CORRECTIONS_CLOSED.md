# Mathematical corrections closed

Every known mathematical defect in the delivered manuscripts, with the correction applied
and where the corrected statement now lives. The purpose of this file is that a reviewer
receives a manuscript with **no known defects**, and can see what was found and fixed
rather than having to rediscover it.

**Status of the list: closed.** No known mathematical defect remains open in documents 01
and 02. Open *questions* are a different matter and are listed in §4.

---

## 1. Corrections closed in document 01

| # | Observation | Correction | Where | Status |
| --- | --- | --- | --- | --- |
| C-1 | The uniform estimate involves `M^{k−1}`, which is undefined at `k = 0` when `M = 0`. The earlier proof said the leaf case was "trivial" but left the ill-formed expression in the statement. | Theorem stated for `k ≥ 1`; the induction carries two clauses, the second being `‖D_v‖ = 0` for `k_v = 0`. | Thm. 9.1; Remark 9.2; Appendix, proof of Thm. 9.1 | closed |
| C-2 | The ordering theorem was proved by adjacent exchange. Adjacent exchange gives a **global** minimum only if the comparison relation is a total preorder, which was not shown. | Two lemmas added: the exchange criterion, and the fact that the relation is induced by the lexicographic key `(sign class of d_i, w_i/d_i)` and is therefore a total preorder. The sorting argument then terminates and is global. | Thm. 8.1; Appendix, Lemmas A.4 and A.5 | closed |
| C-3 | The pathwise formula was stated as an **equality** for `B_ϱ`, but `B_ϱ` satisfies only an inequality, so it has no closed form. Unrolling an inequality does not produce an equation. | A majorant `B̂_v` is defined by the corresponding **equality**; then `B_v ≤ B̂_v` is proved by induction (using `h_{v,j} ≥ 0`), and the closed form is proved as an identity for `B̂_ϱ`. The two are stated separately. | Def. 10.1; Cor. 10.2; Appendix, proof of Cor. 10.2 | closed |
| C-4 | The pathwise formula could be read as an exact attribution of the **error** to vertices. | Stated explicitly that the interaction terms of the exact local decomposition were absorbed into the gains before the recurrence was formed, so each summand attributes a share of the **bound**. | Remark 10.3; Appendix, Remark A.7 | closed |
| C-5 | **The representation-error proposition applied the closure bound `ρ` to the approximate maps.** The proof inserted the unprojected approximate tree and applied the main theorem to it, which requires `‖(I−P_v) μ̂_v(P·,…,P·)‖_op ≤ ρ` — a hypothesis on `μ̂` that is nowhere declared. `δ` bounds `‖μ_v − μ̂_v‖_op` and says nothing about how `μ̂_v` interacts with the prescribed subspaces. | The insertion point is changed from `F_μ̂` to `R_μ`: `‖F_μ − R_μ̂‖ ≤ ‖F_μ − R_μ‖ + ‖R_μ − R_μ̂‖`. The first term is the main theorem applied to the **exact** tree; the second compares two recursively projected evaluations differing only in the maps, and is bounded by a new lemma. The result is **simpler and strictly stronger** than what it replaces: the interaction term `cρ[(M+δ)^{k−1} − M^{k−1}]L_T` disappears entirely. | Prop. 14.1; Remark 14.2; Appendix, Lemma A.8 and proof of Prop. 14.1 | closed |
| C-6 | The admissible class was not stated in one place: field, spaces, projector type, arities, finiteness, boundedness, type compatibility, and the exact meaning of `M`, `ρ`, `L_T` were scattered or implicit. | A standing-hypotheses block (H1)–(H7) with a table giving the exact meaning of the three constants, including that neither `M` nor `ρ` need be attained and that `ρ ≤ M` may always be arranged. | §3.1 | closed |
| C-7 | Degenerate cases were not treated. | A table covering `k = 0`, `k = 1`, `M = 0`, `ρ = 0`, `a_v = 1`, `L_T = 0`, each with the value all four errors take and the form the estimates reduce to. | §3.2 | closed |
| C-8 | The closure-residual map was defined without the inner projectors in one of the two manuscripts, so the hypothesis `‖r_v‖_op ≤ ρ` did not attach to the operator as written. | The definition with inner projectors is used throughout, together with the one-line reason `P_{τ(c_i)}R_i = R_i` that makes the two agree on the arguments at which they are applied. | Def. 3.2; Appendix, Remark A.2 | closed |

### Before and after, for C-5

The previous statement was
```
‖F_μ − R_μ̂‖ ≤ kδ(M+δ)^{k−1}L + cρM^{k−1}L + cρ[(M+δ)^{k−1} − M^{k−1}]L,
```
resting on an undeclared closure hypothesis for `μ̂`. The corrected statement is
```
‖F_μ  − R_μ̂‖ ≤ kρM^{k−1}L     + kδ(M+δ)^{k−1}L,
‖PF_μ − R_μ̂‖ ≤ (k−1)ρM^{k−1}L + kδ(M+δ)^{k−1}L,
```
resting only on `‖μ_v‖_op ≤ M`, `‖r_v‖_op ≤ ρ` for the exact maps, and
`‖μ_v − μ̂_v‖_op ≤ δ`.

The new bound is smaller than the old one by `cρ[(M+δ)^{k−1} − M^{k−1}]L ≥ 0`, so the
correction removes a hypothesis **and** tightens the conclusion.

---

## 2. Corrections closed in document 02

| # | Observation | Correction | Where | Status |
| --- | --- | --- | --- | --- |
| K-1 | The composite kernels `κ_L`, `κ_R` and their difference were used without establishing that they exist or are square-integrable, and an energy was defined as the squared norm of a quantity not shown to be finite. | Lemma proved: `‖κ_L‖_{L²(X⁶)} ≤ ‖κ‖²_{L²(X⁴)}`, hence `‖Φ_κ‖ ≤ 2‖κ‖²` and `𝔈_A(κ) ≤ 4‖κ‖⁴`. Finiteness then gives almost-everywhere absolute convergence of the defining integrals, which legitimises both the composition and the Fubini step. | Lemma 2.4; Remark 2.5; Def. 3.2 | closed |
| K-2 | The converse of the associator criterion was asserted "under suitable density/integrability conditions", with no proof and no statement of what those conditions are. As written it was not a mathematical statement. | Hypothesis named — **separability of `L²(X,ν)`**, which is not automatic — and a proof given by a countable-dense-family argument plus the density of finite sums of product functions. A remark records when separability holds. | Prop. 3.4; Remark 3.5 | closed |
| K-3 | The descent of a graded operator to cohomology omitted the hypothesis that the operator has **degree zero**, without which the compatibility conditions do not typecheck. | Hypothesis stated in the proposition. | Prop. 6.1 | closed |
| K-4 | The Riemannian gradient on the Stiefel manifold was given without naming the metric. The formula stated is that of the embedded Euclidean metric; the canonical metric gives a different gradient. | Metric named, with citations, and a note that the embedded one is what the accompanying computations use. | §5.3 | closed |
| K-5 | The induced Markov operator was presented as a construction, but its hypothesis — that a contraction of the kernel yields a symmetric nonnegative weight with finite positive degree — is satisfied by no exhibited kernel. | Relabelled a **conditional construction**, with the three hypotheses displayed and an explicit remark that no verified instance is known. | Construction 7.1; Remark 7.4 | closed |
| K-6 | Continuum limits, pseudodifferential class membership and microlocal regularity appeared alongside proved material. | Moved to a section titled *Open analytical questions*, phrased as questions, with a note that `D`-modules and the Riemann–Hilbert correspondence are not listed even as questions because no hypothesis relating them to this material exists. | §9 | closed |
| K-7 | Duplicated the main theorem of document 01 and its proof, with no statement of the relationship between the two articles. | Document 02 now cites document 01 for the finite theory and reproves nothing. The finite material retained is only what is needed to state its own hypotheses. | §1.1 | closed |

---

## 3. What was verified but needed no correction

Recorded so that a reviewer knows these were checked rather than skipped.

| Statement | Verification |
| --- | --- |
| Root orthogonality `(E^amb)² = (E^proj)² + (E^⊥)²`, `E^red = E^proj` | Re-derived. Both steps use `P* = P`; the oblique counterexample confirming necessity was checked numerically (`⟨PD,(I−P)D⟩ = −1`). |
| Exact local decomposition | Re-derived. The `2^a`-term multilinear expansion is exact; the identification of the empty-subset remainder with `r_v(R_1,…,R_a)` uses `P_{τ(c_i)}R_i = R_i` and nothing else. No inequality is used. |
| Uniform coefficients `k`, `k−1` | Re-derived term by term and exponent by exponent. The exponent identity `1 + (k_{c_j}−1) + Σ_{i≠j}k_{c_i} = k_v − 1` was checked; base cases `k=1` and `k=2` checked against the general formula. |
| Signed-combination triangle bound | Re-derived. `1 + 1 = 2` for the two-term ternary associator, against `2 + 2 = 4` ambient. |
| Associator / commutator-defect identity | Re-derived by direct expansion; the two sides agree term by term. Holds for any bilinear operation with no algebra axioms, which is now stated. |
| Boundedness of kernel-defined operators | Re-derived. Uses Tonelli rather than Fubini for the measurability step; the citation was corrected accordingly. |
| Soundness of the state-resolved recursion | Re-derived. The complexity claim was **weakened** to a count of recursion steps, excluding the cost of obtaining the block norms it assumes; that is a scope correction, not a defect. |

---

## 4. What remains open — and why it does not block publication of the upper bound

These are open *questions*, not defects. The distinction matters: a theorem does not cease
to be correct because it is not optimal.

| Question | Status | Blocks the upper bound? |
| --- | --- | --- |
| Is `C_T^proj(η) = k−1` at fixed `η > 0`? | open; three outcomes are possible and none is favoured by the evidence | **No.** `C_T^proj(η) ≤ k−1` is proved under the stated hypotheses. Document 01 states the optimality question as open in the abstract, the introduction, a dedicated remark, the limitations and the open problems. |
| The exact constant at `k = 2` | known on part of the parameter range only | no |
| The exact constant at `k = 3` | not attained anywhere tested | no |
| Is the six-term generalised Jacobi expression identically zero? | numerically consistent with zero in 4 000 trials; symbolic check not performed | no; the expression is not used as a diagnostic anywhere |
| Can dimension or projector rank improve on the planar constructions? | open | no |
| Which of the four bounds dominates which | open | no |
| Originality against the literature | **not assessed** | **This is the one that could reposition the contribution.** If the bound turns out to follow from a more general known theorem, the article would need to be restated as a specialisation, a new proof, or a new application. That is a question for the literature audit and an expert reviewer, not for the proof. |

---

## 5. Effect on the delivered artifacts

| Artifact | Change |
| --- | --- |
| `papers/01_recursive_projection_of_multilinear_trees.pdf` | 36 → 39 pages |
| `sources/.../main.tex` | §3.1 standing hypotheses, §3.2 degenerate cases, Def. 10.1 majorant, Cor. 10.2 restated, Prop. 14.1 restated, Remark 14.2 added |
| `sources/.../proofs/full_proofs.tex` | Lemma A.8 (sensitivity of the projected evaluation to the maps) added; proofs of Cor. 10.2 and Prop. 14.1 replaced |
| Acceptance criteria | unchanged: 0 errors, 0 undefined references, 0 undefined citations, 0 overfull boxes, 0 corrupted ligatures, 0 Type 3 fonts |
| Numerical results | **none changed.** Every correction is to a statement or a proof; no table, figure or reported value is affected. |

## 6. Provenance of this list

Items C-1 to C-4, C-6, C-8 and K-1 to K-7 were identified during the audit recorded in
`mathematical_audit.md`. Item C-5 and the sharpening of C-3 were identified by the author
after that audit, on reading the delivered manuscript. Item C-5 is the most serious of the
set: it was an undeclared hypothesis, not a presentational matter, and it survived the
first audit.

