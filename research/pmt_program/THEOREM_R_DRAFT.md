> **Superseded** by `review/theorem_R_v2/THEOREM_R_v2.md` (canonical, 2026-09-13). Kept unchanged below for provenance.

# Theorem R (topology independence) — proof draft

Status: **ADVISORY_PROOF_DRAFT** (2026-09-13). Not independently reviewed. It
supersedes, if correct, the case analyses of `K4_TOPOLOGY.md` §3.3–3.4 and the
"Conjecture R" status in `RECURSION.md`. Numerical falsification of its two new
ingredients is recorded in `lemma3/LEMMA3_CAMPAIGN.md`.

**Theorem R.** For every finite ordered rooted tree `T` with `k` internal
vertices and every `η ∈ (0,1]`,

```
C^P_T(η) = C_k(η) := max_{0 ≤ θ ≤ arcsin η} |1 − (cos θ · e^{iθ})^{k−1}| / η     (class PMT-A).
```

The upper bound holds in the larger **trajectory-closure class** (closure
required only as `‖Q_v μ_v(R_{c_1},…,R_{c_m})‖ ≤ ρ ∏‖R_{c_i}‖`) and for complex
spaces with complex-multilinear laws. The lower bound is Theorem U
(`K4_TOPOLOGY.md` §2, real field).

Normalize `M = 1`, `ρ = η`, unit leaves (Lemma A5.1). Freeze leaf slots
(Lemma A5.2): an internal vertex `v` with internal children `c_1,…,c_m`
(`m ≥ 0`) carries an `m`-linear map `μ_v` of norm `≤ 1` (for `m = 0`, a vector
`f_v` with `‖f_v‖ ≤ 1`).

---

## 1. Chain Gram states and the order O2

For `ρ ≥ 0` and `ψ ∈ [0,π]` let `K(ρ,ψ) := [[1, ρcos ψ],[ρcos ψ, ρ²]]`, the Gram
matrix of a unit vector and a vector of norm `ρ` at angle `ψ`.

**Definition.** A pair `(F,R)` in a real Hilbert space is **dominated by the
chain datum `(ρ, χ)`** if `Gram(F,R) ⪯ K(ρ,ψ)` for some `ψ ∈ [0, min(χ,π)]`.

**Lemma 1.1 (realization).** `Gram(F,R) ⪯ K(ρ,ψ)` iff there are unit `F̂` and
`R̂` with `∠(F̂,R̂) = ψ` and a linear contraction `B` on `span{F̂,R̂}` with
`BF̂ = F`, `B(ρR̂) = R`. `□` (Standard: `Gram(BX) = X^*B^*BX ⪯ X^*X`; conversely
define `B` on the span; it is well defined and contractive by the Gram
inequality.)

**Lemma 1.2 (planar domination).** Let `f, g` satisfy, for all real `a,b` with
`ab ≤ 0`,

```
(N−)      ‖af + bg‖ ≤ |a e^{iS} + b|,       S ∈ [0,π].
```

Then `Gram(f,g) ⪯ K(1,ψ)` for some `ψ ∈ [0,S]`.

*Proof.* Write `G = Gram(f,g)`, `μ := √((1−G_11)(1−G_22))` (`G_11, G_22 ≤ 1` by
`b = 0`, `a = 0`). `K(1,ψ) − G ⪰ 0` iff `cos ψ ∈ [G_12 − μ, G_12 + μ]`. For
`ab ≤ 0`, (N−) reads `a²(1−G_11) + b²(1−G_22) − 2|ab|(cos S − G_12) ≥ 0`, i.e.
`G_12 + μ ≥ cos S`. Also `G_12 − μ ≤ √(G_11G_22) ≤ 1`. So
`[G_12 − μ, G_12 + μ] ∩ [cos S, 1] ≠ ∅`; take `cos ψ` in it. `□`

*Remark.* This is where "extra alignment cannot help" becomes a lemma: (N−)
bounds alignment only from below, and any excess alignment is absorbed by a
**smaller** dilation angle `ψ ≤ S`. The earlier k=4 proofs insisted on `ψ = S`
and therefore needed repair arguments and residual cases.

## 2. The tensor angle inequality

**Lemma 2.1 (TA_m).** Let `u_i, v_i` be unit vectors in real Hilbert spaces
`H_i` with `∠(u_i, v_i) = ψ_i`, `S := Σψ_i`. For all real `a,b` with `ab ≤ 0`,

```
‖a · u_1⊗⋯⊗u_m + b · v_1⊗⋯⊗v_m‖_π ≤ |a e^{i min(S,π)} + b|,
```

where `‖·‖_π` is the projective tensor norm (dual to the multilinear operator
norm).

