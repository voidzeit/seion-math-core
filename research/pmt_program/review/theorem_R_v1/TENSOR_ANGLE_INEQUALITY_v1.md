# The tensor angle inequality — standalone statement, v1

Frozen 2026-09-13 with `REVIEW_PACKAGE_v1.md` (Theorem T there). Status
`ADVISORY_PROOF_DRAFT`. Self-contained: it uses no PMT notation. Novelty not
established; the angle-addition mechanism is related to the scaled relative
graph calculus of Ryu–Hannah–Yin (arXiv:1902.09788), and the precise relation
still has to be checked.

## Statement

For real Hilbert spaces `H_1,…,H_m`, the projective norm of
`T ∈ H_1 ⊗ ⋯ ⊗ H_m` is

```
‖T‖_π = inf{ Σ_j |c_j| : T = Σ_j c_j x^j_1 ⊗ ⋯ ⊗ x^j_m, ‖x^j_i‖ = 1 }
      = sup{ W(T) : W m-linear, |W(x_1,…,x_m)| ≤ ∏‖x_i‖ }.
```

**Theorem T.** Let `u_i, v_i ∈ H_i` be unit vectors, `ψ_i := ∠(u_i,v_i) ∈ [0,π]`
and `S := Σ_i ψ_i`. Then for all real `a, b` with `ab ≤ 0`:

```
‖a · u_1⊗⋯⊗u_m + b · v_1⊗⋯⊗v_m‖_π ≤ |a e^{i min(S,π)} + b|.
```

Equivalently, for `t ≥ 0`: `‖⊗u_i − t⊗v_i‖_π² ≤ 1 + t² − 2t cos(min(S,π))`.

**Sharpness.** If `S ≤ π`, equality holds for every choice of the `u_i, v_i` and
every `t ≥ 0`.

## Proof of the inequality

*Reductions.*

* **Homogeneity.** Take `a = 1`, `b = −t` with `t ≥ 0`. (For `a < 0` negate
  both; for `a = 0` the claim is `|b| ≤ |b|`.)
* **Large angle sum.** If `S ≥ π` the right side is `1 + t`: this is the
  triangle inequality. So assume `S < π`; then every `ψ_i < π`.
* **Dimension.** If some `H_i` has dimension `1`, embed it isometrically in
  `ℝ²`. Projective norms of Hilbert factors are preserved under isometric
  embeddings: a form on the original spaces extends, precomposed with the
  orthogonal projections, to a form of the same norm, and conversely forms
  restrict. The right side is unchanged. So assume `dim H_i ≥ 2`.

*Induction on `m`.*

**Base case `m = 1`.** `‖u − tv‖² = 1 + t² − 2t cos ψ_1`.

**Inductive step `m ≥ 2`.**

1. **Split off the first factor.** Put `X := u_2⊗⋯⊗u_m` and
   `Y := v_2⊗⋯⊗v_m` in `E := H_2⊗_π⋯⊗_π H_m`, and `S' := S − ψ_1 ∈ [0,π)`.
   By associativity of the projective tensor product,
   `‖u_1⊗X − tv_1⊗Y‖_π = sup_β [β(u_1,X) − tβ(v_1,Y)]`, where `β` ranges over
   bilinear forms on `H_1 × E` with `|β(z,W)| ≤ ‖z‖‖W‖_π`.
2. **Riesz map.** Fix such a `β` and a 2-dimensional subspace `Π ⊆ H_1`
   containing `u_1` and `v_1`. By Riesz there is a linear `Λ : E → Π` with
   `β(z,W) = ⟨z, ΛW⟩` for `z ∈ Π`, and `‖ΛW‖ ≤ ‖W‖_π`.
3. **Apply the inductive hypothesis.** Put `p := ΛX` and `q := ΛY`. For
   `αβ' ≤ 0`, `‖αp + β'q‖ ≤ ‖αX + β'Y‖_π ≤ |αe^{iS'} + β'|`. This is condition
   (N−) with angle `S'`.
