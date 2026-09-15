/-
Attainment of the suprema (the constants are maxima).

Statements:
* `PMT.continuous_w`
* `PMT.theorem_R_max_attained`     `sup_{τ ∈ [0, arcsin η]} |1 - w(τ)^n|` is attained (`η ≥ 0`)
* `PMT.gBox_attained`              `gBox η` is attained in `box η` (`η_i ≥ 0`), so `gBox` is a max
* `PMT.heterogeneous_max_attained` some heterogeneous PMT-A tree realises `sup_{A(T,η)} err`
-/
import PMTFormal.Heterogeneous.Sharp

open Real

namespace PMT

theorem continuous_w : Continuous w := by
  unfold w
  fun_prop

/-- **Theorem R constant is a maximum.** -/
theorem theorem_R_max_attained {η : ℝ} (hη0 : 0 ≤ η) (n : ℕ) :
    ∃ τ ∈ Set.Icc 0 (arcsin η), ‖1 - w τ ^ n‖ =
      sSup ((fun τ => ‖1 - w τ ^ n‖) '' Set.Icc 0 (arcsin η)) := by
  have hc : Continuous fun τ => ‖1 - w τ ^ n‖ := by
    have := continuous_w
    fun_prop
  obtain ⟨τ, hτ, hmax⟩ := isCompact_Icc.exists_isMaxOn
    (Set.nonempty_Icc.2 (Real.arcsin_nonneg.2 hη0)) hc.continuousOn
  have hg : IsGreatest ((fun τ => ‖1 - w τ ^ n‖) '' Set.Icc 0 (arcsin η)) ‖1 - w τ ^ n‖ :=
    ⟨⟨τ, hτ, rfl⟩, by rintro _ ⟨s, hs, rfl⟩; exact hmax hs⟩
  exact ⟨τ, hτ, hg.csSup_eq.symm⟩

/-- **`gBox` is a maximum.** -/
theorem gBox_attained {η : List ℝ} (hη : ∀ e ∈ η, 0 ≤ e) :
    ∃ θ ∈ box η, ‖1 - (θ.map w).prod‖ = gBox η := by
  set S : Set (Fin η.length → ℝ) :=
    Set.pi Set.univ (fun i => Set.Icc 0 (arcsin (η.get i))) with hS
  have hSc : IsCompact S := isCompact_univ_pi (fun _ => isCompact_Icc)
  have hSne : S.Nonempty :=
    ⟨0, fun i _ => ⟨le_rfl, Real.arcsin_nonneg.2 (hη _ (List.get_mem η i))⟩⟩
  have hfc : Continuous fun θ : Fin η.length → ℝ => ‖1 - ∏ i, w (θ i)‖ := by
    have := continuous_w
    fun_prop
  obtain ⟨θs, hθsS, hmax⟩ := hSc.exists_isMaxOn hSne hfc.continuousOn
  have hval : ∀ θ : Fin η.length → ℝ, ((List.ofFn θ).map w).prod = ∏ i, w (θ i) := fun θ => by
    rw [List.map_ofFn, List.prod_ofFn]
    rfl
  have hbox : ∀ θ : Fin η.length → ℝ, θ ∈ S → List.ofFn θ ∈ box η := by
    intro θ hθ
    show List.Forall₂ BoxRel _ η
    rw [List.forall₂_iff_get]
    refine ⟨by simp, fun i h₁ h₂ => ?_⟩
    simpa [BoxRel] using hθ ⟨i, h₂⟩ (Set.mem_univ _)
  refine ⟨List.ofFn θs, hbox θs hθsS, ?_⟩
  symm
  apply IsGreatest.csSup_eq
  refine ⟨⟨_, hbox θs hθsS, rfl⟩, ?_⟩
  rintro _ ⟨θ, hθ, rfl⟩
  have hθ2 : List.Forall₂ BoxRel θ η := hθ
  have hlen : θ.length = η.length := hθ2.length_eq
  have hθeq : θ = List.ofFn (fun i : Fin η.length => θ.get (Fin.cast hlen.symm i)) := by
    apply List.ext_get (by simp [hlen])
    intro k h1 h2
    simp
  have hθ'S : (fun i : Fin η.length => θ.get (Fin.cast hlen.symm i)) ∈ S := by
    intro i _
    exact (List.forall₂_iff_get.1 hθ2).2 i (by omega) i.2
  have hprodθ : (θ.map w).prod = ∏ i, w (θ.get (Fin.cast hlen.symm i)) := by
    rw [← hval]
    exact congrArg (fun l => (l.map w).prod) hθeq
  show ‖1 - (θ.map w).prod‖ ≤ ‖1 - ((List.ofFn θs).map w).prod‖
  rw [hprodθ, hval]
  exact hmax hθ'S

/-- **The heterogeneous sharp constant is attained by a tree.** -/
theorem heterogeneous_max_attained {m : ℕ} {e : ℝ} (he : 0 ≤ e) (ch : Fin m → DShape)
    (hη : ∀ x ∈ (DShape.node m e ch).childDefects, 0 ≤ x) :
    ∃ t : HPMTree ℂ, t.dshape = .node m e ch ∧ t.RootAdmFull ∧
      t.err = sSup (errSetH (.node m e ch)) := by
  obtain ⟨θ, hθ, hval⟩ := gBox_attained hη
  obtain ⟨t, hT, hadm, herr⟩ := heterogeneous_witness he ch hθ
  exact ⟨t, hT, hadm, by rw [herr, hval, heterogeneous_sSup he]⟩

end PMT
