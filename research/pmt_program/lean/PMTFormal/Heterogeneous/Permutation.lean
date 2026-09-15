/-
Heterogeneous Theorem R, part 5: permutation and placement invariance (H2).

`gBox` depends only on the multiset of defects; hence the heterogeneous sharp constant of a tree
depends only on the multiset of its non-root defects, not on the arities, the topology, the root
defect, or where each defect sits.

Statements:
* `PMT.gBox_perm`                            `η ~ η' → gBox η = gBox η'`
* `PMT.heterogeneous_placement_independent`  equal non-root defect multisets give equal sharp
                                             constants for arbitrary skeletons
-/
import PMTFormal.Heterogeneous.Sharp

namespace PMT

theorem gBox_image_subset {η η' : List ℝ} (h : η.Perm η') :
    (fun θ : List ℝ => ‖1 - (θ.map w).prod‖) '' box η ⊆
      (fun θ : List ℝ => ‖1 - (θ.map w).prod‖) '' box η' := by
  rintro _ ⟨θ, hθ, rfl⟩
  have hc : Relation.Comp (List.Forall₂ BoxRel) List.Perm θ η' := ⟨η, hθ, h⟩
  rw [List.forall₂_comp_perm_eq_perm_comp_forall₂] at hc
  obtain ⟨θ', hperm, hθ'⟩ := hc
  exact ⟨θ', hθ', by simp only [(hperm.map w).prod_eq]⟩

/-- **Permutation invariance (H2).** -/
theorem gBox_perm {η η' : List ℝ} (h : η.Perm η') : gBox η = gBox η' := by
  unfold gBox
  rw [Set.Subset.antisymm (gBox_image_subset h) (gBox_image_subset h.symm)]

/-- **Placement independence (H2).** Two defect skeletons (possibly with different arities,
topologies and root defects) whose non-root defect lists are permutations of each other have the
same heterogeneous sharp constant. -/
theorem heterogeneous_placement_independent {m m' : ℕ} {e e' : ℝ} (he : 0 ≤ e) (he' : 0 ≤ e')
    (ch : Fin m → DShape) (ch' : Fin m' → DShape)
    (h : (DShape.node m e ch).childDefects.Perm (DShape.node m' e' ch').childDefects) :
    sSup (errSetH (.node m e ch)) = sSup (errSetH (.node m' e' ch')) := by
  rw [heterogeneous_sSup he, heterogeneous_sSup he', gBox_perm h]

end PMT
