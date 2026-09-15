/-
Heterogeneous Theorem R, part 3: the nodewise-angle witness (H4, construction).

Model: all spaces are `ℂ` as a real inner product space, leaves carry `1`.
* non-root node `u` with angle `θ_u`: `μ(x) = e^{iθ_u} ∏ slot(xᵢ)`, `P = Re`, defect `e_u`
* root:                               `μ(x) = ∏ slot(xᵢ)`,          `P = id`
The node angles are independent; the only constraint is `θ_u ∈ [0, arcsin e_u]`, which gives
`sin θ_u ≤ e_u` and hence full closure with defect `e_u`.

Statements:
* `PMT.AShape`                angle-annotated defect skeletons
* `PMT.AShape.exists_fill`    every `θ ∈ box(defects T)` is the preorder angle list of a valid
                              angle annotation of `T`
* `PMT.witH_eval`             `F = e^{i Σθ}`, `R = ∏ cos θ` on every non-root witness subtree
* `PMT.witH_admFull`          non-root witness subtrees are heterogeneous PMT-A admissible
* `PMT.witRootH_err`          `err = |1 - ∏_{u non-root} w(θ_u)|`
* `PMT.heterogeneous_witness` for every `θ ∈ box(childDefects T)` there is a tree in `A(T, η)`
                              whose error is exactly `|1 - ∏ w(θ_u)|`
-/
import PMTFormal.WitnessAdm
import PMTFormal.Heterogeneous.Upper

open Real Complex
open scoped RealInnerProductSpace

namespace PMT

/-- Defect skeletons with one angle per internal node. -/
inductive AShape where
  | leaf
  | node (m : ℕ) (e θ : ℝ) (ch : Fin m → AShape)

namespace AShape

/-- Underlying arity skeleton. -/
def skel : AShape → Shape
  | leaf => .leaf
  | node m _ _ ch => .node m (fun i => (ch i).skel)

/-- Underlying defect skeleton. -/
def dshape : AShape → DShape
  | leaf => .leaf
  | node m e _ ch => .node m e (fun i => (ch i).dshape)

/-- Angles of all internal nodes (preorder, same order as `DShape.defects`). -/
def angles : AShape → List ℝ
  | leaf => []
  | node _ _ θ ch => θ :: (List.ofFn fun i => (ch i).angles).flatten

/-- Every angle lies in its node box `[0, arcsin e]`. -/
def Valid : AShape → Prop
  | leaf => True
  | node _ e θ ch => BoxRel θ e ∧ ∀ i, (ch i).Valid

/-- Every box list is realised by a valid angle annotation. -/
theorem exists_fill (T : DShape) (θ : List ℝ) (h : θ ∈ box T.defects) :
    ∃ a : AShape, a.dshape = T ∧ a.angles = θ ∧ a.Valid := by
  induction T generalizing θ with
  | leaf =>
    have h' : List.Forall₂ BoxRel θ [] := h
    rw [List.forall₂_nil_right_iff] at h'
    exact ⟨leaf, rfl, h'.symm, trivial⟩
  | node m e ch ih =>
    have h' : List.Forall₂ BoxRel θ (e :: (List.ofFn fun i => (ch i).defects).flatten) := h
    cases h' with
    | cons hhead htail =>
      obtain ⟨g, hg, hgi⟩ := forall₂_flatten_ofFn _ _ htail
      choose a ha1 ha2 ha3 using fun i => ih i (g i) (hgi i)
      refine ⟨node m e _ a, ?_, ?_, hhead, ha3⟩
      · simp only [dshape, ha1]
      · simp only [angles, ha2, hg]

end AShape

open HPMTree

/-- Non-root heterogeneous witness subtree. -/
noncomputable def witH : AShape → HPMTree ℂ
  | .leaf => .leaf 1
  | .node m e θ ch =>
      .node m e (law (exp (θ * I)) m (fun i => (ch i).skel)) reProj (fun i => witH (ch i))

/-- Root heterogeneous witness. -/
noncomputable def witRootH (m : ℕ) (e : ℝ) (ach : Fin m → AShape) : HPMTree ℂ :=
  .node m e (law 1 m (fun i => (ach i).skel)) (ContinuousLinearMap.id ℝ ℂ) (fun i => witH (ach i))

theorem witH_dshape (a : AShape) : (witH a).dshape = a.dshape := by
  induction a with
  | leaf => rfl
  | node m e θ ch ih => simp only [witH, dshape, AShape.dshape, ih]

theorem witRootH_dshape (m : ℕ) (e : ℝ) (ach : Fin m → AShape) :
    (witRootH m e ach).dshape = .node m e (fun i => (ach i).dshape) := by
  simp only [witRootH, dshape, witH_dshape]

theorem slot_expH (a : AShape) :
    slot a.skel (exp (((a.angles.sum : ℝ) : ℂ) * I)) = exp (((a.angles.sum : ℝ) : ℂ) * I) := by
  cases a with
  | leaf => simp [slot, AShape.skel, AShape.angles, reProj_apply]
  | node _ _ _ _ => rfl

