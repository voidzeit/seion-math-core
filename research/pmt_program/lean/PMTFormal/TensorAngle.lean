/-
Tensor angle lemma in multilinear form (lifted-angle proof).

For a continuous multilinear map `μ` with `‖μ‖ ≤ 1` and inputs in the closed unit ball,
  `phi (μ x) (μ y) ≤ ∑ i, phi (x i) (y i)`.
Proof: telescoping through the mixed tuples `mixTuple x y k` (slots `< k` from `y`, the rest from
`x`), the triangle inequality for `phi`, and contraction monotonicity in the single changed slot.

Statement:
* `PMT.phi_multilinear_le`
-/
import PMTFormal.LiftedAngle

open Real
open scoped RealInnerProductSpace

namespace PMT

variable {E G : Type*} [NormedAddCommGroup E] [InnerProductSpace ℝ E]
  [NormedAddCommGroup G] [InnerProductSpace ℝ G]

omit [InnerProductSpace ℝ E] in
/-- Product of norms of a tuple with one slot replaced is at most the norm of the new entry. -/
theorem prod_norm_update_le {m : ℕ} (z : Fin m → E) (hz : ∀ i, ‖z i‖ ≤ 1) (j : Fin m) (v : E) :
    ∏ i, ‖Function.update z j v i‖ ≤ ‖v‖ := by
  classical
  calc ∏ i, ‖Function.update z j v i‖
      ≤ ∏ i, (if i = j then ‖v‖ else 1) := by
        apply Finset.prod_le_prod (fun i _ => norm_nonneg _)
        intro i _
        by_cases h : i = j
        · rw [h, Function.update_self, if_pos rfl]
        · rw [Function.update_of_ne h, if_neg h]
          exact hz i
    _ = ‖v‖ := by simp

theorem norm_apply_le_one {m : ℕ} (μ : ContinuousMultilinearMap ℝ (fun _ : Fin m => E) G)
    (hμ : ‖μ‖ ≤ 1) (z : Fin m → E) (hz : ∀ i, ‖z i‖ ≤ 1) : ‖μ z‖ ≤ 1 := by
  calc ‖μ z‖ ≤ ‖μ‖ * ∏ i, ‖z i‖ := μ.le_opNorm z
    _ ≤ 1 * 1 := by
        apply mul_le_mul hμ (Finset.prod_le_one (fun i _ => norm_nonneg _) (fun i _ => hz i))
          (Finset.prod_nonneg fun i _ => norm_nonneg _) zero_le_one
    _ = 1 := by ring

/-- Mixed tuple: slots with index `< k` from `y`, the others from `x`. -/
def mixTuple {m : ℕ} (x y : Fin m → E) (k : ℕ) : Fin m → E :=
  fun i => if (i : ℕ) < k then y i else x i

omit [InnerProductSpace ℝ E] in
theorem mixTuple_norm_le {m : ℕ} {x y : Fin m → E} (hx : ∀ i, ‖x i‖ ≤ 1) (hy : ∀ i, ‖y i‖ ≤ 1)
    (k : ℕ) (i : Fin m) : ‖mixTuple x y k i‖ ≤ 1 := by
  unfold mixTuple
  split_ifs
  · exact hy i
  · exact hx i

/-- One slot of the telescoping sum. -/
theorem phi_mix_step {m : ℕ} (μ : ContinuousMultilinearMap ℝ (fun _ : Fin m => E) G)
    (hμ : ‖μ‖ ≤ 1) (x y : Fin m → E) (hx : ∀ i, ‖x i‖ ≤ 1) (hy : ∀ i, ‖y i‖ ≤ 1)
    (j : Fin m) :
    phi (μ (mixTuple x y j)) (μ (mixTuple x y ((j : ℕ) + 1))) ≤ phi (x j) (y j) := by
  classical
  have hzj : mixTuple x y j = Function.update (mixTuple x y j) j (x j) := by
    funext i
    by_cases h : i = j
    · rw [h, Function.update_self]
      simp only [mixTuple, lt_irrefl, if_false]
    · rw [Function.update_of_ne h]
  have hzk1 : mixTuple x y ((j : ℕ) + 1) = Function.update (mixTuple x y j) j (y j) := by
    funext i
    by_cases h : i = j
    · rw [h, Function.update_self]
      simp only [mixTuple]
      rw [if_pos (Nat.lt_succ_self _)]
    · rw [Function.update_of_ne h]
      have hi : (i : ℕ) ≠ (j : ℕ) := fun e => h (Fin.ext e)
      simp only [mixTuple]
      by_cases hlt : (i : ℕ) < (j : ℕ)
      · rw [if_pos hlt, if_pos (by omega)]
      · rw [if_neg hlt, if_neg (by omega)]
  have e12 : phi (μ (mixTuple x y j)) (μ (mixTuple x y ((j : ℕ) + 1))) =
      phi (μ (Function.update (mixTuple x y j) j (x j)))
        (μ (Function.update (mixTuple x y j) j (y j))) :=
    congrArg₂ phi (congrArg μ hzj) (congrArg μ hzk1)
  have hcontr : ∀ s t : ℝ,
      ‖s • μ (Function.update (mixTuple x y j) j (x j)) +
          t • μ (Function.update (mixTuple x y j) j (y j))‖ ≤ ‖s • x j + t • y j‖ := by
    intro s t
    rw [← ContinuousMultilinearMap.map_update_smul, ← ContinuousMultilinearMap.map_update_smul,
      ← ContinuousMultilinearMap.map_update_add]
    calc ‖μ (Function.update (mixTuple x y j) j (s • x j + t • y j))‖
        ≤ ‖μ‖ * ∏ i, ‖Function.update (mixTuple x y j) j (s • x j + t • y j) i‖ := μ.le_opNorm _
      _ ≤ 1 * ‖s • x j + t • y j‖ :=
          mul_le_mul hμ (prod_norm_update_le _ (mixTuple_norm_le hx hy _) j _)
            (Finset.prod_nonneg fun i _ => norm_nonneg _) zero_le_one
      _ = ‖s • x j + t • y j‖ := one_mul _
  have hc := phi_le_of_contr (f := μ (Function.update (mixTuple x y j) j (x j)))
    (g := μ (Function.update (mixTuple x y j) j (y j))) (hx j) (hy j) hcontr
  exact e12.trans_le hc.2.2

