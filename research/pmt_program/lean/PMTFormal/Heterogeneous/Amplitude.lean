/-
A posteriori, amplitude-aware forward error bound for arbitrary local perturbations.

This is **not** part of Theorem R and is not sharp. It is the rigorous companion certificate used when
Theorem R's worst-case scale `Λ_T` is vacuous, and it covers any local perturbation (orthogonal or
approximate projection, rounding, quantisation) as long as the local deviation is measured.

Model (`ATree`): every leaf stores an exact value `z` and a computed value `zt`; every internal node
stores a multilinear law `μ`, an operator-norm bound `M`, and the computed value `Rt`. The exact
evaluation is `F = μ(F_children)`; the computed evaluation is `R = Rt`. The local deviation is
`d_v = ‖μ(R_children) − Rt‖` (leaves: `‖z − zt‖`).

Bound (`ebound`), computable from run data and the bounds `M_v`:
  `e_v = M_v · Σ_i (e_i · ∏_{j ≠ i} (‖R_j‖ + e_j)) + d_v`.

Statements:
* `PMT.ATree.err_le_ebound`   `‖F − R‖ ≤ ebound` at every node
* `PMT.ATree.norm_F_ge`       `‖R‖ − ebound ≤ ‖F‖` (a posteriori amplitude of the exact result)
-/
import PMTFormal.Heterogeneous.Upper

open Real

namespace PMT

/-- Trees with exact and computed values at every vertex. -/
inductive ATree (G : Type*) [NormedAddCommGroup G] [InnerProductSpace ℝ G] where
  | leaf (z zt : G)
  | node (m : ℕ) (M : ℝ) (μ : ContinuousMultilinearMap ℝ (fun _ : Fin m => G) G) (Rt : G)
      (ch : Fin m → ATree G)

namespace ATree

variable {G : Type*} [NormedAddCommGroup G] [InnerProductSpace ℝ G]

/-- Exact evaluation. -/
def F : ATree G → G
  | leaf z _ => z
  | node _ _ μ _ ch => μ (fun i => (ch i).F)

/-- Computed (stored) value. -/
def R : ATree G → G
  | leaf _ zt => zt
  | node _ _ _ Rt _ => Rt

/-- Local deviation. -/
def dev : ATree G → ℝ
  | leaf z zt => ‖z - zt‖
  | node _ _ μ Rt ch => ‖μ (fun i => (ch i).R) - Rt‖

/-- Operator-norm bounds hold at every node. -/
def NormOK : ATree G → Prop
  | leaf _ _ => True
  | node _ M μ _ ch => ‖μ‖ ≤ M ∧ ∀ i, (ch i).NormOK

/-- The a posteriori error bound. -/
noncomputable def ebound : ATree G → ℝ
  | leaf z zt => ‖z - zt‖
  | node _ M μ Rt ch =>
      M * ∑ i, ∏ j, (if j = i then (ch i).ebound else ‖(ch j).R‖ + (ch j).ebound) +
        ‖μ (fun i => (ch i).R) - Rt‖

/-- **A posteriori amplitude-aware error bound.** -/
theorem err_le_ebound (t : ATree G) (ht : t.NormOK) : ‖t.F - t.R‖ ≤ t.ebound := by
  induction t with
  | leaf z zt => exact le_rfl
  | node m M μ Rt ch ih =>
    obtain ⟨hμ, hch⟩ := ht
    have hih : ∀ i, ‖(ch i).F - (ch i).R‖ ≤ (ch i).ebound := fun i => ih i (hch i)
    have he0 : ∀ i, 0 ≤ (ch i).ebound := fun i => (norm_nonneg _).trans (hih i)
    have hM0 : 0 ≤ M := (norm_nonneg μ).trans hμ
    have hsplit : μ (fun i => (ch i).F) - Rt =
        (μ (fun i => (ch i).F) - μ (fun i => (ch i).R)) + (μ (fun i => (ch i).R) - Rt) := by
      abel
    show ‖μ (fun i => (ch i).F) - Rt‖ ≤ _
    rw [hsplit]
    refine (norm_add_le _ _).trans (add_le_add ?_ le_rfl)
    classical
    refine (μ.norm_image_sub_le' _ _).trans ?_
    refine mul_le_mul hμ (Finset.sum_le_sum fun i _ => Finset.prod_le_prod ?_ ?_)
      (Finset.sum_nonneg fun i _ => Finset.prod_nonneg fun j _ => by
        split_ifs <;> positivity) hM0
    · intro j _
      split_ifs <;> positivity
    · intro j _
      split_ifs with hji
      · subst hji
        exact hih j
      · refine max_le ?_ (le_add_of_nonneg_right (he0 j))
        calc ‖(ch j).F‖ = ‖((ch j).F - (ch j).R) + (ch j).R‖ := by rw [sub_add_cancel]
          _ ≤ ‖(ch j).F - (ch j).R‖ + ‖(ch j).R‖ := norm_add_le _ _
          _ ≤ ‖(ch j).R‖ + (ch j).ebound := by linarith [hih j]

/-- The exact result has amplitude at least `‖R‖ − ebound`. -/
theorem norm_F_ge (t : ATree G) (ht : t.NormOK) : ‖t.R‖ - t.ebound ≤ ‖t.F‖ := by
  have h := err_le_ebound t ht
  have h2 : ‖t.R‖ ≤ ‖t.F‖ + ‖t.F - t.R‖ := by
    calc ‖t.R‖ = ‖t.F - (t.F - t.R)‖ := by rw [sub_sub_cancel]
      _ ≤ ‖t.F‖ + ‖t.F - t.R‖ := norm_sub_le _ _
  linarith

end ATree

end PMT
