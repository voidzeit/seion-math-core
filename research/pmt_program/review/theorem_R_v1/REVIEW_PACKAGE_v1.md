# Topology independence of the sharp projected-error constant — review package v1

**Frozen for review on 2026-09-13.** Mathematical source:
`research/pmt_program/THEOREM_R_DRAFT.md` at commit
`f80f4e8825e991252160e60eb693bc08dd07b9a7` (copy: `THEOREM_R_DRAFT_v1.md`).
This package restates the same proof with every step as an explicit lemma, all
hypotheses listed, and all degenerate cases handled inline. Any correction
produces `v2`; this file is not edited after the freeze (checksums in
`FREEZE_v1.json`).

Status: **ADVISORY_PROOF_DRAFT**. Author-side audit only (`AUDIT_v1.md`); no
independent review yet. Novelty not established.

The reader needs nothing else from the repository.

---

## 0. Setting

### 0.1 Class PMT-A (real)

* `T` is a finite rooted tree. `V_int` are its internal vertices,
  `k := |V_int| ≥ 1`, and `r` is the root.
* Every vertex `w` carries a finite-dimensional **real** Hilbert space `H_w`.
* Every internal `v` carries an orthogonal projector `P_v = P_v² = P_v^*`
  (any rank, including `0` and full), with `Q_v := I − P_v`.
* Every internal `v` carries a multilinear law `μ_v` on the spaces of its
  children (leaves or internal vertices), with multilinear operator norm
  `‖μ_v‖ := sup{‖μ_v(x_1,…)‖ : ‖x_i‖ ≤ 1} ≤ M`.
* Leaves carry data `z_ℓ ≠ 0`. Put `F_ℓ = R_ℓ = z_ℓ`, and for internal `v`:
  `F_v = μ_v(F_children)` and `R_v = P_v μ_v(R_children)`.
* Projected error: `E^P_T := ‖P_rF_r − R_r‖`.
* **Closure.** `‖Q_v μ_v(x_1,…)‖ ≤ ρ ∏‖x_i‖` whenever each argument in an
  internal-child slot lies in that child's `Ran P`. Arguments in leaf slots are
  arbitrary. Here `0 < ρ ≤ M` and `η := ρ/M`.
* `C^P_T(η) := sup E^P_T / (ρ M^{k−1} ∏‖z_ℓ‖)` over all admissible
  realizations, all dimensions and all ranks.

### 0.2 The target constant

```
w(θ) := cos θ · e^{iθ},       C_k(η) := max_{0 ≤ θ ≤ arcsin η} |1 − w(θ)^{k−1}| / η.
```

**Theorem R.** For every finite rooted tree `T` with `k` internal vertices and
every `η ∈ (0,1]`: `C^P_T(η) = C_k(η)`.

### 0.3 Normalizations used throughout

**N1 (scaling).** Scaling all laws by `λ` and leaves by `ν_ℓ` leaves the ratio
invariant, so we take `M = 1`, `ρ = η` and unit leaves.

**N2 (leaf freezing).** Fix the leaf arguments of every law at the (unit) leaf
data. This gives, at each internal `v` with internal children `c_1,…,c_m`
(`m ≥ 0`), a multilinear map on the internal slots. It has norm `≤ 1`, the
evaluations are unchanged, and it satisfies the **trajectory closure**

```
(TC)   ‖Q_v μ_v(R_{c_1},…,R_{c_m})‖ ≤ η ∏_i ‖R_{c_i}‖
```

because `R_{c_i} ∈ Ran P_{c_i}` and the leaf values are admissible leaf-slot
inputs. For `m = 0`, `μ_v` is a vector `f_v` with `‖f_v‖ ≤ 1` and
`‖Q_vf_v‖ ≤ η`.

**The upper bound below uses only: norms `≤ 1`, orthogonality of each `P_v`,
and (TC).**

### 0.4 Notation

For `ρ ≥ 0` and `ψ ∈ [0,π]`:

```
K(ρ,ψ) := [[1, ρ cos ψ], [ρ cos ψ, ρ²]]     (Gram matrix of a unit vector and a vector of norm ρ at angle ψ).
```

`∠(a,b) := arccos(⟨a,b⟩/(‖a‖‖b‖)) ∈ [0,π]`; this is a metric on the unit
sphere, so the triangle inequality for angles holds. `⪯` is the Löwner order.
`‖·‖_π` is the projective tensor norm, dual to the multilinear operator norm.

---

## 1. Lower bound

**Theorem U.** `C^P_T(η) ≥ C_k(η)` for every `T` and `η`.

