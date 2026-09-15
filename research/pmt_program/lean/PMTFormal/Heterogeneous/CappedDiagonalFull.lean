/-
H3 proved: the capped-equal-angle (water-filling) reduction.

For defects `η_i ≥ 0`, with `α_i = arcsin η_i`,

  `gBox η = sup_{τ ∈ [0, π/2]} |1 - ∏ w(min(α_i, τ))|`,

and the supremum is attained. `gBox` is therefore a one-dimensional maximisation.

Proof outline (all steps below are machine-checked):
1. `log_cos_tangent`: for `x, y ∈ [0, π/2)`, `log cos x ≤ log cos y - tan y · (x - y)`
   (monotonicity of `log cos t + tan y · t` on each side of `y`).
2. `cos_le_capped_mul_exp`: for `x ∈ [0, α]`, `τ ∈ [0, π/2)`, `c = min(α, τ)`,
   `cos x ≤ cos c · exp(-tan τ · (x - c))`.
3. `prod_cos_le_waterfill`: for `θ` in the box with `Σ θ ≥ Σ min(α_i, τ)`,
   `∏ cos θ_i ≤ ∏ cos min(α_i, τ)` (the case `τ = π/2` forces `θ = α`).
4. `exists_capped_level`: intermediate value theorem for `τ ↦ Σ min(α_i, τ)`.
5. `cos_sum_le_prod_cos_list`: `cos(Σ θ) ≤ ∏ cos θ` when `θ_i ≥ 0`, `Σ θ ≤ π/2` (Lemma 6.1, lists).
6. `box_value_le_capped`: with `Θ' = min(Σ θ, π)` and a level `τ` with `Σ min(α_i, τ) = Θ'`,
   `|1 - ∏ w(θ_i)|² = 1 + C² - 2C cos Σθ ≤ 1 + C² - 2C cos Θ' ≤ 1 + C_c² - 2C_c cos Θ'`,
   using `C ≤ C_c` and `C + C_c ≥ 2 cos Θ'`.

Statements:
* `PMT.capped_equal_angle`   `CappedEqualAngle η` for every `η ≥ 0` (H3)
* `PMT.gBox_eq_capped`       `gBox η = sSup (cappedValues η)`
* `PMT.gBox_eq_capped_max`   `∃ τ ∈ [0, π/2], gBox η = |1 - ∏ w(min(arcsin η_i, τ))|`
-/
import PMTFormal.Heterogeneous.CappedDiagonal
import PMTFormal.Heterogeneous.Attainment

open Real

namespace PMT

/-! ### Step 1: tangent inequality for `log cos` -/

