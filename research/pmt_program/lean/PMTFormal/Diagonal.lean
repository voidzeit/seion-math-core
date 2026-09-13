/-
Theorem R v2, Section 6: the Diagonal Lemma (PMT-free).

Statements:
* `PMT.cos_sum_le_prod_cos`      Lemma 6.1 (subadditivity, hypothesis Σθ ≤ π/2)
* `PMT.prod_cos_le_cos_mean_pow` Lemma 6.2 (∏ cos θⱼ ≤ cos(Θ/n)^n on [0, π/2]^n, via Jensen for
                                  cos plus AM–GM; no separate θⱼ = π/2 case is needed)
* `PMT.diagonal_capped`          Lemma 6.3, "moreover" part (the form used by the upper bound)
* `PMT.diagonal_lemma`           Lemma 6.3, uncapped form
-/
import Mathlib

open Real Finset

namespace PMT

/-- `w θ = cos θ · e^{iθ}`. -/
noncomputable def w (θ : ℝ) : ℂ := (Real.cos θ : ℂ) * Complex.exp (θ * Complex.I)

/-- `|1 - r e^{iφ}|² = 1 - 2 r cos φ + r²` for real `r, φ`. -/
theorem normSq_one_sub_mul_exp (r φ : ℝ) :
    Complex.normSq (1 - (r : ℂ) * Complex.exp (φ * Complex.I)) =
      1 - 2 * r * Real.cos φ + r ^ 2 := by
  have h := Complex.exp_mul_I (φ : ℂ)
  rw [h, ← Complex.ofReal_cos, ← Complex.ofReal_sin, Complex.normSq_apply]
  simp only [Complex.sub_re, Complex.one_re, Complex.mul_re, Complex.ofReal_re, Complex.ofReal_im,
    Complex.add_re, Complex.add_im, Complex.mul_im, Complex.I_re, Complex.I_im, Complex.sub_im,
    Complex.one_im]
  nlinarith [Real.sin_sq_add_cos_sq φ]

/-- `w t ^ n = cos(t)^n · e^{i n t}`. -/
theorem w_pow (t : ℝ) (n : ℕ) :
    w t ^ n = ((Real.cos t ^ n : ℝ) : ℂ) * Complex.exp (((n : ℝ) * t : ℝ) * Complex.I) := by
  unfold w
  rw [mul_pow, ← Complex.exp_nat_mul]
  push_cast
  ring_nf

/-- `∏ w θᵢ = (∏ cos θᵢ) · e^{i Σ θᵢ}`. -/
theorem prod_w {ι : Type*} (s : Finset ι) (θ : ι → ℝ) :
    ∏ i ∈ s, w (θ i) =
      ((∏ i ∈ s, Real.cos (θ i) : ℝ) : ℂ) * Complex.exp (((∑ i ∈ s, θ i : ℝ) : ℂ) * Complex.I) := by
  unfold w
  rw [Finset.prod_mul_distrib, ← Complex.exp_sum]
  push_cast
  rw [Finset.sum_mul]