*Hypotheses used:* none beyond PMT-A.

*Construction.* Take all spaces `ℝ² ≅ ℂ`, leaves `e_0 = 1`, and every `P_v`
the orthogonal projection onto `ℝ`. Fix `θ ∈ [0, arcsin η]`.

* **Non-root internal `v`:**
  `μ_v(x_1,…) := e^{iθ} · ∏_{internal slots} x_i · ∏_{leaf slots} ⟨x_j, e_0⟩`
  (product in `ℂ`). Its norm is `1`. On projected internal inputs and
  arbitrary leaf inputs every factor is real, so the output is
  `e^{iθ}·(real)` and the closure defect equals `sin θ ≤ η`.
* **Induction.** `F_v = e^{i k_v θ}` and `R_v = cos^{k_v} θ`, where `k_v` is the
  number of internal vertices in the subtree of `v`.
* **Root:** `μ_r(x) := Re(λ ∏x_i ∏⟨x_j,e_0⟩)·e_0` with `|λ| = 1`. Its norm is
  `1` and its closure defect is `0`. It gives
  `E^P_T = |Re(λ(e^{i(k−1)θ} − cos^{k−1}θ))|`, which equals
  `|1 − w(θ)^{k−1}|` for a suitable `λ`.

Maximize over `θ`. `□`

---

## 2. Upper bound: the lemmas

### Definition (domination)

A pair `(F,R)` of vectors in a real Hilbert space is **dominated by
`(ρ, χ)`**, with `ρ ≥ 0` and `χ ≥ 0`, if

```
Gram(F,R) ⪯ K(ρ,ψ)   for some ψ ∈ [0, min(χ, π)].
```

### Lemma A (contraction realization)

*Hypotheses:* `Gram(F,R) ⪯ K(ρ,ψ)`, with `ρ ≥ 0` and `ψ ∈ [0,π]`.

*Conclusion:* Let `X` be a 2-dimensional real Hilbert space with unit vectors
`F̂, R̂`, `∠(F̂,R̂) = ψ`. There is a linear map `B : X → H` with `‖B‖ ≤ 1`,
`BF̂ = F` and `B(ρR̂) = R`. In particular `‖F‖ ≤ 1` and `‖R‖ ≤ ρ`.

*Proof.* For real `α, β`:
`‖αF + βR‖² = (α,β)Gram(F,R)(α,β)ᵀ ≤ (α,β)K(ρ,ψ)(α,β)ᵀ = ‖αF̂ + βρR̂‖²`.

* **Definition on the span.** Put `B(αF̂ + βρR̂) := αF + βR`. This is well
  defined, since `αF̂ + βρR̂ = 0` forces `αF + βR = 0`. It is contractive on
  `span{F̂, ρR̂}`.
* **Extension.** Extend `B` by `0` on the orthogonal complement of that span
  in `X`. Then `‖B‖ ≤ 1`.
* **Degenerate cases.** This covers `ρ = 0` (then `R = 0`) and
  `ψ ∈ {0, π}` (then `R = ±ρF`).

The two norm bounds are the diagonal entries of the Löwner inequality. `□`

### Lemma B (planar domination: (N−) ⟹ domination) — *danger point 1*

*Hypotheses:* `f, g` lie in a real Hilbert space, `S ∈ [0, π]`, and

```
(N−)   ‖af + bg‖ ≤ |a e^{iS} + b|    for all real a, b with ab ≤ 0.
```

*Conclusion:* `Gram(f,g) ⪯ K(1,ψ)` for some `ψ ∈ [0, S]`.

*Proof.* Write `G := Gram(f,g)`.

1. Taking `b = 0`, then `a = 0`, gives `G_11 ≤ 1` and `G_22 ≤ 1`. Put
   `A := 1 − G_11 ≥ 0`, `B' := 1 − G_22 ≥ 0`, `μ := √(AB')`.
2. Since `|ae^{iS} + b|² = a² + b² + 2ab cos S`, (N−) is equivalent to
   `a²A + b²B' − 2|ab|(cos S − G_12) ≥ 0` for all `a, b`.
   For fixed `|a|, |b|` this is a quadratic form in `(|a|, |b|)`, so it holds
   for all `a, b` iff `cos S − G_12 ≤ μ`, that is
   **`G_12 + μ ≥ cos S`**. (If `cos S − G_12 ≤ 0` there is nothing to prove.
   Otherwise, minimizing over the ratio `|a|:|b|` gives the condition, and this
   includes `A = 0` or `B' = 0`.)
