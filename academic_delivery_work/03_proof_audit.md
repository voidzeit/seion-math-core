# 03 — Proof audit

Every definition, lemma, proposition, theorem, corollary and stated identity in manuscripts 01 and
02 was read in full and checked against the twelve criteria of §9 of the governing instruction:
domain/codomain, hypotheses, base cases, inductive steps, norm estimates, constants and exponents,
degenerate cases, which structural properties are actually used, applicability of cited results,
equality vs. upper bound, upper bound vs. sharp constant, lower construction vs. global optimum.

Sources: `papers/tree_stability_v4/{main.tex, proofs/full_proofs.tex}` and
`papers/kernel_integrated_laws_v5/main.tex`, both at `2e419ef`.

Manuscripts 03, 04 and 05 contain no theorem statements. They are audited in
`01_statement_evidence_table.md` instead.

---

## 1. Summary

| Classification | Count | Results |
| --- | ---: | --- |
| Complete proof | 8 | 01: Lem. magnitudes, Prop. root geometry, Thm. subset expansion, Thm. ordering, Cor. path sum, Cor. signed forest, Prop. approximation+projection. 02: Thm. curvature identity. |
| Complete after an explicitly documented correction | 4 | A-1 … A-4 below |
| Proof sketch | 2 | 01 Thm. `dp` (soundness argued, complexity asserted); 02 §Mixed-mask recurrence (soundness "proved for the declared finite configuration", not shown) |
| Conditional result | 3 | 02: kernel boundedness, cohomological descent, Hodge compatibility — all correct *under* hypotheses that are stated but not all verified for the objects at hand |
| Standard consequence requiring citation | 4 | 02: Stiefel tangent space and Riemannian gradient; Dirichlet-form positivity; spectral-dimension definition; Davis–Kahan-type bound invoked in 03 block D |
| **Incomplete** | 3 | B-1, B-2, B-3 below |
| False as stated | 0 | — |
| Open | 6 | §6 |

**No statement in either manuscript was found to be false.** The central theorem is correct. The
three incomplete items are all in manuscript 02's analytic sections, and two of the three are
repairable with short arguments supplied below.

---

## 2. Manuscript 01 — result-by-result

### 2.1 Lemma (subtree magnitudes) — `full_proofs.tex` §Magnitude induction — **complete**

`‖F_v‖ ≤ M^{k_v}L_v` and `‖R_v‖ ≤ M^{k_v}L_v`.

Checked: base case at a leaf uses `Q_v` isometric, giving `‖F_v‖ = ‖z_v‖`. Inductive step uses
multilinearity and the definition of `‖·‖_op`. The `R` case additionally uses **contractivity of an
orthogonal projector** (`‖P_v x‖ ≤ ‖x‖`), which the proof states. Exponent check:
`M · M^{Σ_i k_{c_i}} = M^{1+Σ k_{c_i}} = M^{k_v}` ✓.

### 2.2 Proposition (exact root geometry) — **complete**

`(E^{amb})² = (E^{proj})² + (E^⊥)²` and `E^{red} = E^{proj}`.

Checked. `F − R = (PF − R) + (I − P)F` requires `R ∈ ran P`, which holds because
`R = R_ϱ = P μ_ϱ(…)` — stated. First summand in `ran P`, second in `(ran P)^⊥`, Pythagoras applies.
Second identity: `Q*F − Q*R = Q*(PF − R)` uses `Q*(I−P) = 0`, and `Q*` restricted to `ran P` is an
isometry. Both facts follow from `Q*Q = I` and `P = QQ*`.

**Orthogonality is essential and the manuscript proves it is.** The counterexample in
§Counterexamples (`P = [[1,1],[0,0]]`, `D = (0,1)ᵀ`, `PD = (1,0)ᵀ`, `(I−P)D = (−1,1)ᵀ`,
`⟨PD,(I−P)D⟩ = −1 ≠ 0`) is verified correct: `P² = [[1,1],[0,0]] = P` so `P` is idempotent but not
self-adjoint, and the decomposition is not orthogonal.

### 2.3 Theorem (exact child-error subset expansion) — **complete**

`D_v = r_v(R_1,…,R_a) + Σ_{∅≠S⊆[a]} μ_v(y_1^S,…,y_a^S)`.