theorem log_cos_tangent {x y : ℝ} (hx0 : 0 ≤ x) (hx : x < π / 2) (hy0 : 0 ≤ y) (hy : y < π / 2) :
    Real.log (Real.cos x) ≤ Real.log (Real.cos y) - Real.tan y * (x - y) := by
  set g : ℝ → ℝ := fun t => Real.log (Real.cos t) + Real.tan y * t with hg
  have hmem : ∀ t, 0 ≤ t → t < π / 2 → t ∈ Set.Ioo (-(π / 2)) (π / 2) := fun t h0 h1 =>
    ⟨by linarith [Real.pi_pos], h1⟩
  have hderiv : ∀ t ∈ Set.Ioo (-(π / 2)) (π / 2),
      HasDerivAt g (Real.tan y - Real.tan t) t := by
    intro t ht
    have h1 := (Real.hasDerivAt_cos t).log (Real.cos_pos_of_mem_Ioo ht).ne'
    have h2 := (hasDerivAt_id t).const_mul (Real.tan y)
    exact (h1.add h2).congr_deriv (by simp only [Real.tan_eq_sin_div_cos]; ring)
  have hcont : ∀ a b, 0 ≤ a → b < π / 2 → ContinuousOn g (Set.Icc a b) := fun a b ha hb t ht =>
    (hderiv t (hmem t (ha.trans ht.1) (ht.2.trans_lt hb))).continuousAt.continuousWithinAt
  have hdiff : ∀ a b, 0 ≤ a → b < π / 2 → DifferentiableOn ℝ g (interior (Set.Icc a b)) :=
    fun a b ha hb t ht => by
      rw [interior_Icc] at ht
      exact (hderiv t (hmem t (ha.trans ht.1.le) (ht.2.trans hb))).differentiableAt.differentiableWithinAt
  have hgxy : g x ≤ g y := by
    rcases le_total x y with hxy | hxy
    · have hmono : MonotoneOn g (Set.Icc x y) := by
        refine monotoneOn_of_deriv_nonneg (convex_Icc x y) (hcont x y hx0 hy) (hdiff x y hx0 hy) ?_
        intro t ht
        rw [interior_Icc] at ht
        rw [(hderiv t (hmem t (hx0.trans ht.1.le) (ht.2.trans hy))).deriv, sub_nonneg]
        exact Real.strictMonoOn_tan.monotoneOn (hmem t (hx0.trans ht.1.le) (ht.2.trans hy))
          (hmem y hy0 hy) ht.2.le
      exact hmono ⟨le_rfl, hxy⟩ ⟨hxy, le_rfl⟩ hxy
    · have hanti : AntitoneOn g (Set.Icc y x) := by
        refine antitoneOn_of_deriv_nonpos (convex_Icc y x) (hcont y x hy0 hx) (hdiff y x hy0 hx) ?_
        intro t ht
        rw [interior_Icc] at ht
        rw [(hderiv t (hmem t (hy0.trans ht.1.le) (ht.2.trans hx))).deriv, sub_nonpos]
        exact Real.strictMonoOn_tan.monotoneOn (hmem y hy0 hy)
          (hmem t (hy0.trans ht.1.le) (ht.2.trans hx)) ht.1.le
      exact hanti ⟨le_rfl, hxy⟩ ⟨hxy, le_rfl⟩ hxy
  simp only [hg] at hgxy
  linarith

/-! ### Step 2: pointwise multiplicative form -/

theorem cos_le_capped_mul_exp {x a τ : ℝ} (hx0 : 0 ≤ x) (hxa : x ≤ a) (ha : a ≤ π / 2)
    (hτ0 : 0 ≤ τ) (hτ : τ < π / 2) :
    Real.cos x ≤ Real.cos (min a τ) * Real.exp (-(Real.tan τ * (x - min a τ))) := by
  set c := min a τ with hc
  have hc0 : 0 ≤ c := le_min (hx0.trans hxa) hτ0
  have hcτ : c ≤ τ := min_le_right _ _
  have hcπ : c < π / 2 := hcτ.trans_lt hτ
  have hcos_c : 0 < Real.cos c := Real.cos_pos_of_mem_Ioo ⟨by linarith [Real.pi_pos], hcπ⟩
  rcases lt_or_ge x (π / 2) with hxπ | hxπ
  · have htan : Real.tan c ≤ Real.tan τ :=
      Real.strictMonoOn_tan.monotoneOn ⟨by linarith [Real.pi_pos], hcπ⟩
        ⟨by linarith [Real.pi_pos], hτ⟩ hcτ
    have hslope : (Real.tan τ - Real.tan c) * (x - c) ≤ 0 := by
      rcases le_total a τ with haτ | haτ
      · have : c = a := min_eq_left haτ
        exact mul_nonpos_of_nonneg_of_nonpos (sub_nonneg.2 htan) (by rw [this]; linarith)
      · have : c = τ := min_eq_right haτ
        rw [this, sub_self, zero_mul]
    have hlog := log_cos_tangent hx0 hxπ hc0 hcπ
    have hcos_x : 0 < Real.cos x := Real.cos_pos_of_mem_Ioo ⟨by linarith [Real.pi_pos], hxπ⟩
    calc Real.cos x = Real.exp (Real.log (Real.cos x)) := (Real.exp_log hcos_x).symm
      _ ≤ Real.exp (Real.log (Real.cos c) - Real.tan τ * (x - c)) :=
          Real.exp_le_exp.2 (by nlinarith [hlog, hslope])
      _ = Real.cos c * Real.exp (-(Real.tan τ * (x - c))) := by
          rw [sub_eq_add_neg, Real.exp_add, Real.exp_log hcos_c]
  · have hxeq : x = π / 2 := le_antisymm (hxa.trans ha) hxπ
    rw [hxeq, Real.cos_pi_div_two]
    exact mul_nonneg hcos_c.le (Real.exp_pos _).le

/-! ### Step 3: water-filling maximises `∏ cos` -/

