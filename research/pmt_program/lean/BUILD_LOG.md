# Build record

* Date: 2026-09-13
* Host: Windows 10, elan-installed Lean `4.33.1` (commit `819816b2e0a3`), Mathlib `v4.33.1`
  (see `lake-manifest.json`)
* Commands:
  ```bash
  lake exe cache get
  ```
  ```bash
  lake build
  ```
  ```bash
  lake env lean AxiomsCheck.lean
  ```
* Result: `Build completed successfully (8709 jobs).` No `sorry`/`admit` in `PMTFormal/`.

`#print axioms` (from `AxiomsCheck.lean`):

```
'PMT.cos_sum_le_prod_cos' depends on axioms: [propext, Classical.choice, Quot.sound]
'PMT.prod_cos_le_cos_mean_pow' depends on axioms: [propext, Classical.choice, Quot.sound]
'PMT.diagonal_capped' depends on axioms: [propext, Classical.choice, Quot.sound]
'PMT.diagonal_lemma' depends on axioms: [propext, Classical.choice, Quot.sound]
'PMT.rootError_eq' depends on axioms: [propext, Classical.choice, Quot.sound]
'PMT.rootError_equal_angles' depends on axioms: [propext, Classical.choice, Quot.sound]
```

Only Lean's standard axioms appear; no `sorryAx`.

Elaborated statements of the two central results:

```
PMT.diagonal_lemma : ∀ (n : ℕ), 0 < n → ∀ (α : ℝ), 0 < α → α ≤ Real.pi / 2 →
  ∀ (θ : Fin n → ℝ), (∀ (j : Fin n), θ j ∈ Set.Icc 0 α) →
    ∃ t ∈ Set.Icc 0 α, Complex.normSq (1 - ∏ j, PMT.w (θ j)) ≤ Complex.normSq (1 - PMT.w t ^ n)
PMT.rootError_eq : ∀ (ks : List PMT.WTree),
  PMT.rootError ks = ‖1 - (List.map PMT.w (PMT.WTree.anglesL ks)).prod‖
```

Scope: see `README.md`. Not formalised: O2, the tensor angle inequality, Lemma 3,
and the admissibility (norm and closure) of the witness laws.