theorem witH_eval (a : AShape) :
    (witH a).F = exp (((a.angles.sum : ℝ) : ℂ) * I) ∧
      (witH a).R = (((a.angles.map Real.cos).prod : ℝ) : ℂ) := by
  induction a with
  | leaf => simp [witH, F, R, AShape.angles]
  | node m e θ ch ih =>
    constructor
    · simp only [witH, F, law_apply, fun i => (ih i).1, slot_expH]
      rw [← Complex.exp_sum, ← Complex.exp_add]
      congr 1
      simp only [AShape.angles, List.sum_cons, sum_flatten_ofFn]
      push_cast
      rw [add_mul, Finset.sum_mul]
    · simp only [witH, R, law_apply, fun i => (ih i).2, slot_real, reProj_apply]
      rw [← Complex.ofReal_prod, Complex.re_mul_ofReal, Complex.exp_ofReal_mul_I_re]
      simp only [AShape.angles, List.map_cons, List.prod_cons, map_cos_prod_flatten]

theorem witH_admFull (a : AShape) (ha : a.Valid) : (witH a).AdmFull := by
  induction a with
  | leaf => simp [witH, AdmFull]
  | node m e θ ch ih =>
    obtain ⟨hθ, hch⟩ := ha
    refine ⟨hθ.defect_nonneg, norm_law_le (Complex.norm_exp_ofReal_mul_I θ) m _,
      reProj_isOrthProj, ?_, fun i => ih i (hch i)⟩
    intro x hx
    -- every slot value is real
    have hreal : ∀ i, slot (ch i).skel (x i) = ((x i).re : ℂ) := by
      intro i
      have hi : (witH (ch i)).InRan (x i) := hx i
      cases hci : ch i with
      | leaf => simp [AShape.skel, slot, reProj_apply]
      | node m' e' θ' ch' =>
        rw [hci] at hi
        simp only [witH, InRan, reProj_apply] at hi
        simp only [AShape.skel, slot, ContinuousLinearMap.id_apply]
        exact hi.symm
    set r : ℝ := ∏ i, (x i).re with hr
    have hμx : law (exp (θ * I)) m (fun i => (ch i).skel) x = exp (θ * I) * (r : ℂ) := by
      rw [law_apply, Finset.prod_congr rfl (fun i _ => hreal i), ← Complex.ofReal_prod]
    have hdiff : law (exp (θ * I)) m (fun i => (ch i).skel) x -
        reProj (law (exp (θ * I)) m (fun i => (ch i).skel) x) =
        ((Real.sin θ * r : ℝ) : ℂ) * I := by
      rw [hμx, reProj_apply, Complex.re_mul_ofReal, Complex.exp_ofReal_mul_I_re]
      apply Complex.ext <;>
        simp [Complex.exp_ofReal_mul_I_re, Complex.exp_ofReal_mul_I_im, Complex.cos_ofReal_re,
          Complex.sin_ofReal_re]
    have hr_le : |r| ≤ ∏ i, ‖x i‖ := by
      rw [hr, Finset.abs_prod]
      exact Finset.prod_le_prod (fun i _ => abs_nonneg _) (fun i _ => Complex.abs_re_le_norm _)
    rw [hdiff, norm_mul, Complex.norm_I, mul_one, Complex.norm_real, Real.norm_eq_abs, abs_mul,
      abs_of_nonneg hθ.sin_nonneg]
    exact mul_le_mul hθ.sin_le hr_le (abs_nonneg _) hθ.defect_nonneg

theorem witRootH_rootAdmFull {m : ℕ} {e : ℝ} (he : 0 ≤ e) (ach : Fin m → AShape)
    (ha : ∀ i, (ach i).Valid) : (witRootH m e ach).RootAdmFull := by
  refine ⟨he, norm_law_le (by simp) m _, id_isOrthProj, ?_, fun i => witH_admFull (ach i) (ha i)⟩
  intro x _
  simp only [ContinuousLinearMap.id_apply, sub_self, norm_zero]
  exact mul_nonneg he (Finset.prod_nonneg fun i _ => norm_nonneg _)

theorem witRootH_err (m : ℕ) (e : ℝ) (ach : Fin m → AShape) :
    (witRootH m e ach).err = ‖1 - (((List.ofFn fun i => (ach i).angles).flatten).map w).prod‖ := by
  simp only [witRootH, err, ContinuousLinearMap.id_apply, law_apply, one_mul,
    fun i => (witH_eval (ach i)).1, fun i => (witH_eval (ach i)).2, slot_expH, slot_real]
  rw [← Complex.exp_sum, ← Complex.ofReal_prod, list_prod_w, map_cos_prod_flatten,
    sum_flatten_ofFn, ← Finset.sum_mul, ← Complex.ofReal_sum]
  exact norm_exp_sub_real _ _

/-- **Heterogeneous witness (H4, construction).** For every defect skeleton `T` with root defect
`e ≥ 0` and every angle list `θ ∈ box(childDefects T)` there is a heterogeneous PMT-A tree over `ℂ`
with skeleton `T` and projected error exactly `|1 - ∏ w(θ_u)|`. -/
theorem heterogeneous_witness {m : ℕ} {e : ℝ} (he : 0 ≤ e) (ch : Fin m → DShape) {θ : List ℝ}
    (hθ : θ ∈ box (DShape.node m e ch).childDefects) :
    ∃ t : HPMTree ℂ, t.dshape = .node m e ch ∧ t.RootAdmFull ∧
      t.err = ‖1 - (θ.map w).prod‖ := by
  obtain ⟨g, hg, hgi⟩ := forall₂_flatten_ofFn (fun i => (ch i).defects) θ hθ
  choose a ha1 ha2 ha3 using fun i => AShape.exists_fill (ch i) (g i) (hgi i)
  refine ⟨witRootH m e a, ?_, witRootH_rootAdmFull he a ha3, ?_⟩
  · simp only [witRootH_dshape, ha1]
  · rw [witRootH_err, hg]
    simp only [ha2]

end PMT
