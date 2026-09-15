/-
Heterogeneous Theorem R, part 4: sharp constant (H1 + H4) and uniform recovery.

Statements:
* `PMT.errSetH T`                     projected root errors of heterogeneous PMT-A trees over `ℂ`
                                      with defect skeleton `T`
* `PMT.heterogeneous_lower`           every box value is attained by some tree in `A(T, η)`
* `PMT.heterogeneous_sSup`            `sup_{A(T,η)} err = gBox(childDefects T)`
* `PMT.heterogeneous_sharp`           no ambient space does better: any heterogeneous PMT-A tree over
                                      any real inner product space has `err ≤ sup errSetH T`
* `PMT.uniform_gBox_eq`               `gBox(η, …, η) = sup_{τ ∈ [0, arcsin η]} |1 - w(τ)^n|` (`η > 0`)
* `PMT.heterogeneous_uniform_recovery` with equal defects the heterogeneous constant is Theorem R's
-/
import PMTFormal.Heterogeneous.Witness

open Real

namespace PMT

open HPMTree

/-- Projected root errors of heterogeneous PMT-A realisations (over `ℂ`) of a defect skeleton. -/
def errSetH (T : DShape) : Set ℝ :=
  {x | ∃ t : HPMTree ℂ, t.dshape = T ∧ t.RootAdmFull ∧ t.err = x}

/-- **Heterogeneous Theorem R, lower bound (H4).** -/
theorem heterogeneous_lower {m : ℕ} {e : ℝ} (he : 0 ≤ e) (ch : Fin m → DShape) {θ : List ℝ}
    (hθ : θ ∈ box (DShape.node m e ch).childDefects) :
    ∃ x ∈ errSetH (.node m e ch), ‖1 - (θ.map w).prod‖ ≤ x := by
  obtain ⟨t, hT, hadm, herr⟩ := heterogeneous_witness he ch hθ
  exact ⟨t.err, ⟨t, hT, hadm, rfl⟩, herr.ge⟩

/-- **Heterogeneous Theorem R, sharp constant.** For every defect skeleton with at least one internal
node and root defect `e ≥ 0`, the supremum of the projected root error over heterogeneous PMT-A
realisations equals `gBox` of the non-root defects. -/
theorem heterogeneous_sSup {m : ℕ} {e : ℝ} (he : 0 ≤ e) (ch : Fin m → DShape) :
    sSup (errSetH (.node m e ch)) = gBox (DShape.node m e ch).childDefects := by
  apply csSup_eq_csSup_of_forall_exists_le
  · rintro x ⟨t, hT, hadm, rfl⟩
    obtain ⟨θ, hθ, hle⟩ := heterogeneous_upper t hadm
    rw [hT] at hθ
    exact ⟨_, ⟨θ, hθ, rfl⟩, hle⟩
  · rintro y ⟨θ, hθ, rfl⟩
    exact heterogeneous_lower he ch hθ

/-- Complex realisations are extremal among all real inner product spaces. -/
theorem heterogeneous_sharp {G : Type*} [NormedAddCommGroup G] [InnerProductSpace ℝ G]
    {m : ℕ} {e : ℝ} (he : 0 ≤ e) (ch : Fin m → DShape) (t : HPMTree G)
    (hT : t.dshape = .node m e ch) (ht : t.RootAdmFull) :
    t.err ≤ sSup (errSetH (.node m e ch)) := by
  rw [heterogeneous_sSup he, ← hT]
  exact heterogeneous_le_gBox t ht

