# 01 — Statement–evidence table

One row per major statement across the five manuscripts. Every numerical value below was traced to
its source file and, where the source is a dataset, **recomputed** during this audit. Recomputed
values are marked ✓ (agrees) or ✗ (does not agree) with the manuscript.

Support categories used (instruction §7, no numeric ranking):
`proved` · `proved under stated assumptions` · `exact algebraic identity` ·
`rigorous numerical enclosure` · `statistical result under the stated sampling protocol` ·
`exploratory numerical observation` · `counterexample` · `negative result in the tested regime` ·
`inconclusive` · `open problem` · `not independently verified`

Independent verification is **pending for every row**. Nothing in this corpus has been checked by a
person other than the author.

---

## Manuscript 01 — recursive projection of multilinear composition trees

### S-1.1 Exact root geometry

| Field | Content |
| --- | --- |
| Statement | `(E_𝔗^{amb})² = (E_𝔗^{proj})² + (E_𝔗^⊥)²` and `E_𝔗^{red} = E_𝔗^{proj}` |
| Assumptions | Finite typed tree; `P_τ = Q_τQ_τ*` with `Q_τ` isometric, hence `P_τ` an **orthogonal** projector; `R_ϱ ∈ ran P` |
| Scope | All finite-dimensional (indeed all Hilbert) settings with orthogonal projectors |
| Support | Proof (`full_proofs.tex` Prop. root geometry); re-derived in this audit |
| Strength | **exact algebraic identity** |
| Source | `papers/tree_stability_v4/proofs/full_proofs.tex` §Magnitude induction and exact root geometry; `main.tex` Prop. `prop:root` |
| Permissible | "The ambient error decomposes orthogonally into its projected and orthogonal parts; the reduced-coordinate error equals the projected error exactly." |
| Prohibited | Any statement of this identity without the orthogonality hypothesis. |
| Verification | pending |

### S-1.2 Failure under oblique projection

| Field | Content |
| --- | --- |
| Statement | S-1.1 can fail if `P` is idempotent but not self-adjoint |
| Assumptions | none |
| Scope | explicit `2×2` example |
| Support | `P = [[1,1],[0,0]]`, `D = (0,1)ᵀ`: `PD = (1,0)ᵀ`, `(I−P)D = (−1,1)ᵀ`, `⟨PD,(I−P)D⟩ = −1`. **Recomputed ✓** |
| Strength | **counterexample** |
| Source | `main.tex` §Counterexamples and negative controls, item 1 |
| Permissible | "Orthogonality of the projectors is necessary, not decorative." |
| Verification | pending |

### S-1.3 Exact child-error subset expansion

| Field | Content |
| --- | --- |
| Statement | `D_v = r_v(R_1,…,R_a) + Σ_{∅≠S⊆[a]} μ_v(y_1^S,…,y_a^S)` |
| Assumptions | `μ_v` multilinear; `r_v = (I−P_v)μ_v(P_{c_1}·,…,P_{c_a}·)`; `R_i ∈ ran P_{c_i}` |
| Scope | every internal vertex of every valid typed tree |
| Support | Proof; re-derived. **No inequality is used.** |
| Strength | **exact algebraic identity** |
| Source | `main.tex` Thm. `thm:subset`; `full_proofs.tex` Thm. `thm:subset-full` |
| Permissible | "an exact decomposition"; "singleton subsets are first-order propagation, larger subsets are cross-branch interaction" |
| Prohibited | calling it a bound, a certificate, or a calculus |
| Verification | pending. See `03_proof_audit.md` A-1: manuscript 02 states the same theorem with a **different, non-equivalent** definition of `r_v`. |

### S-1.4 Universal coefficients `k` and `k−1`

| Field | Content |
| --- | --- |
| Statement | `E^{amb} ≤ kρM^{k−1}L_𝔗`, `E^⊥ ≤ kρM^{k−1}L_𝔗`, `E^{proj} = E^{red} ≤ (k−1)ρM^{k−1}L_𝔗` |
| Assumptions | `‖μ_v‖_op ≤ M` and `‖r_v‖_op ≤ ρ` at **every** internal vertex; orthogonal projectors; `k ≥ 1`; finite tree. Heterogeneous types, laws and arities are permitted. |
| Scope | finite-dimensional; the argument is in fact dimension-free given the operator-norm bounds |
| Support | Induction on the tree; verified term by term and exponent by exponent in this audit |
| Strength | **proved under stated assumptions** (upper bound) |
| Source | `main.tex` Thm. `thm:homogeneous`; `full_proofs.tex` Thm. `thm:homogeneous-full` |
| Permissible | "We prove the upper bounds …. The reduction from `k` to `k−1` follows from the removal of the root orthogonal residual by the final projection." |
| Prohibited | "the constant is `k−1`"; "sharp"; "optimal"; any suggestion that the projected coefficient is attained at fixed `η > 0` |
| Verification | pending. Correction A-2 (`M^{k−1}` undefined at `k=0`) applies. |

### S-1.5 Optimal telescoping order