Verified independently. Multilinear expansion of `μ_v(R_1+D_1, …, R_a+D_a)` over all `2^a` subsets is
exact. The `S = ∅` term is `μ_v(R_1,…,R_a)`; subtracting `R_v = P_vμ_v(R_1,…,R_a)` leaves
`(I−P_v)μ_v(R_1,…,R_a)`. That equals `r_v(R_1,…,R_a)` because `R_i ∈ ran P_{c_i}`, so
`P_{c_i}R_i = R_i` and the definition
`r_v = (I−P_v)μ_v(P_{c_1}·,…,P_{c_a}·)` applies. **No inequality is used** — the proof says so, and
that is correct. This is an exact identity, and the rewritten manuscript must say "identity", never
"bound".

> **Correction A-1 (documented).** In manuscript 02 the same theorem is stated with
> `r_v(R_1,…,R_a) = (I−P_v)μ_v(R_1,…,R_a)` — i.e. **without** the inner projectors. That form is
> correct *only because* `R_i ∈ ran P_{c_i}`, which 02 never says at that point. 02's version is not
> the definition of the operator whose norm is bounded by `ρ` (that operator is
> `(I−P_v)μ_v(P·,…,P·)`), so the hypothesis `‖r_v‖_op ≤ ρ` does not attach to 02's `r_v` as written.
> **Fix:** adopt 01's definition verbatim, and add the one-line remark `P_{c_i}R_i = R_i`.

### 2.4 Theorem (universal `k` and `k−1` coefficients) — **complete, with A-2**

`E^{amb} ≤ kρM^{k−1}L_𝔗`, `E^⊥ ≤ kρM^{k−1}L_𝔗`, `E^{proj} = E^{red} ≤ (k−1)ρM^{k−1}L_𝔗`.

This is the principal result of the whole corpus and was checked term by term.

**Ambient.** Multilinear telescoping in any fixed slot order gives
`‖μ_v(F_1,…,F_a) − μ_v(R_1,…,R_a)‖ ≤ M Σ_j ‖F_j−R_j‖ ∏_{i<j}‖R_i‖ ∏_{i>j}‖F_i‖`.
Substituting the inductive hypothesis and the magnitude lemma, the `j`-th summand is at most
`M · k_{c_j}ρM^{k_{c_j}−1}L_{c_j} · ∏_{i≠j} M^{k_{c_i}}L_{c_i} = k_{c_j}ρM^{Σ_i k_{c_i}}L_v = k_{c_j}ρM^{k_v−1}L_v`.
Exponent verified: `1 + (k_{c_j}−1) + Σ_{i≠j}k_{c_i} = Σ_i k_{c_i} = k_v − 1` ✓.
Summing, `Σ_j k_{c_j} = k_v − 1`, so the propagated contribution is `≤ (k_v−1)ρM^{k_v−1}L_v`.
The local residual adds `ρ∏_j‖R_j‖ ≤ ρM^{k_v−1}L_v`. Total `k_vρM^{k_v−1}L_v` ✓.

**Projected.** `E^{proj} = ‖PF − R‖ = ‖P(F−R)‖ = ‖PD_ϱ‖` (using `R ∈ ran P`, so `PR = R`), and
`P r_ϱ = 0`, so `PD_ϱ = P(μ_ϱ(F_1,…,F_a) − μ_ϱ(R_1,…,R_a))`. Since `‖P‖ = 1`, the same telescoping
bound applies **without** the local-residual term, giving `(k−1)ρM^{k−1}L_𝔗` ✓. Note the induction
is on the *ambient* bound for children; only the root step differs. Both manuscripts get this right.

**Orthogonal.** `(I−P)F = (I−P)(F−R)` since `(I−P)R = 0`, so `E^⊥ ≤ ‖D_ϱ‖ ≤ kρM^{k−1}L_𝔗` ✓.
(This is weaker than it could be but is correctly stated as an upper bound.)

**Base cases verified.**
`k = 1`: `D_ϱ = r_ϱ(R_1,…,R_a)` since all `D_i = 0`, so `E^{amb} ≤ ρL`, matching `1·ρ·M⁰·L`; and
`E^{proj} = ‖P r_ϱ(…)‖ = 0`, matching `(1−1)ρM⁰L = 0` ✓. The manuscript states this explicitly.
`k = 2`: `E^{amb} ≤ 2ρML`, `E^{proj} ≤ ρML` ✓.

> **Correction A-2 (documented).** `M^{k−1}` at `k = 0` is `M^{−1}`, undefined for `M = 0`. Both
> proofs say "trivial for a leaf", which is true, but the *statement* as displayed is ill-formed at
> `k = 0`. **Fix:** state the theorem for `k ≥ 1`, and record the leaf convention separately
> (`E = 0` at a leaf). One sentence.