*Proof.* If `S ≥ π` the right side is `|a| + |b|`: triangle inequality. Let
`S < π`; by homogeneity `a = 1`, `b = −t`, `t ≥ 0`. Induction on `m`.
`m = 1`: Hilbert norm, `‖u − tv‖² = 1 + t² − 2t cos ψ`.
`m ≥ 2`: put `X := u_2⊗⋯⊗u_m`, `Y := v_2⊗⋯⊗v_m` in `E := H_2⊗_π⋯⊗_π H_m`,
`S' := S − ψ_1`. By associativity of `⊗_π`,
`‖u_1⊗X − t v_1⊗Y‖_π = sup_β [β(u_1,X) − tβ(v_1,Y)]` over bilinear forms on
`H_1 × E` with `‖β‖ ≤ 1`. Restrict the first argument to
`Π := span{u_1, v_1}` and write `β(z,W) = ⟨z, ΛW⟩` with `Λ : E → Π` linear,
`‖ΛW‖ ≤ ‖W‖_π`. Put `p := ΛX`, `q := ΛY`. By induction,
`‖αp + βq‖ ≤ ‖αX + βY‖_π ≤ |αe^{iS'} + β|` for `αβ ≤ 0`, so Lemma 1.2 and 1.1
give unit `p̂, q̂` at angle `ψ̃ ≤ S'` and a contraction `C` with `Cp̂ = p`,
`Cq̂ = q`. Let `Rot` be the rotation of `Π` with `Rot v_1 = u_1`. Then

```
β(u_1,X) − tβ(v_1,Y) = ⟨u_1, Cp̂ − t·Rot Cq̂⟩ ≤ ‖Cp̂ − t·Rot Cq̂‖.
```

Dilate `C` to an isometry `V = (C, (I − C^*C)^{1/2})` into `Π ⊕ D` and put
`R̃ := Rot ⊕ I_D`, an isometry with `∠(w, R̃w) ≤ ψ_1` for every unit `w`
(`⟨w,R̃w⟩ = ‖w_Π‖² cos ψ_1 + ‖w_D‖² ≥ cos ψ_1`). The `Π`-component of
`Vp̂ − tR̃Vq̂` is `Cp̂ − t·Rot Cq̂`, so the right side is at most
`‖Vp̂ − tR̃Vq̂‖`, where `‖Vp̂‖ = 1`, `‖tR̃Vq̂‖ = t` and
`∠(Vp̂, R̃Vq̂) ≤ ψ̃ + ψ_1 ≤ S < π`. Hence it is `≤ |1 − te^{iS}|`. `□`

For `m = 2` this is the nuclear-norm identity used for MIXED; for `m = 3` it
contains the STAR computation. The complex-multiplication form shows it is an
equality when the `u_i, v_i` are coplanar with consistent orientation.

## 3. Propagation through a non-root vertex (Lemma 3)

**Lemma 3.1.** Let `v` be a non-root internal vertex with internal children
`c_1,…,c_m` (`m ≥ 0`). Suppose each `(F_{c_i}, R_{c_i})` is dominated by
`(ρ_i, χ_i)`. Then there is `θ_v ∈ [0, arcsin η]` such that `(F_v, R_v)` is
dominated by `(ρ_v, χ_v) := (cos θ_v ∏ρ_i, θ_v + Σχ_i)`.

*Proof.*
(a) *Reduce the children.* By Lemma 1.1 pick unit `F̂_i`, `R̂_i` at angles
`ψ_i ≤ min(χ_i, π)` and contractions `B_i` with `B_iF̂_i = F_{c_i}`,
`B_i(ρ_iR̂_i) = R_{c_i}`. Replace `μ_v` by `μ'(x_1,…) := μ_v(B_1x_1,…)`: norm
`≤ 1`, same `F_v`, and `μ_v(R_{c_1},…) = ρ μ'(R̂_1,…)` with `ρ := ∏ρ_i`.
Trajectory closure: `‖Q_v μ'(R̂_1,…)‖ = ‖Q_v μ_v(R_{c_i})‖/ρ ≤ η∏‖R_{c_i}‖/ρ ≤ η`,
since `‖R_{c_i}‖ ≤ ρ_i`. (If `ρ = 0` then `R_v = 0` and the claim is trivial.)

(b) *Planar domination of the raw output.* Put `f := μ'(F̂_1,…,F̂_m)`,
`g := μ'(R̂_1,…,R̂_m)`, `S := Σψ_i`. For `ab ≤ 0`,
`‖af + bg‖ = sup_{‖ω‖≤1} ⟨ω, μ'(a⊗F̂ + b⊗R̂)⟩ ≤ ‖a⊗F̂ + b⊗R̂‖_π ≤ |ae^{i min(S,π)} + b|`
by TA_m. (For `m = 0`, `f = g = f_v` and this is `|a+b|‖f_v‖ ≤ |a+b|`.)
Lemma 1.2 and 1.1: unit `F̂', Ê'` at angle `ψ̃ ≤ min(S,π)` and a contraction
`C` with `CF̂' = f`, `CÊ' = g`.

