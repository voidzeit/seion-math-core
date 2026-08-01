# Notation and conventions

> **Addendum: what was actually adopted.** This document was written during the audit, before
> the manuscripts were rewritten. The rewrite adopted its substance with one deliberate
> simplification, recorded here so that the two agree.
>
> | Object | Proposed below | Adopted in the delivered manuscripts | Reason |
> | --- | --- | --- | --- |
> | set of types | `𝒯` | **`𝒯`** (`\mathcal T`) | as proposed; document 01's former `𝔗` is gone |
> | composition tree | `𝔗` | **`T`** | Once the rotation family is renamed `G_η` (document 01) and the kernel operator is renamed `𝒦_κ` with the graded cohomology operator renamed `S` (document 02), the letter `T` collides with nothing. Keeping it avoids `E_𝔗^{proj}` throughout a 36-page article for no gain. |
> | root vertex | `ϱ` | **`ϱ`** | as proposed; frees `r` for the closure-residual map `r_v` |
> | error components | `D^∥`, `D^⊥` | **`D^∥`, `D^⊥`** | as proposed |
> | root errors | `E^{amb}`, `E^{proj}`, `E^⊥`, `E^{red}` | as proposed | `E^{proj}` replaces `E^P`, removing the collision with the projector |
> | measure on `X` | `ν` | **`ν`** | as proposed; `μ` is reserved for the multilinear maps |
> | integral kernel | `κ` | **`κ`** | as proposed; `K` stays with the coefficient tensor |
> | kernel operator | `𝒦_κ` | **`𝒦_κ`** | as proposed |
> | variational energies | `𝔈` | **`𝔈`** | as proposed; frees `E` for the four root errors |
> | left multiplication | `𝖫_x` | **`𝖫_x`** | as proposed; frees `L` for the leaf-norm product |
> | rotation family | `G_η` | **`G_η`** | as proposed; frees `T` |
> | Lagrange weight in the truncated energy | `w_d` | **`w_d`** | as proposed; frees `η = ρ/M` |
> | associator energy | `𝔈_A(κ)` | **`𝔈_A(κ)`** | as proposed; frees `ρ` for the closure bound |
>
> Every one of the 14 blocking collisions listed in §1 is resolved by the adopted scheme.
> The 11 that were internal to document 02 are resolved by the renamings above; the
> remainder were between documents and are resolved because document 02 no longer
> introduces trees as an object of its own.

---

## Original audit document

# 02 — Notation and conventions

Common notation for manuscripts 01 (`tree_stability_v4`) and 02 (`kernel_integrated_laws_v5`), with
the conventions that manuscript 03 must adopt where it refers to the same objects.

Two things are recorded here: the **standardised notation to be used**, and the **collisions in the
present sources** that force the standardisation. The collisions are not stylistic; several of them
put two mathematically distinct objects behind one symbol inside a single document.

---

## 1. Symbol collisions found in the current sources

Each was located by direct reading. "Same document" collisions are the serious ones.