**What the proof does and does not give.** It uses: multilinearity, `‖P‖ = 1`, orthogonality of `P`
(for the projected case only), finite dimensionality (nowhere essentially — the argument is
dimension-free given bounded operator norms), and type compatibility (only to make composition
defined). It is a chain of **triangle inequalities**. It yields an upper bound and **nothing about
optimality**. The manuscript states this correctly in §Projected-root improvement and again in
§Limitations; that wording must be preserved.

### 2.5 Theorem (globally optimal telescoping order) — **complete**

Independently re-derived. With prefix `A = ∏_{s<t} r`, suffix `B = ∏_{s>t} f`, exchanging adjacent
slots `i, j` leaves all other terms fixed and compares `w_i f_j + r_i w_j` against
`w_j f_i + r_j w_i`, i.e. `w_i d_j ≤ w_j d_i` with `d_i = f_i − r_i` ✓ (matches the manuscript).

Case check, using `w_i ≥ 0`:
* both `d` nonzero, same sign ⟹ `d_i d_j > 0`, divide ⟹ `w_i/d_i ≤ w_j/d_j` ✓ (holds for both
  positive and both negative);
* `d_i > 0`, `d_j < 0` ⟹ `w_i d_j ≤ 0 ≤ w_j d_i`, so positive precedes negative ✓;
* `d_i = 0`, `d_j > 0` ⟹ `i` before `j` is no worse iff `w_i d_j ≤ 0`, i.e. only if `w_i = 0`; so
  positive precedes zero ✓;
* `d_i = 0`, `d_j < 0` ⟹ `w_i d_j ≤ 0` always ✓, so zero precedes negative ✓.

The stated order (positive `d`, then zero, then negative; increasing `w_i/d_i` inside each nonzero
class) is exactly consistent with all four cases.

> **Correction A-3 (documented).** The proof ends "Repeatedly exchanging inverted adjacent pairs
> never increases `C` and terminates at the stated order. Every permutation can be transformed in
> this way, proving global optimality." An adjacent-exchange argument gives a **global** minimum only
> if the comparison relation is a **total preorder**. It is: the relation is induced by the
> lexicographic key `(sign-class rank, w_i/d_i)`, with class ranks `positive < zero < negative`, and
> the four cases above show the exchange condition agrees with that key. **Fix:** add that sentence.
> Without it this is an exchange heuristic, not a proof of global optimality.

**Scope guard already present and correct:** "The theorem optimizes this scalar telescoping family
only." Exhaustive property tests against all permutations through arity seven are reported. Keep
both.

### 2.6 Theorem (sound mixed-state dynamic program) — **proof sketch**

Soundness: expand by the subset theorem, split each `D_i` orthogonally into `D_i^∥ + D_i^⊥`, bound
each of the `3^{a_v} − 1` non-all-`R` state vectors by the corresponding certified block operator
norm times child magnitude bounds, and take a minimum of independently valid upper bounds. Each step
is a correct application of the operator-norm inequality, and "the minimum of valid upper bounds is
a valid upper bound" is immediate. **The soundness argument is complete.**

The complexity claim `O(|𝔗|3^{a_max} + |𝔗|a_max log a_max)` is *asserted* from the two counts
(`3^{a_v} − 1` state vectors, `a_v log a_v` to sort) without accounting for the cost of evaluating
each block norm, which is where the real work is. The manuscript's own Limitations concedes that
operator norms are exact only for declared constructions. **Classification: proof sketch.**
**Fix:** state the complexity as a count of *recursion steps*, or add the per-node norm-evaluation
cost as an explicit factor.

The hypothesis "assume certified bounds for every full, projected-output and normal-output mixed
block of each node law" is a genuine and non-trivial assumption; it should be displayed as a
hypothesis, not embedded in the sentence.

### 2.7 Corollary (residual-source path sum) — **complete, with A-4**

