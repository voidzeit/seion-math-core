/-
A posteriori certification: scaled heterogeneous bound under trajectory-only closure.

For a concrete execution it suffices to know the projection defect along the realised reduced
trajectory, `‖(I - P_v) μ_v(R_{c_1}, …, R_{c_m})‖ ≤ ρ_v ∏ ‖R_{c_i}‖`, instead of the PMT-A closure over
every admissible input. The operator-norm bound `‖μ_v‖ ≤ M_v` is still required globally. No closure
is required at the root.

Statements:
* `PMT.SPMTree.AdmTC`, `PMT.SPMTree.RootAdmTC`         trajectory admissibility, `M_v > 0`
* `PMT.SPMTree.normalize_rootAdm`                       normalisation preserves it
* `PMT.heterogeneous_scaled_upper_of_admTC`             `E_T^P ≤ Λ_T · gBox(ρ/M)`
* `PMT.SPMTree.AdmTC0`, `PMT.SPMTree.RootAdmTC0`       the same with `M_v ≥ 0`
* `PMT.heterogeneous_scaled_upper_of_admTC_nonneg`      `E_T^P ≤ Λ_T · gBox(ρ/M)` for `M_v ≥ 0`
-/
import PMTFormal.Heterogeneous.ScaledZero

open Real
open scoped RealInnerProductSpace

namespace PMT

namespace SPMTree

variable {G : Type*} [NormedAddCommGroup G] [InnerProductSpace ℝ G]

/-- Every internal node has `M_v > 0`. -/
def PosM : SPMTree G → Prop
  | leaf _ => True
  | node _ M _ _ _ ch => 0 < M ∧ ∀ i, (ch i).PosM

/-- Scaled trajectory-closure admissibility (`M_v > 0`). -/
def AdmTC : SPMTree G → Prop
  | leaf _ => True
  | node _ M ρ μ P ch => 0 < M ∧ 0 ≤ ρ ∧ ‖μ‖ ≤ M ∧ IsOrthProj P ∧
      ‖μ (fun i => (ch i).R) - P (μ (fun i => (ch i).R))‖ ≤ ρ * ∏ i, ‖(ch i).R‖ ∧
      ∀ i, (ch i).AdmTC

/-- Root trajectory admissibility: no closure at the root. -/
def RootAdmTC : SPMTree G → Prop
  | leaf _ => False
  | node _ M _ μ P ch => 0 < M ∧ ‖μ‖ ≤ M ∧ IsOrthProj P ∧ ∀ i, (ch i).AdmTC

theorem posM_of_admTC : ∀ t : SPMTree G, t.AdmTC → t.PosM
  | leaf _, _ => trivial
  | node _ _ _ _ _ ch, h => ⟨h.1, fun i => posM_of_admTC (ch i) (h.2.2.2.2.2 i)⟩

theorem Λ_nonneg_of_posM : ∀ t : SPMTree G, t.PosM → 0 ≤ t.Λ
  | leaf z, _ => norm_nonneg z
  | node _ _ _ _ _ ch, h =>
    mul_nonneg h.1.le (Finset.prod_nonneg fun i _ => Λ_nonneg_of_posM (ch i) (h.2 i))

theorem normalize_eval_of_posM (t : SPMTree G) (ht : t.PosM) :
    t.Λ • t.normalize.F = t.F ∧ t.Λ • t.normalize.R = t.R := by
  induction t with
  | leaf z =>
    have hz : ‖z‖ • ‖z‖⁻¹ • z = z := by
      by_cases h0 : z = 0
      · simp [h0]
      · exact smul_inv_smul₀ (norm_ne_zero_iff.2 h0) z
    exact ⟨hz, hz⟩
  | node m M ρ μ P ch ih =>
    obtain ⟨hM, hch⟩ := ht
    have hF : (fun i => (ch i).F) = fun i => (ch i).Λ • (ch i).normalize.F :=
      funext fun i => ((ih i (hch i)).1).symm
    have hR : (fun i => (ch i).R) = fun i => (ch i).Λ • (ch i).normalize.R :=
      funext fun i => ((ih i (hch i)).2).symm
    have hc : M * (∏ i, (ch i).Λ) * M⁻¹ = ∏ i, (ch i).Λ := by
      field_simp
    constructor
    · simp only [Λ, normalize, HPMTree.F, F]
      rw [smul_apply, smul_smul, hc, hF, ContinuousMultilinearMap.map_smul_univ]
    · simp only [Λ, normalize, HPMTree.R, R]
      rw [smul_apply, ← ContinuousLinearMap.map_smul, smul_smul, hc, hR,
        ContinuousMultilinearMap.map_smul_univ]