| # | Symbol | Meaning 1 | Meaning 2 | Where | Severity |
| --- | --- | --- | --- | --- | --- |
| C-1 | `μ` | the multilinear laws `μ_v` | **the measure** on `X`, in "(X, μ) a σ-finite measure space" and in `dμ(q)`, `dμ^{⊗5}` | 02, same document, ~10 lines apart | **Blocking.** `T_K(f,g,h)(p) = ∭K(p;q,r,s)f(q)g(r)h(s)dμ(q)dμ(r)dμ(s)` sits in a paper whose central object is called `μ`. |
| C-2 | `T` | the composition tree `T`, `k(T)`, `E_T` | the kernel operator `T_K` | 02 | **Blocking** |
| C-3 | `T` | as above | a graded operator descending to cohomology, "`Td = dT ⟹ T` descends" | 02 §Finite cohomology; also §Exact mathematical status, where both appear in the same displayed list | **Blocking** |
| C-4 | `T` | as above | the extremizer rotation matrix `T_η` | 01 §Sharpness constructions | Moderate |
| C-5 | `T` | as above | the signed-forest terms `T_1`, `T_2`, and `cos(T_1,T_2)` in 03 block H | 01 §Signed polynomial expressions; 03 | Moderate — here `T_α` *is* a tree, so it is defensible, but `cos(T_1,T_2)` treats them as vectors |
| C-6 | `r` | the local residual map `r_v = (I−P_v)μ_v(P·,…,P·)` | "let `r` be the root" | 02 §Exact root-error geometry defines `r` = root, then §Exact subset expansion uses `r_v` = residual | **Blocking**, same document |
| C-7 | `r` | as above | the scalar bound `r_i` on `‖R_i‖` in the telescoping cost `C(π)` | 01 and 02, both | **Blocking** |
| C-8 | `r` | as above | the reduced rank, `St(d,r)`, `I_r`, "sum over all `r` columns" | 02 §Variational program; 03 block F | Moderate |
| C-9 | `P` | the orthogonal projector `P_τ = Q_τQ_τ*` | the superscript in `E_T^P` (an error *type*, not an operator) | 01 and 02 | Moderate — `E_T^P` reads as "`P` applied to `E`" |
| C-10 | `P` | as above | the mixed-state label `P` in `S = {R, P, N}` | 02 §Mixed-mask calculus | **Blocking** — `Π^R = Π^P = P` is written in the same line, which is genuinely hard to parse |
| C-11 | `P` | as above | the Markov operator `P_K`, `P_K(p,s)` | 02 §Markov operator | Moderate |
| C-12 | `η` | `η = ρ/M`, the closure-to-norm ratio governing every sharpness question | the Lagrange weight in `E_total^Λ = E_assoc^Λ + η·E_d^Λ` | 02, same document | **Blocking** |
| C-13 | `ρ` | the uniform closure-residual bound | `ρ_μ = ‖C_μ‖_op` (per-law, compatible) | 02 | Minor — consistent, but `ρ` vs `ρ_μ` should be stated |
| C-14 | `ρ` | as above | `ρ_A(K) := ‖Φ_K‖²_{L²}`, the **associator energy** — a squared `L²` norm, not a residual bound | 02 §Kernel of the associator | **Blocking** — a bound and a squared energy under one letter |
| C-15 | `A` | the associator `A(x,y,z)`, `A_μ^{(5)}`, `A_K` | the arity `a`, `a_v` (visually adjacent, and `A_v` appears in the canonical-object tuple as "declared composition defects") | 02 §The complete canonical object | Minor |
| C-16 | `K` | the coefficient tensor of a law, `K ∈ V⊗V*⊗…` | the integral kernel `K(p;q,r,s) ∈ L²(X⁴)` | 02, §Typed a-ary law vs §Ternary kernel | **Blocking** — this is exactly the instruction's §8 prohibition (a tensor and an integral kernel under one symbol) |
| C-17 | `K` | as above | `K` in the block-B commutator `C_θ = UΦU*ΔK − KΔUΦ*U*` | 03 block B | Cross-document |
| C-18 | `𝔗` (`\Types`) vs `𝒯` (`\cT`) vs `𝒯` (`\mathcal T`) | 01 uses `\Types = 𝔗` for the set of types and defines `\cT` without using it; 02 uses `\mathcal T` for the set of types; 02 also writes `𝔖` for the state alphabet and `𝔖` again for the whole canonical object | 01 vs 02, and 02 internally | **Blocking** — `𝔖` is the three-state alphabet in §Mixed-mask calculus and the entire canonical structure in §The complete canonical object |
| C-19 | `E` | the four root errors `E_T^{amb}`, `E_T^P`, `E_T^N`, `E_T^{red}` | the variational energies `E(θ)`, `E_A`, `E_C`, `E_cyc`, `E_FI`, `E_R`, `E_P`, `E_closure`, `E_d^Λ`, `E_total^Λ` | 02, same document | **Blocking** — `E_P` is a projector-idempotency penalty while `E_T^P` is a projected error |
| C-20 | `L` | `L_T = ∏_ℓ‖z_ℓ‖`, the leaf-norm product | `L_x z = x∘z`, the left-multiplication operator, and `L_{[x,y]}` | 02 §Curvature | **Blocking**, same document |
| C-21 | `Λ` / `λ` | `λ_v = ρ_v∏B^R_{c_i}`, the local residual source | `λ_A, λ_C, λ_cyc, λ_FI, λ_R, λ_P`, the energy weights; and `λ_r`, the CP weights | 02 | **Blocking** — three distinct uses |
| C-22 | `D` | `D_v = F_v − R_v`, the local discrepancy | `D_μ^{N,M}`, `D_P^{N,M}`, the multiscale transport defects | 02 §Multiscale structure | Moderate |
| C-23 | `C` | `C(π)`, the telescoping cost | `C_μ`, the leakage map | `C_T^P(η)`, the optimal constant | `C⁰→C¹→…`, the cochain complex; `C_θ`, the block-B commutator model | 02 (four uses) + 03 | **Blocking** |
| C-24 | `Φ` | `Φ_K = K_L − K_R`, the associator defect kernel | `Φ` in block B's `C_θ = UΦU*ΔK − …` | 02 vs 03 | Cross-document |
| C-25 | `Π` | `Π_cyc`, the cyclic projector | `Π^R, Π^P, Π^N`, the state projectors | `Π_{≤Λ}`, the spectral projector | 02 (three uses) | **Blocking** |

