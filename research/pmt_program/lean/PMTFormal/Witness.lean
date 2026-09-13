/-
Theorem R v2, Theorem 8.1: evaluation of the universal sharp witness.

Model. All spaces are ℝ² ≅ ℂ, leaves carry e₀ = 1, and leaf slots enter through `Re(·)`. Since
`Re(1) = 1`, each leaf slot contributes the factor 1 to both evaluations, so it is omitted below.
A tree is its internal-node skeleton: `node θ children`, where `θ` is the node's leakage angle
(ignored at the root).

* non-root node:  F = e^{iθ} · ∏ F(child),   R = Re(e^{iθ} · ∏ R(child))   (P = Re)
* root:           F_r = ∏ F(child),          R_r = ∏ R(child)              (P_r = I)
* E^P = |F_r - R_r|.

This file checks the *evaluation* only: `rootError ks = |1 - ∏_{non-root nodes} w(θ_v)|`, and the
equal-angle specialisation `|1 - w(t)^(k-1)|`. Admissibility (norms and closure of the complex
product laws) is the elementary argument written in Theorem 8.1 and is not formalised here.
-/
import PMTFormal.Diagonal

namespace PMT

/-- Internal-node skeleton with one angle per node. -/
inductive WTree where
  | node : ℝ → List WTree → WTree

mutual
/-- Ambient value of a non-root node. -/
noncomputable def WTree.F : WTree → ℂ
  | .node θ ks => Complex.exp (θ * Complex.I) * WTree.prodF ks
/-- Product of the ambient values of a list of children. -/
noncomputable def WTree.prodF : List WTree → ℂ
  | [] => 1
  | k :: ks => WTree.F k * WTree.prodF ks
end

mutual
/-- Reduced value of a non-root node (`P = Re`). -/
noncomputable def WTree.R : WTree → ℂ
  | .node θ ks => (((Complex.exp (θ * Complex.I) * WTree.prodR ks).re : ℝ) : ℂ)
/-- Product of the reduced values of a list of children. -/
noncomputable def WTree.prodR : List WTree → ℂ
  | [] => 1
  | k :: ks => WTree.R k * WTree.prodR ks
end

mutual
/-- Angles of all internal nodes of a subtree. -/
def WTree.angles : WTree → List ℝ
  | .node θ ks => θ :: WTree.anglesL ks
/-- Angles of all internal nodes of a list of subtrees. -/
def WTree.anglesL : List WTree → List ℝ
  | [] => []
  | k :: ks => WTree.angles k ++ WTree.anglesL ks
end

mutual
theorem WTree.F_eq : ∀ t : WTree, t.F = Complex.exp (((t.angles.sum : ℝ) : ℂ) * Complex.I)
  | .node θ ks => by
    rw [WTree.F, WTree.prodF_eq ks, WTree.angles, List.sum_cons, ← Complex.exp_add]
    push_cast
    ring_nf
theorem WTree.prodF_eq : ∀ ks : List WTree,
    WTree.prodF ks = Complex.exp ((((WTree.anglesL ks).sum : ℝ) : ℂ) * Complex.I)
  | [] => by simp [WTree.prodF, WTree.anglesL]
  | k :: ks => by
    rw [WTree.prodF, WTree.F_eq k, WTree.prodF_eq ks, WTree.anglesL, List.sum_append,
      ← Complex.exp_add]
    push_cast
    ring_nf
end

mutual
theorem WTree.R_eq : ∀ t : WTree, t.R = (((t.angles.map Real.cos).prod : ℝ) : ℂ)
  | .node θ ks => by
    rw [WTree.R, WTree.prodR_eq ks, WTree.angles, List.map_cons, List.prod_cons]
    congr 1
    rw [Complex.mul_re, Complex.ofReal_re, Complex.ofReal_im, Complex.exp_ofReal_mul_I_re]
    ring
theorem WTree.prodR_eq : ∀ ks : List WTree,
    WTree.prodR ks = ((((WTree.anglesL ks).map Real.cos).prod : ℝ) : ℂ)
  | [] => by simp [WTree.prodR, WTree.anglesL]
  | k :: ks => by
    rw [WTree.prodR, WTree.R_eq k, WTree.prodR_eq ks, WTree.anglesL, List.map_append,
      List.prod_append]
    push_cast
    ring
end

/-- Product of `w` over a list: `∏ w θ = (∏ cos θ) · e^{i Σ θ}`. -/
theorem list_prod_w (l : List ℝ) :
    (l.map w).prod = (((l.map Real.cos).prod : ℝ) : ℂ) * Complex.exp (((l.sum : ℝ) : ℂ) * Complex.I) := by
  induction l with
  | nil => simp
  | cons a l ih =>
    rw [List.map_cons, List.prod_cons, ih, List.map_cons, List.prod_cons, List.sum_cons, w]
    push_cast
    rw [add_mul, Complex.exp_add]
    ring

/-- Projected error of the witness with root children `ks` (`P_r = I`). -/
noncomputable def rootError (ks : List WTree) : ℝ := ‖WTree.prodF ks - WTree.prodR ks‖

/-- **Theorem 8.1 (evaluation).** `E^P = |1 - ∏_{non-root internal nodes} w(θ_v)|`. -/
theorem rootError_eq (ks : List WTree) :
    rootError ks = ‖1 - ((WTree.anglesL ks).map w).prod‖ := by
  set l := WTree.anglesL ks
  set c : ℝ := (l.map Real.cos).prod
  set Θ : ℝ := l.sum
  rw [rootError, WTree.prodF_eq, WTree.prodR_eq, list_prod_w]
  -- |e^{iΘ} - c| = |1 - c e^{-iΘ}| = |conj(1 - c e^{iΘ})| = |1 - c e^{iΘ}|
  have hu : ‖Complex.exp (((Θ : ℝ) : ℂ) * Complex.I)‖ = 1 := Complex.norm_exp_ofReal_mul_I Θ
  have key : (Complex.exp ((Θ : ℂ) * Complex.I) - (c : ℂ)) =
      Complex.exp ((Θ : ℂ) * Complex.I) *
        (starRingEnd ℂ) (1 - (c : ℂ) * Complex.exp ((Θ : ℂ) * Complex.I)) := by
    rw [map_sub, map_one, map_mul, Complex.conj_ofReal, ← Complex.exp_conj, map_mul,
      Complex.conj_ofReal, Complex.conj_I]
    rw [mul_sub, mul_one, mul_left_comm, ← Complex.exp_add]
    ring_nf
    simp
  rw [key, norm_mul, hu, one_mul, Complex.norm_conj]

/-- Equal angles: `E^P = |1 - w(t)^(k-1)|`, where `k - 1` is the number of non-root internal nodes. -/
theorem rootError_equal_angles (ks : List WTree) (t : ℝ) (h : ∀ θ ∈ WTree.anglesL ks, θ = t) :
    rootError ks = ‖1 - w t ^ (WTree.anglesL ks).length‖ := by
  rw [rootError_eq]
  have hmap : (WTree.anglesL ks).map w = (WTree.anglesL ks).map (fun _ => w t) :=
    List.map_congr_left (fun θ hθ => by rw [h θ hθ])
  rw [hmap, List.map_const', List.prod_replicate]

end PMT
