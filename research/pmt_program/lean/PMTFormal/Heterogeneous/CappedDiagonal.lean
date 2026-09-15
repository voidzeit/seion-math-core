/-
Heterogeneous Theorem R, H3 (kept separate): the capped-equal-angle reduction.

H3 is an efficient-evaluation question about `gBox`; it is NOT used by the sharp heterogeneous
theorem (`heterogeneous_upper`, `heterogeneous_lower`, `heterogeneous_sSup`, `gBox_perm`,
`heterogeneous_placement_independent`). No other module imports this file except the library root.

The hypothesis is recorded as a `Prop`, not as an axiom and not as a `sorry`:

  `CappedEqualAngle η  :≡  gBox η = sup_{τ ∈ [0, π/2]} |1 - ∏ w(min(arcsin η_i, τ))|`

Statements:
* `PMT.cappedAngles`, `PMT.cappedValues`, `PMT.CappedEqualAngle`
* `PMT.cappedAngles_mem_box`         the capped curve stays in the box (`η_i ≥ 0`)
* `PMT.sSup_capped_le_gBox`          the easy half: capped supremum `≤ gBox`
* `PMT.cappedEqualAngle_iff`         H3 is equivalent to the hard half `gBox ≤ capped supremum`
* `PMT.cappedEqualAngle_replicate`   H3 holds for equal defects (via the Diagonal Lemma)
The general case is OPEN.
-/
import PMTFormal.Heterogeneous.Sharp

open Real

namespace PMT

/-- Capped equal angles `θ_i(τ) = min(arcsin η_i, τ)`. -/
noncomputable def cappedAngles (η : List ℝ) (τ : ℝ) : List ℝ :=
  η.map fun e => min (arcsin e) τ

/-- Values of `|1 - ∏ w|` along the capped curve, `τ ∈ [0, π/2]`. -/
noncomputable def cappedValues (η : List ℝ) : Set ℝ :=
  (fun τ => ‖1 - ((cappedAngles η τ).map w).prod‖) '' Set.Icc 0 (π / 2)

/-- **H3 (hypothesis, not assumed anywhere).** -/
def CappedEqualAngle (η : List ℝ) : Prop :=
  gBox η = sSup (cappedValues η)

theorem cappedAngles_mem_box {η : List ℝ} (hη : ∀ e ∈ η, 0 ≤ e) {τ : ℝ} (hτ : 0 ≤ τ) :
    cappedAngles η τ ∈ box η := by
  show List.Forall₂ BoxRel _ η
  rw [cappedAngles, List.forall₂_map_left_iff, List.forall₂_same]
  intro e he
  exact ⟨le_min (Real.arcsin_nonneg.2 (hη e he)) hτ, min_le_left _ _⟩

theorem bddAbove_cappedValues (η : List ℝ) : BddAbove (cappedValues η) :=
  ⟨2, by rintro _ ⟨τ, _, rfl⟩; exact norm_one_sub_prod_w_le_two _⟩

theorem cappedValues_nonempty (η : List ℝ) : (cappedValues η).Nonempty :=
  ⟨_, 0, ⟨le_rfl, by linarith [Real.pi_pos]⟩, rfl⟩

/-- The easy half of H3. -/
theorem sSup_capped_le_gBox {η : List ℝ} (hη : ∀ e ∈ η, 0 ≤ e) :
    sSup (cappedValues η) ≤ gBox η :=
  csSup_le (cappedValues_nonempty η) fun _ ⟨_, hτ, hy⟩ =>
    hy ▸ le_gBox (cappedAngles_mem_box hη hτ.1)

theorem cappedEqualAngle_iff {η : List ℝ} (hη : ∀ e ∈ η, 0 ≤ e) :
    CappedEqualAngle η ↔ gBox η ≤ sSup (cappedValues η) :=
  ⟨fun h => h.le, fun h => le_antisymm h (sSup_capped_le_gBox hη)⟩

/-- H3 holds when all defects are equal. -/
theorem cappedEqualAngle_replicate {η : ℝ} (hη0 : 0 < η) (n : ℕ) :
    CappedEqualAngle (List.replicate n η) := by
  have hη : ∀ e ∈ List.replicate n η, 0 ≤ e := fun e he => by
    rw [List.eq_of_mem_replicate he]; exact hη0.le
  rw [cappedEqualAngle_iff hη, uniform_gBox_eq hη0]
  refine csSup_le ⟨_, 0, ⟨le_rfl, Real.arcsin_nonneg.2 hη0.le⟩, rfl⟩ ?_
  rintro _ ⟨τ, hτ, rfl⟩
  refine le_csSup (bddAbove_cappedValues _)
    ⟨τ, ⟨hτ.1, hτ.2.trans (Real.arcsin_le_pi_div_two η)⟩, ?_⟩
  simp only [cappedAngles, List.map_replicate, min_eq_right hτ.2, List.prod_replicate]

end PMT
