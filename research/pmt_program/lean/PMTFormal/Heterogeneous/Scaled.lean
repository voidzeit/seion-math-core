/-
Heterogeneous Theorem R, scaled form (`M_v > 0`).

Every internal node carries `(M_v, ρ_v)` with `‖μ_v‖ ≤ M_v`, `M_v > 0`, `ρ_v ≥ 0`, and full closure
`‖(I - P_v) μ_v(x)‖ ≤ ρ_v ∏ ‖x_i‖` on admissible inputs. Leaves are arbitrary vectors.
With `Λ_T = (∏_v M_v)(∏_ℓ ‖z_ℓ‖)` and nodewise defects `η_v = ρ_v / M_v`:

  `E_T^P ≤ Λ_T · gBox(η_non-root)`,  and  `sup E_T^P / Λ_T = gBox(η_non-root)`.

The case `M_v = 0` is not covered here (it is a separate, degenerate lemma: `μ_v = 0`).

Statements:
* `PMT.SPMTree`, `PMT.SPMTree.Λ`, `PMT.SPMTree.dshape` (defect `ρ/M`), `PMT.SPMTree.AdmFull`
* `PMT.SPMTree.normalize`            `μ ↦ M⁻¹ μ`, `z ↦ ‖z‖⁻¹ z` (`0⁻¹ = 0` handles zero leaves)
* `PMT.SPMTree.err_eq`               `err = Λ · err(normalize)`
* `PMT.heterogeneous_scaled_upper`   `err ≤ Λ · gBox(childDefects)`
* `PMT.heterogeneous_scaled_sSup`    `sup_{Λ > 0} err/Λ = gBox(childDefects)` (over `ℂ`)
-/
import PMTFormal.Heterogeneous.Sharp

open Real
open scoped RealInnerProductSpace

namespace PMT

/-- Projected multilinear trees with nodewise `(M_v, ρ_v)`. -/
inductive SPMTree (G : Type*) [NormedAddCommGroup G] [InnerProductSpace ℝ G] where
  | leaf (z : G)
  | node (m : ℕ) (M ρ : ℝ) (μ : ContinuousMultilinearMap ℝ (fun _ : Fin m => G) G)
      (P : G →L[ℝ] G) (ch : Fin m → SPMTree G)

namespace SPMTree

variable {G : Type*} [NormedAddCommGroup G] [InnerProductSpace ℝ G]

def F : SPMTree G → G
  | leaf z => z
  | node _ _ _ μ _ ch => μ (fun i => (ch i).F)

def R : SPMTree G → G
  | leaf z => z
  | node _ _ _ μ P ch => P (μ (fun i => (ch i).R))

def err : SPMTree G → ℝ
  | leaf _ => 0
  | node _ _ _ μ P ch => ‖P (μ (fun i => (ch i).F)) - P (μ (fun i => (ch i).R))‖

def InRan : SPMTree G → G → Prop
  | leaf _, _ => True
  | node _ _ _ _ P _, v => P v = v

/-- `Λ_T = (∏_v M_v)(∏_ℓ ‖z_ℓ‖)`. -/
def Λ : SPMTree G → ℝ
  | leaf z => ‖z‖
  | node _ M _ _ _ ch => M * ∏ i, (ch i).Λ

/-- Defect skeleton with nodewise defects `ρ_v / M_v`. -/
noncomputable def dshape : SPMTree G → DShape
  | leaf _ => .leaf
  | node m M ρ _ _ ch => .node m (ρ / M) (fun i => (ch i).dshape)

/-- Scaled heterogeneous PMT-A admissibility (`M_v > 0`). -/
def AdmFull : SPMTree G → Prop
  | leaf _ => True
  | node _ M ρ μ P ch => 0 < M ∧ 0 ≤ ρ ∧ ‖μ‖ ≤ M ∧ IsOrthProj P ∧
      (∀ x : (i : Fin _) → G, (∀ i, (ch i).InRan (x i)) →
        ‖μ x - P (μ x)‖ ≤ ρ * ∏ i, ‖x i‖) ∧
      ∀ i, (ch i).AdmFull

def RootAdmFull : SPMTree G → Prop
  | leaf _ => False
  | node m M ρ μ P ch => (node m M ρ μ P ch).AdmFull

/-- Normalisation to a heterogeneous tree with `‖μ‖ ≤ 1` and leaves in the unit ball. -/
noncomputable def normalize : SPMTree G → HPMTree G
  | leaf z => .leaf (‖z‖⁻¹ • z)
  | node m M ρ μ P ch => .node m (ρ / M) (M⁻¹ • μ) P (fun i => (ch i).normalize)

theorem Λ_nonneg : ∀ t : SPMTree G, t.AdmFull → 0 ≤ t.Λ
  | leaf z, _ => norm_nonneg z
  | node _ _ _ _ _ ch, h =>
    mul_nonneg h.1.le (Finset.prod_nonneg fun i _ => Λ_nonneg (ch i) (h.2.2.2.2.2 i))