3. `K(1,ψ) − G` has diagonal `(A, B') ≥ 0`. So it is `⪰ 0` iff
   `(cos ψ − G_12)² ≤ μ²`, i.e. `cos ψ ∈ I := [G_12 − μ, G_12 + μ]`.
4. `I ∩ [cos S, 1] ≠ ∅`:
   * `G_12 − μ ≤ |G_12| ≤ √(G_11 G_22) ≤ 1`;
   * `cos S ≤ G_12 + μ` by step 2.
5. Choose `cos ψ ∈ I ∩ [cos S, 1]`. Then `ψ := arccos(cos ψ) ∈ [0, S]`, because
   `S ≤ π` and `arccos` is decreasing. `□`

*Remark.* (N−) bounds the alignment `G_12` only from below. Any excess
alignment is absorbed by choosing `ψ < S`.

### Theorem T (tensor angle inequality) — *danger point 2*

Stated and proved in full in `TENSOR_ANGLE_INEQUALITY_v1.md`, where sharpness
is also shown. Statement:

*Hypotheses:* `m ≥ 1`; unit vectors `u_i, v_i` in real Hilbert spaces `H_i`;
`ψ_i := ∠(u_i,v_i)`; `S := Σψ_i`; real `a, b` with `ab ≤ 0`.

*Conclusion:*

```
‖a · u_1⊗⋯⊗u_m + b · v_1⊗⋯⊗v_m‖_π ≤ |a e^{i min(S,π)} + b|.
```

### Lemma C (child substitution and closure normalization) — *danger point 3*

*Hypotheses:*

1. `v` is internal with internal children `c_1,…,c_m`, `m ≥ 1`.
2. `μ_v` has norm `≤ 1` and satisfies (TC).
3. Each `(F_{c_i}, R_{c_i})` is dominated by `(ρ_i, χ_i)`, via some
   `ψ_i ∈ [0, min(χ_i,π)]`.

*Conclusion:* Let `X_i` be a 2-dimensional space with unit `F̂_i, R̂_i` at
angle `ψ_i`, and let `B_i` be as in Lemma A. Put
`μ'(x_1,…,x_m) := μ_v(B_1x_1,…,B_mx_m)` on `X_1 × ⋯ × X_m`, and
`ρ := ∏ρ_i`. Then:

* (i) `‖μ'‖ ≤ 1`;
* (ii) `F_v = μ'(F̂_1,…,F̂_m)`, and `μ_v(R_{c_1},…) = ρ·μ'(R̂_1,…,R̂_m)`;
* (iii) if `ρ > 0`, then `‖Q_v μ'(R̂_1,…,R̂_m)‖ ≤ η`;
* (iv) if `ρ = 0`, then `μ_v(R_{c_1},…) = 0`.

*Proof.*

* (i) Composition with contractions.
* (ii) Multilinearity and `B_i(ρ_iR̂_i) = R_{c_i}`.
* (iii) By (ii) and (TC),
  `‖Q_vμ'(R̂)‖ = ‖Q_vμ_v(R_c)‖/ρ ≤ η∏‖R_{c_i}‖/ρ ≤ η`, using
  `‖R_{c_i}‖ ≤ ρ_i` (Lemma A). Only the trajectory `R̂_i` is used, and it is
  exactly what (TC) controls.
* (iv) Some `ρ_i = 0`, so `R_{c_i} = 0` by Lemma A. `□`

### Lemma D (propagation through a non-root vertex; "Lemma 3")

*Hypotheses:* the hypotheses of Lemma C for a non-root internal `v`, with
`m ≥ 0`. For `m = 0` there is nothing to assume.

*Conclusion:* There is `θ_v ∈ [0, arcsin η]` such that `(F_v, R_v)` is
dominated by

```
(ρ_v, χ_v) := (cos θ_v · ∏ρ_i,  θ_v + Σχ_i)      (empty product 1, empty sum 0).
```

*Proof.*

*Case `ρ := ∏ρ_i = 0`* (only possible for `m ≥ 1`). By Lemma C(iv),
`R_v = P_v·0 = 0`, and `‖F_v‖ ≤ ∏‖F_{c_i}‖ ≤ 1`. So
`Gram(F_v,0) = diag(‖F_v‖², 0) ⪯ K(0, 0)`. Take `θ_v = 0`; then `ρ_v = 0` and
`0 ≤ χ_v`.

*Case `ρ > 0`.*

