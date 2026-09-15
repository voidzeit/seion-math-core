/-
Monotonicity of the box constant and the uniform fallback.

Statements:
* `PMT.gBox_mono`                  `η ≤ ξ` coordinatewise  ⟹  `gBox η ≤ gBox ξ`
                                   (no sign hypothesis: an empty box gives `gBox = 0`)
* `PMT.gBox_le_replicate`          `gBox η ≤ gBox (c, …, c)` whenever every `η_i ≤ c`
* `PMT.gBox_le_uniform_fallback`   with `c = max η > 0`:
                                   `gBox η ≤ sup_{τ ∈ [0, arcsin c]} |1 - w(τ)^n|`, `n = |η|`
                                   (the uniform Theorem R constant at the largest defect)
-/
import PMTFormal.Heterogeneous.ScaledZero

open Real

namespace PMT

theorem forall₂_boxRel_mono {θ η ξ : List ℝ} (h1 : List.Forall₂ BoxRel θ η)
    (h2 : List.Forall₂ (· ≤ ·) η ξ) : List.Forall₂ BoxRel θ ξ := by
  induction h1 generalizing ξ with
  | nil =>
    cases h2
    exact .nil
  | cons hab _ ih =>
    cases h2 with
    | cons hb t2 => exact .cons ⟨hab.1, hab.2.trans (Real.arcsin_le_arcsin hb)⟩ (ih t2)

theorem box_mono {η ξ : List ℝ} (h : List.Forall₂ (· ≤ ·) η ξ) : box η ⊆ box ξ :=
  fun _ hθ => forall₂_boxRel_mono hθ h

/-- **Monotonicity of `gBox`.** -/
theorem gBox_mono {η ξ : List ℝ} (h : List.Forall₂ (· ≤ ·) η ξ) : gBox η ≤ gBox ξ := by
  rcases (box η).eq_empty_or_nonempty with he | hne
  · have : gBox η = 0 := by
      rw [gBox, he, Set.image_empty, Real.sSup_empty]
    rw [this]
    exact gBox_nonneg ξ
  · exact csSup_le_csSup (bddAbove_box_image ξ) (hne.image _) (Set.image_mono (box_mono h))

theorem forall₂_le_replicate : ∀ (η : List ℝ) (c : ℝ), (∀ e ∈ η, e ≤ c) →
    List.Forall₂ (· ≤ ·) η (List.replicate η.length c)
  | [], _, _ => .nil
  | a :: l, c, h => .cons (h a (by simp)) (forall₂_le_replicate l c fun e he => h e (by simp [he]))

/-- Replacing every defect by a common upper bound can only increase `gBox`. -/
theorem gBox_le_replicate {η : List ℝ} {c : ℝ} (h : ∀ e ∈ η, e ≤ c) :
    gBox η ≤ gBox (List.replicate η.length c) :=
  gBox_mono (forall₂_le_replicate η c h)

/-- **Uniform fallback.** With `c` an upper bound of the defects (`0 < c`), `gBox η` is at most the
uniform Theorem R constant `sup_{τ ∈ [0, arcsin c]} |1 - w(τ)^n|` with `n = |η|`. -/
theorem gBox_le_uniform_fallback {η : List ℝ} {c : ℝ} (hc : 0 < c) (h : ∀ e ∈ η, e ≤ c) :
    gBox η ≤ sSup ((fun τ => ‖1 - w τ ^ η.length‖) '' Set.Icc 0 (arcsin c)) :=
  (gBox_le_replicate h).trans (uniform_gBox_eq hc η.length).le

end PMT