theorem normalize_dshape (t : SPMTree G) : t.normalize.dshape = t.dshape := by
  induction t with
  | leaf z => rfl
  | node m M ρ μ P ch ih => simp only [normalize, dshape, HPMTree.dshape, ih]

theorem inRan_normalize (t : SPMTree G) (v : G) : t.normalize.InRan v ↔ t.InRan v := by
  cases t <;> rfl

theorem normalize_eval (t : SPMTree G) (ht : t.AdmFull) :
    t.Λ • t.normalize.F = t.F ∧ t.Λ • t.normalize.R = t.R := by
  induction t with
  | leaf z =>
    have hz : ‖z‖ • ‖z‖⁻¹ • z = z := by
      by_cases h0 : z = 0
      · simp [h0]
      · exact smul_inv_smul₀ (norm_ne_zero_iff.2 h0) z
    exact ⟨hz, hz⟩
  | node m M ρ μ P ch ih =>
    obtain ⟨hM, -, -, -, -, hch⟩ := ht
    have hF : (fun i => (ch i).F) = fun i => (ch i).Λ • (ch i).normalize.F :=
      funext fun i => ((ih i (hch i)).1).symm
    have hR : (fun i => (ch i).R) = fun i => (ch i).Λ • (ch i).normalize.R :=
      funext fun i => ((ih i (hch i)).2).symm
    have hc : M * (∏ i, (ch i).Λ) * M⁻¹ = ∏ i, (ch i).Λ := by
      field_simp
    constructor
    · simp only [Λ, normalize, HPMTree.F, F]
      rw [smul_apply, smul_smul, hc, hF,
        ContinuousMultilinearMap.map_smul_univ]
    · simp only [Λ, normalize, HPMTree.R, R]
      rw [smul_apply, ← ContinuousLinearMap.map_smul, smul_smul, hc, hR,
        ContinuousMultilinearMap.map_smul_univ]

theorem err_eq (t : SPMTree G) (ht : t.RootAdmFull) : t.err = t.Λ * t.normalize.err := by
  cases t with
  | leaf z => exact ht.elim
  | node m M ρ μ P ch =>
    obtain ⟨hM, -, -, -, -, hch⟩ := ht
    have hF : (fun i => (ch i).F) = fun i => (ch i).Λ • (ch i).normalize.F :=
      funext fun i => ((normalize_eval (ch i) (hch i)).1).symm
    have hR : (fun i => (ch i).R) = fun i => (ch i).Λ • (ch i).normalize.R :=
      funext fun i => ((normalize_eval (ch i) (hch i)).2).symm
    have hΛ0 : 0 ≤ ∏ i, (ch i).Λ := Finset.prod_nonneg fun i _ => Λ_nonneg (ch i) (hch i)
    simp only [err, HPMTree.err, Λ, normalize]
    rw [hF, hR, ContinuousMultilinearMap.map_smul_univ, ContinuousMultilinearMap.map_smul_univ,
      smul_apply, smul_apply,
      ContinuousLinearMap.map_smul, ContinuousLinearMap.map_smul, ContinuousLinearMap.map_smul,
      ContinuousLinearMap.map_smul, ← smul_sub, ← smul_sub, norm_smul, norm_smul,
      Real.norm_of_nonneg hΛ0, Real.norm_of_nonneg (inv_nonneg.2 hM.le)]
    field_simp

theorem normalize_admFull (t : SPMTree G) (ht : t.AdmFull) : t.normalize.AdmFull := by
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
    · intro x hx
      have h := hcl x (fun i => (inRan_normalize (ch i) (x i)).1 (hx i))
      rw [smul_apply, ContinuousLinearMap.map_smul, ← smul_sub,
        norm_smul, norm_inv, Real.norm_of_nonneg hM.le, div_eq_inv_mul, mul_assoc]
      exact mul_le_mul_of_nonneg_left h (inv_nonneg.2 hM.le)

theorem normalize_rootAdmFull (t : SPMTree G) (ht : t.RootAdmFull) :
    t.normalize.RootAdmFull := by
  cases t with
  | leaf z => exact ht.elim
  | node m M ρ μ P ch => exact normalize_admFull _ ht

/-- Embedding of normalised heterogeneous trees (`M_v = 1`, `ρ_v = e_v`). -/
def ofH : HPMTree G → SPMTree G
  | .leaf z => leaf z
  | .node m e μ P ch => node m 1 e μ P (fun i => ofH (ch i))

theorem ofH_eval (t : HPMTree G) : (ofH t).F = t.F ∧ (ofH t).R = t.R := by
  induction t with
  | leaf z => exact ⟨rfl, rfl⟩
  | node m e μ P ch ih =>
    exact ⟨by simp only [ofH, F, HPMTree.F, fun i => (ih i).1],
      by simp only [ofH, R, HPMTree.R, fun i => (ih i).2]⟩

