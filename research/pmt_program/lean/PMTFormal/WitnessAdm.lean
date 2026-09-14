/-
Universal sharp witness in the general tree model: admissibility (norms, projectors, full closure)
and exact evaluation of the root error. Theorem 8.1 of Theorem R v2, now inside `PMTree`.

Model: all spaces are `ℂ` as a real inner product space, leaves carry `1`.
* non-root node: `μ(x) = e^{iθ} ∏ slot(xᵢ)`, `P = Re`   (slot = `Re` on leaf children, `id` otherwise)
* root:          `μ(x) = ∏ slot(xᵢ)`,        `P = id`

Statements:
* `PMT.Shape`, `PMT.PMTree.shape`
* `PMT.wit_admFull`     every non-root witness subtree is PMT-A admissible (full closure)
* `PMT.witRoot_admFull` the root witness is admissible
* `PMT.witRoot_err`     `err = |1 - w(θ)^(k-1)|`
-/
import PMTFormal.Tree

open Real Complex
open scoped RealInnerProductSpace

namespace PMT

/-- Tree shapes (internal-node skeletons with arities; leaves carry no data). -/
inductive Shape where
  | leaf
  | node (m : ℕ) (ch : Fin m → Shape)

namespace Shape

/-- Number of internal nodes of a shape. -/
def internal : Shape → ℕ
  | leaf => 0
  | node _ ch => 1 + ∑ i, (ch i).internal

end Shape

namespace PMTree

variable {G : Type*} [NormedAddCommGroup G] [InnerProductSpace ℝ G]

/-- The shape of a tree. -/
def shape : PMTree G → Shape
  | leaf _ => .leaf
  | node m _ _ ch => .node m (fun i => (ch i).shape)

theorem internal_shape (t : PMTree G) : t.shape.internal = t.internal := by
  induction t with
  | leaf z => rfl
  | node m μ P ch ih => simp only [shape, Shape.internal, internal, ih]

/-- PMT-A admissibility at the root as well (full closure everywhere). -/
def RootAdmFull (η : ℝ) : PMTree G → Prop
  | leaf _ => False
  | node _ μ P ch => ‖μ‖ ≤ 1 ∧ IsOrthProj P ∧
      (∀ x : (i : Fin _) → G, (∀ i, (ch i).InRan (x i)) →
        ‖μ x - P (μ x)‖ ≤ η * ∏ i, ‖x i‖) ∧
      ∀ i, (ch i).AdmFull η

theorem rootAdm_of_rootAdmFull {η : ℝ} (t : PMTree G) (ht : t.RootAdmFull η) : t.RootAdm η := by
  cases t with
  | leaf z => exact ht.elim
  | node m μ P ch =>
    obtain ⟨hμ, hP, _, hch⟩ := ht
    exact ⟨hμ, hP, fun i => admTC_of_admFull (ch i) (hch i)⟩

end PMTree

open PMTree

/-- `Re` as an `ℝ`-linear map `ℂ → ℂ`. -/
noncomputable def reProj : ℂ →L[ℝ] ℂ := ofRealCLM.comp reCLM

theorem reProj_apply (z : ℂ) : reProj z = (z.re : ℂ) := rfl

theorem reProj_isOrthProj : IsOrthProj reProj where
  idem u := by simp [reProj_apply]
  symm u v := by
    simp only [reProj_apply, Complex.inner, Complex.mul_re, Complex.conj_re, Complex.conj_im,
      Complex.ofReal_re, Complex.ofReal_im]
    ring

theorem id_isOrthProj : IsOrthProj (ContinuousLinearMap.id ℝ ℂ) where
  idem _ := rfl
  symm _ _ := rfl

/-- Slot map: `Re` on leaf slots, identity on internal slots. -/
noncomputable def slot : Shape → (ℂ →L[ℝ] ℂ)
  | .leaf => reProj
  | .node _ _ => ContinuousLinearMap.id ℝ ℂ

theorem norm_slot_le (s : Shape) (z : ℂ) : ‖slot s z‖ ≤ ‖z‖ := by
  cases s with
  | leaf =>
    simp only [slot, reProj_apply, Complex.norm_real, Real.norm_eq_abs]
    exact Complex.abs_re_le_norm z
  | node m ch => exact le_rfl

/-- Witness law: `c · ∏ slot(xᵢ)`. -/
noncomputable def law (c : ℂ) (m : ℕ) (ch : Fin m → Shape) :
    ContinuousMultilinearMap ℝ (fun _ : Fin m => ℂ) ℂ :=
  c • (ContinuousMultilinearMap.mkPiAlgebra ℝ (Fin m) ℂ).compContinuousLinearMap
    (fun i => slot (ch i))

theorem law_apply (c : ℂ) (m : ℕ) (ch : Fin m → Shape) (x : Fin m → ℂ) :
    law c m ch x = c * ∏ i, slot (ch i) (x i) := by
  simp [law, ContinuousMultilinearMap.mkPiAlgebra_apply]