theorem box_replicate_mem {η : ℝ} :
    ∀ (n : ℕ) (θ : List ℝ), θ ∈ box (List.replicate n η) → ∀ x ∈ θ, BoxRel x η
  | 0, θ, h => by
    have h' : List.Forall₂ BoxRel θ [] := h
    rw [List.forall₂_nil_right_iff] at h'
    simp [h']
  | n + 1, θ, h => by
    have h' : List.Forall₂ BoxRel θ (η :: List.replicate n η) := h
    cases h' with
    | cons hhead htail =>
      intro x hx
      rcases List.mem_cons.1 hx with rfl | hx
      · exact hhead
      · exact box_replicate_mem n _ htail x hx

theorem replicate_mem_box {η τ : ℝ} (hτ : BoxRel τ η) :
    ∀ n : ℕ, List.replicate n τ ∈ box (List.replicate n η)
  | 0 => List.Forall₂.nil
  | n + 1 => List.Forall₂.cons hτ (replicate_mem_box hτ n)

theorem length_of_mem_box {η θ : List ℝ} (h : θ ∈ box η) : θ.length = η.length :=
  List.Forall₂.length_eq h

/-- **Uniform recovery.** With all defects equal to `η > 0` the box constant is the Theorem R
constant `sup_{τ ∈ [0, arcsin η]} |1 - w(τ)^n|` (this is the only place the Diagonal Lemma enters). -/
theorem uniform_gBox_eq {η : ℝ} (hη0 : 0 < η) (n : ℕ) :
    gBox (List.replicate n η) =
      sSup ((fun τ => ‖1 - w τ ^ n‖) '' Set.Icc 0 (arcsin η)) := by
  have hα0 : 0 < arcsin η := Real.arcsin_pos.2 hη0
  have hα : arcsin η ≤ π / 2 := Real.arcsin_le_pi_div_two η
  apply csSup_eq_csSup_of_forall_exists_le
  · rintro y ⟨θ, hθ, rfl⟩
    have hlen : θ.length = n := by rw [length_of_mem_box hθ, List.length_replicate]
    have hmem := box_replicate_mem n θ hθ
    rcases Nat.eq_zero_or_pos n with h0 | hpos
    · refine ⟨_, ⟨0, ⟨le_rfl, hα0.le⟩, rfl⟩, ?_⟩
      have hnil : θ = [] := List.eq_nil_of_length_eq_zero (hlen.trans h0)
      simp [hnil, h0]
    · obtain ⟨τ, hτ, hle⟩ := diagonal_lemma θ.length (hlen ▸ hpos) (arcsin η) hα0 hα θ.get
        (fun j => hmem _ (List.get_mem θ j))
      refine ⟨_, ⟨τ, hτ, rfl⟩, ?_⟩
      have hprod : ∏ j, w (θ.get j) = (θ.map w).prod := by
        rw [← List.prod_ofFn]
        congr 1
        apply List.ext_get (by simp)
        intro k h1 h2
        simp
      rw [hprod, Complex.normSq_eq_norm_sq, Complex.normSq_eq_norm_sq, hlen] at hle
      exact (abs_le_of_sq_le_sq' hle (norm_nonneg _)).2
  · rintro y ⟨τ, hτ, rfl⟩
    refine ⟨_, ⟨List.replicate n τ, replicate_mem_box hτ n, rfl⟩, ?_⟩
    simp only [List.map_replicate, List.prod_replicate, le_refl]

/-- **Uniform recovery of Theorem R.** If every non-root defect equals `η > 0`, the heterogeneous
sharp constant is `sup_{τ ∈ [0, arcsin η]} |1 - w(τ)^(k-1)|`, `k - 1` = number of non-root nodes. -/
theorem heterogeneous_uniform_recovery {η : ℝ} (hη0 : 0 < η) {m : ℕ} {e : ℝ} (he : 0 ≤ e)
    (ch : Fin m → DShape) (h : ∀ x ∈ (DShape.node m e ch).childDefects, x = η) :
    sSup (errSetH (.node m e ch)) =
      sSup ((fun τ => ‖1 - w τ ^ (DShape.node m e ch).childDefects.length‖) ''
        Set.Icc 0 (arcsin η)) := by
  rw [heterogeneous_sSup he, ← uniform_gBox_eq hη0, ← List.eq_replicate_iff.2 ⟨rfl, h⟩]

end PMT
