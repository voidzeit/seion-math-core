/-
Specification lemmas: the Lean admissibility conditions are equivalent to the unit-ball
formulations of `ADMISSIBLE_CLASS_PMT_A.md` (A2 norm, A5 projected closure).

Statements:
* `PMT.bound_iff_unit_ball`     for a multilinear map and slot sets closed under scaling:
                                `∀ x ∈ ∏S, ‖f x‖ ≤ M ∏‖xᵢ‖  ↔  ∀ x ∈ ∏S, ‖xᵢ‖ ≤ 1 → ‖f x‖ ≤ M`
* `PMT.opNorm_le_iff_unit_ball` A2: `‖μ‖ ≤ M ↔ sup_{‖xᵢ‖ ≤ 1} ‖μ x‖ ≤ M`
* `PMT.HPMTree.closure_iff_unit_ball`  A5: the Lean closure condition at a node is the multilinear
                                norm bound of `Q μ` restricted to the product of admissible slots
                                (`Ran P_c` for internal children, the whole space for leaves)
-/
import PMTFormal.Heterogeneous.Upper

open Real
open scoped RealInnerProductSpace

namespace PMT

theorem bound_iff_unit_ball {G H : Type*} [NormedAddCommGroup G] [NormedSpace ℝ G]
    [NormedAddCommGroup H] [NormedSpace ℝ H] {m : ℕ}
    (f : MultilinearMap ℝ (fun _ : Fin m => G) H) (S : Fin m → Set G)
    (hS : ∀ i (c : ℝ) (x : G), x ∈ S i → c • x ∈ S i) {M : ℝ} (hM : 0 ≤ M) :
    (∀ x : Fin m → G, (∀ i, x i ∈ S i) → ‖f x‖ ≤ M * ∏ i, ‖x i‖) ↔
      (∀ x : Fin m → G, (∀ i, x i ∈ S i) → (∀ i, ‖x i‖ ≤ 1) → ‖f x‖ ≤ M) := by
  constructor
  · intro h x hx h1
    calc ‖f x‖ ≤ M * ∏ i, ‖x i‖ := h x hx
      _ ≤ M * 1 := mul_le_mul_of_nonneg_left
          (Finset.prod_le_one (fun i _ => norm_nonneg _) (fun i _ => h1 i)) hM
      _ = M := mul_one M
  · intro h x hx
    by_cases hz : ∃ i, x i = 0
    · obtain ⟨i, hi⟩ := hz
      rw [f.map_coord_zero i hi, norm_zero]
      exact mul_nonneg hM (Finset.prod_nonneg fun i _ => norm_nonneg _)
    · push Not at hz
      have hy1 : ∀ i, ‖‖x i‖⁻¹ • x i‖ ≤ 1 := fun i => by
        rw [norm_smul, norm_inv, norm_norm, inv_mul_cancel₀ (norm_ne_zero_iff.2 (hz i))]
      have hbound := h (fun i => ‖x i‖⁻¹ • x i) (fun i => hS i _ _ (hx i)) hy1
      have hxy : x = fun i => ‖x i‖ • (‖x i‖⁻¹ • x i) :=
        funext fun i => (smul_inv_smul₀ (norm_ne_zero_iff.2 (hz i)) (x i)).symm
      have hprod0 : 0 ≤ ∏ i, ‖x i‖ := Finset.prod_nonneg fun i _ => norm_nonneg _
      calc ‖f x‖ = ‖f (fun i => ‖x i‖ • (‖x i‖⁻¹ • x i))‖ := by rw [← hxy]
        _ = (∏ i, ‖x i‖) * ‖f (fun i => ‖x i‖⁻¹ • x i)‖ := by
          rw [f.map_smul_univ, norm_smul, Real.norm_of_nonneg hprod0]
        _ ≤ (∏ i, ‖x i‖) * M := mul_le_mul_of_nonneg_left hbound hprod0
        _ = M * ∏ i, ‖x i‖ := mul_comm _ _

/-- **A2.** The Lean operator-norm bound is the paper's unit-ball bound. -/
theorem opNorm_le_iff_unit_ball {G H : Type*} [NormedAddCommGroup G] [NormedSpace ℝ G]
    [NormedAddCommGroup H] [NormedSpace ℝ H] {m : ℕ}
    (μ : ContinuousMultilinearMap ℝ (fun _ : Fin m => G) H) {M : ℝ} (hM : 0 ≤ M) :
    ‖μ‖ ≤ M ↔ ∀ x : Fin m → G, (∀ i, ‖x i‖ ≤ 1) → ‖μ x‖ ≤ M := by
  rw [ContinuousMultilinearMap.opNorm_le_iff hM]
  have h := bound_iff_unit_ball μ.toMultilinearMap (fun _ => Set.univ)
    (fun _ _ _ _ => Set.mem_univ _) hM
  simp only [Set.mem_univ, forall_const, ContinuousMultilinearMap.coe_coe] at h
  exact h

namespace HPMTree

variable {G : Type*} [NormedAddCommGroup G] [InnerProductSpace ℝ G]

theorem inRan_smul (t : HPMTree G) (c : ℝ) (v : G) (h : t.InRan v) : t.InRan (c • v) := by
  cases t with
  | leaf z => trivial
  | node m e μ P ch =>
    show P (c • v) = c • v
    rw [map_smul]
    exact congrArg (c • ·) h

/-- **A5.** The Lean closure condition at a node equals the unit-ball form of
`‖Q_v μ_v‖` restricted to `∏ Ran P̂_{c_i}`. -/
theorem closure_iff_unit_ball {m : ℕ} (μ : ContinuousMultilinearMap ℝ (fun _ : Fin m => G) G)
    (P : G →L[ℝ] G) (ch : Fin m → HPMTree G) {e : ℝ} (he : 0 ≤ e) :
    (∀ x : Fin m → G, (∀ i, (ch i).InRan (x i)) → ‖μ x - P (μ x)‖ ≤ e * ∏ i, ‖x i‖) ↔
      (∀ x : Fin m → G, (∀ i, (ch i).InRan (x i)) → (∀ i, ‖x i‖ ≤ 1) →
        ‖μ x - P (μ x)‖ ≤ e) := by
  have h := bound_iff_unit_ball (μ - P.compContinuousMultilinearMap μ).toMultilinearMap
    (fun i => {v | (ch i).InRan v}) (fun i c v hv => inRan_smul (ch i) c v hv) he
  exact h

end HPMTree

end PMT