theorem prod_cos_le_capped_mul_exp {τ : ℝ} (hτ0 : 0 ≤ τ) (hτ : τ < π / 2) :
    ∀ {θ η : List ℝ}, List.Forall₂ BoxRel θ η →
      (θ.map Real.cos).prod ≤ ((cappedAngles η τ).map Real.cos).prod *
        Real.exp (-(Real.tan τ * (θ.sum - (cappedAngles η τ).sum))) := by
  intro θ η h
  induction h with
  | nil => simp [cappedAngles]
  | @cons x e l η' hxe htail ih =>
    have hxmem : x ∈ Set.Icc 0 (π / 2) := ⟨hxe.nonneg, hxe.le_pi_div_two⟩
    have hP0 : 0 ≤ (l.map Real.cos).prod :=
      List.prod_nonneg fun y hy => by
        obtain ⟨z, hz, rfl⟩ := List.mem_map.1 hy
        exact Real.cos_nonneg_of_mem_Icc ⟨by linarith [(box_mem htail z hz).1, Real.pi_pos],
          (box_mem htail z hz).2⟩
    have hpt := cos_le_capped_mul_exp hxe.nonneg hxe.2 (Real.arcsin_le_pi_div_two e) hτ0 hτ
    have hcap : cappedAngles (e :: η') τ = min (arcsin e) τ :: cappedAngles η' τ := rfl
    rw [hcap, List.map_cons, List.prod_cons, List.map_cons, List.prod_cons, List.sum_cons,
      List.sum_cons]
    calc Real.cos x * (l.map Real.cos).prod
        ≤ (Real.cos (min (arcsin e) τ) * Real.exp (-(Real.tan τ * (x - min (arcsin e) τ)))) *
          (((cappedAngles η' τ).map Real.cos).prod *
            Real.exp (-(Real.tan τ * (l.sum - (cappedAngles η' τ).sum)))) :=
          mul_le_mul hpt ih hP0 (le_trans (Real.cos_nonneg_of_mem_Icc
            ⟨by linarith [hxmem.1, Real.pi_pos], hxmem.2⟩) hpt)
      _ = Real.cos (min (arcsin e) τ) * ((cappedAngles η' τ).map Real.cos).prod *
          Real.exp (-(Real.tan τ * (x + l.sum - (min (arcsin e) τ + (cappedAngles η' τ).sum)))) := by
          rw [show -(Real.tan τ * (x + l.sum - (min (arcsin e) τ + (cappedAngles η' τ).sum))) =
            -(Real.tan τ * (x - min (arcsin e) τ)) + -(Real.tan τ * (l.sum - (cappedAngles η' τ).sum))
            by ring, Real.exp_add]
          ring

theorem eq_of_forall₂_le_of_sum_le : ∀ {θ α : List ℝ}, List.Forall₂ (· ≤ ·) θ α →
    α.sum ≤ θ.sum → θ = α := by
  intro θ α h hs
  induction h with
  | nil => rfl
  | @cons a b l m hab htail ih =>
    rw [List.sum_cons, List.sum_cons] at hs
    have hlm : l.sum ≤ m.sum := by
      clear ih hs
      induction htail with
      | nil => simp
      | cons h _ ih' => simp only [List.sum_cons]; linarith
    have hab' : a = b := le_antisymm hab (by linarith)
    rw [hab', ih (by linarith)]

theorem cappedAngles_pi_div_two (η : List ℝ) : cappedAngles η (π / 2) = η.map arcsin := by
  unfold cappedAngles
  exact List.map_congr_left fun e _ => min_eq_left (Real.arcsin_le_pi_div_two e)

theorem forall₂_le_arcsin {θ η : List ℝ} (h : List.Forall₂ BoxRel θ η) :
    List.Forall₂ (· ≤ ·) θ (η.map arcsin) := by
  rw [List.forall₂_map_right_iff]
  exact h.imp fun _ _ hb => hb.2

theorem cos_capped_nonneg (e τ : ℝ) (hτ : τ ∈ Set.Icc 0 (π / 2)) :
    0 ≤ Real.cos (min (arcsin e) τ) :=
  Real.cos_nonneg_of_mem_Icc ⟨le_min (Real.neg_pi_div_two_le_arcsin e)
    (by linarith [hτ.1, Real.pi_pos]), (min_le_right _ _).trans hτ.2⟩

theorem prod_cos_capped_nonneg (η : List ℝ) {τ : ℝ} (hτ : τ ∈ Set.Icc 0 (π / 2)) :
    0 ≤ ((cappedAngles η τ).map Real.cos).prod := by
  induction η with
  | nil => simp [cappedAngles]
  | cons e η ih =>
    show 0 ≤ Real.cos (min (arcsin e) τ) * ((cappedAngles η τ).map Real.cos).prod
    exact mul_nonneg (cos_capped_nonneg e τ hτ) ih

/-- **Water-filling.** For `θ` in the box whose sum is at least the capped sum at level `τ`,
`∏ cos θ_i ≤ ∏ cos min(arcsin η_i, τ)`. -/
theorem prod_cos_le_waterfill {η θ : List ℝ} (hθ : θ ∈ box η) {τ : ℝ} (hτ : τ ∈ Set.Icc 0 (π / 2))
    (hsum : (cappedAngles η τ).sum ≤ θ.sum) :
    (θ.map Real.cos).prod ≤ ((cappedAngles η τ).map Real.cos).prod := by
  have h2 : List.Forall₂ BoxRel θ η := hθ
  rcases lt_or_eq_of_le hτ.2 with hlt | heq
  · have hmain := prod_cos_le_capped_mul_exp hτ.1 hlt h2
    have htan : 0 ≤ Real.tan τ := by
      rw [Real.tan_eq_sin_div_cos]
      exact div_nonneg (Real.sin_nonneg_of_nonneg_of_le_pi hτ.1 (by linarith [Real.pi_pos]))
        (Real.cos_nonneg_of_mem_Icc ⟨by linarith [hτ.1, Real.pi_pos], hτ.2⟩)
    have hexp : Real.exp (-(Real.tan τ * (θ.sum - (cappedAngles η τ).sum))) ≤ 1 := by
      rw [Real.exp_le_one_iff]
      nlinarith [mul_nonneg htan (sub_nonneg.2 hsum)]
    calc (θ.map Real.cos).prod ≤ ((cappedAngles η τ).map Real.cos).prod *
          Real.exp (-(Real.tan τ * (θ.sum - (cappedAngles η τ).sum))) := hmain
      _ ≤ ((cappedAngles η τ).map Real.cos).prod * 1 :=
          mul_le_mul_of_nonneg_left hexp (prod_cos_capped_nonneg η hτ)
      _ = _ := mul_one _
  · rw [heq, cappedAngles_pi_div_two] at hsum ⊢
    rw [eq_of_forall₂_le_of_sum_le (forall₂_le_arcsin h2) hsum]

/-! ### Step 4: a level with prescribed capped sum -/

theorem continuous_capped_sum (η : List ℝ) : Continuous fun τ => (cappedAngles η τ).sum := by
  induction η with
  | nil => simp only [cappedAngles, List.map_nil, List.sum_nil]; exact continuous_const
  | cons e η ih =>
    show Continuous fun τ => min (arcsin e) τ + (cappedAngles η τ).sum
    exact (continuous_const.min continuous_id).add ih

theorem capped_sum_zero {η : List ℝ} (hη : ∀ e ∈ η, 0 ≤ e) : (cappedAngles η 0).sum = 0 := by
  induction η with
  | nil => simp [cappedAngles]
  | cons e η ih =>
    show min (arcsin e) 0 + (cappedAngles η 0).sum = 0
    rw [min_eq_right (Real.arcsin_nonneg.2 (hη e (by simp))), ih fun x hx => hη x (by simp [hx]),
      add_zero]

theorem exists_capped_level {η : List ℝ} (hη : ∀ e ∈ η, 0 ≤ e) {Θ : ℝ} (h0 : 0 ≤ Θ)
    (h1 : Θ ≤ (η.map arcsin).sum) :
    ∃ τ ∈ Set.Icc 0 (π / 2), (cappedAngles η τ).sum = Θ := by
  have hmem : Θ ∈ Set.Icc ((fun τ => (cappedAngles η τ).sum) 0)
      ((fun τ => (cappedAngles η τ).sum) (π / 2)) := by
    simp only
    rw [capped_sum_zero hη, cappedAngles_pi_div_two]
    exact ⟨h0, h1⟩
  obtain ⟨τ, hτ, hτeq⟩ := intermediate_value_Icc (by positivity : (0 : ℝ) ≤ π / 2)
    (continuous_capped_sum η).continuousOn hmem
  exact ⟨τ, hτ, hτeq⟩

/-! ### Step 5: Lemma 6.1 on lists -/

theorem cos_sum_le_prod_cos_list :
    ∀ (l : List ℝ), (∀ x ∈ l, 0 ≤ x) → l.sum ≤ π / 2 → Real.cos l.sum ≤ (l.map Real.cos).prod
  | [], _, _ => by simp
  | a :: l, hpos, hsum => by
    rw [List.sum_cons] at hsum ⊢
    rw [List.map_cons, List.prod_cons]
    have ha0 : 0 ≤ a := hpos a (by simp)
    have hl0 : 0 ≤ l.sum := List.sum_nonneg fun x hx => hpos x (by simp [hx])
    have ih := cos_sum_le_prod_cos_list l (fun x hx => hpos x (by simp [hx])) (by linarith)
    have hcosa : 0 ≤ Real.cos a := Real.cos_nonneg_of_mem_Icc ⟨by linarith [Real.pi_pos], by linarith⟩
    have hsina : 0 ≤ Real.sin a := Real.sin_nonneg_of_nonneg_of_le_pi ha0 (by linarith [Real.pi_pos])
    have hsinl : 0 ≤ Real.sin l.sum :=
      Real.sin_nonneg_of_nonneg_of_le_pi hl0 (by linarith [Real.pi_pos])
    rw [Real.cos_add]
    nlinarith [mul_nonneg hsina hsinl, mul_le_mul_of_nonneg_left ih hcosa]

/-! ### Step 6: every box value is dominated by a capped value -/

theorem box_sum_le {η θ : List ℝ} (hθ : θ ∈ box η) : θ.sum ≤ (η.map arcsin).sum := by
  have h : List.Forall₂ BoxRel θ η := hθ
  clear hθ
  induction h with
  | nil => simp
  | cons hab _ ih => simp only [List.map_cons, List.sum_cons]; linarith [hab.2]

theorem box_value_le_capped {η : List ℝ} (hη : ∀ e ∈ η, 0 ≤ e) {θ : List ℝ} (hθ : θ ∈ box η) :
    ∃ τ ∈ Set.Icc 0 (π / 2),
      ‖1 - (θ.map w).prod‖ ≤ ‖1 - ((cappedAngles η τ).map w).prod‖ := by
  have hmem := box_mem hθ
  have hΘ0 : 0 ≤ θ.sum := List.sum_nonneg fun x hx => (hmem x hx).1
  set Θ' := min θ.sum π with hΘ'
  have hΘ'0 : 0 ≤ Θ' := le_min hΘ0 Real.pi_pos.le
  have hΘ'le : Θ' ≤ θ.sum := min_le_left _ _
  obtain ⟨τ, hτ, hτsum⟩ := exists_capped_level hη hΘ'0 (hΘ'le.trans (box_sum_le hθ))
  refine ⟨τ, hτ, ?_⟩
  set C := (θ.map Real.cos).prod with hC
  set Cc := ((cappedAngles η τ).map Real.cos).prod with hCc
  have hC0 : 0 ≤ C := (prod_cos_le_scale zero_le_one le_rfl θ hmem).1
  have hCle : C ≤ Cc := prod_cos_le_waterfill hθ hτ (by rw [hτsum]; exact hΘ'le)
  have hcos : Real.cos Θ' ≤ Real.cos θ.sum := by
    rcases le_total θ.sum π with h | h
    · rw [hΘ', min_eq_left h]
    · rw [hΘ', min_eq_right h, Real.cos_pi]
      exact Real.neg_one_le_cos _
  have h2cos : 2 * Real.cos Θ' ≤ C + Cc := by
    by_cases hπ2 : Θ' ≤ π / 2
    · have hsum : θ.sum ≤ π / 2 := by
        rcases le_total θ.sum π with h | h
        · rwa [hΘ', min_eq_left h] at hπ2
        · rw [hΘ', min_eq_right h] at hπ2
          linarith [Real.pi_pos]
      have hL := cos_sum_le_prod_cos_list θ (fun x hx => (hmem x hx).1) hsum
      have : Θ' = θ.sum := by
        rw [hΘ']
        exact min_eq_left (by linarith [Real.pi_pos])
      rw [this]
      linarith
    · push Not at hπ2
      have : Real.cos Θ' ≤ 0 :=
        Real.cos_nonpos_of_pi_div_two_le_of_le hπ2.le (by linarith [min_le_right θ.sum π, Real.pi_pos])
      linarith [le_trans hC0 hCle]
  have hsq1 := norm_sq_one_sub_prod_w θ
  have hsq2 := norm_sq_one_sub_prod_w (cappedAngles η τ)
  rw [hτsum] at hsq2
  rw [← hC] at hsq1
  rw [← hCc] at hsq2
  have hsq : ‖1 - (θ.map w).prod‖ ^ 2 ≤ ‖1 - ((cappedAngles η τ).map w).prod‖ ^ 2 := by
    rw [hsq1, hsq2]
    nlinarith [mul_le_mul_of_nonneg_left hcos hC0,
      mul_nonneg (sub_nonneg.2 hCle) (by linarith : (0 : ℝ) ≤ C + Cc - 2 * Real.cos Θ')]
  exact (abs_le_of_sq_le_sq' hsq (norm_nonneg _)).2

/-! ### H3 -/

theorem zero_mem_box {η : List ℝ} (hη : ∀ e ∈ η, 0 ≤ e) : η.map (fun _ => (0 : ℝ)) ∈ box η := by
  show List.Forall₂ BoxRel _ η
  rw [List.forall₂_map_left_iff, List.forall₂_same]
  exact fun e he => ⟨le_rfl, Real.arcsin_nonneg.2 (hη e he)⟩

/-- **H3 (capped-equal-angle reduction), proved.** -/
theorem capped_equal_angle {η : List ℝ} (hη : ∀ e ∈ η, 0 ≤ e) : CappedEqualAngle η := by
  rw [cappedEqualAngle_iff hη]
  refine csSup_le (Set.Nonempty.image _ ⟨_, zero_mem_box hη⟩) ?_
  rintro _ ⟨θ, hθ, rfl⟩
  obtain ⟨τ, hτ, hle⟩ := box_value_le_capped hη hθ
  exact hle.trans (le_csSup (bddAbove_cappedValues η) ⟨τ, hτ, rfl⟩)

/-- `gBox` as a one-dimensional supremum. -/
theorem gBox_eq_capped {η : List ℝ} (hη : ∀ e ∈ η, 0 ≤ e) : gBox η = sSup (cappedValues η) :=
  capped_equal_angle hη

theorem continuous_capped_prod_w (η : List ℝ) :
    Continuous fun τ => ((cappedAngles η τ).map w).prod := by
  induction η with
  | nil => simp only [cappedAngles, List.map_nil, List.prod_nil]; exact continuous_const
  | cons e η ih =>
    show Continuous fun τ => w (min (arcsin e) τ) * ((cappedAngles η τ).map w).prod
    exact (continuous_w.comp (continuous_const.min continuous_id)).mul ih

/-- **`gBox` is attained on the water-filling curve.** -/
theorem gBox_eq_capped_max {η : List ℝ} (hη : ∀ e ∈ η, 0 ≤ e) :
    ∃ τ ∈ Set.Icc 0 (π / 2),
      gBox η = ‖1 - ((η.map fun e => min (arcsin e) τ).map w).prod‖ := by
  have hc : Continuous fun τ => ‖1 - ((cappedAngles η τ).map w).prod‖ :=
    (continuous_const.sub (continuous_capped_prod_w η)).norm
  obtain ⟨τ, hτ, hmax⟩ := isCompact_Icc.exists_isMaxOn
    (Set.nonempty_Icc.2 (by positivity : (0 : ℝ) ≤ π / 2)) hc.continuousOn
  refine ⟨τ, hτ, ?_⟩
  rw [gBox_eq_capped hη]
  have hg : IsGreatest (cappedValues η) ‖1 - ((cappedAngles η τ).map w).prod‖ :=
    ⟨⟨τ, hτ, rfl⟩, by rintro _ ⟨s, hs, rfl⟩; exact hmax hs⟩
  exact hg.csSup_eq

end PMT