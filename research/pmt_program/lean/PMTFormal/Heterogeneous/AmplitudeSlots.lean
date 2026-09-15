/-
Slot-wise a posteriori error bound (refinement of `Amplitude.lean`).

Telescoping with exact values on the left and computed values on the right
(`MultilinearMap.map_sub_map_piecewise`):

  `μ F − μ R = Σ_i μ(F_{<i}, F_i − R_i, R_{>i})`.

So `‖μ F − μ R‖ ≤ Σ_i K_i ‖F_i − R_i‖` for any slot constants `K_i ≥ 0` with
`‖μ(F_{<i}, x, R_{>i})‖ ≤ K_i ‖x‖` for all `x`. Two admissible choices:

* general: `K_i = ‖μ‖ · ∏_{j<i} ‖F_j‖ · ∏_{j>i} ‖R_j‖` (`slot_const_general`; in practice
  `‖F_j‖ ≤ ‖R_j‖ + e_j`);
* exact prefix: if `F_j = R_j` for all `j < i` (e.g. leaf children), the slot map is
  `x ↦ μ(update R i x)`, whose operator norm can be computed from the run (`slot_args_eq_update`).

Statements:
* `PMT.norm_sub_le_slots`           node-level telescoping bound
* `PMT.slot_const_general`          general slot constant
* `PMT.slot_args_eq_update`         exact-prefix reduction
* `PMT.KTree.err_le_sbound`         tree recursion `e_v = Σ_i K_i e_i + d_v`
-/
import PMTFormal.Heterogeneous.Amplitude

open Real

namespace PMT

variable {G : Type*} [NormedAddCommGroup G] [InnerProductSpace ℝ G]

/-- Mixed argument tuple: exact values before `i`, `x` at `i`, computed values after `i`. -/
def slotArgs {m : ℕ} (F R : Fin m → G) (i : Fin m) (x : G) : Fin m → G :=
  fun j => if j < i then F j else if i = j then x else R j

