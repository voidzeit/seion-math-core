/-
Heterogeneous Theorem R, part 1: the box constant (PMT-free).

For a list `η = (η_1, …, η_n)` of nodewise defects:

* `PMT.BoxRel θ e`        `θ ∈ [0, arcsin e]`
* `PMT.box η`             angle lists `θ` of the same length with `θ_i ∈ [0, arcsin η_i]`
* `PMT.gBox η`            `sup_{θ ∈ box η} |1 - ∏ w(θ_i)|`   (`w θ = cos θ · e^{iθ}`)
* `PMT.le_gBox`           every box value is below `gBox`
* `PMT.box_capped`        root reduction: for `θ ∈ box η` there is `θ' ∈ box η` with
                          `1 - 2 R cos(min(Θ, π)) + R² ≤ |1 - ∏ w(θ'_i)|²`
                          (`R = ∏ cos θ_i`, `Θ = Σ θ_i`). Proof: uniform angle scaling by `π/Θ`
                          when `Θ > π`; no Diagonal Lemma and no capped-equal-angle reduction.
* `PMT.forall₂_flatten_ofFn`  splitting a box list along a flattened family of defect lists

Nothing here assumes `0 ≤ η_i` or `η_i ≤ 1`: a negative defect gives an empty factor, and
`arcsin` saturates at `π/2` above `1`.
-/
import PMTFormal.Witness

open Real

namespace PMT

/-- Box relation between one angle and one defect: `θ ∈ [0, arcsin e]`. -/
def BoxRel (θ e : ℝ) : Prop := θ ∈ Set.Icc 0 (arcsin e)

/-- The angle box of a defect list. -/
def box (η : List ℝ) : Set (List ℝ) := {θ | List.Forall₂ BoxRel θ η}

/-- **Heterogeneous box constant** `G_box(η) = sup_{θ ∈ box η} |1 - ∏ w(θ_i)|`. -/
noncomputable def gBox (η : List ℝ) : ℝ :=
  sSup ((fun θ : List ℝ => ‖1 - (θ.map w).prod‖) '' box η)

theorem BoxRel.nonneg {θ e : ℝ} (h : BoxRel θ e) : 0 ≤ θ := h.1

theorem BoxRel.le_pi_div_two {θ e : ℝ} (h : BoxRel θ e) : θ ≤ π / 2 :=
  h.2.trans (Real.arcsin_le_pi_div_two e)

theorem BoxRel.defect_nonneg {θ e : ℝ} (h : BoxRel θ e) : 0 ≤ e :=
  Real.arcsin_nonneg.1 (h.1.trans h.2)

/-- `θ ∈ [0, arcsin e]` implies `sin θ ≤ e` (for every real `e`). -/
theorem BoxRel.sin_le {θ e : ℝ} (h : BoxRel θ e) : Real.sin θ ≤ e := by
  rcases le_or_gt e 1 with he1 | he1
  · calc Real.sin θ ≤ Real.sin (arcsin e) :=
          Real.sin_le_sin_of_le_of_le_pi_div_two (by linarith [Real.pi_pos, h.1])
            (Real.arcsin_le_pi_div_two e) h.2
      _ = e := Real.sin_arcsin (by linarith [h.defect_nonneg]) he1
  · exact (Real.sin_le_one θ).trans he1.le

theorem BoxRel.sin_nonneg {θ e : ℝ} (h : BoxRel θ e) : 0 ≤ Real.sin θ :=
  Real.sin_nonneg_of_nonneg_of_le_pi h.1 (by linarith [h.le_pi_div_two, Real.pi_pos])

theorem norm_w_le_one (θ : ℝ) : ‖w θ‖ ≤ 1 := by
  rw [w, norm_mul, Complex.norm_exp_ofReal_mul_I, mul_one, Complex.norm_real, Real.norm_eq_abs]
  exact Real.abs_cos_le_one θ

theorem norm_prod_w_le_one : ∀ l : List ℝ, ‖(l.map w).prod‖ ≤ 1
  | [] => by simp
  | a :: l => by
    rw [List.map_cons, List.prod_cons, norm_mul]
    exact mul_le_one₀ (norm_w_le_one a) (norm_nonneg _) (norm_prod_w_le_one l)

theorem norm_one_sub_prod_w_le_two (l : List ℝ) : ‖1 - (l.map w).prod‖ ≤ 2 :=
  (norm_sub_le _ _).trans (by rw [norm_one]; linarith [norm_prod_w_le_one l])

theorem bddAbove_box_image (η : List ℝ) :
    BddAbove ((fun θ : List ℝ => ‖1 - (θ.map w).prod‖) '' box η) :=
  ⟨2, by rintro _ ⟨θ, _, rfl⟩; exact norm_one_sub_prod_w_le_two θ⟩

theorem le_gBox {η θ : List ℝ} (hθ : θ ∈ box η) : ‖1 - (θ.map w).prod‖ ≤ gBox η :=
  le_csSup (bddAbove_box_image η) ⟨θ, hθ, rfl⟩

theorem box_mem {η θ : List ℝ} (hθ : θ ∈ box η) : ∀ x ∈ θ, x ∈ Set.Icc 0 (π / 2) := by
  have h : List.Forall₂ BoxRel θ η := hθ
  clear hθ
  induction h with
  | nil => simp
  | cons hab _ ih =>
    intro x hx
    rcases List.mem_cons.1 hx with rfl | hx
    · exact ⟨hab.nonneg, hab.le_pi_div_two⟩
    · exact ih x hx