**Count: 25 collisions, of which 14 are blocking and 11 of the blocking ones are internal to
manuscript 02.** Manuscript 02 cannot be published in its current notation.

---

## 2. Standardised notation

### 2.1 Types and spaces

| Symbol | Meaning | Notes |
| --- | --- | --- |
| `𝒯` | the finite set of types | Replaces 01's `𝔗` and 02's `𝒯`. Used identically in both. |
| `τ ∈ 𝒯` | a type | |
| `𝕂 ∈ {ℝ, ℂ}` | the scalar field | |
| `V_τ` | ambient finite-dimensional Hilbert space of type `τ` | |
| `W_τ` | reduced finite-dimensional Hilbert space of type `τ` | |
| `Q_τ : W_τ → V_τ` | isometric embedding, `Q_τ*Q_τ = I_{W_τ}` | |
| `P_τ = Q_τQ_τ*` | orthogonal projector on `V_τ`, `P_τ² = P_τ = P_τ*`, `‖P_τ‖ = 1` | |
| `ran P_τ` | the reduced subspace inside `V_τ` | Use `ran P_τ`, never "tangent space" |
| `(ran P_τ)^⊥` | its orthogonal complement | Use "orthogonal complement", never "normal space" |
| `d_τ = dim V_τ`, `m_τ = dim W_τ` | | Frees `r` (C-8) |

### 2.2 Laws and trees

| Symbol | Meaning |
| --- | --- |
| `μ_v : ∏_{j=1}^{a_v} V_{τ(v,j)} → V_{τ(v)}` | the multilinear map at internal vertex `v` |
| `a_v` | arity of `v`; `a_max = max_v a_v` |
| `‖μ‖_op` | multilinear operator norm, `sup_{‖x_j‖=1}‖μ(x_1,…,x_a)‖` |
| `\bar μ = Q*μ(Q·,…,Q·)` | the reduced law |
| `𝒞_μ = (I−P_{τ_0})μ(P_{τ_1}·,…,P_{τ_a}·)` | the **closure-leakage map** (01 writes `r_v`; see §2.4) |
| `𝔗` | a finite rooted ordered typed tree | **Replaces `T`.** Frees `T` for operators (C-2, C-3, C-4). |
| `Int 𝔗` | internal vertices; `k(𝔗) = \|Int 𝔗\|` |
| `Leaves 𝔗` | leaves |
| `ϱ ∈ Int 𝔗` | the root | **Replaces "let `r` be the root"** (C-6) |
| `z_ℓ ∈ W_{τ(ℓ)}` | reduced leaf datum |
| `L_𝔗 = ∏_{ℓ∈Leaves 𝔗} ‖z_ℓ‖` | leaf-norm product. **`L` is reserved for this.** Left multiplication (C-20) is written `𝖫_x`. |
| `ℱ = Σ_α c_α 𝔗_α` | a finite signed linear combination of composition trees |

### 2.3 Evaluations and errors

| Symbol | Meaning |
| --- | --- |
| `F_ℓ = R_ℓ = Q_{τ(ℓ)}z_ℓ` | leaf value |
| `F_v = μ_v(F_{c_1},…,F_{c_{a_v}})` | unprojected (ambient) evaluation |
| `R_v = P_{τ(v)}μ_v(R_{c_1},…,R_{c_{a_v}})` | recursively projected evaluation |
| `D_v = F_v − R_v` | local discrepancy |
| `D_v^∥ = P_v D_v` | **projected component** |
| `D_v^⊥ = (I − P_v)D_v` | **orthogonal component** |

**Adopt `∥/⊥` (instruction §8) in place of the sources' `D^P/D^N`.** This resolves C-9 and C-10 at
once: the superscript `P` no longer collides with the projector, and the state alphabet becomes
`{R, ∥, ⊥}` instead of `{R, P, N}`.

The four root errors, with `F = F_ϱ`, `R = R_ϱ`, `P = P_{τ(ϱ)}`, `Q = Q_{τ(ϱ)}`:

| Standardised | In 01 and 02 | Definition |
| --- | --- | --- |
| `E_𝔗^{amb}` | `E_T^{amb}` | `‖F − R‖` |
| `E_𝔗^{proj}` | `E_T^P` | `‖PF − R‖` |
| `E_𝔗^{⊥}` | `E_T^N` | `‖(I−P)F‖` |
| `E_𝔗^{red}` | `E_T^{red}` | `‖Q*F − Q*R‖` |

Both sources prove `(E^{amb})² = (E^{proj})² + (E^⊥)²` and `E^{red} = E^{proj}`.

**Reserve `E` for these four quantities.** The variational energies (C-19) become `𝔈`:
`𝔈(θ), 𝔈_assoc, 𝔈_closure, 𝔈_cyc, 𝔈_FI, 𝔈_proj, 𝔈_d^Λ, 𝔈_total^Λ`. Their weights (C-21) become
`w_A, w_C, …`, freeing `λ`.

### 2.4 Constants

| Symbol | Meaning | Guard |
| --- | --- | --- |
| `M` | uniform bound, `‖μ_v‖_op ≤ M` for all `v ∈ Int 𝔗` | |
| `ρ` | uniform bound, `‖𝒞_{μ_v}‖_op ≤ ρ` for all `v ∈ Int 𝔗` | **`ρ` is reserved for this.** The associator energy (C-14) becomes `𝔈_A(K) = ‖Φ_K‖²_{L²(X⁶)}` — it is an energy, and belongs with the other `𝔈`'s. |
| `η = ρ/M` | the closure-to-norm ratio | **Reserved.** The Lagrange weight (C-12) becomes `w_d`. |
| `δ` | law-approximation error, `‖μ_v − \hatμ_v‖_op ≤ δ` | |
| `λ_v = ρ_v ∏_i B^R_{c_i}` | local residual source in the pathwise bound | Sole surviving use of `λ`; CP weights become `σ_r` |
| `h_{v,j}` | transport gain from child slot `j` through vertex `v` | |
| `C_𝔗^{proj}(η) = sup 𝒜(𝔗,η) E^{proj}/(ρM^{k−1}L_𝔗)` | the **exact** (unknown) constant | Must never be written where an upper bound is meant — see `03_proof_audit.md` §6 |
| `𝔠_𝔗^{proj}` | a **proved upper bound** for `C_𝔗^{proj}` | Distinct glyph, deliberately |
| `\underline{c}_𝔗^{proj}` | a **certified lower bound** from an explicit construction | |

**This three-way distinction is the single most important notational change.** In the current
sources the same expression `(k−1)` is used for (i) a proved upper bound, (ii) a conjectured exact
value, and (iii) a table column heading; and `certified_lower_bound` in the data takes the value
`0.0` in 1794 of 9945 registered rows, where it is vacuous. See `03_proof_audit.md` §6.3.

### 2.5 Analytic setting (manuscript 02 only)

| Symbol | Meaning | Replaces |
| --- | --- | --- |
| `(X, ν)` | σ-finite measure space; `H = L²(X, ν)` | **`(X, μ)`** — resolves C-1 |
| `dν(q)` | integration | `dμ(q)` |
| `κ(p; q_1,…,q_a) ∈ L²(X^{a+1})` | the integral kernel | **`K`** — resolves C-16; `K` stays with the coefficient tensor |
| `𝒦_κ(f_1,…,f_a)(p) = ∫_{X^a} κ(p;q)∏_j f_j(q_j) dν^{⊗a}` | the kernel-defined multilinear operator | **`T_K`** — resolves C-2/C-3 |
| `κ_L`, `κ_R`, `Φ_κ = κ_L − κ_R` | composite and defect kernels | `K_L`, `K_R`, `Φ_K` |
| `𝒲(p,s)`, `𝖽(p)`, `𝒫(p,s)`, `Δ_𝒫 = I − 𝒫` | the symmetric weight, degree, Markov kernel, induced Laplacian | `W_K`, `d_K`, `P_K`, `Δ_K` — resolves C-11 and frees `d` for the differential |
| `d_p : C^p → C^{p+1}`, `d*`, `Δ_Hodge = dd* + d*d` | the cochain differential, adjoint, Hodge Laplacian | keeps `d` unambiguous |
| `Π_{≤Λ}` | spectral projector of `Δ_Hodge` below `Λ` | **the only `Π`** — the cyclic projector becomes `Sym_cyc`, the state projectors become `P` and `I−P` directly (C-25) |
| `𝖫_x z = x ∘ z` | left multiplication | resolves C-20 |
| `A(x,y,z) = (x∘y)∘z − x∘(y∘z)` | the associator | |
| `R_std(x,y) = [𝖫_x,𝖫_y] − 𝖫_{[x,y]}` | the operator commutator defect | |
| `R_alg := A` | the **associator-based algebraic tensor** | defined by convention only; see below |