4. **Planar domination** (Lemma B of the package, reproduced here).
   * Write `G := Gram(p,q)` and `μ := √((1−G_11)(1−G_22))`.
   * (N−) is equivalent to `G_12 + μ ≥ cos S'`.
   * Pick `cos ψ̃ ∈ [G_12 − μ, G_12 + μ] ∩ [cos S', 1]`. This set is nonempty
     since `G_12 − μ ≤ 1`.
   * Then `ψ̃ ∈ [0, S']` and `Gram(p,q) ⪯ Gram(p̂,q̂)` for unit `p̂, q̂` at
     angle `ψ̃`.
   * Hence there is a linear `C` with `‖C‖ ≤ 1`, `Cp̂ = p` and `Cq̂ = q`
     (define it on the span; it is well defined and contractive by the Gram
     inequality).
5. **Rotate.** Let `Rot` be the rotation of `Π` with `Rot v_1 = u_1`, by angle
   `ψ_1`. Then `⟨v_1, q⟩ = ⟨u_1, Rot q⟩`, so

   ```
   β(u_1,X) − tβ(v_1,Y) = ⟨u_1, Cp̂ − t·Rot Cq̂⟩ ≤ ‖Cp̂ − t·Rot Cq̂‖.
   ```

6. **Dilate.** Let `V := (C, (I − C^*C)^{1/2})`. It is an isometry into
   `Π ⊕ D`. Put `R̃ := Rot ⊕ I_D`.
   * `R̃` is an isometry, and `⟨w, R̃w⟩ = ‖w_Π‖² cos ψ_1 + ‖w_D‖² ≥ cos ψ_1`
     for unit `w`. So `∠(w, R̃w) ≤ ψ_1`.
   * The `Π`-component of `Vp̂ − tR̃Vq̂` is `Cp̂ − t·Rot Cq̂`, so the last
     quantity in step 5 is `≤ ‖Vp̂ − tR̃Vq̂‖`.
7. **Conclude.** `‖Vp̂‖ = 1`, `‖tR̃Vq̂‖ = t`, and
   `∠(Vp̂, R̃Vq̂) ≤ ∠(Vp̂,Vq̂) + ∠(Vq̂,R̃Vq̂) ≤ ψ̃ + ψ_1 ≤ S < π`. Therefore
   `‖Vp̂ − tR̃Vq̂‖² ≤ 1 + t² − 2t cos S`.

Take the supremum over `β`. `□`

## Proof of sharpness (`S ≤ π`)

1. **Coordinates.** In each factor pick a 2-dimensional `Π_i ∋ u_i, v_i` and
   identify `Π_i ≅ ℂ` isometrically, with `v_i ↦ 1` and `u_i ↦ e^{iψ_i}`
   (choose the orientation). Let `π_i` be the orthogonal projection onto
   `Π_i`, read as a complex number, so `|π_i x| ≤ ‖x‖`.
2. **The form.** For `|λ| = 1` put `W(x_1,…,x_m) := Re(λ ∏_i π_i x_i)`. It is
   real `m`-linear with `|W| ≤ ∏‖x_i‖`.
3. **Evaluate.**
   `W(⊗u_i) − tW(⊗v_i) = Re(λ(e^{iS} − t))`. Choosing `λ` gives
   `|e^{iS} − t| = |1 − te^{iS}|`. `□`

For `S > π` the bound `1 + t` is only the triangle inequality, and equality is
not claimed.

## Remarks

* **`m = 2`.** For real `2×2` matrices `K = uu'ᵀ − tvv'ᵀ`, the statement is
  `‖K‖_*² = ‖K‖_F² + 2|det K| = 1 + t² − 2t cos(ψ_1 + ψ_2)`.
* **The sign condition `ab ≤ 0` is essential.** For `ab > 0` the natural bound
  involves `cos(ψ_1 − ψ_2)`, not `cos S`.
* **Numerical control.** A cutting-plane LP evaluation of `‖·‖_π` over random
  unequal angles and `t ∈ [0,2]` (`m = 2`: 120 cases, `m = 3`: 80, `m = 4`: 12)
  finds the LP upper value within `1.6·10⁻⁷` of the bound
  (`lemma3/tensor_angle_lp.py`).
* **Complex spaces.** For complex spaces with complex-multilinear forms the
  inequality follows by realification, since a complex-multilinear form of norm
  `≤ 1` is a real-multilinear form of norm `≤ 1` on the realified spaces. That
  gives the upper bound; sharpness over `ℂ` is not claimed.