| Field | Content |
| --- | --- |
| Statement | Sorting by (sign class of `d_i = f_i − r_i`: positive, zero, negative; then increasing `w_i/d_i` within each nonzero class) globally minimises `C(π) = Σ_t w_{π_t}∏_{s<t}r_{π_s}∏_{s>t}f_{π_s}` |
| Assumptions | `e_i, r_i, f_i, G_i ≥ 0`, `w_i = G_ie_i` |
| Scope | **the declared scalar telescoping family only** — not all bounding methods |
| Support | Adjacent-exchange argument; all four sign cases re-derived in this audit; exhaustive permutation tests through arity 7 reported |
| Strength | **proved** (within the declared family) |
| Source | `main.tex` Thm. `thm:order`; `full_proofs.tex` Thm. `thm:ordering-full` |
| Permissible | "globally optimal within the declared scalar telescoping family" |
| Prohibited | "the optimal evaluation order" without the qualifier |
| Verification | pending. Correction A-3 (transitivity of the exchange preorder must be stated) applies. |

### S-1.6 State-resolved recursion (soundness) and its complexity

| Field | Content |
| --- | --- |
| Statement | The three-state recursion over `{R, ∥, ⊥}` returns valid upper bounds; work `O(\|𝔗\|3^{a_max} + \|𝔗\|a_max log a_max)` |
| Assumptions | **certified bounds for every block operator norm of every node law** — a strong, non-automatic hypothesis |
| Scope | declared arities 2–4 |
| Support | Soundness: complete argument. Complexity: asserted from two counts, **omitting the cost of evaluating each block norm** |
| Strength | soundness **proved under stated assumptions**; complexity **inconclusive as stated** |
| Source | `main.tex` Thm. `thm:dp`; `full_proofs.tex` Thm. `thm:dp-full` |
| Permissible | "the recursion is sound"; "linear in the number of vertices for fixed arity, **per recursion step**" |
| Prohibited | quoting the complexity as an end-to-end cost |
| Verification | pending |

### S-1.7 Pathwise residual bound

