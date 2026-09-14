# Build record

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