> **Correction A-4 (documented) — this is the item flagged in §9.3 of the governing instruction, and
> the flag is justified.** The corollary is correct **as an identity for the scalar recurrence**
> `B_v ≤ λ_v + Σ_j h_{v,j}B_{c_j}`: unrolling an affine recurrence over a tree gives exactly
> `Σ_v λ_v ∏_{(a,j)∈path(v,ϱ)} h_{a,j}` ✓. It is **not** an exact expansion of the multilinear cross
> terms — the subset expansion's `|S| ≥ 2` interaction terms have been absorbed into the scalar gains
> `h_{a,j}` before unrolling. The current text ("The scalar nodewise recurrence is affine in each
> local source `λ_v`") is *technically* accurate but a reader may take the path sum for an exact
> attribution of error to sources. **Fix:** state explicitly, at the theorem, that this is the exact
> expansion of a **valid scalar upper-bound recurrence**, and that cross-branch interaction terms are
> already subsumed in the gains. Manuscript 02's phrasing ("This attributes error to each node and
> path individually") is the more misleading of the two and must be rewritten.

The projected variant (root source omitted, last gain a projected-output gain) follows from
`P r_ϱ = 0` ✓.

### 2.8 Corollary (signed-forest triangle certificate) — **complete**

`E^{proj}_ℱ ≤ Σ_α |c_α| B^{proj}_{𝔗_α}`. Triangle inequality plus the previous theorem ✓.
"The two-term, two-node ternary associator has coefficient at most two": each tree has `k = 2`, hence
`k−1 = 1`, and two terms give `2` ✓. Consistent with the body text ("1+1 = 2, not the ambient
2+2 = 4"). The remark that syntactically identical trees may first be combined exactly is correct and
is the only *unconditional* cancellation statement — the manuscript says so.

### 2.9 Proposition (approximation plus projection) — **complete**

`E_repr ≤ kδ(M+δ)^{k−1}L`, and the closure coefficient splits as
`cρ(M+δ)^{k−1}L = cρM^{k−1}L + cρ[(M+δ)^{k−1} − M^{k−1}]L`, `c ∈ {k, k−1}`.

Verified: inserting the ambient `\hatμ`-tree and telescoping over the `k` node-law replacements gives
`δ(M+δ)^{k−1}L` per replacement (the `≤ M+δ` bound covers the not-yet-replaced factors) ✓. The
displayed split is an algebraic partition of one valid upper bound, and the proof says so ("No
equality with the observed total error is asserted") ✓. Table caption "Components sum to a theorem
upper, not to observed error" is correct and must be kept.

### 2.10 The `\VThreeMaxRelativeGap` statement — **traceable, but misstated in the abstract**

Not a theorem, but a headline claim, and it fails criterion 12 (lower construction vs. global
optimum). See §6.3.

---

## 3. Manuscript 02 — result-by-result

### 3.1 Restatements of manuscript 01

Theorem "Error orthogonality" ≡ 01 Prop. root geometry; Theorem "Exact nodewise expansion" ≡ 01 Thm.
subset (modulo A-1); Theorem "Ambient-to-projected coefficient improvement" ≡ 01 Thm. homogeneous;
the telescoping proposition, path-sum display, signed-forest bound and representation-error bound
likewise. All are correct where correct in 01, and inherit corrections A-1 through A-4.

02's inductive proof of the main theorem is a valid alternative arrangement (it does the root step
directly rather than at a general internal vertex). It also carries the `M^{−1}` issue of A-2.

02's base-case discussion is a genuine addition: `k = 1` gives `PF − R = 0` exactly, and the `k = 2`
sentence "leakage created at `u` can be turned tangential by `v`; leakage created at `v` itself
vanishes on projection" is the correct mechanism, though "tangential" must go (see
`02_notation_and_conventions.md` §3.2).

### 3.2 Theorem (curvature identity) — **complete**

`R_std(x,y)z = A(y,x,z) − A(x,y,z)` with `R_std(x,y) = [𝖫_x,𝖫_y] − 𝖫_{[x,y]}`,
`A(x,y,z) = (x∘y)∘z − x∘(y∘z)`, `[x,y] = x∘y − y∘x`.

Re-derived independently:
`R_std(x,y)z = x∘(y∘z) − y∘(x∘z) − (x∘y)∘z + (y∘x)∘z`.
`−A(x,y,z) = x∘(y∘z) − (x∘y)∘z`; `A(y,x,z) = (y∘x)∘z − y∘(x∘z)`.
Sum `= x∘(y∘z) − (x∘y)∘z + (y∘x)∘z − y∘(x∘z)` ✓. **Identical.**

The accompanying remark ("An outright identity `R_std = A` requires additional hypotheses… The
universal identity currently defensible is the antisymmetrized difference") is correct and is exactly
the position §9.4 of the governing instruction requires. **Keep it verbatim.** No claim
"curvature equals associator" is made anywhere in the manuscript — this was checked.

The bilinear operation `∘` must be declared: the identity holds for **any** bilinear `∘` on a vector
space, with no algebra axioms. State that.

### 3.3 Proposition (boundedness of the kernel-defined operator) — **conditional, proof complete**

`κ ∈ L²(X⁴) ⟹ ‖𝒦_κ(f,g,h)‖_2 ≤ ‖κ‖_{L²(X⁴)}‖f‖_2‖g‖_2‖h‖_2`.

Proof given as "Cauchy–Schwarz on `X³` followed by Fubini in the output variable". Verified:
`|𝒦_κ(f,g,h)(p)| ≤ ‖κ(p;·,·,·)‖_{L²(X³)}·‖f⊗g⊗h‖_{L²(X³)} = ‖κ(p;·)‖_2‖f‖_2‖g‖_2‖h‖_2`,
then integrate `|·|²` over `p` ✓. The step needs **Tonelli** (nonnegative integrand) for
measurability of `p ↦ ‖κ(p;·)‖_2` and σ-finiteness, which is assumed. The proof cites "Fubini"; it
should cite Tonelli. Minor.

The `n`-ary statement `κ_n ∈ L²(X^{n+1})` follows identically ✓.

Kernel stability `‖𝒦_κ(f,g,h) − 𝒦_{\tildeκ}(f,g,h)‖_2 ≤ ‖κ−\tildeκ‖_2‖f‖‖g‖‖h‖` is immediate from
linearity in the kernel ✓. The conclusion drawn — "`κ_n → κ` in `L²` implies strong convergence on
each fixed triple" — is correct.

### 3.4 Composite and defect kernels — **INCOMPLETE (B-1), but repairable; proof supplied**

The manuscript defines
`κ_L(p;q_1..q_5) = ∫ κ(p;u,q_4,q_5)κ(u;q_1,q_2,q_3)dν(u)`, similarly `κ_R`, sets `Φ_κ = κ_L − κ_R`,
asserts `A_κ(f_1,…,f_5)(p) = ∫_{X^5}Φ_κ(p;q)∏f_j(q_j)`, and defines
`ρ_A(κ) := ‖Φ_κ‖²_{L²(X⁶)}`.

**Nothing establishes that `κ_L`, `κ_R` are defined a.e. or lie in `L²(X⁶)`, or that the interchange
of integration producing the displayed identity is legitimate.** This is precisely the gap §9.5 of
the governing instruction warns about.

**It is repairable, and the required bound is true.** By Cauchy–Schwarz in `u`,
`|κ_L(p;q)|² ≤ (∫|κ(p;u,q_4,q_5)|²dν(u))·(∫|κ(u;q_1,q_2,q_3)|²dν(u))`.
Integrating over `(p,q_1,…,q_5)` and using Tonelli, the two factors separate:

> `‖κ_L‖_{L²(X⁶)} ≤ ‖κ‖²_{L²(X⁴)}`, and hence `‖Φ_κ‖_{L²(X⁶)} ≤ 2‖κ‖²_{L²(X⁴)}`,
> so `ρ_A(κ) ≤ 4‖κ‖⁴_{L²(X⁴)}`.

Finiteness of `‖κ_L‖_2` then gives finiteness of the inner integral for a.e. `(p,q)`, which
legitimises the composition; and absolute integrability of
`Φ_κ(p;q)∏f_j(q_j)` over `X^5` for a.e. `p` follows from Cauchy–Schwarz, which legitimises Fubini in
the displayed identity.

**Fix:** insert the above as a lemma with its two-line proof, before the definition of `ρ_A`.
**Authorization not required** — this closes the gap without changing any claim.

### 3.5 Converse of the associator-vanishing criterion — **INCOMPLETE (B-2), repairable; proof supplied**

Stated: "If `Φ_κ = 0` a.e., the product is associative under the stated convention; under suitable
density/integrability conditions, if the associator vanishes on all products of test functions then
`Φ_κ = 0` a.e. (converse also holds)."

The forward direction is immediate ✓. The converse is asserted with **"suitable
density/integrability conditions" left unspecified**, and no proof. As written the sentence is not a
mathematical statement.

**Repair, with the hypothesis made explicit.** Assume `Φ_κ ∈ L²(X⁶)` (which §3.4 now supplies) and
that `L²(X,ν)` is **separable** — this is the missing hypothesis, and it is not automatic; it holds
when `ν` is σ-finite and the σ-algebra is countably generated. Then: pick a countable dense set
`{g_m} ⊂ L²(X,ν)`. For each 5-tuple from `{g_m}`, `A_κ(g_{m_1},…,g_{m_5}) = 0` in `L²(X)`, so
`∫Φ_κ(p;q)∏g_{m_j}(q_j)dν^{⊗5}(q) = 0` for a.e. `p`, off a null set `N_{m_1…m_5}`. The union over
the countably many 5-tuples is null. Off it, `Φ_κ(p;·) ∈ L²(X⁵)` annihilates a set whose finite
linear span is dense in `L²(X⁵)` (finite sums of products of a dense family span densely in the
tensor product), hence `Φ_κ(p;·) = 0`. So `Φ_κ = 0` a.e. ∎

**Fix:** replace "under suitable density/integrability conditions" with the separability hypothesis
and the four-line proof above. **Authorization not required.**

**Note also:** the parenthesis "(converse also holds)" appended to a sentence that *is* the converse
is either redundant or claims a third statement. It must be deleted or made precise.

### 3.6 Mixed-mask recurrence — **proof sketch**

The full expansion `μ_v(F_1,…,F_a) = Σ_{σ∈{R,∥,⊥}^a} μ_v(Z_1^σ,…,Z_a^σ)` is exact ✓ (it is the
subset expansion with each `D_i` split orthogonally). The recurrence
`b_v^χ ≤ λ_v^χ + Σ_{σ≠(R,…,R)} β_v^χ(σ)∏_i b_i^{σ_i}` with `λ_v^∥ = 0`, `λ_v^⊥ ≤ ρ_v∏_i b_i^R` then
follows by the operator-norm inequality ✓.

The parenthetical "(with `Π^R = Π^∥ = P`, `Π^⊥ = I−P`, though `R` and `∥` states retain different
magnitude bounds)" is doing real work and is confusing as written: the *projectors* coincide but the
*magnitude bounds* differ (`b^R ≤ M^k L`, `b^∥ ≤ (k−1)ρM^{k−1}L`). **Fix:** separate the two
statements.

"its soundness is proved for the declared finite configuration" — no proof is given in 02, and 01's
`full_proofs.tex` contains it. **Fix:** cite 01.

### 3.7 Cochain descent and Hodge compatibility — **conditional, correct**

"`T(ker d_p) ⊆ ker d_p` and `T(im d_{p−1}) ⊆ im d_{p−1}` ⟹ `T_*: H^p → H^p` well defined;
sufficient condition `Td = dT`" ✓ standard, and the one-line justification given is correct. Requires
`T` graded of degree 0 — **not stated**. Add.

"`[T,d] = 0` and `[T,d*] = 0` ⟹ `[T,Δ] = 0`, so `T` preserves `ℋ^p = ker Δ_p`" ✓ immediate from
`Δ = dd* + d*d`. Finite complex with inner products, so `d*` exists. Correct.

**Guard required (instruction §9.6).** These are statements about an abstract finite cochain complex.
The manuscript must not let them read as results about the de Rham complex of a manifold. §Spectral
truncation then works with `Π_{≤Λ}` for the Hodge Laplacian "on a compact manifold" — that is a
different, infinite-dimensional setting, and the transition is made in one sentence with no
hypotheses. **Fix:** separate into "finite cochain complexes" (proved) and "spectral truncation on a
compact manifold" (conditional construction), and state that
`𝔈_d^Λ(κ) = 0` gives commutation **within the truncation only**, never a continuum statement. 02's
existing remark that a local minimum does not imply `𝔈_d^Λ = 0` is correct and must be kept.

### 3.8 Markov operator and induced Laplacian — **INCOMPLETE (B-3) in one step, otherwise correct**

Self-adjointness of `𝒫` on `L²(X,ν)`, `dν = 𝖽 dμ`: verified,
`⟨𝒫f, g⟩_ν = ∬𝒲(p,s)f(s)\bar g(p)dν'(s)dν'(p)`-type computation is symmetric under `p ↔ s` because
`𝒲` is symmetric ✓.

Dirichlet form `⟨f, Δ_𝒫 f⟩_{L²(ν)} = ½∬|f(p)−f(s)|²𝒲(p,s)dμ(p)dμ(s)` ✓ (expand and use symmetry of
`𝒲`; the cross term is real because the form is Hermitian). Hence `Δ_𝒫 ≥ 0` ✓.

**B-3.** The construction is introduced with "Suppose a declared kernel contraction yields a
symmetric nonnegative function `𝒲(p,s) = 𝒲(s,p) ≥ 0`". **No such contraction is exhibited**, and no
condition on `κ` is given under which the contraction is symmetric or nonnegative. Additionally,
`𝖽(p) = ∫𝒲(p,s)dμ(s)` needs `𝖽(p) < ∞` and `𝖽(p) > 0` a.e., stated only as "where `𝖽(p) > 0`". The
whole section is therefore a **conditional construction whose hypothesis has no verified instance**.
**Fix:** label it "Proposed construction" and state the three missing hypotheses (existence of the
contraction, symmetry, `0 < 𝖽 < ∞` a.e.) as standing assumptions.

Spectral dimension: `Θ(t) = Tr(e^{−tΔ_𝒫})` requires trace class — stated as a hypothesis ✓;
`Θ(t) ∼ Ct^{−d_s/2}` as `t ↓ 0` and `d_s = −2 lim d log Θ/d log t` — the manuscript's own remark
"Existence of this limit is an additional hypothesis, not an automatic consequence of the ternary
kernel" is correct and sufficient ✓. **Keep.**

### 3.9 Stiefel geometry — **standard consequence requiring citation**

`St(d,r) = {Q : Q*Q = I_r}`, `T_Q St = {Z : Q*Z + Z*Q = 0}`,
`grad 𝔈(Q) = G − Q sym(Q*G)` ✓ all correct and standard. **No citation is given** (manuscript 02 has
no bibliography at all). Must cite a standard reference for the canonical/Euclidean-metric
Riemannian gradient on the Stiefel manifold, and state which metric is meant — the formula given is
the one for the **embedded Euclidean metric**, and that must be said, since the canonical metric
gives a different gradient.

### 3.10 Multiscale transport defects — **definitions only, correctly labelled**

`𝒟_μ^{N,M} = J_N^M μ_N − μ_M(J_N^M·,…,J_N^M·)` and `𝒟_P^{N,M} = P_M J_N^M − J_N^M P_N` are
definitions; no theorem is asserted. The accompanying remark — that a finite decreasing sequence does
not establish a continuum limit, and that one would additionally need topologies, uniform bounds,
compactness, convergence of laws and projectors, stability of identities, and identification of the
limit — is correct and is the right standard. **Keep verbatim.**

---

## 4. Where the four criteria of §9.10–9.12 are violated in the current text

| Criterion | Violation | Location |
| --- | --- | --- |
| equality vs. upper bound | The abstract writes `E^{amb} ≤ kρM^{k−1}L` and `E^P = E^{red} ≤ (k−1)ρM^{k−1}L` on one line; the middle `=` is an **exact identity** (Prop. root geometry) and the outer `≤` is a bound. Readable as one chained relation. | 01 abstract; 01 §Homogeneous universal bounds; 02 Thm. `kk1` |
| upper bound vs. sharp constant | "A gated planar-rotation construction **matches the ambient coefficient** in registered cells" — true, but juxtaposed with the theorem it reads as sharpness. It is sharpness *of the ambient coefficient, in specific cells*, at specific `η`. | 01 abstract |
| lower construction vs. global optimum | `certified_lower_bound = 0.0` in 1794 of 9945 rows is reported through the aggregate "maximum unresolved relative gap 1"; a lower bound of `0` for a nonnegative quantity is **vacuous**, not a construction. | 01 abstract; `artifacts/index/optimality_gaps_v3.csv` |
| upper bound vs. sharp constant | "Directed interval calculations certify 60 small cells globally." Of the 60 rows with `global_optimum_certified = True` in `artifacts/research_v3/block_A_exact_atlas.csv`, **30 are projected-error cells with lower = upper = 0** — the `k = 1` case, where the theorem itself proves `E^{proj} = 0`. Half the "globally certified" cells are the case the theorem makes trivial. | 01 abstract |

---

## 5. Defect in the evidence taxonomy that reaches the manuscript

`scripts/tree_constants_v3_pipeline.py:438-444`:

```python
def _exact_status(lower: float, upper: float) -> str:
    if upper == 0.0 and lower == 0.0:
        return "EXACT_OPTIMAL_CONSTANT"
    relative = (upper - lower) / upper if upper else 0.0
    if relative <= 1.0e-10:
        return "NEAR_OPTIMAL_WITH_CERTIFIED_GAP"
    return "CERTIFIED_UPPER_BOUND_AND_CERTIFIED_LOWER_BOUND"
```

Measured consequence in `artifacts/index/optimality_gaps_v3.csv` (9945 rows):

| Situation | Rows | Label assigned | Correct reading |
| --- | ---: | --- | --- |
| `lower = upper = 0` (trivial `k=1` projected case) | 30 | `EXACT_OPTIMAL_CONSTANT` | The constant is zero **by the theorem**. Not an optimisation result. |
| `lower = upper = 1 > 0` (genuinely determined) | 45 | `NEAR_OPTIMAL_WITH_CERTIFIED_GAP` | These are the **exactly determined** cases. Mislabelled. |
| `lower = 0 < upper` (no positive lower bound at all) | 1794 | `CERTIFIED_UPPER_BOUND_AND_CERTIFIED_LOWER_BOUND` | A "certified lower bound" of `0` for a nonnegative quantity is **vacuous**. |

**The label is inverted for the 45 genuinely exact cases and misleading for the 1794 vacuous ones.**
This propagates into manuscript 01's Table `optimality_gaps` (which reports `exact` and `near` counts
per error type) and into the abstract's `\VThreeExactCells` and `\VThreeMaxRelativeGap`.