| Field | Content |
| --- | --- |
| Statement | `B^{amb}_{𝔗,path} = Σ_{v∈Int𝔗} λ_v ∏_{(a,j)∈path(v,ϱ)} h_{a,j}` is valid; for projected error the root source is omitted and the last gain is a projected-output gain |
| Assumptions | a **valid scalar recurrence** `B_v ≤ λ_v + Σ_j h_{v,j}B_{c_j}` |
| Scope | the scalar recurrence, not the multilinear expansion |
| Support | Exact unrolling of an affine recurrence |
| Strength | **proved under stated assumptions** |
| Source | `main.tex` §Nodewise path-sum bounds; `full_proofs.tex` Cor. `cor:path-full` |
| Permissible | "the exact expansion of a valid scalar upper-bound recurrence; cross-branch interaction terms are already subsumed in the transport gains" |
| Prohibited | "attributes error to each node and path individually" (manuscript 02's phrasing) — it attributes *a bound*, not the error |
| Verification | pending. Correction A-4 applies. |

### S-1.8 Signed-forest triangle bound

| Field | Content |
| --- | --- |
| Statement | `E^{proj}_ℱ ≤ Σ_α \|c_α\| B^{proj}_{𝔗_α}`; in particular the two-term two-vertex ternary associator has coefficient at most 2 |
| Assumptions | finite compatible signed combination |
| Scope | all such combinations |
| Support | Triangle inequality + S-1.4 |
| Strength | **proved under stated assumptions** |
| Source | `main.tex` §Signed polynomial expressions; `full_proofs.tex` Cor. signed-forest |
| Permissible | "at most 2"; "syntactically identical trees may first be combined exactly — this is the only unconditional cancellation statement" |
| Prohibited | claiming that adversarial search establishes a smaller *certified* constant |
| Verification | pending |

### S-1.9 Approximation plus projection

| Field | Content |
| --- | --- |
| Statement | `E_repr ≤ kδ(M+δ)^{k−1}L`; the closure term splits as `cρM^{k−1}L + cρ[(M+δ)^{k−1} − M^{k−1}]L`, `c ∈ {k, k−1}` |
| Assumptions | `‖μ_v‖ ≤ M`, `‖μ_v − \hatμ_v‖ ≤ δ`, `‖\hatμ_v‖ ≤ M+δ`; homogeneous `k`-vertex tree |
| Scope | finite-dimensional |
| Support | Telescoping over the `k` law replacements; the split is an algebraic partition of one valid bound |
| Strength | **proved under stated assumptions** |
| Source | `main.tex` §Approximation plus projection; `full_proofs.tex` Prop. `prop:cp-full` |
| Permissible | "the components sum to a proved upper bound, not to the observed error" (already the table caption — keep) |
| Prohibited | reading the three components as a decomposition of the actual error |
| Verification | pending |

### S-1.10 Adversarial lower bounds for five named signed forests

| Field | Content |
| --- | --- |
| Statement | Best lower bounds found: five-input ternary associator 1.373 (ratio 0.686 to the bound 2.0); anchored associator 1.658 (0.829); Jacobiator 2.983 (0.994 to bound 3.0); Filippov fundamental identity 1.664 (0.416 to bound 4.0); declared 6-term GJI variant `~0` |
| Assumptions | 4000 random-tensor trials + 200 derivative-free refinement steps per forest; operator norm numerically normalised to ≈1; **independently random leaf inputs** (a deliberate correction to the pipeline's earlier identical-unit-input convention, which can trivially collapse permutation-antisymmetric terms) |
| Scope | these five forests, this parameterisation, these trial counts |
| Support | numerical optimisation |
| Strength | **exploratory numerical observation** — optimisers improve lower bounds; they never certify that no better point exists (the manuscript says exactly this) |
| Source | `main.tex` §Adversarial cancellation-aware search; `artifacts/research_v3/signed_forest_adversarial_search_v5.json`; `scripts/signed_forest_adversarial_search_v5.py` |
| Permissible | "the plain triangle bound was not improved upon for the Jacobiator in the tested search — a negative result for cancellation-aware reasoning in that case"; "the associator and Filippov bounds remain open, with substantially tighter lower bounds than previously recorded" |
| Prohibited | the word **sharp** for the Jacobiator. The manuscript currently prints "\textsc{sharp}" in the verdict column. A ratio of 0.994 from a finite search is not sharpness. |
| Verification | pending |

### S-1.11 The 6-term GJI variant evaluates to zero

| Field | Content |
| --- | --- |
| Statement | Ambient, projected and orthogonal error all in `10⁻¹⁶`–`10⁻²¹` across all 4000 trials plus five reseeded spot checks, under both leaf-input conventions |
| Scope | this declared convention for the six-term generalised Jacobi identity |
| Support | numerical evaluation only |
| Strength | **inconclusive** — consistent with an identically vanishing expression, but no symbolic verification has been performed |
| Source | `main.tex` §Adversarial cancellation-aware search; `docs/research/signed_forest_terminal_status_v5.md` |
| Permissible | Instruction §13 wording verbatim: "The quantity evaluated at numerical precision zero in all trials. This suggests that the current formula may define an identically vanishing expression. A symbolic verification is required before the quantity can be used as a nontrivial diagnostic." |
| Prohibited | `NOT_CERTIFIABLE_AS_DEFINED` as a verdict; also any sharpness verdict |
| Verification | pending; symbolic check is an explicit open item |

### S-1.12 Registered optimality gaps — **misstated in the abstract**

| Field | Content |
| --- | --- |
| Statement as printed | "across the full gap registry the maximum unresolved absolute and relative gaps are 32 and 1" |
| What the data says | `artifacts/index/optimality_gaps_v3.csv`, 9945 rows. **Recomputed:** max `absolute_gap` = 32.0 ✓, max `relative_gap` = 1.0 ✓. But `relative_gap := (upper − lower)/upper` (`src/seion_core/research_v3/interval_certification.py:130-141`), so `relative_gap = 1` ⟺ `certified_lower_bound = 0`. **1794 of 9945 rows (18.0 %) have a certified lower bound of exactly 0** (ambient 395, orthogonal 267, projected 1162). The worst absolute-gap row is `lower = 0`, `upper = 32`. |
| Scope | the registered gated-rotation constructions |
| Support | rigorous numerical enclosure of the *lower constructions*; the *upper* is the theorem |
| Strength | **open problem** for those 1794 rows — a lower bound of 0 for a nonnegative quantity is vacuous |
| Permissible | "In 1794 of 9945 registered configurations no positive lower bound was obtained, so the admissible range spans the whole interval from 0 to the proved upper bound." |
| Prohibited | printing `1` as if it were a small residual gap; the phrase "certified lower bound" for the value 0 |
| Verification | recomputed in this audit; independent verification pending |

### S-1.13 "60 small cells certified globally" — **half are the trivial case**

| Field | Content |
| --- | --- |
| Statement as printed | "Directed interval calculations certify 60 small cells globally" |
| What the data says | `artifacts/research_v3/block_A_exact_atlas.csv`, 4185 rows. **Recomputed:** `global_optimum_certified` is true in exactly 60 rows ✓. Breakdown: 12 ambient with constant 1, 12 orthogonal with constant 1, 36 projected of which **30 have `lower = upper = 0`** and 6 have constant 1. |
| Interpretation | The 30 projected zero-cells are the `k = 1` case, where the manuscript's own theorem gives `E^{proj} = 0` identically. They are not an optimisation result. |
| Strength | 30 cells: **exact algebraic identity** (already implied by S-1.4). 30 cells: **rigorous numerical enclosure** matching the upper bound. |
| Permissible | "Thirty configurations attain the upper bound exactly under directed interval enclosure; a further thirty are the single-vertex case, where the projected constant is zero by Theorem …." |
| Prohibited | "60 small cells certified globally" without that split |
| Verification | recomputed in this audit |

### S-1.14 Status-label defect propagating into the tables

| Field | Content |
| --- | --- |
| Statement | `_exact_status` (`scripts/tree_constants_v3_pipeline.py:438-444`) returns `EXACT_OPTIMAL_CONSTANT` **only** when `upper == lower == 0` |
| Measured consequence | 30 rows with `lower = upper = 0` → `EXACT_OPTIMAL_CONSTANT`; **45 rows with `lower = upper = 1 > 0`, i.e. genuinely exactly determined, → `NEAR_OPTIMAL_WITH_CERTIFIED_GAP`**; 1794 vacuous rows → `CERTIFIED_UPPER_BOUND_AND_CERTIFIED_LOWER_BOUND` |
| Strength | implementation defect, **not** a mathematical error |
| Source | recomputed in this audit from `artifacts/index/optimality_gaps_v3.csv` |
| Consequence | manuscript 01's Table `optimality_gaps` and the macros `\VThreeExactCells`, `\VThreeMaxRelativeGap` inherit it |
| Action | must be corrected in code and the tables regenerated, or explicitly relabelled in the manuscript. **Author decision required** — reported numbers change. |
| Verification | recomputed in this audit |

### S-1.15 CPU/GPU parity, finite base study size

| Field | Content |
| --- | --- |
| Statement | 15 493 distinct configurations; 81 445 enumerated tree occurrences; 1530 exhaustive leakage masks; maximum CPU/GPU difference `1.922×10⁻⁸` |
| Source | `generated_results.tex`, generated by `scripts/build_tree_constants_v3_tables.py` from `artifacts/index/` |
| Strength | **exploratory numerical observation**; the parity figure is a validation threshold, not a theorem error (the manuscript's table caption already says so — keep) |
| Permissible | "the maximum absolute difference between CPU and GPU evaluation was `1.9×10⁻⁸` on the tested configurations" |
| Prohibited | any hardware-performance generalisation |
| Verification | pending |

### S-1.16 Provenance mismatch

| Field | Content |
| --- | --- |
| Statement | `\VThreeSourceCommit` = `b718f4e51785` |
| What is true | `b718f4e` is "feat(research): add nodewise tree constants v3 system", an **ancestor of `main`**. The manuscript is at `2e419ef`. All generated tables and figures in manuscript 01 therefore trace to `b718f4e`, not to the manuscript's own commit. |
| Strength | provenance defect |
| Note | The manuscript's own table caption concedes this ("the displayed source commit is the development checkpoint and is replaced by the immutable v3 source commit for the canonical final rerun"). The replacement has not happened. |
| Action | either rerun the pipeline at the delivery commit, or state plainly in `provenance.md` that the numerical evidence is from `b718f4e` and the manuscript text from `2e419ef` |
| Verification | verified in this audit |

---

## Manuscript 02 — kernel-defined multilinear operators

Rows S-2.1 … S-2.5 restate manuscript 01 (S-1.1, S-1.3, S-1.4, S-1.5, S-1.7, S-1.8, S-1.9) and carry
the same assumptions, scope, support and permissible wording, **plus** correction A-1. They are not
repeated here. See `00_source_audit.md` R-1.

### S-2.6 Associator / left-operator identity

| Field | Content |
| --- | --- |
| Statement | `R_std(x,y)z = A(y,x,z) − A(x,y,z)`, where `R_std(x,y) = [𝖫_x,𝖫_y] − 𝖫_{[x,y]}`, `A(x,y,z) = (x∘y)∘z − x∘(y∘z)`, `[x,y] = x∘y − y∘x` |
| Assumptions | `∘` bilinear. **No algebra axioms are needed** — this must be stated. |
| Scope | any bilinear operation on a vector space |
| Support | Direct expansion; re-derived in this audit ✓ |
| Strength | **exact algebraic identity** |
| Source | `kernel_integrated_laws_v5/main.tex` Thm. `thm:curvature` |
| Permissible | "We define an associator-based algebraic tensor `R_alg := A`. This is a definition; it is not, without additional structure, the curvature tensor of a connection." (The manuscript already says the equivalent — keep it.) |
| Prohibited | "curvature equals associator". **The manuscript does not say this anywhere** — checked. |
| Verification | pending |

### S-2.7 Boundedness of kernel-defined multilinear operators

| Field | Content |
| --- | --- |
| Statement | `κ ∈ L²(X^{a+1}) ⟹ ‖𝒦_κ(f_1,…,f_a)‖_2 ≤ ‖κ‖_2 ∏_j‖f_j‖_2` |
| Assumptions | `(X,ν)` σ-finite; Tonelli (the manuscript cites Fubini — should be Tonelli) |
| Scope | `L²` kernels |
| Support | Cauchy–Schwarz on `X^a` then integration in the output variable; verified |
| Strength | **proved under stated assumptions** |
| Source | `main.tex` §Kernel-integrated realization |
| Verification | pending |

### S-2.8 Composite and defect kernels — **gap, with repair available**

| Field | Content |
| --- | --- |
| Statement as written | `κ_L`, `κ_R` are defined; `Φ_κ = κ_L − κ_R`; `A_κ(f_1,…,f_5)(p) = ∫Φ_κ ∏f_j`; `ρ_A(κ) := ‖Φ_κ‖²_{L²(X⁶)}` |
| What is missing | No proof that `κ_L, κ_R` are a.e. defined or lie in `L²(X⁶)`, and no justification of the interchange of integration |
| Repair (supplied in `03_proof_audit.md` §3.4) | Cauchy–Schwarz in the composition variable gives `‖κ_L‖_{L²(X⁶)} ≤ ‖κ‖²_{L²(X⁴)}`, hence `‖Φ_κ‖ ≤ 2‖κ‖²` and `ρ_A(κ) ≤ 4‖κ‖⁴`. Finiteness then legitimises both the composition and the Fubini step. |
| Strength once repaired | **proved under stated assumptions** |
| Action | insert the lemma. No claim changes. **No authorization required.** |
| Verification | derived in this audit; independent verification pending |

### S-2.9 Converse of the associator-vanishing criterion — **incomplete as stated**

| Field | Content |
| --- | --- |
| Statement as written | "under suitable density/integrability conditions, if the associator vanishes on all products of test functions then `Φ_κ = 0` a.e. (converse also holds)" |
| Problem | "suitable conditions" are unspecified; no proof; the trailing parenthesis is either redundant or a third claim |
| Repair (supplied in `03_proof_audit.md` §3.5) | Add **separability of `L²(X,ν)`** as an explicit hypothesis (not automatic; holds for σ-finite `ν` on a countably generated σ-algebra), then a four-line countable-dense-family argument gives the converse. |
| Strength as written | **inconclusive**. Once repaired: **proved under stated assumptions**. |
| Action | rewrite with the hypothesis and proof. **No authorization required.** |
| Verification | derived in this audit |

### S-2.10 Cochain descent and Hodge compatibility

| Field | Content |
| --- | --- |
| Statement | `Td = dT ⟹ T` descends to `H^p`; `[T,d] = [T,d*] = 0 ⟹ [T,Δ] = 0`, so `T` preserves `ℋ^p` |
| Assumptions | finite cochain complex with inner products; `T` graded of degree 0 (**not stated — must be added**) |
| Scope | finite complexes only |
| Support | standard argument, correctly given |
| Strength | **proved under stated assumptions** — but standard, and requires a citation |
| Prohibited | letting these read as results about the de Rham complex of a manifold |
| Verification | pending |

### S-2.11 Finite spectral truncation

| Field | Content |
| --- | --- |
| Statement | If `𝔈_d^Λ(κ) = 0` then the operators commute with `d, d*` **within the truncation** and descend to truncated cohomology |
| Assumptions | compact manifold; `Π_{≤Λ}` the spectral projector of the Hodge Laplacian |
| Scope | **truncated**; not a continuum statement |
| Support | formal construction |
| Strength | **conditional construction, finite/truncated regime** |
| Permissible | "within the spectral truncation" — always |
| Prohibited | any continuum conclusion. The manuscript's remark that a local minimum does not imply `𝔈_d^Λ = 0` is correct and must be kept. |
| Verification | pending |

### S-2.12 Induced Markov operator and Laplacian — **hypothesis has no verified instance**

| Field | Content |
| --- | --- |
| Statement | `𝒫` self-adjoint on `L²(X,ν)`; `⟨f,Δ_𝒫 f⟩ = ½∬\|f(p)−f(s)\|²𝒲(p,s)`, hence `Δ_𝒫 ≥ 0` |
| Assumptions | "a declared kernel contraction yields a symmetric nonnegative `𝒲`". **No such contraction is exhibited, and no condition on `κ` is given under which one exists.** Also needs `0 < 𝖽(p) < ∞` a.e. |
| Scope | conditional |
| Support | The algebra is correct given `𝒲`; verified |
| Strength | **conditional construction whose hypothesis has no verified instance** |
| Action | relabel as "Proposed construction" with the three hypotheses displayed |
| Verification | pending |

### S-2.13 Spectral dimension

| Field | Content |
| --- | --- |
| Statement | If `e^{−tΔ_𝒫}` is trace class and `Θ(t) ∼ Ct^{−d_s/2}` as `t ↓ 0`, then `d_s = −2 lim_{t↓0} d log Θ/d log t` |
| Strength | **definition under stated hypotheses** |
| Note | The manuscript's own remark — "Existence of this limit is an additional hypothesis, not an automatic consequence of the ternary kernel" — is correct and sufficient. **Keep verbatim.** |
| Verification | pending |

### S-2.14 Multiscale transport

| Field | Content |
| --- | --- |
| Statement | Definitions of `𝒟_μ^{N,M}`, `𝒟_P^{N,M}` only; no theorem |
| Note | The accompanying remark — that a finite decreasing sequence of such values does not establish a continuum limit, which would additionally require topologies, uniform bounds, compactness, convergence of laws and projectors, stability of identities, and identification of the limit — is correct and is the standard the whole corpus should meet. **Keep verbatim.** |
| Strength | **open problem** |
| Verification | pending |

### S-2.15 The "open geometric program"

| Field | Content |
| --- | --- |
| Items | continuum limits; `Ψ⁰` membership; microlocal regularity; `D`-modules and the Riemann–Hilbert correspondence; algebraisation of the limiting projector |
| Strength | **open problem** — none is a result, none is a consequence |
| Action | present in a section titled *Open analytical questions*, with no forward-looking claim, per instruction §9.6 |
| Verification | not applicable |

---

## Manuscript 03 — numerical study

All numerical values in this section were **recomputed from the committed artifacts at `8e09941`**
during this audit.

### S-3.1 Orthogonal projector identities (block A)

| Field | Content |
| --- | --- |
| Statement | `P = UU*` is idempotent and self-adjoint to machine precision for any orthonormal `U` |
| Scope | 5 seeds plus an exact `n = 2` case at tolerance `10⁻¹⁴`; extended to 416 sweep executions |
| Support | **identity verified by construction** — this is a theorem about `UU*`, not a measurement |
| Strength | **exact algebraic identity** |
| Permissible | "This holds by construction and is never evidence about the relevance of the learned subspace." (The manuscript already says this — keep.) |
| Verification | recomputed: `block_a_idem_rel` ≤ `3.3×10⁻¹⁶` across the sweep ✓ |

### S-3.2 Commutator approximation fails in trained models (block B)

| Field | Content |
| --- | --- |
| Statement | The parameterised model `C_θ` performs at or worse than predicting zero in **all 15** historical checkpoints with block-B data (`coherence_ratio ≤ 0`) |
| Assumptions | those 15 checkpoints, that objective, that parameterisation |
| Scope | **the tested regime only** |
| Support | numerical comparison against the zero predictor |
| Strength | **negative result in the tested regime** |
| Permissible | "The proposed approximation did not outperform the zero approximation in any of the fifteen available trained models. This is restricted to the parameterisation, objectives, and trained models examined here; it is not an impossibility theorem for the model class." |
| Prohibited | `REFUTED_IN_DEPLOYED_REGIME` |
| Verification | pending |

### S-3.3 Block B ablation matrix — **one figure overstated**

| Field | Content |
| --- | --- |
| Statement as printed | Table row "Frozen projector, train law | **0.000000**", and in prose "reaches unexplained-rel **exactly 0** even with `U` left at its random initial value"; atlas Fig. 2 caption "reaches exactly zero (displayed at the floor for the log axis)" |
| What the data says | `spectral/certification_v18/artifacts/block_b_ablation_matrix.json`: `final_comm_unexplained_rel = 2.463683527245667×10⁻⁷`. **Recomputed ✗ — it is not zero.** |
| Other rows | isolated `8.096×10⁻⁵` ✓ (printed 0.000081); +closure `3.514×10⁻⁴` ✓; +associator `8.486×10⁻³` ✓; joint `5.995×10⁻³` ✓; frozen-law `0.99249` ✓; staged `4.654×10⁻⁴` ✓. All correct except the one above. |
| Action | print `2.5×10⁻⁷` and say "at the numerical floor of this training run", not "exactly 0" |
| Strength | **exploratory numerical observation** (7 regimes, `n=16`, rank 4, cp-rank 4, 400 steps, one configuration each) |
| Verification | recomputed in this audit |

### S-3.4 Mechanism diagnosis for block B

| Field | Content |
| --- | --- |
| Statement | The failure is a structural conflict with the associator/GJI objective, mediated through the law's parameters — not capacity, gradient starvation, or projector-search difficulty |
| Support | the 7-regime ablation above, **one run per regime** |
| Strength | **exploratory numerical observation**, described by the manuscript as "the best-supported diagnosis" — correct hedging, keep it |
| Prohibited | presenting a single run per regime as a controlled experiment with replicates |
| Verification | pending |

### S-3.5 No subspace transport across resolutions (blocks E, J, M)

| Field | Content |
| --- | --- |
| Statement as printed | "All transported angles sit at 1.41–1.53 rad, essentially the maximum possible (π/2 = 1.571); the trained lift beats both baselines in only 2 of 3 pairs, by margins (0.02–0.15 rad)" |
| What the data says | `block_e_interscale_experiment.json`. **"2 of 3" ✓ recomputed** (`beats_random`/`beats_interpolation` are true/false/true). **The range "1.41–1.53" ✗:** trained forward angles are `1.4101, 1.4721, 1.4067` (range 1.407–1.472); random baselines `1.4797, 1.4165, 1.5532`; interpolation baselines `1.5267, 1.4681, 1.4462`; backward angles `1.3313, 1.5404, 1.3701`. Over all reported angles the range is **1.331–1.553**, not 1.41–1.53. |
| Action | state which set of angles the range refers to, and quote it correctly |
| Scope | three resolutions (`n = 12, 18, 24`), one frozen Gaussian-kernel lift per pair, independently initialised and trained |
| Strength | **negative result in the tested regime** |
| Permissible | "The tested multiresolution models provided no evidence of persistent subspace structure across the examined resolutions." |
| Prohibited | `NO_PERSISTENCE_SIGNAL_IN_DECLARED_REGIME` |
| Verification | recomputed in this audit |

### S-3.6 Unexplained per-mode anomaly (block M)

| Field | Content |
| --- | --- |
| Statement | One mode of nine compared shows a near-exact match (`1.5×10⁻⁸` rad), unexplained |
| Strength | **inconclusive** — correctly retained by the manuscript as an open anomaly rather than smoothed into a verdict. **Keep this practice.** |
| Verification | pending |

### S-3.7 Approximate closure (block G) — **"statistically validated" is not supported**

| Field | Content |
| --- | --- |
| Statement as printed | 2000-sample empirical distribution plus adversarial gradient ascent; status `STATISTICALLY_VALIDATED_PASS` |
| Problem | Instruction §16 requires, for that term: the sampling population or stochastic model, the statistic, the number of independent observations, the uncertainty calculation, the inferential procedure, and the limits of generalisation. **None of the six appears anywhere in manuscript 03.** |
| Action | replace with "observed over 2000 sampled configurations", or supply the six items |
| Strength | **exploratory numerical observation** until the sampling model is stated |
| Note | The manuscript is already explicit that "no interval/SOS certified bound was derived this pass" — that honesty must be preserved. |
| Verification | pending |

### S-3.8 Associator constant is not sharp for the tested family (block H)

| Field | Content |
| --- | --- |
| Statement | The bound `‖A(x,y,z)‖ ≤ 2\hat M²‖x‖‖y‖‖z‖` is never violated in 500 trials (300 random + 200 adversarial); maximum observed ratio 0.452; mean `cos(T_1,T_2) = 0.067` |
| Sweep extension | pilot 96 executions: range 0.130–0.957, mean 0.334. **Recomputed ✓ exactly.** S1 320 executions: range 0.042–0.957, mean 0.240; mean by `n`: 0.404, 0.257, 0.182, 0.118. **Recomputed ✓** (atlas Fig. 8 caption says "0.40 at n=12 to 0.11 at n=96"; the value at `n=96` is 0.118, which rounds to 0.12) |
| Scope | this law family, these dimensions |
| Strength | **exploratory numerical observation** |
| Permissible | "the observed ratio remained well below the analytical upper bound throughout, and decreased monotonically with ambient dimension" |
| Prohibited | inferring anything about manuscript 01's `k−1` question — **see `03_proof_audit.md` §7. These are different quantities.** |
| Verification | recomputed in this audit |

### S-3.9 Cyclic symmetrisation is a construction identity (block N)

| Field | Content |
| --- | --- |
| Statement | Raw cyclic defect 4.60 vs symmetrised `8.2×10⁻³³` — a 31-order gap |
| Strength | **exact algebraic identity** — `Sym_cyc μ` is cyclic by construction because `Π_cyc` is an orthogonal projector onto the cyclic-invariant subspace |
| Permissible caption | "Cyclic residual before and after exact symmetrisation. The post-symmetrisation value follows by construction." (The manuscript already says "a construction identity, never learned evidence" — keep.) |
| Verification | pending |

### S-3.10 GJI ratio is not shown to be bounded (block N)

| Field | Content |
| --- | --- |
| Statement | Adversarial maximum 5.98 against a mean of 0.43; supremum not shown bounded |
| Sweep | pilot reproduces 4.65–5.92 across 96 executions. **Recomputed ✓ exactly.** |
| Strength | **open problem** |
| Verification | recomputed in this audit |

### S-3.11 Methodological error found and corrected (blocks J, M)

| Field | Content |
| --- | --- |
| Statement | Comparing subspace bases by free-unitary Procrustes is vacuous, because the unitary group acts transitively on same-size orthonormal frames; an early version consequently reported independent random tensors as gauge-equivalent |
| Support | caught by the block's own required negative control; fixed with principal angles |
| Strength | **counterexample** / methodological correction |
| Note | This is the strongest item in manuscript 03 and should be prominent, not buried. The mathematical statement (transitivity of `U(n)` on orthonormal `k`-frames) is standard and true. |
| Verification | pending |

### S-3.12 Gauge-invariance defect in the block F loss

| Field | Content |
| --- | --- |
| Statement | The first version of the test loss was not gauge-invariant (single-column construction, 0.87 % discrepancy, caught by the test itself); corrected by summing over all `r` columns, giving a Frobenius quantity exactly invariant under right multiplication by a unitary |
| Strength | **counterexample** / methodological correction; the invariance of the corrected form is an **exact algebraic identity** |
| Verification | pending |

### S-3.13 Non-identifiability across seeds (block F)

| Field | Content |
| --- | --- |
| Statement | Three seeds all reach near-zero loss, but the pairwise maximum principal angle between converged subspaces is 1.55 rad (≈ 89°) |
| Strength | **negative result in the tested regime** — a genuine non-identifiability finding |
| Scope | 3 seeds, one configuration |
| Prohibited | three seeds are not a statistical sample |
| Verification | pending |

### S-3.14 Legacy scoring reclassification

| Field | Content |
| --- | --- |
| Statement | All 19 unique historical runs are capped at exploratory status; all have `eval_mode="screening"`, including directories named `*_CERT_*`; the 9 logged runs share `seed=3` and form **one continuous non-strict-resume chain**, not nine independent trials; two distinct `script_sha256` values appear across the lineage |
| Strength | **verified provenance finding** |
| Note | This is exactly the distinction instruction §16 demands between independent configurations and resumed executions. It is correct, important, and should be prominent. |
| Verification | pending |

### S-3.15 GPU does not overtake CPU — **but the cell count double-counts**

| Field | Content |
| --- | --- |
| Statement as printed | "96 cells" (pilot), "320 cells" (S1), "416 total sweep cells", and — critically — "Block H's associator ratio, evaluated across **96 independent configurations**" |
| What the data says | **Recomputed:** `pilot_results.parquet` has 96 rows but **48 unique `scientific_instance_id`**, each with two `execution_id`s (one `cpu`, one `cuda`). `s1_results.parquet` has 320 rows but **160 unique `scientific_instance_id`**, likewise. So "416 cells" = **208 distinct mathematical configurations, each executed twice**. |
| Consequence | "96 independent configurations" is wrong by a factor of two. Instruction §16: *"Do not count resumed executions as independent experiments"* — the same principle applies to the same configuration on two devices. |
| Action | report "208 distinct configurations, 416 executions (each configuration on CPU and on CUDA)" |
| Timing result | CUDA/CPU mean wall time by `n`: 12 → 3.24×, 24 → 3.31×, 48 → 3.51×, 96 → 3.17×. **Recomputed ✓** (manuscript prints 3.25/3.31/3.51/3.18 — rounding only). Per-`n` means 9.44/30.64, 9.31/30.80, 9.83/34.50, 7.90/25.09 **✓ exact**. |
| Wall-time totals | Manuscript: pilot 945.5 s, S1 6316.5 s. Sum of per-cell `wall_time_seconds`: **942.8 s** and **6300.8 s**. Small excess, presumably scheduler overhead — should be stated. |
| Failures | 0 in both. **Recomputed ✓** |
| Strength | **negative result in the tested regime** — GPU never overtakes CPU for these four blocks anywhere in `n ∈ {12,24,48,96}` |
| Prohibited | any asymptotic-complexity or general hardware conclusion from this benchmark |
| Verification | recomputed in this audit |

### S-3.16 Coverage limits

| Field | Content |
| --- | --- |
| Statement | Only blocks A, G, H, N were extended with a device parameter and swept. Blocks B, C, D, E, F, I, J, K, L, M remain single-configuration and CPU-only. Stages S2 and S3 were not executed. |
| Strength | **stated scope limitation** — correct and must be kept |
| Verification | verified against the block modules at `8e09941` |

### S-3.17 Global outcome

| Field | Content |
| --- | --- |
| Statement | No block reaches a status stronger than exploratory or "statistically validated" for any scientific claim; blocks B, E, J, M sit in an explicit failed state |
| Strength | **administrative conclusion** — per instruction §12 it must not be encoded as a mathematical status |
| Permissible | "Submission is deferred because the originality review and several sharpness questions remain unresolved, and because four of the fourteen experimental questions produced negative results for their scientific claims." |
| Prohibited | `FAIL_CLOSED_DYNAMIC_EXPLANATION_GATE_NOT_ESTABLISHED`; `PASS_A_TO_N_PARTIAL_CERTIFICATION` |
| Verification | not applicable |

---

## Manuscript 04 — software and reproducibility

Per instruction §21.4 this paper must make **no independent mathematical claim**. It currently does
not. Its factual claims:

| ID | Statement | Strength | Verification |
| --- | --- | --- | --- |
| S-4.1 | 85 tests pass | **verified in this audit**: `python -m pytest spectral/certification_v18/tests -q` in a clean detached worktree of `8e09941` → **85 passed in 51.09 s** ✓ | recomputed |
| S-4.2 | CPU/CUDA agreement at float64: idempotence `1.312×10⁻¹⁵` vs `1.198×10⁻¹⁵`; self-adjointness `0.0` vs `2.220×10⁻¹⁶`; unexplained-rel agreeing to `4.4×10⁻¹⁶` relative | exploratory, **single case** (`n=24`, seed 0). The manuscript already says only the third quantity is large enough for a meaningful relative comparison — correct. | pending |
| S-4.3 | Wall time 19.1 ms CPU vs 835.1 ms CUDA (~44× ) at `n=24` | **single-case timing.** Instruction §23: "Do not generalize a single timing comparison into a hardware-performance conclusion." The manuscript correctly defers to the swept measurement (S-3.15) instead. Keep that structure. | pending |
| S-4.4 | Process-global TF32 contamination hazard: the legacy script sets `torch.backends.cuda.matmul.allow_tf32 = True` and `torch.set_float32_matmul_precision("high")` unconditionally at import when CUDA is available | verified by reading the legacy script; a genuine and well-documented hazard | pending |
| S-4.5 | `.to(device)` does not update the plain Python `device`/`dtype` attributes on `CyclicCPProduct` | implementation finding, documented in `model.py` | pending |
| S-4.6 | CI is green on real GitHub Actions; `pip-audit` found a genuine setuptools CVE; schema-drift detector hand-verified by deliberate tampering | **not verified in this audit** — requires network access to the Actions history | **unverified** |
| S-4.7 | Clean-environment reproduction of the full suite has **not** been done | correctly recorded as an open gap. Keep. | verified as still open |

**Missing from manuscript 04 relative to instruction §19:** the scientific purpose of the software,
the mathematical objects represented, the reference-vs-optimised implementation distinction, the
experiment specification, and the instructions for independent reproduction. The current text is
close to the "list of repository paths" that §19 forbids. This is the largest rewrite in the package.

---

## Manuscript 05 — supplementary figures

| ID | Item | Issue | Action |
| --- | --- | --- | --- |
| S-5.1 | All nine figures | PNG + SVG only; **no vector PDF** | regenerate with a PDF backend (§18.1) |
| S-5.2 | Fig. 1 caption "A-N certification dashboard" | branded; encodes internal statuses visually — exactly what §21.5 forbids for a supplement | retitle "Summary of conclusions and evidence types across the numerical studies" |
| S-5.3 | Fig. 2 caption "reaches exactly zero (displayed at the floor for the log axis)" | the value is `2.5×10⁻⁷`, not zero (S-3.3); also **displays a floor without reporting it numerically** (§18.3) | correct the value; state the plotting floor |
| S-5.4 | Fig. 4 caption "the shaded region is the unresolved gap between the proved upper bound (2) and the best adversarially-found ratio (0.452)" | correct as stated, and correctly refuses to call it near-sharp | keep; retitle to "Observed values and the analytical upper bound for the associator estimate" |
| S-5.5 | Fig. 5 caption "sits at machine-precision zero (`8.2×10⁻³³`, displayed at a floor for visibility)" | correctly reports both the value and the floor — **this is the model the other captions should follow** | keep |
| S-5.6 | Fig. 7 caption | single-dimension timing; correctly labelled "an honest negative scaling result for this problem size" | keep |
| S-5.7 | Fig. 8 caption "the full 416-cell pilot+S1 sweep" | 416 executions = 208 configurations (S-3.15) | restate |
| S-5.8 | Figs. 3, 6, 8, 9 | no uncertainty intervals and no sample counts shown on the figures themselves (§18.1) | add `n` per point, or state in the caption why not |
| S-5.9 | §"What is intentionally not included here" | explicitly lists four omissions rather than silently dropping them | **keep — this is exemplary and should be retained verbatim** |

---

## Cross-cutting

| Item | Finding |
| --- | --- |
| Independent verification | **Zero rows verified by a person other than the author.** No row may be described as independently verified. |
| Originality | Not assessed for any row. A bounded search found no verbatim match for several formulations; that is not evidence. Requires §14. |
| Statements weakened by this audit | S-1.10 (remove "sharp"), S-1.12, S-1.13, S-3.3, S-3.5, S-3.7, S-3.15 |
| Statements found false | none |
| Values recomputed and confirmed | 19 |
| Values recomputed and found not to agree | 4 (S-1.13 interpretation, S-3.3, S-3.5, S-3.15) |