/-- **Lemma 6.1.** If `θᵢ ≥ 0` and `Σ θᵢ ≤ π/2` then `cos (Σ θᵢ) ≤ ∏ cos θᵢ`. -/
theorem cos_sum_le_prod_cos {ι : Type*} (s : Finset ι) (θ : ι → ℝ)
    (hpos : ∀ i ∈ s, 0 ≤ θ i) (hsum : ∑ i ∈ s, θ i ≤ π / 2) :
    Real.cos (∑ i ∈ s, θ i) ≤ ∏ i ∈ s, Real.cos (θ i) := by
  classical
  induction s using Finset.induction_on with
  | empty => simp
  | insert a s ha ih =>
    rw [Finset.sum_insert ha] at hsum ⊢
    rw [Finset.prod_insert ha]
    have hs0 : 0 ≤ ∑ i ∈ s, θ i :=
      Finset.sum_nonneg fun i hi => hpos i (Finset.mem_insert_of_mem hi)
    have ha0 : 0 ≤ θ a := hpos a (Finset.mem_insert_self a s)
    have ih' := ih (fun i hi => hpos i (Finset.mem_insert_of_mem hi)) (by linarith)
    have hcosa : 0 ≤ Real.cos (θ a) :=
      Real.cos_nonneg_of_mem_Icc ⟨by linarith [Real.pi_pos], by linarith⟩
    have hsina : 0 ≤ Real.sin (θ a) :=
      Real.sin_nonneg_of_nonneg_of_le_pi ha0 (by linarith [Real.pi_pos])
    have hsins : 0 ≤ Real.sin (∑ i ∈ s, θ i) :=
      Real.sin_nonneg_of_nonneg_of_le_pi hs0 (by linarith [Real.pi_pos])
    rw [Real.cos_add]
    nlinarith [mul_nonneg hsina hsins, mul_le_mul_of_nonneg_left ih' hcosa]

/-- **Lemma 6.2.** For `θⱼ ∈ [0, π/2]`, `∏ cos θⱼ ≤ cos (Θ/n) ^ n` with `Θ = Σ θⱼ`. -/
theorem prod_cos_le_cos_mean_pow (n : ℕ) (hn : 0 < n) (θ : Fin n → ℝ)
    (h : ∀ j, θ j ∈ Set.Icc 0 (π / 2)) :
    ∏ j, Real.cos (θ j) ≤ Real.cos ((∑ j, θ j) / n) ^ n := by
  have hn' : (0 : ℝ) < n := by exact_mod_cast hn
  have hmem : ∀ j, θ j ∈ Set.Icc (-(π / 2)) (π / 2) :=
    fun j => ⟨by linarith [(h j).1, Real.pi_pos], (h j).2⟩
  have hc : ∀ j, 0 ≤ Real.cos (θ j) := fun j => Real.cos_nonneg_of_mem_Icc (hmem j)
  have hw1 : ∑ _j : Fin n, (1 : ℝ) / n = 1 := by
    simp [Finset.card_univ]
    field_simp
  -- AM–GM with equal weights
  have amgm := Real.geom_mean_le_arith_mean_weighted (Finset.univ : Finset (Fin n))
    (fun _ => (1 : ℝ) / n) (fun j => Real.cos (θ j)) (fun _ _ => by positivity) hw1
    (fun j _ => hc j)
  -- Jensen for the concave cosine
  have jensen := (strictConcaveOn_cos_Icc.concaveOn).le_map_sum (t := Finset.univ)
    (w := fun _ => (1 : ℝ) / n) (p := θ) (fun _ _ => by positivity) hw1 (fun j _ => hmem j)
  simp only [smul_eq_mul] at jensen
  have hmeanθ : ∑ j, (1 : ℝ) / n * θ j = (∑ j, θ j) / n := by
    rw [← Finset.mul_sum]
    ring
  rw [hmeanθ] at jensen
  have hprod : ∏ j, Real.cos (θ j) = (∏ j, Real.cos (θ j) ^ ((1 : ℝ) / n)) ^ n := by
    rw [← Finset.prod_pow]
    refine Finset.prod_congr rfl fun j _ => ?_
    rw [← Real.rpow_natCast, ← Real.rpow_mul (hc j)]
    field_simp
    simp
  rw [hprod]
  exact pow_le_pow_left₀ (Finset.prod_nonneg fun j _ => Real.rpow_nonneg (hc j) _)
    (amgm.trans jensen) n

/-- **Lemma 6.3, capped form.** For `θ ∈ [0, α]^n` with `0 < α ≤ π/2`, there is `t ∈ [0, α]` with
`1 - 2 R cos(min(Θ, π)) + R² ≤ |1 - w(t)^n|²`, where `R = ∏ cos θⱼ` and `Θ = Σ θⱼ`. -/
theorem diagonal_capped (n : ℕ) (hn : 0 < n) (α : ℝ) (hα0 : 0 < α) (hα : α ≤ π / 2)
    (θ : Fin n → ℝ) (hθ : ∀ j, θ j ∈ Set.Icc 0 α) :
    ∃ t ∈ Set.Icc 0 α,
      1 - 2 * (∏ j, Real.cos (θ j)) * Real.cos (min (∑ j, θ j) π) + (∏ j, Real.cos (θ j)) ^ 2
        ≤ Complex.normSq (1 - w t ^ n) := by
  set R := ∏ j, Real.cos (θ j) with hRdef
  set Θ := ∑ j, θ j with hΘdef
  have hn' : (0 : ℝ) < n := by exact_mod_cast hn
  have hθ' : ∀ j, θ j ∈ Set.Icc 0 (π / 2) := fun j => ⟨(hθ j).1, (hθ j).2.trans hα⟩
  have hR0 : 0 ≤ R := Finset.prod_nonneg fun j _ =>
    Real.cos_nonneg_of_mem_Icc ⟨by linarith [(hθ j).1, Real.pi_pos], (hθ' j).2⟩
  have hΘ0 : 0 ≤ Θ := Finset.sum_nonneg fun j _ => (hθ j).1
  have hΘle : Θ ≤ n * α := by
    calc Θ ≤ ∑ _j : Fin n, α := Finset.sum_le_sum fun j _ => (hθ j).2
      _ = n * α := by simp
  have hjensen : R ≤ Real.cos (Θ / n) ^ n := prod_cos_le_cos_mean_pow n hn θ hθ'
  have hW : ∀ t : ℝ, Complex.normSq (1 - w t ^ n) =
      1 - 2 * (Real.cos t ^ n) * Real.cos ((n : ℝ) * t) + (Real.cos t ^ n) ^ 2 := by
    intro t
    rw [w_pow, normSq_one_sub_mul_exp]
  by_cases hΘπ : Θ ≤ π
  · refine ⟨Θ / n, ⟨by positivity, by rw [div_le_iff₀ hn']; linarith⟩, ?_⟩
    rw [min_eq_left hΘπ, hW]
    have hnt : (n : ℝ) * (Θ / n) = Θ := by field_simp
    rw [hnt]
    have hRcos : Real.cos Θ ≤ R := by
      by_cases h2 : Θ ≤ π / 2
      · exact cos_sum_le_prod_cos Finset.univ θ (fun j _ => (hθ j).1) h2
      · push Not at h2
        exact (Real.cos_nonpos_of_pi_div_two_le_of_le h2.le (by linarith [Real.pi_pos])).trans hR0
    nlinarith [mul_nonneg (sub_nonneg.2 hjensen)
      (by linarith : (0 : ℝ) ≤ Real.cos (Θ / n) ^ n + R - 2 * Real.cos Θ)]
  · push Not at hΘπ
    have hπn : π / n ≤ α := by
      rw [div_le_iff₀ hn']
      linarith
    refine ⟨π / n, ⟨by positivity, hπn⟩, ?_⟩
    rw [min_eq_right hΘπ.le, Real.cos_pi, hW]
    have hnt : (n : ℝ) * (π / n) = π := by field_simp
    rw [hnt, Real.cos_pi]
    have hΘn : Θ / n ≤ π / 2 := by
      rw [div_le_iff₀ hn']
      nlinarith
    have hb : R ≤ Real.cos (π / n) ^ n := by
      refine hjensen.trans (pow_le_pow_left₀ ?_ ?_ n)
      · exact Real.cos_nonneg_of_mem_Icc ⟨by linarith [Real.pi_pos, div_nonneg hΘ0 hn'.le], hΘn⟩
      · exact Real.cos_le_cos_of_nonneg_of_le_pi (by positivity) (by linarith [Real.pi_pos])
          (div_le_div_of_nonneg_right hΘπ.le hn'.le)
    nlinarith

/-- **Lemma 6.3.** For `θ ∈ [0, α]^n` there is `t ∈ [0, α]` with `|1 - ∏ w θⱼ| ≤ |1 - w(t)^n|`
(stated for squared norms). Together with the diagonal choice this gives equality of maxima. -/
theorem diagonal_lemma (n : ℕ) (hn : 0 < n) (α : ℝ) (hα0 : 0 < α) (hα : α ≤ π / 2)
    (θ : Fin n → ℝ) (hθ : ∀ j, θ j ∈ Set.Icc 0 α) :
    ∃ t ∈ Set.Icc 0 α, Complex.normSq (1 - ∏ j, w (θ j)) ≤ Complex.normSq (1 - w t ^ n) := by
  obtain ⟨t, ht, hle⟩ := diagonal_capped n hn α hα0 hα θ hθ
  refine ⟨t, ht, le_trans ?_ hle⟩
  have hR0 : 0 ≤ ∏ j, Real.cos (θ j) := Finset.prod_nonneg fun j _ =>
    Real.cos_nonneg_of_mem_Icc ⟨by linarith [(hθ j).1, Real.pi_pos], (hθ j).2.trans hα⟩
  rw [prod_w, normSq_one_sub_mul_exp]
  have hcos : Real.cos (min (∑ j, θ j) π) ≤ Real.cos (∑ j, θ j) := by
    rcases le_total (∑ j, θ j) π with h | h
    · rw [min_eq_left h]
    · rw [min_eq_right h, Real.cos_pi]
      exact Real.neg_one_le_cos _
  nlinarith [mul_le_mul_of_nonneg_left hcos hR0]

end PMT