**Fix required before the numerical tables can be published.** Two options, both requiring the
author's decision because they change reported numbers:
(a) correct `_exact_status` and regenerate the tables; or
(b) leave the data untouched and relabel in the manuscript, adding a footnote defining each state.
Option (a) is the honest one. Either way the three-way distinction of
`02_notation_and_conventions.md` §2.4 must be used.

---

## 6. Open problems, restated in academic prose

These remain open. Nothing in this audit narrows any of them.

1. **Exact projected constant at fixed `η > 0`.** `C_𝔗^{proj}(η) ≤ k−1` is proved;
   `C_𝔗^{proj}(η) = k−1` is not. For two internal vertices the exact constant is known for part of
   the admissible parameter range only — 6 of 75 homogeneous gated-rotation configurations attain the
   bound, with gaps elsewhere from `3.75×10⁻⁷` (as `η → 0`) to `1`. For three internal vertices no
   configuration or error type attains optimality; the projected gap floor is 35 %.
   *(Replaces `OPEN_K2_WITH_CERTIFIED_GAP` and `OPEN_K3_WITH_CERTIFIED_TOPOLOGY_GAPS`.)*

2. **Whether ambient dimension or projector rank can improve on embedded planar constructions.** The
   two-dimensional gated-rotation family embeds isometrically into larger spaces, preserving its
   value; whether additional coordinates ever help is unknown.