theorem ofH_err (t : HPMTree G) : (ofH t).err = t.err := by
  cases t with
  | leaf z => rfl
  | node m e μ P ch =>
    simp only [ofH, err, HPMTree.err, fun i => (ofH_eval (ch i)).1, fun i => (ofH_eval (ch i)).2]

theorem ofH_dshape (t : HPMTree G) : (ofH t).dshape = t.dshape := by
  induction t with
  | leaf z => rfl
  | node m e μ P ch ih => simp only [ofH, dshape, HPMTree.dshape, div_one, ih]

theorem inRan_ofH (t : HPMTree G) (v : G) : (ofH t).InRan v ↔ t.InRan v := by
  cases t <;> rfl

theorem ofH_admFull (t : HPMTree G) (ht : t.AdmFull) : (ofH t).AdmFull := by
  induction t with
  | leaf z => trivial
  | node m e μ P ch ih =>
    obtain ⟨he, hμ, hP, hcl, hch⟩ := ht
    exact ⟨one_pos, he, hμ, hP, fun x hx => hcl x (fun i => (inRan_ofH (ch i) (x i)).1 (hx i)),
      fun i => ih i (hch i)⟩

end SPMTree

open SPMTree

/-- **Heterogeneous Theorem R, scaled upper bound** (`M_v > 0`):
`E_T^P ≤ (∏_v M_v)(∏_ℓ ‖z_ℓ‖) · gBox(ρ_u / M_u : u non-root)`. -/
theorem heterogeneous_scaled_upper {G : Type*} [NormedAddCommGroup G] [InnerProductSpace ℝ G]
    (t : SPMTree G) (ht : t.RootAdmFull) :
    t.err ≤ t.Λ * gBox t.dshape.childDefects := by
  have hΛ : 0 ≤ t.Λ := by
    cases t with
    | leaf z => exact ht.elim
    | node m M ρ μ P ch => exact Λ_nonneg _ ht
  rw [err_eq t ht, ← normalize_dshape]
  exact mul_le_mul_of_nonneg_left (heterogeneous_le_gBox _ (normalize_rootAdmFull t ht)) hΛ

theorem witH_Λ (a : AShape) : (ofH (witH a)).Λ = 1 := by
  induction a with
  | leaf => simp only [witH, ofH, Λ, norm_one]
  | node m e θ ch ih => simp only [witH, ofH, Λ, ih, Finset.prod_const_one, mul_one]

theorem witRootH_Λ (m : ℕ) (e : ℝ) (a : Fin m → AShape) : (ofH (witRootH m e a)).Λ = 1 := by
  simp only [witRootH, ofH, Λ, witH_Λ, Finset.prod_const_one, mul_one]

/-- **Heterogeneous Theorem R, scaled sharp constant.** Over scaled heterogeneous PMT-A trees in `ℂ`
with skeleton `T` (root defect `e ≥ 0`) and `Λ_T > 0`, `sup E_T^P / Λ_T = gBox(childDefects T)`. -/
theorem heterogeneous_scaled_sSup {m : ℕ} {e : ℝ} (he : 0 ≤ e) (ch : Fin m → DShape) :
    sSup {x | ∃ t : SPMTree ℂ, t.dshape = .node m e ch ∧ t.RootAdmFull ∧ 0 < t.Λ ∧
      t.err / t.Λ = x} = gBox (DShape.node m e ch).childDefects := by
  apply csSup_eq_csSup_of_forall_exists_le
  · rintro x ⟨t, hT, hadm, hΛ, rfl⟩
    obtain ⟨θ, hθ, hle⟩ := heterogeneous_upper _ (normalize_rootAdmFull t hadm)
    rw [normalize_dshape, hT] at hθ
    refine ⟨_, ⟨θ, hθ, rfl⟩, ?_⟩
    rw [err_eq t hadm, mul_div_cancel_left₀ _ hΛ.ne']
    exact hle
  · rintro y ⟨θ, hθ, rfl⟩
    obtain ⟨g, hg, hgi⟩ := forall₂_flatten_ofFn (fun i => (ch i).defects) θ hθ
    choose a ha1 ha2 ha3 using fun i => AShape.exists_fill (ch i) (g i) (hgi i)
    refine ⟨_, ⟨ofH (witRootH m e a), ?_, ofH_admFull _ (witRootH_rootAdmFull he a ha3), ?_, rfl⟩, ?_⟩
    · rw [ofH_dshape, witRootH_dshape]
      simp only [ha1]
    · rw [witRootH_Λ]
      exact one_pos
    · rw [witRootH_Λ, div_one, ofH_err, witRootH_err, hg]
      simp only [ha2, le_refl]

end PMT