theorem err_eq_of_posM (t : SPMTree G) (ht : t.PosM) : t.err = t.Λ * t.normalize.err := by
  cases t with
  | leaf z => simp only [err, normalize, HPMTree.err, mul_zero]
  | node m M ρ μ P ch =>
    obtain ⟨hM, hch⟩ := ht
    have hF : (fun i => (ch i).F) = fun i => (ch i).Λ • (ch i).normalize.F :=
      funext fun i => ((normalize_eval_of_posM (ch i) (hch i)).1).symm
    have hR : (fun i => (ch i).R) = fun i => (ch i).Λ • (ch i).normalize.R :=
      funext fun i => ((normalize_eval_of_posM (ch i) (hch i)).2).symm
    have hΛ0 : 0 ≤ ∏ i, (ch i).Λ :=
      Finset.prod_nonneg fun i _ => Λ_nonneg_of_posM (ch i) (hch i)
    simp only [err, HPMTree.err, Λ, normalize]
    rw [hF, hR, ContinuousMultilinearMap.map_smul_univ, ContinuousMultilinearMap.map_smul_univ,
      smul_apply, smul_apply,
      ContinuousLinearMap.map_smul, ContinuousLinearMap.map_smul, ContinuousLinearMap.map_smul,
      ContinuousLinearMap.map_smul, ← smul_sub, ← smul_sub, norm_smul, norm_smul,
      Real.norm_of_nonneg hΛ0, Real.norm_of_nonneg (inv_nonneg.2 hM.le)]
    field_simp

/-- A subtree with `Λ = 0` (some zero leaf) has zero normalised reduced value. -/
theorem normalize_R_eq_zero (t : SPMTree G) (hp : t.PosM) (hΛ : t.Λ = 0) :
    t.normalize.R = 0 := by
  induction t with
  | leaf z =>
    have hz : z = 0 := norm_eq_zero.1 hΛ
    show ‖z‖⁻¹ • z = 0
    rw [hz, smul_zero]
  | node m M ρ μ P ch ih =>
    obtain ⟨hM, hch⟩ := hp
    have hprod : ∏ i, (ch i).Λ = 0 := (mul_eq_zero.1 hΛ).resolve_left hM.ne'
    obtain ⟨i, -, hi⟩ := Finset.prod_eq_zero_iff.1 hprod
    show P ((M⁻¹ • μ) fun j => (ch j).normalize.R) = 0
    rw [(M⁻¹ • μ).map_coord_zero i (ih i (hch i) hi), map_zero]