---

## 3. Conventions that must be stated in both mathematical papers

1. **Projectors are orthogonal.** Every result depends on it. Manuscript 01 already gives the
   oblique counterexample (`P = [[1,1],[0,0]]`, `D = (0,1)ᵀ`, so `PD = (1,0)ᵀ` and
   `(I−P)D = (−1,1)ᵀ` are not orthogonal). Keep it, and cite it from manuscript 02.

2. **`ran P` is a fixed linear subspace, not a tangent space.** Use *projected* and *orthogonal*, or
   *range* and *orthogonal complement*. Reserve "tangent" for `T_Q St(d,r)`, the only genuine tangent
   space in the corpus.

3. **`R_alg := A` is a definition, not a theorem.** State immediately after it that this is not,
   without additional structure, the curvature tensor of a connection. The one theorem available is
   `R_std(x,y)z = A(y,x,z) − A(x,y,z)`, which is an identity between an operator commutator defect
   and an antisymmetrised associator — not "curvature equals associator".

4. **Distinguish `ρ` from sampled diagnostics.** Manuscript 02 already flags that
   `𝔈_closure = 𝔼[‖(I−P)μ(PX_1,…,PX_a)‖²/(‖μ(PX_1,…,PX_a)‖² + ε)]` is not `ρ_μ = ‖𝒞_μ‖_op`. Keep
   that remark; manuscript 03's block G reports the sampled quantity and must not be read as bounding
   the operator norm.

5. **Empty products and the `k = 0` case.** `M^{k−1}` at `k = 0` is `M^{−1}`, undefined when `M = 0`.
   The convention must be stated: *at a leaf, `k = 0` and the estimate reads `0 ≤ 0`.* Both papers
   currently write "the claims are trivial for a leaf", which is true but leaves `M^{−1}` on the
   page. See `03_proof_audit.md` §3.1.

6. **Upper bound, exact constant, lower construction are three different objects** (§2.4). An
   attained value is a lower bound only after admissibility is verified; an optimiser result is
   never a certificate.

7. **Norms.** `‖·‖` is the Hilbert norm; `‖·‖_op` the multilinear operator norm; `‖·‖_F` Frobenius;
   `‖·‖_HS` Hilbert–Schmidt; `‖·‖_2` the `L²(X,ν)` norm. Manuscript 01's Limitations already records
   that operator norms are exact only for declared constructions and that general dense/CP laws may
   use Frobenius upper bounds — this must appear wherever `M` is used, not only in Limitations.

---

## 4. Cross-manuscript agreement table

What manuscript 03 must adopt where it discusses the same objects.

| Object | 01 | 02 | 03 (current) | Standard |
| --- | --- | --- | --- | --- |
| orthogonal projector | `P_τ` | `P_τ` | `P = UU*` | `P_τ = Q_τQ_τ*`; 03 keeps `U` for the frame but writes `P = UU*` with `U` isometric |
| associator | (implicit, via signed forests) | `A`, `A_μ^{(5)}`, `A_e` | `A(x,y,z)` | `A` for the binary associator, `A^{(5)}_μ` for the five-input ternary one; never one "associator score" across conventions |
| associator upper bound | `2` for the two-term signed forest, from `k−1 = 1` per tree | `2ρML` | `2\hat M²‖x‖‖y‖‖z‖` | **These are three different bounds with different hypotheses.** 03's is a plain triangle bound on `‖A‖` with no projection; 01/02's is a projected-error bound. `03_proof_audit.md` §7 records that 03's figure "the constant 2 is not sharp" and 01's open problem "is `k−1` sharp" are **not the same question** and must not be cross-referenced as if they were. |
| principal angles | not used | not used | used throughout (E, F, M) | `θ_1 ≥ … ≥ θ_m`, in radians, with `π/2 ≈ 1.5708` stated |
| closure defect | `ρ` (operator norm) | `ρ_μ` and `𝔈_closure` | sampled, block G | 03 reports `𝔈_closure`; label it as such |
