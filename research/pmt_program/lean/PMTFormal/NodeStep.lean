/-
Lemma 3 (nodewise O2 preservation) and the root reading, in lifted-angle form.

`Dom F R ρ χ` means: `‖F‖ ≤ 1`, `ρ ≥ 0`, and `R = ρ • R̂` for some `R̂` in the unit ball with
`phi F R̂ ≤ χ`. This is equivalent to Definition 2.1 (O2) of Theorem R v2 (see
`research/pmt_program/lifted_angle/LIFTED_ANGLE_PROOF.md`).

Statements:
* `PMT.phi_proj`    `phi g (P g / cos θ) ≤ θ` with `sin θ = ‖g - P g‖`
* `PMT.node_step`   Lemma 3: children dominated by `(ρᵢ, χᵢ)` and trajectory closure give
                    `θ ∈ [0, arcsin η]` with the node dominated by `(cos θ ∏ ρᵢ, θ + ∑ χᵢ)`
* `PMT.root_step`   root reading: `‖P(μ F) - P(μ R)‖² ≤ 1 + ρ² - 2 ρ cos(min(∑ χᵢ, π))`
-/
import PMTFormal.TensorAngle

open Real
open scoped RealInnerProductSpace

namespace PMT

variable {G : Type*} [NormedAddCommGroup G] [InnerProductSpace ℝ G]

/-- O2 domination in lifted-angle form. -/
def Dom (F R : G) (ρ χ : ℝ) : Prop :=
  ‖F‖ ≤ 1 ∧ 0 ≤ ρ ∧ ∃ Rh : G, ‖Rh‖ ≤ 1 ∧ R = ρ • Rh ∧ phi F Rh ≤ χ

/-- `P` is an orthogonal projector (idempotent and symmetric). -/
structure IsOrthProj (P : G →L[ℝ] G) : Prop where
  idem : ∀ u, P (P u) = P u
  symm : ∀ u v, ⟪P u, v⟫ = ⟪u, P v⟫

namespace IsOrthProj

variable {P : G →L[ℝ] G}

theorem inner_self_P (hP : IsOrthProj P) (u : G) : ⟪u, P u⟫ = ‖P u‖ ^ 2 := by
  rw [← real_inner_self_eq_norm_sq, hP.symm, hP.idem]

theorem pythag (hP : IsOrthProj P) (u : G) : ‖P u‖ ^ 2 + ‖u - P u‖ ^ 2 = ‖u‖ ^ 2 := by
  rw [norm_sub_sq_real, hP.inner_self_P]
  ring