/-- **Tensor angle lemma (multilinear form).** -/
theorem phi_multilinear_le {m : ℕ} (μ : ContinuousMultilinearMap ℝ (fun _ : Fin m => E) G)
    (hμ : ‖μ‖ ≤ 1) (x y : Fin m → E) (hx : ∀ i, ‖x i‖ ≤ 1) (hy : ∀ i, ‖y i‖ ≤ 1) :
    phi (μ x) (μ y) ≤ ∑ i, phi (x i) (y i) := by
  classical
  let a : Fin m → ℝ := fun i => phi (x i) (y i)
  have claim : ∀ k, k ≤ m →
      phi (μ x) (μ (mixTuple x y k)) ≤ ∑ i : Fin m, (if (i : ℕ) < k then a i else 0) := by
    intro k
    induction k with
    | zero =>
      intro _
      have h0 : mixTuple x y 0 = x := by
        funext i
        simp only [mixTuple, Nat.not_lt_zero, if_false]
      rewrite [h0, phi_self (norm_apply_le_one μ hμ x hx)]
      exact Finset.sum_nonneg fun i _ => by simp
    | succ k ih =>
      intro hk
      have hkm : k < m := hk
      let j : Fin m := ⟨k, hkm⟩
      have hjk : (j : ℕ) = k := rfl
      have step := phi_mix_step μ hμ x y hx hy j
      rw [hjk] at step
      have hsplit : ∀ i : Fin m, (if (i : ℕ) < k + 1 then a i else 0) =
          (if (i : ℕ) < k then a i else 0) + (if i = j then a i else 0) := by
        intro i
        have hij : i = j ↔ (i : ℕ) = k := Fin.ext_iff
        by_cases h1 : (i : ℕ) < k
        · have hne : ¬ i = j := by rw [hij]; omega
          rw [if_pos (by omega), if_pos h1, if_neg hne, add_zero]
        · by_cases h2 : (i : ℕ) = k
          · rw [if_pos (by omega), if_neg h1, if_pos (hij.2 h2), zero_add]
          · have hne : ¬ i = j := by rw [hij]; exact h2
            rw [if_neg (by omega), if_neg h1, if_neg hne, add_zero]
      have hsum : ∑ i : Fin m, (if (i : ℕ) < k + 1 then a i else 0) =
          ∑ i : Fin m, (if (i : ℕ) < k then a i else 0) + a j := by
        rw [Finset.sum_congr rfl (fun i _ => hsplit i), Finset.sum_add_distrib]
        congr 1
        simp
      calc phi (μ x) (μ (mixTuple x y (k + 1)))
          ≤ phi (μ x) (μ (mixTuple x y k)) + phi (μ (mixTuple x y k)) (μ (mixTuple x y (k + 1))) :=
            phi_triangle _ _ _
        _ ≤ ∑ i : Fin m, (if (i : ℕ) < k then a i else 0) + a j :=
            add_le_add (ih (Nat.le_of_succ_le hk)) step
        _ = _ := hsum.symm
  have hm : mixTuple x y m = y := by
    funext i
    simp only [mixTuple]
    rw [if_pos i.isLt]
  have h := claim m le_rfl
  rw [hm] at h
  have hs : ∑ i : Fin m, (if (i : ℕ) < m then a i else 0) = ∑ i, a i :=
    Finset.sum_congr rfl (fun i _ => if_pos i.isLt)
  rw [hs] at h
  exact h

end PMT
