/-
Additive baseline: `gBox η ≤ Σ η_u`.

The naive telescoping estimate for nodewise defects is additive (`E ≤ Λ_T Σ_u η_u`). It follows
from `|1 - ∏ z_u| ≤ Σ |1 - z_u|` for `|z_u| ≤ 1` and `|1 - w(θ)| = sin θ ≤ η` on the box. The sharp
constant `gBox` never exceeds it; it agrees with it to first order in the defects.

Statements:
* `PMT.norm_one_sub_w`       `|1 - w θ| = |sin θ|`
* `PMT.norm_one_sub_mul_le`  `|1 - a p| ≤ |1 - a| + |1 - p|` for `|a| ≤ 1`
* `PMT.box_value_le_sum`     every box value is `≤ Σ η_u`
* `PMT.gBox_le_sum`          `gBox η ≤ Σ η_u` (`η_u ≥ 0`)
-/
import PMTFormal.Heterogeneous.Attainment

open Real

namespace PMT

theorem norm_one_sub_w (θ : ℝ) : ‖1 - w θ‖ = |Real.sin θ| := by
  have h : ‖1 - w θ‖ ^ 2 = Real.sin θ ^ 2 := by
    rw [← Complex.normSq_eq_norm_sq, w, normSq_one_sub_mul_exp]
    nlinarith [Real.sin_sq_add_cos_sq θ]
  rw [← Real.sqrt_sq (norm_nonneg _), h, Real.sqrt_sq_eq_abs]

theorem norm_one_sub_mul_le {a p : ℂ} (ha : ‖a‖ ≤ 1) : ‖1 - a * p‖ ≤ ‖1 - a‖ + ‖1 - p‖ := by
  have h : 1 - a * p = (1 - a) + a * (1 - p) := by ring
  rw [h]
  refine (norm_add_le _ _).trans (add_le_add le_rfl ?_)
  rw [norm_mul]
  exact mul_le_of_le_one_left (norm_nonneg _) ha

theorem box_value_le_sum {η θ : List ℝ} (hθ : θ ∈ box η) : ‖1 - (θ.map w).prod‖ ≤ η.sum := by
  have h : List.Forall₂ BoxRel θ η := hθ
  clear hθ
  induction h with
  | nil => simp
  | cons hab _ ih =>
    rw [List.map_cons, List.prod_cons, List.sum_cons]
    refine (norm_one_sub_mul_le (norm_w_le_one _)).trans (add_le_add ?_ ih)
    rw [norm_one_sub_w, abs_of_nonneg hab.sin_nonneg]
    exact hab.sin_le

/-- **Additive baseline.** -/
theorem gBox_le_sum {η : List ℝ} (hη : ∀ e ∈ η, 0 ≤ e) : gBox η ≤ η.sum := by
  obtain ⟨θ, hθ, hval⟩ := gBox_attained hη
  rw [← hval]
  exact box_value_le_sum hθ

end PMT