theorem norm_sub_le_slots {m : ℕ} (μ : ContinuousMultilinearMap ℝ (fun _ : Fin m => G) G)
    (F R : Fin m → G) (K : Fin m → ℝ)
    (hK : ∀ i x, ‖μ (slotArgs F R i x)‖ ≤ K i * ‖x‖) :
    ‖μ F - μ R‖ ≤ ∑ i, K i * ‖F i - R i‖ := by
  classical
  have h := μ.toMultilinearMap.map_sub_map_piecewise F R Finset.univ
  rw [Finset.piecewise_univ] at h
  have h' : μ F - μ R = ∑ i, μ (slotArgs F R i (F i - R i)) := by
    simp only [ContinuousMultilinearMap.coe_coe] at h
    rw [h]
    refine Finset.sum_congr rfl fun i _ => congrArg μ (funext fun j => ?_)
    simp only [slotArgs, Finset.mem_univ, true_implies]
    split_ifs with h1 h2 <;> simp_all
  rw [h']
  refine (norm_sum_le _ _).trans (Finset.sum_le_sum fun i _ => hK i _)

theorem slot_const_general {m : ℕ} (μ : ContinuousMultilinearMap ℝ (fun _ : Fin m => G) G)
    (F R : Fin m → G) (i : Fin m) (x : G) :
    ‖μ (slotArgs F R i x)‖ ≤
      ‖μ‖ * (∏ j, (if j < i then ‖F j‖ else if i = j then 1 else ‖R j‖)) * ‖x‖ := by
  classical
  calc ‖μ (slotArgs F R i x)‖ ≤ ‖μ‖ * ∏ j, ‖slotArgs F R i x j‖ := μ.le_opNorm _
    _ = ‖μ‖ * (∏ j, (if j < i then ‖F j‖ else if i = j then 1 else ‖R j‖)) * ‖x‖ := by
      rw [mul_assoc]
      congr 1
      have hsplit : ∏ j, ‖slotArgs F R i x j‖ =
          ∏ j, ((if j < i then ‖F j‖ else if i = j then 1 else ‖R j‖) *
            (if i = j then ‖x‖ else 1)) := by
        refine Finset.prod_congr rfl fun j _ => ?_
        simp only [slotArgs]
        by_cases hji : j < i
        · have : i ≠ j := fun h => (lt_irrefl j) (h ▸ hji)
          simp [hji, this]
        · by_cases hij : i = j
          · subst hij; simp
          · simp [hji, hij]
      rw [hsplit, Finset.prod_mul_distrib, Finset.prod_ite_eq]
      simp

omit [NormedAddCommGroup G] [InnerProductSpace ℝ G] in
theorem slot_args_eq_update {m : ℕ} (F R : Fin m → G) (i : Fin m) (x : G)
    (hF : ∀ j, j < i → F j = R j) :
    slotArgs F R i x = Function.update R i x := by
  funext j
  simp only [slotArgs, Function.update]
  by_cases hji : j < i
  · have : j ≠ i := ne_of_lt hji
    simp [hji, this, hF j hji]
  · by_cases hij : i = j
    · subst hij; simp
    · have : j ≠ i := fun h => hij h.symm
      simp [hji, hij, this]

/-- Trees with exact/computed values and per-slot constants at every internal node. -/
inductive KTree (G : Type*) [NormedAddCommGroup G] [InnerProductSpace ℝ G] where
  | leaf (z zt : G)
  | node (m : ℕ) (μ : ContinuousMultilinearMap ℝ (fun _ : Fin m => G) G) (K : Fin m → ℝ) (Rt : G)
      (ch : Fin m → KTree G)

namespace KTree

def F : KTree G → G
  | leaf z _ => z
  | node _ μ _ _ ch => μ (fun i => (ch i).F)

def R : KTree G → G
  | leaf _ zt => zt
  | node _ _ _ Rt _ => Rt

/-- Slot constants are nonnegative and bound the mixed slot maps. -/
def SlotOK : KTree G → Prop
  | leaf _ _ => True
  | node _ μ K _ ch => (∀ i, 0 ≤ K i) ∧
      (∀ i x, ‖μ (slotArgs (fun j => (ch j).F) (fun j => (ch j).R) i x)‖ ≤ K i * ‖x‖) ∧
      ∀ i, (ch i).SlotOK

noncomputable def sbound : KTree G → ℝ
  | leaf z zt => ‖z - zt‖
  | node _ μ K Rt ch => ∑ i, K i * (ch i).sbound + ‖μ (fun i => (ch i).R) - Rt‖

/-- **Slot-wise a posteriori error bound.** -/
theorem err_le_sbound (t : KTree G) (ht : t.SlotOK) : ‖t.F - t.R‖ ≤ t.sbound := by
  induction t with
  | leaf z zt => exact le_rfl
  | node m μ K Rt ch ih =>
    obtain ⟨hK0, hK, hch⟩ := ht
    have hsplit : μ (fun i => (ch i).F) - Rt =
        (μ (fun i => (ch i).F) - μ (fun i => (ch i).R)) + (μ (fun i => (ch i).R) - Rt) := by
      abel
    show ‖μ (fun i => (ch i).F) - Rt‖ ≤ _
    rw [hsplit]
    refine (norm_add_le _ _).trans (add_le_add ?_ le_rfl)
    refine (norm_sub_le_slots μ _ _ K hK).trans (Finset.sum_le_sum fun i _ => ?_)
    exact mul_le_mul_of_nonneg_left (ih i (hch i)) (hK0 i)

end KTree

/-! ### Automatic slot constants and the compact recurrence -/

/-- `Σ_i a_i ∏_{j<i}(r_j + a_j) ∏_{j>i} r_j = ∏_j (r_j + a_j) − ∏_j r_j`. -/
theorem sum_slot_prod_eq : ∀ {m : ℕ} (r a : Fin m → ℝ),
    ∑ i, a i * ∏ j, (if j < i then r j + a j else if i = j then 1 else r j) =
      ∏ j, (r j + a j) - ∏ j, r j
  | 0, r, a => by simp
  | m + 1, r, a => by
    have ih := sum_slot_prod_eq (fun j : Fin m => r j.succ) (fun j => a j.succ)
    have h0 : ∏ j, (if j < (0 : Fin (m + 1)) then r j + a j else if (0 : Fin (m + 1)) = j then 1
        else r j) = ∏ j : Fin m, r j.succ := by
      rw [Fin.prod_univ_succ]
      simp [(Fin.succ_ne_zero _).symm]
    have hs : ∀ k : Fin m, ∏ j, (if j < k.succ then r j + a j else if k.succ = j then 1 else r j) =
        (r 0 + a 0) * ∏ j : Fin m, (if j < k then r j.succ + a j.succ else if k = j then 1
          else r j.succ) := by
      intro k
      rw [Fin.prod_univ_succ]
      simp [Fin.succ_lt_succ_iff, Fin.succ_inj, Fin.succ_pos]
    rw [Fin.sum_univ_succ, h0]
    simp_rw [hs]
    have hmul : ∑ k : Fin m, a k.succ * ((r 0 + a 0) * ∏ j : Fin m,
        (if j < k then r j.succ + a j.succ else if k = j then 1 else r j.succ)) =
        (r 0 + a 0) * ∑ k : Fin m, a k.succ * ∏ j : Fin m,
          (if j < k then r j.succ + a j.succ else if k = j then 1 else r j.succ) := by
      rw [Finset.mul_sum]
      exact Finset.sum_congr rfl fun k _ => by ring
    rw [hmul, ih, Fin.prod_univ_succ (fun j => r j + a j), Fin.prod_univ_succ r]
    ring

namespace ATree

/-- Compact a posteriori bound: `A_v = d_v + M_v (∏_i (‖R_i‖ + A_i) − ∏_i ‖R_i‖)`. -/
noncomputable def abound : ATree G → ℝ
  | leaf z zt => ‖z - zt‖
  | node _ M μ Rt ch =>
      M * (∏ i, (‖(ch i).R‖ + (ch i).abound) - ∏ i, ‖(ch i).R‖) + ‖μ (fun i => (ch i).R) - Rt‖

/-- **Automatic a posteriori bound** (slot constants derived from `M_v` and child bounds). -/
theorem err_le_abound (t : ATree G) (ht : t.NormOK) : ‖t.F - t.R‖ ≤ t.abound := by
  classical
  induction t with
  | leaf z zt => exact le_rfl
  | node m M μ Rt ch ih =>
    obtain ⟨hμ, hch⟩ := ht
    have hih : ∀ i, ‖(ch i).F - (ch i).R‖ ≤ (ch i).abound := fun i => ih i (hch i)
    have hA0 : ∀ i, 0 ≤ (ch i).abound := fun i => (norm_nonneg _).trans (hih i)
    have hM0 : 0 ≤ M := (norm_nonneg μ).trans hμ
    have hFj : ∀ j, ‖(ch j).F‖ ≤ ‖(ch j).R‖ + (ch j).abound := fun j => by
      calc ‖(ch j).F‖ = ‖((ch j).F - (ch j).R) + (ch j).R‖ := by rw [sub_add_cancel]
        _ ≤ ‖(ch j).F - (ch j).R‖ + ‖(ch j).R‖ := norm_add_le _ _
        _ ≤ ‖(ch j).R‖ + (ch j).abound := by linarith [hih j]
    have hsplit : μ (fun i => (ch i).F) - Rt =
        (μ (fun i => (ch i).F) - μ (fun i => (ch i).R)) + (μ (fun i => (ch i).R) - Rt) := by
      abel
    show ‖μ (fun i => (ch i).F) - Rt‖ ≤ _
    rw [hsplit]
    refine (norm_add_le _ _).trans (add_le_add ?_ le_rfl)
    set Fs : Fin m → G := fun i => (ch i).F
    set Rs : Fin m → G := fun i => (ch i).R
    have hnode := norm_sub_le_slots μ Fs Rs
      (fun i => ‖μ‖ * (∏ j, (if j < i then ‖Fs j‖ else if i = j then 1 else ‖Rs j‖)))
      (fun i x => slot_const_general μ Fs Rs i x)
    refine hnode.trans ?_
    rw [← sum_slot_prod_eq (fun j => ‖(ch j).R‖) (fun j => (ch j).abound), Finset.mul_sum]
    refine Finset.sum_le_sum fun i _ => ?_
    have hfac : ∀ j, 0 ≤ (if j < i then ‖(ch j).R‖ + (ch j).abound else if i = j then 1
        else ‖(ch j).R‖) := fun j => by
      split_ifs
      · exact add_nonneg (norm_nonneg _) (hA0 j)
      · exact zero_le_one
      · exact norm_nonneg _
    have hprod : ∏ j, (if j < i then ‖Fs j‖ else if i = j then 1 else ‖Rs j‖) ≤
        ∏ j, (if j < i then ‖(ch j).R‖ + (ch j).abound else if i = j then 1 else ‖(ch j).R‖) := by
      refine Finset.prod_le_prod (fun j _ => by split_ifs <;> positivity) fun j _ => ?_
      split_ifs
      · exact hFj j
      · exact le_rfl
      · exact le_rfl
    calc ‖μ‖ * (∏ j, (if j < i then ‖Fs j‖ else if i = j then 1 else ‖Rs j‖)) * ‖Fs i - Rs i‖
        ≤ M * (∏ j, (if j < i then ‖(ch j).R‖ + (ch j).abound else if i = j then 1
            else ‖(ch j).R‖)) * (ch i).abound :=
          mul_le_mul (mul_le_mul hμ hprod (Finset.prod_nonneg fun j _ => by split_ifs <;> positivity)
            hM0) (hih i) (norm_nonneg _) (mul_nonneg hM0 (Finset.prod_nonneg fun j _ => hfac j))
      _ = M * ((ch i).abound * ∏ j, (if j < i then ‖(ch j).R‖ + (ch j).abound else if i = j then 1
            else ‖(ch j).R‖)) := by ring

end ATree

end PMT