theorem normalize_admTC (t : SPMTree G) (ht : t.AdmTC) : t.normalize.AdmTC := by
  induction t with
  | leaf z =>
    show ‖‖z‖⁻¹ • z‖ ≤ 1
    by_cases h0 : z = 0
    · simp [h0]
    · rw [norm_smul, norm_inv, norm_norm, inv_mul_cancel₀ (norm_ne_zero_iff.2 h0)]
  | node m M ρ μ P ch ih =>
    obtain ⟨hM, hρ, hμ, hP, hcl, hch⟩ := ht
    refine ⟨div_nonneg hρ hM.le, ?_, hP, ?_, fun i => ih i (hch i)⟩
    · rw [norm_smul, norm_inv, Real.norm_of_nonneg hM.le, inv_mul_le_iff₀ hM, mul_one]
      exact hμ
    · have hpc : ∀ i, (ch i).PosM := fun i => posM_of_admTC _ (hch i)
      have hkey : ‖μ (fun i => (ch i).normalize.R) - P (μ (fun i => (ch i).normalize.R))‖ ≤
          ρ * ∏ i, ‖(ch i).normalize.R‖ := by
        by_cases hz : ∃ i, (ch i).Λ = 0
        · obtain ⟨i, hi⟩ := hz
          rw [μ.map_coord_zero i (normalize_R_eq_zero (ch i) (hpc i) hi), map_zero, sub_zero,
            norm_zero]
          exact mul_nonneg hρ (Finset.prod_nonneg fun i _ => norm_nonneg _)
        · push Not at hz
          have hpos : ∀ i, 0 < (ch i).Λ := fun i =>
            lt_of_le_of_ne (Λ_nonneg_of_posM _ (hpc i)) (hz i).symm
          have hL0 : 0 < ∏ i, (ch i).Λ := Finset.prod_pos fun i _ => hpos i
          have hRi : ∀ i, (ch i).R = (ch i).Λ • (ch i).normalize.R := fun i =>
            ((normalize_eval_of_posM (ch i) (hpc i)).2).symm
          simp only [hRi] at hcl
          rw [μ.map_smul_univ, map_smul, ← smul_sub, norm_smul,
            Real.norm_of_nonneg hL0.le] at hcl
          have hprod : ∏ i, ‖(ch i).Λ • (ch i).normalize.R‖ =
              (∏ i, (ch i).Λ) * ∏ i, ‖(ch i).normalize.R‖ := by
            rw [← Finset.prod_mul_distrib]
            exact Finset.prod_congr rfl fun i _ => by
              rw [norm_smul, Real.norm_of_nonneg (hpos i).le]
          rw [hprod] at hcl
          refine le_of_mul_le_mul_left ?_ hL0
          calc (∏ i, (ch i).Λ) * ‖μ (fun i => (ch i).normalize.R) -
                P (μ (fun i => (ch i).normalize.R))‖
              ≤ ρ * ((∏ i, (ch i).Λ) * ∏ i, ‖(ch i).normalize.R‖) := hcl
            _ = (∏ i, (ch i).Λ) * (ρ * ∏ i, ‖(ch i).normalize.R‖) := mul_left_comm _ _ _
      show ‖(M⁻¹ • μ) (fun i => (ch i).normalize.R) -
          P ((M⁻¹ • μ) (fun i => (ch i).normalize.R))‖ ≤ ρ / M * ∏ i, ‖(ch i).normalize.R‖
      rw [smul_apply, map_smul, ← smul_sub, norm_smul, norm_inv, Real.norm_of_nonneg hM.le,
        div_eq_inv_mul, mul_assoc]
      exact mul_le_mul_of_nonneg_left hkey (inv_nonneg.2 hM.le)

theorem normalize_rootAdm (t : SPMTree G) (ht : t.RootAdmTC) : t.normalize.RootAdm := by
  cases t with
  | leaf z => exact ht.elim
  | node m M ρ μ P ch =>
    obtain ⟨hM, hμ, hP, hch⟩ := ht
    refine ⟨?_, hP, fun i => normalize_admTC (ch i) (hch i)⟩
    show ‖M⁻¹ • μ‖ ≤ 1
    rw [norm_smul, norm_inv, Real.norm_of_nonneg hM.le, inv_mul_le_iff₀ hM, mul_one]
    exact hμ

end SPMTree

open SPMTree

/-- **A posteriori heterogeneous bound** (`M_v > 0`): closure only along the realised reduced
trajectory suffices for `E_T^P ≤ Λ_T · gBox(ρ_u / M_u : u non-root)`. -/
theorem heterogeneous_scaled_upper_of_admTC {G : Type*} [NormedAddCommGroup G]
    [InnerProductSpace ℝ G] (t : SPMTree G) (ht : t.RootAdmTC) :
    t.err ≤ t.Λ * gBox t.dshape.childDefects := by
  have hp : t.PosM := by
    cases t with
    | leaf z => exact ht.elim
    | node m M ρ μ P ch => exact ⟨ht.1, fun i => posM_of_admTC (ch i) (ht.2.2.2 i)⟩
  obtain ⟨θ, hθ, hle⟩ := heterogeneous_upper_of_rootAdm _ (normalize_rootAdm t ht)
  rw [normalize_dshape] at hθ
  rw [err_eq_of_posM t hp]
  exact mul_le_mul_of_nonneg_left (hle.trans (le_gBox hθ)) (Λ_nonneg_of_posM t hp)

namespace SPMTree

variable {G : Type*} [NormedAddCommGroup G] [InnerProductSpace ℝ G]

/-- Trajectory admissibility allowing `M_v = 0`. -/
def AdmTC0 : SPMTree G → Prop
  | leaf _ => True
  | node _ M ρ μ P ch => 0 ≤ M ∧ 0 ≤ ρ ∧ ‖μ‖ ≤ M ∧ IsOrthProj P ∧
      ‖μ (fun i => (ch i).R) - P (μ (fun i => (ch i).R))‖ ≤ ρ * ∏ i, ‖(ch i).R‖ ∧
      ∀ i, (ch i).AdmTC0

