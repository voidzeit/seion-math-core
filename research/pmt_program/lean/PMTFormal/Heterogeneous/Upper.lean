/-
Heterogeneous Theorem R, part 2: nodewise-defect trees and the upper bound (H1).

Every internal node `v` carries its own defect `e_v`. Normalisation is the same as in `Tree.lean`
(`‖μ_v‖ ≤ 1`, leaves in the unit ball); the closure constant at `v` is `e_v` (paper: `η_v = ρ_v/M_v`).

Statements:
* `PMT.HPMTree`                trees whose internal nodes carry `(m, e, μ, P, children)`
* `PMT.DShape`                 defect skeletons; `defects` (all internal nodes, preorder),
                               `childDefects` (all non-root internal nodes)
* `PMT.HPMTree.AdmFull`        heterogeneous PMT-A admissibility (full closure with `e_v`)
* `PMT.HPMTree.RootAdmFull`    the same at a tree that is not a bare leaf (the class `A(T, η)`)
* `PMT.envelopeH`              every non-root subtree is dominated by `(∏ cos θ, ∑ θ)` with
                               `θ ∈ box(defects)`: one angle per internal node, `θ_u ≤ arcsin e_u`
* `PMT.heterogeneous_upper`    `err ≤ |1 - ∏ w(θ_u)|` for some `θ ∈ box(childDefects)`
* `PMT.heterogeneous_le_gBox`  `err ≤ gBox(childDefects)`
-/
import PMTFormal.Tree
import PMTFormal.Heterogeneous.BoxConstant

open Real
open scoped RealInnerProductSpace

namespace PMT

/-- A projected multilinear tree with nodewise defects, over one real inner product space `G`. -/
inductive HPMTree (G : Type*) [NormedAddCommGroup G] [InnerProductSpace ℝ G] where
  | leaf (z : G)
  | node (m : ℕ) (e : ℝ) (μ : ContinuousMultilinearMap ℝ (fun _ : Fin m => G) G)
      (P : G →L[ℝ] G) (ch : Fin m → HPMTree G)

/-- Defect skeletons: arities and one defect per internal node. -/
inductive DShape where
  | leaf
  | node (m : ℕ) (e : ℝ) (ch : Fin m → DShape)

namespace DShape

/-- Defects of all internal nodes (preorder). -/
def defects : DShape → List ℝ
  | leaf => []
  | node _ e ch => e :: (List.ofFn fun i => (ch i).defects).flatten

/-- Defects of all non-root internal nodes. -/
def childDefects : DShape → List ℝ
  | leaf => []
  | node _ _ ch => (List.ofFn fun i => (ch i).defects).flatten

end DShape

namespace HPMTree

variable {G : Type*} [NormedAddCommGroup G] [InnerProductSpace ℝ G]

/-- Ambient evaluation `F`. -/
def F : HPMTree G → G
  | leaf z => z
  | node _ _ μ _ ch => μ (fun i => (ch i).F)

/-- Reduced evaluation `R`. -/
def R : HPMTree G → G
  | leaf z => z
  | node _ _ μ P ch => P (μ (fun i => (ch i).R))

/-- Projected root error `‖P_r F_r - R_r‖` (zero for a bare leaf). -/
def err : HPMTree G → ℝ
  | leaf _ => 0
  | node _ _ μ P ch => ‖P (μ (fun i => (ch i).F)) - P (μ (fun i => (ch i).R))‖

/-- `v` lies in the admissible input set of the slot occupied by this subtree. -/
def InRan : HPMTree G → G → Prop
  | leaf _, _ => True
  | node _ _ _ P _, v => P v = v

/-- The defect skeleton of a tree. -/
def dshape : HPMTree G → DShape
  | leaf _ => .leaf
  | node m e _ _ ch => .node m e (fun i => (ch i).dshape)

/-- Trajectory-closure admissibility with nodewise defects (normalised). -/
def AdmTC : HPMTree G → Prop
  | leaf z => ‖z‖ ≤ 1
  | node _ e μ P ch => 0 ≤ e ∧ ‖μ‖ ≤ 1 ∧ IsOrthProj P ∧
      ‖μ (fun i => (ch i).R) - P (μ (fun i => (ch i).R))‖ ≤ e * ∏ i, ‖(ch i).R‖ ∧
      ∀ i, (ch i).AdmTC

/-- Heterogeneous PMT-A admissibility (normalised): full closure with `e_v` at every node. -/
def AdmFull : HPMTree G → Prop
  | leaf z => ‖z‖ ≤ 1
  | node _ e μ P ch => 0 ≤ e ∧ ‖μ‖ ≤ 1 ∧ IsOrthProj P ∧
      (∀ x : (i : Fin _) → G, (∀ i, (ch i).InRan (x i)) →
        ‖μ x - P (μ x)‖ ≤ e * ∏ i, ‖x i‖) ∧
      ∀ i, (ch i).AdmFull

/-- Root admissibility for the upper bound: no closure is required at the root. -/
def RootAdm : HPMTree G → Prop
  | leaf _ => False
  | node _ _ μ P ch => ‖μ‖ ≤ 1 ∧ IsOrthProj P ∧ ∀ i, (ch i).AdmTC

/-- Heterogeneous PMT-A admissibility of a tree with at least one internal node. -/
def RootAdmFull : HPMTree G → Prop
  | leaf _ => False
  | node m e μ P ch => (node m e μ P ch).AdmFull