1. **Raw output.** Put `f := μ'(F̂_1,…)` and `g := μ'(R̂_1,…)`, so `F_v = f` and
   `R_v = ρP_vg`. For `m = 0`, put `f = g := f_v`, `ρ := 1` and `S := 0`.
   Otherwise put `S := Σψ_i`.
2. **(N−) with `S' := min(S,π)`.**
   * `m = 0`: `‖af + bg‖ = |a+b|‖f_v‖ ≤ |a+b|`.
   * `m ≥ 1`: for `ab ≤ 0`,
     `‖af + bg‖ = sup_{‖ω‖≤1}⟨ω, μ'(a⊗F̂ + b⊗R̂)⟩ ≤ ‖a⊗F̂ + b⊗R̂‖_π ≤ |ae^{iS'} + b|`,
     by Lemma C(i) and Theorem T.
3. **Domination of the raw output.** Lemma B gives `ψ̃ ∈ [0, S']` with
   `Gram(f,g) ⪯ K(1,ψ̃)`. Lemma A gives `C : Y → H_v`, `‖C‖ ≤ 1`, with
   `CF̂' = f` and `CÊ' = g` for unit `F̂', Ê'` at angle `ψ̃`.
4. **Dilation.** Let `V := (C, (I − C^*C)^{1/2}) : Y → H_v ⊕ Y`. It is an
   isometry. Put `P' := P_v ⊕ I` and `Q' := I − P' = Q_v ⊕ 0`. Define
   `F̃ := VF̂'` and `R̃ := ρP'VÊ'`. Their `H_v`-components are `CF̂' = F_v` and
   `ρP_vCÊ' = R_v`. Coordinate projection is a contraction, so
   `Gram(F_v,R_v) ⪯ Gram(F̃,R̃)`.
5. **Norms.** `‖F̃‖ = 1`. `‖VÊ'‖ = 1` and
   `‖Q'VÊ'‖ = ‖Q_vg‖ ≤ η` by Lemma C(iii) (for `m = 0`, by N2). Define
   `θ_v := arcsin‖Q_vg‖ ∈ [0, arcsin η]`. Then `‖R̃‖ = ρ cos θ_v = ρ_v`.
6. **Angle.**
   * If `R̃ = 0`, then `ρ_v = 0` and `Gram(F̃,R̃) = K(0,0)`: dominated.
   * Otherwise `∠(F̃,R̃) ≤ ∠(VF̂', VÊ') + ∠(VÊ', P'VÊ') = ψ̃ + θ_v`. The first
     angle is preserved by the isometry. The second is `θ_v`, since
     `⟨y, P'y⟩ = ‖P'y‖²` and `‖P'y‖ = cos θ_v` for the unit vector
     `y = VÊ'`.
   * Hence `Gram(F̃,R̃) = K(ρ_v, ∠(F̃,R̃))` with
     `∠ ≤ min(ψ̃ + θ_v, π) ≤ min(χ_v, π)`, because `ψ̃ ≤ S' ≤ Σχ_i`.
7. Steps 4 and 6 give the claim. `□`

### Lemma E (root reading)

*Hypotheses:* the root `r` has internal children `c_1,…,c_m`, `m ≥ 1`; each
`(F_{c_i}, R_{c_i})` is dominated by `(ρ_i, χ_i)`; `‖μ_r‖ ≤ 1`. No closure is
needed at the root.

*Conclusion:* With `ρ := ∏ρ_i` and `S := Σψ_i` (the `ψ_i` from the
dominations),

```
E^P_T ≤ |1 − ρ e^{i min(S,π)}|.
```

*Proof.* `E^P_T = ‖P_r(μ_r(F_c) − μ_r(R_c))‖`, because
`R_r = P_rμ_r(R_c)`. Substitute the children as in Lemma C(i)–(ii); this does
not use (TC). Then

```
E^P_T = ‖P_r μ'(⊗F̂ − ρ⊗R̂)‖ ≤ ‖⊗F̂ − ρ⊗R̂‖_π ≤ |1 − ρ e^{i min(S,π)}|
```

by Theorem T with `a = 1`, `b = −ρ`. If `ρ = 0`, the bound is `1 ≥ E^P_T`,
since `R_c = 0` and `‖F_c‖ ≤ 1`. `□`

### Lemma F (angle bookkeeping) — *danger point 4*

*Hypotheses:* Lemma D is applied to every non-root internal vertex, children
before parents, and Lemma E at the root.

*Conclusion:* There are angles `θ_u ∈ [0, arcsin η]`, one for each of the
`k − 1` non-root internal vertices `u`, such that