theorem box_scale {η θ : List ℝ} (hθ : θ ∈ box η) {c : ℝ} (hc0 : 0 ≤ c) (hc1 : c ≤ 1) :
    θ.map (c * ·) ∈ box η := by
  show List.Forall₂ BoxRel _ η
  rw [List.forall₂_map_left_iff]
  exact List.Forall₂.imp
    (fun a _ h => ⟨mul_nonneg hc0 h.1, (by nlinarith [h.1] : c * a ≤ a).trans h.2⟩) hθ

/-- Scaling angles in `[0, π/2]` by `c ∈ [0, 1]` does not decrease `∏ cos`. -/
theorem prod_cos_le_scale {c : ℝ} (hc0 : 0 ≤ c) (hc1 : c ≤ 1) :
    ∀ l : List ℝ, (∀ x ∈ l, x ∈ Set.Icc 0 (π / 2)) →
      0 ≤ (l.map Real.cos).prod ∧ (l.map Real.cos).prod ≤ ((l.map (c * ·)).map Real.cos).prod
  | [] => fun _ => by simp
  | a :: l => fun h => by
    have ha := h a (by simp)
    obtain ⟨h0, h1⟩ := prod_cos_le_scale hc0 hc1 l (fun x hx => h x (by simp [hx]))
    have hcos : 0 ≤ Real.cos a :=
      Real.cos_nonneg_of_mem_Icc ⟨by linarith [ha.1, Real.pi_pos], ha.2⟩
    have hca : Real.cos a ≤ Real.cos (c * a) :=
      Real.cos_le_cos_of_nonneg_of_le_pi (mul_nonneg hc0 ha.1) (by linarith [ha.2, Real.pi_pos])
        (by nlinarith [ha.1])
    simp only [List.map_cons, List.prod_cons]
    exact ⟨mul_nonneg hcos h0, mul_le_mul hca h1 h0 (hcos.trans hca)⟩

theorem norm_sq_one_sub_prod_w (l : List ℝ) :
    ‖1 - (l.map w).prod‖ ^ 2 =
      1 - 2 * (l.map Real.cos).prod * Real.cos l.sum + (l.map Real.cos).prod ^ 2 := by
  rw [← Complex.normSq_eq_norm_sq, list_prod_w, normSq_one_sub_mul_exp]

/-- **Root reduction inside the box.** -/
theorem box_capped {η θ : List ℝ} (hθ : θ ∈ box η) :
    ∃ θ' ∈ box η,
      1 - 2 * (θ.map Real.cos).prod * Real.cos (min θ.sum π) + (θ.map Real.cos).prod ^ 2
        ≤ ‖1 - (θ'.map w).prod‖ ^ 2 := by
  have hmem := box_mem hθ
  by_cases hΘπ : θ.sum ≤ π
  · refine ⟨θ, hθ, ?_⟩
    rw [min_eq_left hΘπ, norm_sq_one_sub_prod_w]
  · push Not at hΘπ
    have hΘpos : 0 < θ.sum := Real.pi_pos.trans hΘπ
    set c := π / θ.sum with hc
    have hc0 : 0 ≤ c := by positivity
    have hc1 : c ≤ 1 := by rw [hc, div_le_one hΘpos]; exact hΘπ.le
    refine ⟨θ.map (c * ·), box_scale hθ hc0 hc1, ?_⟩
    obtain ⟨hC0, hCle⟩ := prod_cos_le_scale hc0 hc1 θ hmem
    have hsum : (θ.map (c * ·)).sum = π := by
      rw [List.sum_map_mul_left, hc, List.map_id']
      field_simp
    rw [min_eq_right hΘπ.le, Real.cos_pi, norm_sq_one_sub_prod_w, hsum, Real.cos_pi]
    nlinarith

/-- Splitting a list related to a flattened family. -/
theorem forall₂_flatten_ofFn {α β : Type*} {r : α → β → Prop} :
    ∀ {m : ℕ} (f : Fin m → List β) (l : List α), List.Forall₂ r l (List.ofFn f).flatten →
      ∃ g : Fin m → List α, l = (List.ofFn g).flatten ∧ ∀ i, List.Forall₂ r (g i) (f i)
  | 0, f, l, h => ⟨fun i => i.elim0, by simpa using h, fun i => i.elim0⟩
  | m + 1, f, l, h => by
    rw [List.ofFn_succ, List.flatten_cons] at h
    obtain ⟨g, hg, hgi⟩ :=
      forall₂_flatten_ofFn (fun i => f i.succ) _ (List.forall₂_drop_append _ _ _ h)
    refine ⟨fun i => Fin.cases (l.take (f 0).length) g i, ?_, ?_⟩
    · rw [List.ofFn_succ, List.flatten_cons]
      simp only [Fin.cases_zero, Fin.cases_succ]
      rw [← hg, List.take_append_drop]
    · intro i
      refine Fin.cases ?_ (fun j => ?_) i
      · simpa using List.forall₂_take_append _ _ _ h
      · simpa using hgi j

/-- Joining box lists along a flattened family. -/
theorem forall₂_flatten_ofFn_of {α β : Type*} {r : α → β → Prop} {m : ℕ}
    (g : Fin m → List α) (f : Fin m → List β) (h : ∀ i, List.Forall₂ r (g i) (f i)) :
    List.Forall₂ r (List.ofFn g).flatten (List.ofFn f).flatten := by
  induction m with
  | zero => simp
  | succ m ih =>
    rw [List.ofFn_succ, List.flatten_cons, List.ofFn_succ, List.flatten_cons]
    exact List.rel_append (h 0) (ih (fun i => g i.succ) (fun i => f i.succ) (fun i => h i.succ))

end PMT