3. **Cancellation-aware constants for signed forests.** Partially addressed: for the Jacobiator the
   plain triangle bound is empirically not improvable (ratio 0.994) — a genuine negative result for
   that case; the five-input ternary associator (0.686) and Filippov identity (0.416) have improved
   lower bounds but remain open; the declared six-term GJI variant evaluated at machine-precision
   zero in all 4000 trials and five reseeded checks under both leaf-input conventions, and may be an
   identically vanishing expression — symbolic verification required before it is used as a
   diagnostic.

4. **Domination relations among the state-resolved, pathwise, and order-optimised bounds.** No
   ordering is proved; the reported ratios are medians on shared instances.

5. **Validated spectral-norm certificates for general tensors at useful scale.** Frobenius upper
   bounds are currently used where the exact multilinear operator norm is unavailable, which inflates
   `M` and hence every constant.

6. **Analytic extensions.** Continuum limits, `Ψ⁰` membership, microlocal regularity, `D`-modules and
   the Riemann–Hilbert correspondence, and algebraisation of the limiting projector are **not
   results and not consequences**. Manuscript 02 lists them under "Open" and must present them in a
   section titled *Open analytical questions*, with no forward-looking claim.

7. **Originality.** Not assessed. A bounded search found no verbatim match for the projected-root,
   state-resolved, and pathwise formulations; absence from a bounded search is not evidence of
   novelty. Requires the expert comparison of §14 of the governing instruction.

---

## 7. A cross-manuscript conflation that must not be created

Manuscript 01 asks whether the coefficient `k−1` in the **projected-error bound** is sharp.
Manuscript 03 block H reports that the constant `2` in `‖A(x,y,z)‖ ≤ 2\hat M²‖x‖‖y‖‖z‖` is
"empirically far from sharp" (max observed ratio 0.452; across the 416-cell sweep, 0.130–0.957 with
mean 0.334, decreasing monotonically in `n` from 0.40 at `n = 12` to 0.11 at `n = 96`).

**These are different questions about different quantities.** 03's is a plain triangle bound on the
norm of an associator of a *single* law, with no projection anywhere. 01's is a bound on the
*projected error of a signed forest under recursive projection*. The numeral `2` appears in both by
coincidence of `1+1 = 2` and `‖A‖ ≤ ‖μ∘μ‖ + ‖μ∘μ‖`. Any rewritten text that cites one as evidence
about the other would violate §5 of the governing instruction. Both papers currently keep them
apart — manuscript 03's `\thanks` explicitly declares the tree track out of scope. **Preserve that
separation.**