(c) *The vertex projection is one chain step.* `F_v = f`, `R_v = ρP_vg`,
`‖Q_vg‖ ≤ η`. Dilate `C` to an isometry `V`, `P' := P_v ⊕ I`, and put
`F̃ := VF̂'`, `R̃ := ρP'VÊ'`. Their `H_v`-components are `F_v` and `R_v`, so
`Gram(F_v,R_v) ⪯ Gram(F̃,R̃)`. With `sin θ_v := ‖Q'VÊ'‖ = ‖Q_vg‖ ≤ η`:
`‖F̃‖ = 1`, `‖R̃‖ = ρ cos θ_v`, and
`∠(F̃,R̃) ≤ ∠(VF̂',VÊ') + ∠(VÊ', P'VÊ') = ψ̃ + θ_v ≤ Σχ_i + θ_v`. `□`

## 4. The root (Lemma 2) and the proof of Theorem R

By induction from the leaves, Lemma 3.1 gives every non-root internal vertex
`u` an angle `θ_u ∈ [0, arcsin η]` such that `(F_v, R_v)` is dominated by
`(∏_{u ∈ T_v} cos θ_u, Σ_{u ∈ T_v} θ_u)` (internal vertices of the subtree).

At the root with internal children `c_i`: reduce the children as in 3.1(a)
(root closure is not needed) and scalarize by a unit `ω ∈ Ran P_r`:

```
E^P_T = ‖P_r(μ_r(F_c) − μ_r(R_c))‖ ≤ ‖⊗F̂_i − ρ⊗R̂_i‖_π ≤ |1 − ρ e^{i min(S,π)}|,
ρ = ∏_{u ≠ r} cos θ_u,   S = Σψ_i ≤ Θ := Σ_{u ≠ r} θ_u.
```

So `(E^P_T)² ≤ 1 + ρ² − 2ρ cos(min(Θ,π))`, and the scalar step of
`CHAIN_ALL_K.md` §2.4 (`n = k−1` angles in `[0, arcsin η]`: log-concavity,
`ρ ≥ cos Θ`, the case `Θ > π`) gives `E^P_T ≤ max_{θ ≤ arcsin η}|1 − w(θ)^{k−1}|`.
With Theorem U, `C^P_T(η) = C_k(η)`. `□`

## 5. What this changes

* Topology independence holds for all `k` in PMT-A (draft); `a_T = a_k`,
  `η_c`, `G^max_k` are depth-only invariants.
* The state recursion of `RECURSION.md` is exactly the induction above: the state
  of a vertex is its Gram pair up to Löwner domination by a chain Gram matrix
  `K(ρ,ψ)` with `ψ ≤ χ`, and every vertex (linear or multilinear) acts by
  `(ρ,χ) ↦ (cos θ ∏ρ_i, θ + Σχ_i)`: the complex product `z ↦ w(θ)∏z_i`.
* The proof uses only: contractivity, orthogonality of `P_v`, closure along the
  reduced trajectory, isometric dilation, and the projective-norm duality. The
  earlier BBR/STAR residual-case bounds are unnecessary.
* The proposed order O1 (`|a − λζe^{iφ}| ≤ |1 − λze^{iφ}|`) is not used.
* Over `ℂ`: the upper bound holds verbatim (realify; complex projective norms are
  bounded by real ones); the lower bound for skeletons with a vertex having ≥ 2
  internal children remains open, so `PMT-A[C]` constants may still differ.
* DAGs: if one value feeds several slots, TA_m applies with that factor
  repeated and `S` counts it once per slot, which suggests
  `C^P_G(η) ≤ max_θ|1 − w(θ)^{K(G)}|/η` (Conjecture R-DAG). Not checked; the DAG
  class must be frozen first.

## 6. Points a reviewer should check first

1. Lemma 1.2: the reduction of (N−) to `G_12 + μ ≥ cos S` and the use of only
   `ab ≤ 0`.
2. Lemma 2.1: associativity/duality of `⊗_π`, the Riesz map `Λ`, and the angle
   bound for `Rot ⊕ I`.
3. Lemma 3.1(a): the closure normalization `‖R_{c_i}‖ ≤ ρ_i` (from domination).
4. §4: that `S ≤ Θ` and the scalar step apply with `ρ = ∏cos θ_u` exactly.