theorem norm_law_le {c : ℂ} (hc : ‖c‖ = 1) (m : ℕ) (ch : Fin m → Shape) : ‖law c m ch‖ ≤ 1 := by
  refine ContinuousMultilinearMap.opNorm_le_bound zero_le_one fun x => ?_
  rw [law_apply, norm_mul, hc, one_mul, norm_prod, one_mul]
  exact Finset.prod_le_prod (fun i _ => norm_nonneg _) (fun i _ => norm_slot_le _ _)

/-- Non-root witness subtree. -/
noncomputable def wit (θ : ℝ) : Shape → PMTree ℂ
  | .leaf => .leaf 1
  | .node m ch => .node m (law (exp (θ * I)) m ch) reProj (fun i => wit θ (ch i))

/-- Root witness. -/
noncomputable def witRoot (θ : ℝ) : Shape → PMTree ℂ
  | .leaf => .leaf 1
  | .node m ch => .node m (law 1 m ch) (ContinuousLinearMap.id ℝ ℂ) (fun i => wit θ (ch i))

theorem wit_shape (θ : ℝ) (s : Shape) : (wit θ s).shape = s := by
  induction s with
  | leaf => rfl
  | node m ch ih => simp only [wit, shape, ih]

theorem witRoot_shape (θ : ℝ) (s : Shape) : (witRoot θ s).shape = s := by
  cases s with
  | leaf => rfl
  | node m ch => simp only [witRoot, shape, wit_shape]

theorem slot_real (s : Shape) (c : ℝ) : slot s (c : ℂ) = (c : ℂ) := by
  cases s with
  | leaf => simp [slot, reProj_apply]
  | node _ _ => rfl

theorem slot_exp (θ : ℝ) (s : Shape) :
    slot s (exp ((((s.internal : ℝ) * θ : ℝ) : ℂ) * I)) = exp ((((s.internal : ℝ) * θ : ℝ) : ℂ) * I) := by
  cases s with
  | leaf => simp [slot, reProj_apply, Shape.internal]
  | node _ _ => rfl

theorem wit_eval (θ : ℝ) (s : Shape) :
    (wit θ s).F = exp (((s.internal : ℝ) * θ : ℝ) * I) ∧
      (wit θ s).R = ((Real.cos θ ^ s.internal : ℝ) : ℂ) := by
  induction s with
  | leaf => simp [wit, F, R, Shape.internal]
  | node m ch ih =>
    constructor
    · simp only [wit, F, law_apply, fun i => (ih i).1, slot_exp θ]
      rw [← Complex.exp_sum, ← Complex.exp_add]
      congr 1
      simp only [Shape.internal]
      push_cast
      rw [add_mul, add_mul, one_mul, Finset.sum_mul, Finset.sum_mul]
    · simp only [wit, R, law_apply, fun i => (ih i).2, slot_real, reProj_apply]
      rw [← Complex.ofReal_prod, Finset.prod_pow_eq_pow_sum, Complex.re_mul_ofReal,
        Complex.exp_ofReal_mul_I_re, Shape.internal, pow_add, pow_one, mul_comm]

theorem wit_admFull {η : ℝ} (hη1 : η ≤ 1) {θ : ℝ} (hθ : θ ∈ Set.Icc 0 (arcsin η)) :
    ∀ s : Shape, (wit θ s).AdmFull η := by
  intro s
  induction s with
  | leaf => simp [wit, AdmFull]
  | node m ch ih =>
    refine ⟨norm_law_le (Complex.norm_exp_ofReal_mul_I θ) m ch, reProj_isOrthProj, ?_, ih⟩
    intro x hx
    -- every slot value is real
    have hreal : ∀ i, slot (ch i) (x i) = ((x i).re : ℂ) := by
      intro i
      have hi : (wit θ (ch i)).InRan (x i) := hx i
      cases hci : ch i with
      | leaf => simp [slot, reProj_apply]
      | node m' ch' =>
        rw [hci] at hi
        simp only [wit, InRan, reProj_apply] at hi
        simp only [slot, ContinuousLinearMap.id_apply]
        exact hi.symm
    set r : ℝ := ∏ i, (x i).re with hr
    have hμx : law (exp (θ * I)) m ch x = exp (θ * I) * (r : ℂ) := by
      rw [law_apply, Finset.prod_congr rfl (fun i _ => hreal i), ← Complex.ofReal_prod]
    have hdiff : law (exp (θ * I)) m ch x - reProj (law (exp (θ * I)) m ch x) =
        ((Real.sin θ * r : ℝ) : ℂ) * I := by
      rw [hμx, reProj_apply, Complex.re_mul_ofReal, Complex.exp_ofReal_mul_I_re]
      apply Complex.ext <;>
        simp [Complex.exp_ofReal_mul_I_re, Complex.exp_ofReal_mul_I_im, Complex.cos_ofReal_re,
          Complex.sin_ofReal_re]
    have hθ0 : 0 ≤ θ := hθ.1
    have hθπ : θ ≤ π / 2 := hθ.2.trans (Real.arcsin_le_pi_div_two η)
    have hsin0 : 0 ≤ Real.sin θ := Real.sin_nonneg_of_nonneg_of_le_pi hθ0 (by linarith [Real.pi_pos])
    have hsinη : Real.sin θ ≤ η := by
      have hη0 : 0 ≤ η := Real.arcsin_nonneg.1 (hθ0.trans hθ.2)
      calc Real.sin θ ≤ Real.sin (arcsin η) :=
            Real.sin_le_sin_of_le_of_le_pi_div_two (by linarith [Real.pi_pos]) (Real.arcsin_le_pi_div_two η) hθ.2
        _ = η := Real.sin_arcsin (by linarith) hη1
    have hr_le : |r| ≤ ∏ i, ‖x i‖ := by
      rw [hr, Finset.abs_prod]
      exact Finset.prod_le_prod (fun i _ => abs_nonneg _) (fun i _ => Complex.abs_re_le_norm _)
    rw [hdiff, norm_mul, Complex.norm_I, mul_one, Complex.norm_real, Real.norm_eq_abs, abs_mul,
      abs_of_nonneg hsin0]
    exact mul_le_mul hsinη hr_le (abs_nonneg _) ((Real.sin_nonneg_of_nonneg_of_le_pi hθ0
      (by linarith [Real.pi_pos])).trans hsinη)