theorem inRan_R : ∀ t : HPMTree G, t.AdmFull → t.InRan t.R
  | leaf _, _ => trivial
  | node _ _ _ _ _, h => h.2.2.1.idem _

theorem admTC_of_admFull (t : HPMTree G) (ht : t.AdmFull) : t.AdmTC := by
  induction t with
  | leaf z => exact ht
  | node m e μ P ch ih =>
    obtain ⟨he, hμ, hP, hcl, hch⟩ := ht
    exact ⟨he, hμ, hP, hcl _ (fun i => inRan_R (ch i) (hch i)), fun i => ih i (hch i)⟩

theorem rootAdm_of_rootAdmFull (t : HPMTree G) (ht : t.RootAdmFull) : t.RootAdm := by
  cases t with
  | leaf z => exact ht.elim
  | node m e μ P ch =>
    obtain ⟨_, hμ, hP, _, hch⟩ := ht
    exact ⟨hμ, hP, fun i => admTC_of_admFull (ch i) (hch i)⟩

end HPMTree

open HPMTree

variable {G : Type*} [NormedAddCommGroup G] [InnerProductSpace ℝ G]

theorem map_cos_prod_flatten {m : ℕ} (θs : Fin m → List ℝ) :
    (((List.ofFn θs).flatten).map Real.cos).prod = ∏ i, ((θs i).map Real.cos).prod := by
  rw [List.map_flatten, List.prod_flatten, List.map_ofFn, List.map_ofFn, List.prod_ofFn]
  rfl

theorem sum_flatten_ofFn {m : ℕ} (θs : Fin m → List ℝ) :
    ((List.ofFn θs).flatten).sum = ∑ i, (θs i).sum := by
  rw [List.sum_flatten, List.map_ofFn, List.sum_ofFn]
  rfl

/-- **Heterogeneous multiplicative envelope.** -/
theorem envelopeH (t : HPMTree G) (ht : t.AdmTC) :
    ∃ θs ∈ box t.dshape.defects, Dom t.F t.R (θs.map Real.cos).prod θs.sum := by
  induction t with
  | leaf z =>
    exact ⟨[], List.Forall₂.nil, by simpa [F, R] using dom_leaf (show ‖z‖ ≤ 1 from ht)⟩
  | node m e μ P ch ih =>
    obtain ⟨he, hμ, hP, hTC, hch⟩ := ht
    choose θs hbox hdom using fun i => ih i (hch i)
    obtain ⟨θ, hθ, hD⟩ := node_step μ hμ P hP he (fun i => (ch i).F) (fun i => (ch i).R)
      (fun i => ((θs i).map Real.cos).prod) (fun i => (θs i).sum) hdom hTC
    refine ⟨θ :: (List.ofFn θs).flatten, ?_, ?_⟩
    · exact List.Forall₂.cons hθ (forall₂_flatten_ofFn_of θs _ hbox)
    · rw [List.map_cons, List.prod_cons, List.sum_cons, map_cos_prod_flatten, sum_flatten_ofFn]
      exact hD

/-- **Heterogeneous Theorem R, upper bound (H1), under root trajectory closure.** -/
theorem heterogeneous_upper_of_rootAdm (t : HPMTree G) (ht : t.RootAdm) :
    ∃ θ ∈ box t.dshape.childDefects, t.err ≤ ‖1 - (θ.map w).prod‖ := by
  cases t with
  | leaf z => exact ht.elim
  | node m e μ P ch =>
    obtain ⟨hμ, hP, hch⟩ := ht
    choose θs hbox hdom using fun i => envelopeH (ch i) (hch i)
    have hroot := root_step μ hμ P hP (fun i => (ch i).F) (fun i => (ch i).R)
      (fun i => ((θs i).map Real.cos).prod) (fun i => (θs i).sum) hdom
    rw [← map_cos_prod_flatten, ← sum_flatten_ofFn] at hroot
    have hL : (List.ofFn θs).flatten ∈ box (node m e μ P ch).dshape.childDefects :=
      forall₂_flatten_ofFn_of θs _ hbox
    obtain ⟨θ', hθ', hle⟩ := box_capped hL
    refine ⟨θ', hθ', ?_⟩
    exact (abs_le_of_sq_le_sq' (hroot.trans hle) (norm_nonneg _)).2

/-- **Heterogeneous Theorem R, upper bound (H1).** Every heterogeneous PMT-A tree satisfies
`err ≤ |1 - ∏_{u non-root} w(θ_u)|` for some angles `θ_u ∈ [0, arcsin e_u]`. -/
theorem heterogeneous_upper (t : HPMTree G) (ht : t.RootAdmFull) :
    ∃ θ ∈ box t.dshape.childDefects, t.err ≤ ‖1 - (θ.map w).prod‖ :=
  heterogeneous_upper_of_rootAdm t (rootAdm_of_rootAdmFull t ht)

/-- H1 in constant form: `err ≤ gBox(childDefects)`. -/
theorem heterogeneous_le_gBox (t : HPMTree G) (ht : t.RootAdmFull) :
    t.err ≤ gBox t.dshape.childDefects := by
  obtain ⟨θ, hθ, hle⟩ := heterogeneous_upper t ht
  exact hle.trans (le_gBox hθ)

end PMT
