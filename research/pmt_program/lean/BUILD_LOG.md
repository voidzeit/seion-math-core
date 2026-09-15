# Build record

## 2026-09-14 (later) — common ambient space, spec lemmas, additive baseline

* **Result:** `Build completed successfully (8727 jobs).`
* **New files:** `Heterogeneous/SpecLemmas.lean`, `Heterogeneous/Baseline.lean`,
  `Heterogeneous/CommonSpace.lean`.
* **Axioms:** 47 `#print axioms` lines, all `[propext, Classical.choice, Quot.sound]`. The source
  scan is unchanged (no `sorry`, `admit` or `axiom`).
* **Statements:**

```
PMT.heterogeneous_multispace_upper : ∀ {H : PMT.HSpace} (t : PMT.MSTree H),
  t.RootAdmFull0 → t.err ≤ t.Λ * PMT.gBox t.dshape.childDefects
PMT.heterogeneous_multispace_sSup : ∀ {m : ℕ} {e : ℝ}, 0 ≤ e → ∀ (ch : Fin m → PMT.DShape),
  sSup {x | ∃ H t, t.dshape = PMT.DShape.node m e ch ∧ t.RootAdmFull0 ∧ 0 < t.Λ ∧ t.err / t.Λ = x} =
    PMT.gBox (PMT.DShape.node m e ch).childDefects
PMT.opNorm_le_iff_unit_ball : 0 ≤ M → (‖μ‖ ≤ M ↔ ∀ x, (∀ i, ‖x i‖ ≤ 1) → ‖μ x‖ ≤ M)
PMT.HPMTree.closure_iff_unit_ball : 0 ≤ e →
  ((∀ x, (∀ i, (ch i).InRan (x i)) → ‖μ x - P (μ x)‖ ≤ e * ∏ i, ‖x i‖) ↔
    ∀ x, (∀ i, (ch i).InRan (x i)) → (∀ i, ‖x i‖ ≤ 1) → ‖μ x - P (μ x)‖ ≤ e)
PMT.gBox_le_sum : (∀ e ∈ η, 0 ≤ e) → PMT.gBox η ≤ η.sum
```

* **Design note:** the common space is `WithLp 2 (H_v × PiLp 2 (child common spaces))`. A first
  attempt with `PiLp 2` over `Option (Fin m)` failed because `Option.elim` does not reduce at
  instance transparency.

## 2026-09-14 — heterogeneous Theorem R (branch `research/heterogeneous-theorem-r`)

* **Host and toolchain:** as below (Lean `4.33.1`, Mathlib `v4.33.1`). Built in the dedicated
  worktree `seion-pmt-hetero`, created from `origin/main` `f219172`.
* **Result:** `Build completed successfully (8724 jobs).` (After adding `ScaledZero.lean`; the
  run before it had 8723 jobs.)
* **Source scan** (`sorry|admit|axiom|native_decide|implemented_by|extern` over `PMTFormal/`):
  no occurrences. The only textual hit is the docstring of `CappedDiagonal.lean`, which says H3
  is *not* an axiom and *not* a `sorry`.
* **H3 isolation:** `CappedDiagonal`, `CappedEqualAngle` and `cappedValues` occur only in
  `CappedDiagonal.lean`, the library root `PMTFormal.lean` and `AxiomsCheck.lean`.
* **New files:** `Heterogeneous/{BoxConstant, Upper, Witness, Sharp, Permutation, Attainment,
  Scaled, ScaledZero, CappedDiagonal}.lean`.
* **Axioms:** `lake env lean AxiomsCheck.lean` prints 40 `#print axioms` lines (including
  `heterogeneous_scaled_upper_nonneg`). The set of distinct
  axiom lists is exactly one: `[propext, Classical.choice, Quot.sound]`. This covers
  `box_capped`, `envelopeH`, `heterogeneous_upper`, `heterogeneous_le_gBox`,
  `heterogeneous_witness`, `heterogeneous_lower`, `heterogeneous_sSup`, `heterogeneous_sharp`,
  `uniform_gBox_eq`, `heterogeneous_uniform_recovery`, `gBox_perm`,
  `heterogeneous_placement_independent`, `theorem_R_max_attained`, `gBox_attained`,
  `heterogeneous_max_attained`, `heterogeneous_scaled_upper`, `heterogeneous_scaled_sSup`,
  `sSup_capped_le_gBox`, `cappedEqualAngle_replicate`, and all earlier Theorem R declarations.

Elaborated statements:

```
PMT.heterogeneous_upper : ∀ {G} [NormedAddCommGroup G] [InnerProductSpace ℝ G] (t : PMT.HPMTree G),
  t.RootAdmFull → ∃ θ ∈ PMT.box t.dshape.childDefects, t.err ≤ ‖1 - (List.map PMT.w θ).prod‖
PMT.heterogeneous_witness : ∀ {m : ℕ} {e : ℝ}, 0 ≤ e → ∀ (ch : Fin m → PMT.DShape) {θ : List ℝ},
  θ ∈ PMT.box (PMT.DShape.node m e ch).childDefects →
    ∃ t, t.dshape = PMT.DShape.node m e ch ∧ t.RootAdmFull ∧ t.err = ‖1 - (List.map PMT.w θ).prod‖
PMT.heterogeneous_sSup : ∀ {m : ℕ} {e : ℝ}, 0 ≤ e → ∀ (ch : Fin m → PMT.DShape),
  sSup (PMT.errSetH (PMT.DShape.node m e ch)) = PMT.gBox (PMT.DShape.node m e ch).childDefects
PMT.gBox_perm : ∀ {η η' : List ℝ}, η.Perm η' → PMT.gBox η = PMT.gBox η'
PMT.heterogeneous_placement_independent : ∀ {m m' : ℕ} {e e' : ℝ}, 0 ≤ e → 0 ≤ e' →
  ∀ (ch : Fin m → PMT.DShape) (ch' : Fin m' → PMT.DShape),
    (PMT.DShape.node m e ch).childDefects.Perm (PMT.DShape.node m' e' ch').childDefects →
      sSup (PMT.errSetH (PMT.DShape.node m e ch)) = sSup (PMT.errSetH (PMT.DShape.node m' e' ch'))
PMT.uniform_gBox_eq : ∀ {η : ℝ}, 0 < η → ∀ (n : ℕ),
  PMT.gBox (List.replicate n η) = sSup ((fun τ => ‖1 - PMT.w τ ^ n‖) '' Set.Icc 0 (Real.arcsin η))
PMT.heterogeneous_scaled_upper : ∀ {G} [NormedAddCommGroup G] [InnerProductSpace ℝ G] (t : PMT.SPMTree G),
  t.RootAdmFull → t.err ≤ t.Λ * PMT.gBox t.dshape.childDefects
PMT.heterogeneous_scaled_sSup : ∀ {m : ℕ} {e : ℝ}, 0 ≤ e → ∀ (ch : Fin m → PMT.DShape),
  sSup {x | ∃ t, t.dshape = PMT.DShape.node m e ch ∧ t.RootAdmFull ∧ 0 < t.Λ ∧ t.err / t.Λ = x} =
    PMT.gBox (PMT.DShape.node m e ch).childDefects
```

Timing note: an early `Scaled.lean` took 419 s because of unrestricted `simp [witRootH, …]` calls.
They were replaced by `simp only`, and the file now elaborates in about 7 s (plus imports).

## 2026-09-14 — full Theorem R (normalised, single-space)

* **Host:** Windows 10, elan-installed Lean `4.33.1`, Mathlib `v4.33.1` (see `lake-manifest.json`).
* **Commands:**
  ```bash
  lake exe cache get
  ```
  ```bash
  lake build
  ```
  ```bash
  lake env lean AxiomsCheck.lean
  ```
* **Result:** `Build completed successfully (8715 jobs).`
* **Source scan:** no `sorry`, `admit` or `axiom` in `PMTFormal/`.
* **New files:** `LiftedAngle.lean`, `TensorAngle.lean`, `NodeStep.lean`, `Tree.lean`,
  `WitnessAdm.lean`, `TheoremR.lean`.

`#print axioms` (from `AxiomsCheck.lean`): every one of the following depends only on
`[propext, Classical.choice, Quot.sound]`:

```
PMT.cos_sum_le_prod_cos   PMT.prod_cos_le_cos_mean_pow   PMT.diagonal_capped   PMT.diagonal_lemma
PMT.rootError_eq          PMT.rootError_equal_angles     PMT.phi_triangle      PMT.normSq_sub_le
PMT.phi_le_of_contr       PMT.phi_multilinear_le         PMT.phi_proj          PMT.node_step
PMT.root_step             PMT.envelope                   PMT.upper_bound       PMT.wit_admFull
PMT.witRoot_err           PMT.theorem_R_upper            PMT.theorem_R_lower   PMT.theorem_R_sSup
```

Elaborated statements of the three main results:

```
PMT.theorem_R_upper : ∀ {G : Type u_1} [NormedAddCommGroup G] [InnerProductSpace ℝ G] {η : ℝ},
  0 < η → ∀ (t : PMT.PMTree G), PMT.PMTree.RootAdmFull η t →
    ∃ τ ∈ Set.Icc 0 (Real.arcsin η), t.err ≤ ‖1 - PMT.w τ ^ (t.internal - 1)‖
PMT.theorem_R_lower : ∀ {η : ℝ}, 0 < η → η ≤ 1 → ∀ (m : ℕ) (ch : Fin m → PMT.Shape) {τ : ℝ},
  τ ∈ Set.Icc 0 (Real.arcsin η) →
    ∃ t, t.shape = PMT.Shape.node m ch ∧ PMT.PMTree.RootAdmFull η t ∧
      t.err = ‖1 - PMT.w τ ^ ((PMT.Shape.node m ch).internal - 1)‖
PMT.theorem_R_sSup : ∀ {η : ℝ}, 0 < η → η ≤ 1 → ∀ (m : ℕ) (ch : Fin m → PMT.Shape),
  sSup {e | ∃ t, t.shape = PMT.Shape.node m ch ∧ PMT.PMTree.RootAdmFull η t ∧ t.err = e} =
    sSup ((fun τ => ‖1 - PMT.w τ ^ ((PMT.Shape.node m ch).internal - 1)‖) '' Set.Icc 0 (Real.arcsin η))
```

Scope and the gap to the paper statement: see `README.md`.

## 2026-09-13 — Diagonal Lemma and witness evaluation

* **Host:** Windows 10, elan-installed Lean `4.33.1` (commit `819816b2e0a3`), Mathlib `v4.33.1`.
* **Result:** `Build completed successfully (8709 jobs).` No `sorry`/`admit` in `PMTFormal/`.
* **Axioms:** `cos_sum_le_prod_cos`, `prod_cos_le_cos_mean_pow`, `diagonal_capped`,
  `diagonal_lemma`, `rootError_eq` and `rootError_equal_angles` depend only on
  `[propext, Classical.choice, Quot.sound]`.
* **Not formalised at that date:** O2, the tensor angle inequality, Lemma 3, and the
  admissibility of the witness laws. All four are superseded by the 2026-09-14 entry above.