theorem witRoot_admFull {η : ℝ} (hη0 : 0 ≤ η) (hη1 : η ≤ 1) {θ : ℝ}
    (hθ : θ ∈ Set.Icc 0 (arcsin η)) (m : ℕ) (ch : Fin m → Shape) :
    (witRoot θ (.node m ch)).RootAdmFull η := by
  refine ⟨norm_law_le (by simp) m ch, id_isOrthProj, ?_, fun i => wit_admFull hη1 hθ (ch i)⟩
  intro x _
  simp only [ContinuousLinearMap.id_apply, sub_self, norm_zero]
  exact mul_nonneg hη0 (Finset.prod_nonneg fun i _ => norm_nonneg _)

/-- `|e^{iΘ} - c| = |1 - c e^{iΘ}|` for real `c`, `Θ`. -/
theorem norm_exp_sub_real (Θ c : ℝ) :
    ‖exp ((Θ : ℂ) * I) - (c : ℂ)‖ = ‖1 - (c : ℂ) * exp ((Θ : ℂ) * I)‖ := by
  have h1 : Complex.normSq (exp ((Θ : ℂ) * I) - (c : ℂ)) = 1 - 2 * c * Real.cos Θ + c ^ 2 := by
    rw [Complex.normSq_apply]
    simp only [Complex.sub_re, Complex.sub_im, Complex.exp_ofReal_mul_I_re,
      Complex.exp_ofReal_mul_I_im, Complex.ofReal_re, Complex.ofReal_im, sub_zero]
    nlinarith [Real.sin_sq_add_cos_sq Θ]
  have h2 := normSq_one_sub_mul_exp c Θ
  have hsq : ‖exp ((Θ : ℂ) * I) - (c : ℂ)‖ ^ 2 = ‖1 - (c : ℂ) * exp ((Θ : ℂ) * I)‖ ^ 2 := by
    rw [← Complex.normSq_eq_norm_sq, ← Complex.normSq_eq_norm_sq, h1, h2]
  exact (pow_left_inj₀ (norm_nonneg _) (norm_nonneg _) two_ne_zero).1 hsq

theorem witRoot_err (θ : ℝ) (m : ℕ) (ch : Fin m → Shape) :
    (witRoot θ (.node m ch)).err = ‖1 - w θ ^ ((Shape.node m ch).internal - 1)‖ := by
  set n := ∑ i, (ch i).internal with hn
  have hk : (Shape.node m ch).internal - 1 = n := by simp only [Shape.internal, hn]; omega
  rw [hk]
  simp only [witRoot, err, ContinuousLinearMap.id_apply, law_apply, one_mul,
    fun i => (wit_eval θ (ch i)).1, fun i => (wit_eval θ (ch i)).2, slot_exp θ, slot_real]
  rw [← Complex.exp_sum, ← Complex.ofReal_prod, Finset.prod_pow_eq_pow_sum, w_pow]
  have hΘ : ∑ i, ((((ch i).internal : ℝ) * θ : ℝ) : ℂ) * I = (((n : ℝ) * θ : ℝ) : ℂ) * I := by
    rw [← Finset.sum_mul]
    congr 1
    push_cast
    rw [hn, Nat.cast_sum, Finset.sum_mul]
  rw [hΘ, ← hn]
  exact norm_exp_sub_real _ _

end PMT