def RootAdmTC0 : SPMTree G → Prop
  | leaf _ => False
  | node _ M _ μ P ch => 0 ≤ M ∧ ‖μ‖ ≤ M ∧ IsOrthProj P ∧ ∀ i, (ch i).AdmTC0

theorem admTC_of_admTC0 : ∀ t : SPMTree G, t.AdmTC0 → ¬ t.HasZeroM → t.AdmTC
  | leaf _, _, _ => trivial
  | node _ _ _ _ _ ch, ⟨hM, hρ, hμ, hP, hcl, hch⟩, hz =>
    ⟨lt_of_le_of_ne hM (fun h => hz (Or.inl h.symm)), hρ, hμ, hP, hcl,
      fun i => admTC_of_admTC0 (ch i) (hch i) (fun h => hz (Or.inr ⟨i, h⟩))⟩

theorem Λ_nonneg_of_admTC0 : ∀ t : SPMTree G, t.AdmTC0 → 0 ≤ t.Λ
  | leaf z, _ => norm_nonneg z
  | node _ _ _ _ _ ch, h =>
    mul_nonneg h.1 (Finset.prod_nonneg fun i _ => Λ_nonneg_of_admTC0 (ch i) (h.2.2.2.2.2 i))

theorem F_R_zero_of_hasZeroM_tc : ∀ t : SPMTree G, t.AdmTC0 → t.HasZeroM → t.F = 0 ∧ t.R = 0
  | leaf _, _, h => h.elim
  | node _ M _ μ P ch, ⟨_, _, hμ, _, _, hch⟩, h => by
    rcases h with h0 | ⟨i, hi⟩
    · have hμ' : ‖μ‖ ≤ 0 := h0 ▸ hμ
      have hμ0 : μ = 0 := norm_le_zero_iff.1 hμ'
      subst hμ0
      exact ⟨rfl, by simp only [R, zero_apply, map_zero]⟩
    · obtain ⟨hF, hR⟩ := F_R_zero_of_hasZeroM_tc (ch i) (hch i) hi
      refine ⟨μ.map_coord_zero i hF, ?_⟩
      simp only [R]
      rw [μ.map_coord_zero i hR, map_zero]

end SPMTree

/-- **A posteriori heterogeneous bound for `M_v ≥ 0`.** -/
theorem heterogeneous_scaled_upper_of_admTC_nonneg {G : Type*} [NormedAddCommGroup G]
    [InnerProductSpace ℝ G] (t : SPMTree G) (ht : t.RootAdmTC0) :
    t.err ≤ t.Λ * gBox t.dshape.childDefects := by
  cases t with
  | leaf z => exact ht.elim
  | node m M ρ μ P ch =>
    obtain ⟨hM, hμ, hP, hch⟩ := ht
    have hΛ : 0 ≤ (SPMTree.node m M ρ μ P ch).Λ :=
      mul_nonneg hM (Finset.prod_nonneg fun i _ => Λ_nonneg_of_admTC0 (ch i) (hch i))
    by_cases hz : (SPMTree.node m M ρ μ P ch).HasZeroM
    · have herr : (SPMTree.node m M ρ μ P ch).err = 0 := by
        rcases hz with h0 | ⟨i, hi⟩
        · have hμ' : ‖μ‖ ≤ 0 := h0 ▸ hμ
          have hμ0 : μ = 0 := norm_le_zero_iff.1 hμ'
          subst hμ0
          simp only [err, zero_apply, map_zero, sub_self, norm_zero]
        · obtain ⟨hF, hR⟩ := F_R_zero_of_hasZeroM_tc (ch i) (hch i) hi
          simp only [err]
          rw [μ.map_coord_zero i hF, μ.map_coord_zero i hR, sub_self, norm_zero]
      rw [herr]
      exact mul_nonneg hΛ (gBox_nonneg _)
    · have hM' : 0 < M := lt_of_le_of_ne hM (fun h => hz (Or.inl h.symm))
      exact heterogeneous_scaled_upper_of_admTC _
        ⟨hM', hμ, hP, fun i => admTC_of_admTC0 (ch i) (hch i) (fun h => hz (Or.inr ⟨i, h⟩))⟩

end PMT