```
(E^P_T)² ≤ 1 + ρ² − 2ρ cos(min(Θ, π)),     ρ = ∏_{u ≠ r} cos θ_u,   Θ = Σ_{u ≠ r} θ_u.
```

*Proof.* By induction over the tree, using Lemma D:

* `ρ_v = ∏_{u ∈ V_int(T_v)} cos θ_u`;
* `χ_v = Σ_{u ∈ V_int(T_v)} θ_u`,

where `T_v` is the subtree rooted at `v`. At a leaf-only vertex (`m = 0`) these
are `cos θ_v` and `θ_v`. The subtrees of the root's internal children are
pairwise disjoint and their internal vertices are exactly `V_int ∖ {r}`
(tree property: each vertex has one parent). So `∏ρ_{c_i} = ρ` with exactly
`k − 1` factors, and `S = Σψ_i ≤ Σχ_{c_i} = Θ`.

Lemma E gives `(E^P_T)² ≤ 1 + ρ² − 2ρ cos(min(S,π))`. This is
`≤ 1 + ρ² − 2ρ cos(min(Θ,π))`, since `ρ ≥ 0` and `cos` decreases on
`[0,π]`. `□`

### Lemma G (scalar step)

*Hypotheses:* `n ≥ 1`, `θ_1,…,θ_n ∈ [0, arcsin η]`, `ρ = ∏cos θ_j`,
`Θ = Σθ_j`.

*Conclusion:* `1 + ρ² − 2ρ cos(min(Θ,π)) ≤ max_{0≤θ≤arcsin η} |1 − w(θ)^n|²`.

*Proof.*

*Case `Θ ≤ π`.*

1. **Upper bound on `ρ`.** If some `θ_j = π/2`, then `ρ = 0` and the left side
   is `1 = |1 − w(π/2)^n|²`, where `π/2 = arcsin 1` (this needs `η = 1`).
   Otherwise all `θ_j < π/2`, and by concavity of `log cos` on `[0, π/2)`,
   `ρ ≤ b := cos^n(Θ/n)`.
2. **Lower bound on `ρ`.** `cos(A + B) = cos A cos B − sin A sin B ≤ cos A cos B`
   for `A ∈ [0,π]` and `B ∈ [0,π/2]`. Iterating, and multiplying by
   `cos θ_j ≥ 0` at each step, gives `ρ ≥ cos Θ`.
3. **Monotonicity.**
   `(b² − ρ²) − 2 cos Θ (b − ρ) = (b − ρ)(b + ρ − 2 cos Θ) ≥ 0`. If
   `cos Θ ≤ 0` this is clear; otherwise use `b ≥ ρ ≥ cos Θ`.
4. **Conclusion.** The left side is at most
   `1 + b² − 2b cos Θ = |1 − w(Θ/n)^n|²`, and `Θ/n ≤ arcsin η`.

*Case `Θ > π`* (only possible when `n ≥ 3`). The left side is `(1 + ρ)²`. If
all `θ_j < π/2`, then `ρ ≤ cos^n(Θ/n) ≤ cos^n(π/n)`, since `π/n < Θ/n < π/2`.
If some `θ_j = π/2`, then `ρ = 0`. Also
`(1 + cos^n(π/n))² = |1 − w(π/n)^n|²`, because `w(π/n)^n = −cos^n(π/n)`, and
`π/n < Θ/n ≤ arcsin η`. `□`

---

## 3. Theorem R

*Proof.*

* **Lower bound:** Theorem U.
* **Upper bound:** normalize by N1 and N2.
  * If `k = 1`, then `R_r = P_rF_r` and `E^P_T = 0`.
  * If `k ≥ 2`, apply Lemmas D, E, F and G with `n = k − 1`. This gives
    `E^P_T ≤ max_θ |1 − w(θ)^{k−1}| = η C_k(η)`.

Undo the normalization. `□`

## 4. Scope statements (not part of the theorem)

* The upper bound holds in the larger class defined by (TC) alone.
* Complex spaces with complex-multilinear laws: the upper bound should follow
  by realification. This is **not covered by this package** and is not
  claimed here. The lower bound over `ℂ` for trees with a vertex having ≥ 2
  internal children is open.
* DAGs, shared laws, fixed ranks and oblique projectors are outside PMT-A.

## 5. Numerical controls (not premises)

`research/pmt_program/lemma3/LEMMA3_CAMPAIGN.md`:

* 344 000 random vertex cases;
* adversarial search;
* LP checks of Theorem T for `m = 2, 3, 4`;
* 3 000 random trees.

`AUDIT_v1.md`: 6 000 degenerate edge cases. No counterexample in any of them.