theorem norm_le (hP : IsOrthProj P) (u : G) : ‖P u‖ ≤ ‖u‖ := by
  have h := hP.pythag u
  have : ‖P u‖ ^ 2 ≤ ‖u‖ ^ 2 := by nlinarith [sq_nonneg ‖u - P u‖]
  exact (abs_le_of_sq_le_sq' this (norm_nonneg u)).2

end IsOrthProj

theorem dom_of_zero {F : G} (hF : ‖F‖ ≤ 1) {χ : ℝ} (hχ : 0 ≤ χ) : Dom F 0 0 χ :=
  ⟨hF, le_rfl, F, hF, by simp, by rw [phi_self hF]; exact hχ⟩

/-- Projection step: with `q = ‖g - P g‖`, `c = √(1 - q²) > 0`, the vector `c⁻¹ P g` lies in the
unit ball and `phi g (c⁻¹ P g) ≤ arcsin q`. -/
theorem phi_proj {P : G →L[ℝ] G} (hP : IsOrthProj P) {g : G} (hg : ‖g‖ ≤ 1)
    (hc : 0 < 1 - ‖g - P g‖ ^ 2) :
    ‖(√(1 - ‖g - P g‖ ^ 2))⁻¹ • P g‖ ≤ 1 ∧
      phi g ((√(1 - ‖g - P g‖ ^ 2))⁻¹ • P g) ≤ arcsin ‖g - P g‖ := by
  set q := ‖g - P g‖ with hq
  set p := ‖P g‖ with hp
  set c := √(1 - q ^ 2) with hcdef
  have hq0 : 0 ≤ q := norm_nonneg _
  have hp0 : 0 ≤ p := norm_nonneg _
  have hpy : p ^ 2 + q ^ 2 = ‖g‖ ^ 2 := hP.pythag g
  have hc0 : 0 < c := Real.sqrt_pos.2 hc
  have hc2 : c ^ 2 = 1 - q ^ 2 := Real.sq_sqrt hc.le
  have hq1 : q ≤ 1 := by nlinarith [norm_nonneg g]
  have hpc : p ≤ c := by
    have : p ^ 2 ≤ c ^ 2 := by nlinarith [norm_nonneg g]
    exact (abs_le_of_sq_le_sq' this hc0.le).2
  set h := c⁻¹ • P g with hh
  have hnh : ‖h‖ = p / c := by
    rw [hh, norm_smul, Real.norm_eq_abs, abs_of_pos (inv_pos.2 hc0)]
    ring
  have hh1 : ‖h‖ ≤ 1 := by
    rw [hnh, div_le_one hc0]; exact hpc
  refine ⟨hh1, ?_⟩
  have hS0 : 0 ≤ arcsin q := Real.arcsin_nonneg.2 hq0
  have hSπ : arcsin q ≤ π := (Real.arcsin_le_pi_div_two q).trans (by linarith [Real.pi_pos])
  rw [phi_le_iff hg hh1 hS0 hSπ, Real.cos_arcsin, ← hcdef, cphi]
  -- ⟪g, h⟫ = p² / c
  have hinner : ⟪g, h⟫ = p ^ 2 / c := by
    rw [hh, real_inner_smul_right, hP.inner_self_P, ← hp]
    field_simp
  rw [hinner]
  set A := √(1 - ‖g‖ ^ 2) with hA
  set B := √(1 - ‖h‖ ^ 2) with hB
  have hA2 : A ^ 2 = c ^ 2 - p ^ 2 := by
    rw [hA, Real.sq_sqrt (by nlinarith [norm_nonneg g]), hc2]; linarith
  have hB2 : B ^ 2 = (c ^ 2 - p ^ 2) / c ^ 2 := by
    rw [hB, Real.sq_sqrt (by nlinarith [norm_nonneg h]), hnh]
    field_simp
  have hA0 : 0 ≤ A := Real.sqrt_nonneg _
  have hB0 : 0 ≤ B := Real.sqrt_nonneg _
  have hD0 : 0 ≤ c ^ 2 - p ^ 2 := by nlinarith
  have hcAB : c * (A * B) = c ^ 2 - p ^ 2 := by
    have hsq : (c * (A * B)) ^ 2 = (c ^ 2 - p ^ 2) ^ 2 := by
      rw [mul_pow, mul_pow, hA2, hB2]
      field_simp
      try ring
    exact (pow_left_inj₀ (by positivity) hD0 two_ne_zero).1 hsq
  have hAB : A * B = (c ^ 2 - p ^ 2) / c := by
    rw [eq_div_iff hc0.ne']
    linarith [hcAB]
  have hsum : p ^ 2 / c + A * B = c := by
    rw [hAB, ← add_div, div_eq_iff hc0.ne']
    ring
  linarith [hsum]

/-- **Lemma 3 (nodewise O2 preservation).** -/
theorem node_step {m : ℕ} (μ : ContinuousMultilinearMap ℝ (fun _ : Fin m => G) G) (hμ : ‖μ‖ ≤ 1)
    (P : G →L[ℝ] G) (hP : IsOrthProj P) {η : ℝ} (hη0 : 0 ≤ η)
    (F R : Fin m → G) (ρ χ : Fin m → ℝ) (hdom : ∀ i, Dom (F i) (R i) (ρ i) (χ i))
    (hTC : ‖μ R - P (μ R)‖ ≤ η * ∏ i, ‖R i‖) :
    ∃ θ ∈ Set.Icc 0 (arcsin η), Dom (μ F) (P (μ R)) (Real.cos θ * ∏ i, ρ i) (θ + ∑ i, χ i) := by
  classical
  choose Rh hRh using fun i => (hdom i).2.2
  have hF : ∀ i, ‖F i‖ ≤ 1 := fun i => (hdom i).1
  have hρ : ∀ i, 0 ≤ ρ i := fun i => (hdom i).2.1
  have hRh1 : ∀ i, ‖Rh i‖ ≤ 1 := fun i => (hRh i).1
  have hRdef : R = fun i => ρ i • Rh i := funext fun i => (hRh i).2.1
  have hχ : ∀ i, phi (F i) (Rh i) ≤ χ i := fun i => (hRh i).2.2
  have hχ0 : 0 ≤ ∑ i, χ i := Finset.sum_nonneg fun i _ => (phi_nonneg _ _).trans (hχ i)
  set f := μ F with hf
  set g := μ Rh with hg
  set ρ0 := ∏ i, ρ i with hρ0
  have hf1 : ‖f‖ ≤ 1 := norm_apply_le_one μ hμ F hF
  have hg1 : ‖g‖ ≤ 1 := norm_apply_le_one μ hμ Rh hRh1
  have hμR : μ R = ρ0 • g := by rw [hRdef, μ.map_smul_univ]
  have hphi : phi f g ≤ ∑ i, χ i :=
    (phi_multilinear_le μ hμ F Rh hF hRh1).trans (Finset.sum_le_sum fun i _ => hχ i)
  have hρ00 : 0 ≤ ρ0 := Finset.prod_nonneg fun i _ => hρ i
  rcases eq_or_lt_of_le hρ00 with hz | hpos
  · -- ∏ ρᵢ = 0: the reduced branch vanishes
    refine ⟨0, ⟨le_rfl, Real.arcsin_nonneg.2 hη0⟩, ?_⟩
    have hPR : P (μ R) = 0 := by rw [hμR, ← hz, zero_smul, map_zero]
    rw [hPR, ← hz, mul_zero, zero_add]
    exact dom_of_zero hf1 hχ0
  · set q := ‖g - P g‖ with hq
    have hq0 : 0 ≤ q := norm_nonneg _
    -- trajectory closure gives q ≤ η
    have hprodR : ∏ i, ‖R i‖ ≤ ρ0 := by
      rw [hRdef, hρ0]
      apply Finset.prod_le_prod (fun i _ => norm_nonneg _)
      intro i _
      rw [norm_smul, Real.norm_eq_abs, abs_of_nonneg (hρ i)]
      exact mul_le_of_le_one_right (hρ i) (hRh1 i)
    have hTC' : ρ0 * q ≤ η * ρ0 := by
      have e : μ R - P (μ R) = ρ0 • (g - P g) := by
        rw [hμR, map_smul, smul_sub]
      rw [e, norm_smul, Real.norm_eq_abs, abs_of_nonneg hρ00] at hTC
      exact hTC.trans (mul_le_mul_of_nonneg_left hprodR hη0)
    have hqη : q ≤ η := by
      have := hTC'
      nlinarith
    have hθ : arcsin q ∈ Set.Icc 0 (arcsin η) :=
      ⟨Real.arcsin_nonneg.2 hq0, Real.arcsin_le_arcsin hqη⟩
    refine ⟨arcsin q, hθ, ?_⟩
    rw [Real.cos_arcsin]
    have hPR : P (μ R) = ρ0 • P g := by rw [hμR, map_smul]
    rcases eq_or_lt_of_le (show 0 ≤ 1 - q ^ 2 by
        have := hP.pythag g; nlinarith [norm_nonneg g, norm_nonneg (P g)]) with hc0 | hcpos
    · -- q = 1: P g = 0
      have hPg : P g = 0 := by
        have hpy := hP.pythag g
        have : ‖P g‖ ^ 2 ≤ 0 := by nlinarith [norm_nonneg g]
        exact norm_eq_zero.1 (by nlinarith [norm_nonneg (P g)])
      rw [hPR, hPg, smul_zero, ← hc0, Real.sqrt_zero, zero_mul]
      exact dom_of_zero hf1 (add_nonneg hθ.1 hχ0)
    · obtain ⟨hh1, hphih⟩ := phi_proj hP hg1 hcpos
      set c := √(1 - q ^ 2) with hcdef
      have hc0 : 0 < c := Real.sqrt_pos.2 hcpos
      refine ⟨hf1, mul_nonneg hc0.le hρ00, c⁻¹ • P g, hh1, ?_, ?_⟩
      · rw [hPR, smul_smul]
        congr 1
        field_simp
      · calc phi f (c⁻¹ • P g) ≤ phi f g + phi g (c⁻¹ • P g) := phi_triangle _ _ _
          _ ≤ (∑ i, χ i) + arcsin q := add_le_add hphi hphih
          _ = arcsin q + ∑ i, χ i := add_comm _ _

/-- **Root reading.** No closure is needed at the root. -/
theorem root_step {m : ℕ} (μ : ContinuousMultilinearMap ℝ (fun _ : Fin m => G) G) (hμ : ‖μ‖ ≤ 1)
    (P : G →L[ℝ] G) (hP : IsOrthProj P)
    (F R : Fin m → G) (ρ χ : Fin m → ℝ) (hdom : ∀ i, Dom (F i) (R i) (ρ i) (χ i)) :
    ‖P (μ F) - P (μ R)‖ ^ 2 ≤
      1 - 2 * (∏ i, ρ i) * Real.cos (min (∑ i, χ i) π) + (∏ i, ρ i) ^ 2 := by
  classical
  choose Rh hRh using fun i => (hdom i).2.2
  have hF : ∀ i, ‖F i‖ ≤ 1 := fun i => (hdom i).1
  have hρ : ∀ i, 0 ≤ ρ i := fun i => (hdom i).2.1
  have hRh1 : ∀ i, ‖Rh i‖ ≤ 1 := fun i => (hRh i).1
  have hRdef : R = fun i => ρ i • Rh i := funext fun i => (hRh i).2.1
  have hχ : ∀ i, phi (F i) (Rh i) ≤ χ i := fun i => (hRh i).2.2
  have hf1 : ‖μ F‖ ≤ 1 := norm_apply_le_one μ hμ F hF
  have hg1 : ‖μ Rh‖ ≤ 1 := norm_apply_le_one μ hμ Rh hRh1
  have hρ00 : 0 ≤ ∏ i, ρ i := Finset.prod_nonneg fun i _ => hρ i
  have hμR : μ R = (∏ i, ρ i) • μ Rh := by rw [hRdef, μ.map_smul_univ]
  have hphi : phi (μ F) (μ Rh) ≤ min (∑ i, χ i) π :=
    le_min ((phi_multilinear_le μ hμ F Rh hF hRh1).trans (Finset.sum_le_sum fun i _ => hχ i))
      (phi_le_pi _ _)
  have hS0 : 0 ≤ min (∑ i, χ i) π := (phi_nonneg _ _).trans hphi
  have hN := normSq_sub_le hf1 hg1 hS0 (min_le_right _ _) hphi hρ00
  have hproj : ‖P (μ F) - P (μ R)‖ ≤ ‖μ F - (∏ i, ρ i) • μ Rh‖ := by
    rw [← map_sub, hμR]
    exact hP.norm_le _
  calc ‖P (μ F) - P (μ R)‖ ^ 2 ≤ ‖μ F - (∏ i, ρ i) • μ Rh‖ ^ 2 :=
        pow_le_pow_left₀ (norm_nonneg _) hproj 2
    _ ≤ _ := by linarith [hN]

end PMT
