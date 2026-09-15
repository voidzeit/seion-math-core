/-
Heterogeneous Theorem R, scaled form: the degenerate case `M_v = 0` (separate lemma).

If some internal node has `M_v = 0`, then `μ_v = 0`, both evaluations vanish at that node, and by
multilinearity they vanish at every ancestor; hence the projected root error is `0` and the scaled
bound holds trivially (`Λ_T ≥ 0`, `gBox ≥ 0`). Otherwise every `M_v > 0` and `Scaled.lean` applies.
(In Lean `ρ / 0 = 0`, so the skeleton records defect `0` at such a node; the bound is unaffected.)

Statements:
* `PMT.SPMTree.AdmFull0`, `PMT.SPMTree.RootAdmFull0`   admissibility with `M_v ≥ 0`
* `PMT.SPMTree.err_zero_of_hasZeroM`                   some `M_v = 0` ⟹ `err = 0`
* `PMT.gBox_nonneg`
* `PMT.heterogeneous_scaled_upper_nonneg`              `err ≤ Λ_T · gBox(childDefects)` for `M_v ≥ 0`
-/
import PMTFormal.Heterogeneous.Scaled

open Real
open scoped RealInnerProductSpace

namespace PMT

theorem gBox_nonneg (η : List ℝ) : 0 ≤ gBox η :=
  Real.sSup_nonneg fun _ ⟨_, _, h⟩ => h ▸ norm_nonneg _

namespace SPMTree

variable {G : Type*} [NormedAddCommGroup G] [InnerProductSpace ℝ G]

/-- Scaled heterogeneous PMT-A admissibility allowing `M_v = 0`. -/
def AdmFull0 : SPMTree G → Prop
  | leaf _ => True
  | node _ M ρ μ P ch => 0 ≤ M ∧ 0 ≤ ρ ∧ ‖μ‖ ≤ M ∧ IsOrthProj P ∧
      (∀ x : (i : Fin _) → G, (∀ i, (ch i).InRan (x i)) →
        ‖μ x - P (μ x)‖ ≤ ρ * ∏ i, ‖x i‖) ∧
      ∀ i, (ch i).AdmFull0

def RootAdmFull0 : SPMTree G → Prop
  | leaf _ => False
  | node m M ρ μ P ch => (node m M ρ μ P ch).AdmFull0

/-- Some internal node has `M_v = 0`. -/
def HasZeroM : SPMTree G → Prop
  | leaf _ => False
  | node _ M _ _ _ ch => M = 0 ∨ ∃ i, (ch i).HasZeroM

theorem admFull_of_admFull0 : ∀ t : SPMTree G, t.AdmFull0 → ¬ t.HasZeroM → t.AdmFull
  | leaf _, _, _ => trivial
  | node _ _ _ _ _ ch, ⟨hM, hρ, hμ, hP, hcl, hch⟩, hz =>
    ⟨lt_of_le_of_ne hM (fun h => hz (Or.inl h.symm)), hρ, hμ, hP, hcl,
      fun i => admFull_of_admFull0 (ch i) (hch i) (fun h => hz (Or.inr ⟨i, h⟩))⟩

theorem Λ_nonneg0 : ∀ t : SPMTree G, t.AdmFull0 → 0 ≤ t.Λ
  | leaf z, _ => norm_nonneg z
  | node _ _ _ _ _ ch, h =>
    mul_nonneg h.1 (Finset.prod_nonneg fun i _ => Λ_nonneg0 (ch i) (h.2.2.2.2.2 i))

theorem F_R_zero_of_hasZeroM : ∀ t : SPMTree G, t.AdmFull0 → t.HasZeroM → t.F = 0 ∧ t.R = 0
  | leaf _, _, h => h.elim
  | node _ M _ μ P ch, ⟨_, _, hμ, _, _, hch⟩, h => by
    rcases h with h0 | ⟨i, hi⟩
    · have hμ' : ‖μ‖ ≤ 0 := h0 ▸ hμ
      have hμ0 : μ = 0 := norm_le_zero_iff.1 hμ'
      subst hμ0
      exact ⟨rfl, by simp only [R, zero_apply, map_zero]⟩
    · obtain ⟨hF, hR⟩ := F_R_zero_of_hasZeroM (ch i) (hch i) hi
      refine ⟨μ.map_coord_zero i hF, ?_⟩
      simp only [R]
      rw [μ.map_coord_zero i hR, map_zero]

theorem err_zero_of_hasZeroM (t : SPMTree G) (ht : t.RootAdmFull0) (h : t.HasZeroM) :
    t.err = 0 := by
  cases t with
  | leaf z => exact ht.elim
  | node m M ρ μ P ch =>
    obtain ⟨_, _, hμ, _, _, hch⟩ := ht
    rcases h with h0 | ⟨i, hi⟩
    · have hμ' : ‖μ‖ ≤ 0 := h0 ▸ hμ
      have hμ0 : μ = 0 := norm_le_zero_iff.1 hμ'
      subst hμ0
      simp only [err, zero_apply, map_zero, sub_self, norm_zero]
    · obtain ⟨hF, hR⟩ := F_R_zero_of_hasZeroM (ch i) (hch i) hi
      simp only [err]
      rw [μ.map_coord_zero i hF, μ.map_coord_zero i hR, sub_self, norm_zero]

end SPMTree

open SPMTree

/-- **Heterogeneous Theorem R, scaled upper bound for `M_v ≥ 0`.** -/
theorem heterogeneous_scaled_upper_nonneg {G : Type*} [NormedAddCommGroup G]
    [InnerProductSpace ℝ G] (t : SPMTree G) (ht : t.RootAdmFull0) :
    t.err ≤ t.Λ * gBox t.dshape.childDefects := by
  cases t with
  | leaf z => exact ht.elim
  | node m M ρ μ P ch =>
    by_cases hz : (SPMTree.node m M ρ μ P ch).HasZeroM
    · rw [err_zero_of_hasZeroM _ ht hz]
      exact mul_nonneg (Λ_nonneg0 _ ht) (gBox_nonneg _)
    · exact heterogeneous_scaled_upper _ (admFull_of_admFull0 _ ht hz)

end PMT
