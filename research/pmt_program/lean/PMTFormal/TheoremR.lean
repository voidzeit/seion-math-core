/-
Theorem R (normalised form), machine-checked end to end.

Scope of the formal statement (see `README.md` for the exact gap to the paper statement):
* one real inner product space `G` for all nodes and leaves (paper: one space per node);
* normalisation `‖μ_v‖ ≤ 1`, closure constant `η` (paper: `M`, `ρ`, `η = ρ/M`, by scaling);
* leaves in the closed unit ball (paper: nonzero leaves, divided out by `∏ ‖z_ℓ‖`);
* the constant is expressed through `sSup`, not through a named `C_k`.

Statements:
* `PMT.theorem_R_upper`  every PMT-A tree (any `G`) has `err ≤ |1 - w(τ)^(k-1)|` for some
                         `τ ∈ [0, arcsin η]`
* `PMT.theorem_R_lower`  for every shape and every `τ ∈ [0, arcsin η]` there is a PMT-A tree in `ℂ`
                         with that shape and `err = |1 - w(τ)^(k-1)|`
* `PMT.theorem_R_sSup`   for every shape: `sup err = sup_{τ ∈ [0, arcsin η]} |1 - w(τ)^(k-1)|`
                         (over PMT-A realisations in `ℂ`; with `theorem_R_upper` no other `G` does better)
-/
import PMTFormal.WitnessAdm

open Real

namespace PMT

open PMTree

/-- **Theorem R, upper bound.** -/
theorem theorem_R_upper {G : Type*} [NormedAddCommGroup G] [InnerProductSpace ℝ G] {η : ℝ}
    (hη0 : 0 < η) (t : PMTree G) (ht : t.RootAdmFull η) :
    ∃ τ ∈ Set.Icc 0 (arcsin η), t.err ≤ ‖1 - w τ ^ (t.internal - 1)‖ :=
  upper_bound hη0 t (rootAdm_of_rootAdmFull t ht)

/-- **Theorem R, lower bound (universal sharp witness).** -/
theorem theorem_R_lower {η : ℝ} (hη0 : 0 < η) (hη1 : η ≤ 1) (m : ℕ) (ch : Fin m → Shape)
    {τ : ℝ} (hτ : τ ∈ Set.Icc 0 (arcsin η)) :
    ∃ t : PMTree ℂ, t.shape = .node m ch ∧ t.RootAdmFull η ∧
      t.err = ‖1 - w τ ^ ((Shape.node m ch).internal - 1)‖ :=
  ⟨witRoot τ (.node m ch), witRoot_shape τ _, witRoot_admFull hη0.le hη1 hτ m ch,
    witRoot_err τ m ch⟩

/-- **Theorem R, sharp constant.** For every tree shape with at least one internal node, the
supremum of the projected root error over PMT-A realisations equals
`sup_{τ ∈ [0, arcsin η]} |1 - w(τ)^(k-1)|`; it depends on the shape only through `k`. -/
theorem theorem_R_sSup {η : ℝ} (hη0 : 0 < η) (hη1 : η ≤ 1) (m : ℕ) (ch : Fin m → Shape) :
    sSup {e : ℝ | ∃ t : PMTree ℂ, t.shape = .node m ch ∧ t.RootAdmFull η ∧ t.err = e} =
      sSup ((fun τ => ‖1 - w τ ^ ((Shape.node m ch).internal - 1)‖) '' Set.Icc 0 (arcsin η)) := by
  apply csSup_eq_csSup_of_forall_exists_le
  · rintro e ⟨t, hshape, hadm, rfl⟩
    obtain ⟨τ, hτ, hle⟩ := theorem_R_upper hη0 t hadm
    refine ⟨_, ⟨τ, hτ, rfl⟩, ?_⟩
    rw [← hshape, internal_shape]
    exact hle
  · rintro y ⟨τ, hτ, rfl⟩
    obtain ⟨t, hshape, hadm, herr⟩ := theorem_R_lower hη0 hη1 m ch hτ
    exact ⟨t.err, ⟨t, hshape, hadm, rfl⟩, herr.ge⟩

end PMT
