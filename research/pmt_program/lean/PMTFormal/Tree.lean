/-
Projected multilinear trees over one real inner product space, the multiplicative envelope, and
the upper bound of Theorem R (normalised: `‖μ_v‖ ≤ 1`, `ρ = η`, leaves in the unit ball).

Statements:
* `PMT.PMTree`                 trees: leaves carry vectors, internal nodes carry `(m, μ, P, children)`
* `PMT.PMTree.AdmFull`         PMT-A admissibility (full closure: internal slots in `Ran P`, leaf
                               slots arbitrary)
* `PMT.PMTree.AdmTC`           trajectory-closure admissibility (weaker)
* `PMT.PMTree.admTC_of_admFull`
* `PMT.envelope`               every non-root subtree is dominated by `(∏ cos θ, ∑ θ)`, one angle
                               per internal node, all in `[0, arcsin η]`
* `PMT.upper_bound`            `err ≤ |1 - w(τ)^(k-1)|` for some `τ ∈ [0, arcsin η]`
-/
import PMTFormal.NodeStep
import PMTFormal.Diagonal

open Real
open scoped RealInnerProductSpace

namespace PMT

/-- A projected multilinear tree over one real inner product space `G`. -/
inductive PMTree (G : Type*) [NormedAddCommGroup G] [InnerProductSpace ℝ G] where
  | leaf (z : G)
  | node (m : ℕ) (μ : ContinuousMultilinearMap ℝ (fun _ : Fin m => G) G) (P : G →L[ℝ] G)
      (ch : Fin m → PMTree G)

namespace PMTree

variable {G : Type*} [NormedAddCommGroup G] [InnerProductSpace ℝ G]

/-- Ambient evaluation `F`. -/
def F : PMTree G → G
  | leaf z => z
  | node _ μ _ ch => μ (fun i => (ch i).F)

/-- Reduced evaluation `R`. -/
def R : PMTree G → G
  | leaf z => z
  | node _ μ P ch => P (μ (fun i => (ch i).R))

/-- Number of internal nodes. -/
def internal : PMTree G → ℕ
  | leaf _ => 0
  | node _ _ _ ch => 1 + ∑ i, (ch i).internal

/-- Projected root error `‖P_r F_r - R_r‖` (zero for a bare leaf). -/
def err : PMTree G → ℝ
  | leaf _ => 0
  | node _ μ P ch => ‖P (μ (fun i => (ch i).F)) - P (μ (fun i => (ch i).R))‖

/-- `v` lies in the admissible input set of the slot occupied by this subtree. -/
def InRan : PMTree G → G → Prop
  | leaf _, _ => True
  | node _ _ P _, v => P v = v

/-- Trajectory-closure admissibility (normalised). -/
def AdmTC (η : ℝ) : PMTree G → Prop
  | leaf z => ‖z‖ ≤ 1
  | node _ μ P ch => ‖μ‖ ≤ 1 ∧ IsOrthProj P ∧
      ‖μ (fun i => (ch i).R) - P (μ (fun i => (ch i).R))‖ ≤ η * ∏ i, ‖(ch i).R‖ ∧
      ∀ i, (ch i).AdmTC η

/-- PMT-A admissibility (normalised): full closure at every internal node. -/
def AdmFull (η : ℝ) : PMTree G → Prop
  | leaf z => ‖z‖ ≤ 1
  | node _ μ P ch => ‖μ‖ ≤ 1 ∧ IsOrthProj P ∧
      (∀ x : (i : Fin _) → G, (∀ i, (ch i).InRan (x i)) →
        ‖μ x - P (μ x)‖ ≤ η * ∏ i, ‖x i‖) ∧
      ∀ i, (ch i).AdmFull η

/-- Root admissibility for the upper bound: no closure is required at the root. -/
def RootAdm (η : ℝ) : PMTree G → Prop
  | leaf _ => False
  | node _ μ P ch => ‖μ‖ ≤ 1 ∧ IsOrthProj P ∧ ∀ i, (ch i).AdmTC η

theorem inRan_R {η : ℝ} : ∀ t : PMTree G, t.AdmFull η → t.InRan t.R
  | leaf _, _ => trivial
  | node _ _ _ _, h => h.2.1.idem _

theorem admTC_of_admFull {η : ℝ} (t : PMTree G) (ht : t.AdmFull η) : t.AdmTC η := by
  induction t with
  | leaf z => exact ht
  | node m μ P ch ih =>
    obtain ⟨hμ, hP, hcl, hch⟩ := ht
    exact ⟨hμ, hP, hcl _ (fun i => inRan_R (ch i) (hch i)), fun i => ih i (hch i)⟩

end PMTree

open PMTree

variable {G : Type*} [NormedAddCommGroup G] [InnerProductSpace ℝ G]

theorem dom_leaf {z : G} (hz : ‖z‖ ≤ 1) : Dom z z 1 0 :=
  ⟨hz, zero_le_one, z, hz, by simp, by rw [phi_self hz]⟩

/-- **Multiplicative envelope.** -/
theorem envelope {η : ℝ} (hη0 : 0 ≤ η) (t : PMTree G) (ht : t.AdmTC η) :
    ∃ θs : List ℝ, θs.length = t.internal ∧ (∀ θ ∈ θs, θ ∈ Set.Icc 0 (arcsin η)) ∧
      Dom t.F t.R (θs.map Real.cos).prod θs.sum := by
  induction t with
  | leaf z =>
    exact ⟨[], rfl, by simp, by simpa [F, R] using dom_leaf (show ‖z‖ ≤ 1 from ht)⟩
  | node m μ P ch ih =>
    obtain ⟨hμ, hP, hTC, hch⟩ := ht
    choose θs hlen hmem hdom using fun i => ih i (hch i)
    obtain ⟨θ, hθ, hD⟩ := node_step μ hμ P hP hη0 (fun i => (ch i).F) (fun i => (ch i).R)
      (fun i => ((θs i).map Real.cos).prod) (fun i => (θs i).sum) hdom hTC
    refine ⟨θ :: (List.ofFn θs).flatten, ?_, ?_, ?_⟩
    · simp only [List.length_cons, List.length_flatten, List.map_ofFn, internal, List.sum_ofFn,
        Function.comp_def, hlen]
      ring
    · intro x hx
      rcases List.mem_cons.1 hx with rfl | hx
      · exact hθ
      · obtain ⟨l, hl, hxl⟩ := List.mem_flatten.1 hx
        obtain ⟨i, rfl⟩ := List.mem_ofFn.1 hl
        exact hmem i x hxl
    · have hprod : ((θ :: (List.ofFn θs).flatten).map Real.cos).prod =
          Real.cos θ * ∏ i, ((θs i).map Real.cos).prod := by
        rw [List.map_cons, List.prod_cons, List.map_flatten, List.prod_flatten, List.map_ofFn,
          List.map_ofFn, List.prod_ofFn]
        rfl
      have hsum : (θ :: (List.ofFn θs).flatten).sum = θ + ∑ i, (θs i).sum := by
        rw [List.sum_cons, List.sum_flatten, List.map_ofFn, List.sum_ofFn]
        rfl
      rw [hprod, hsum]
      exact hD

/-- **Upper bound of Theorem R** (normalised). -/
theorem upper_bound {η : ℝ} (hη0 : 0 < η) (t : PMTree G) (ht : t.RootAdm η) :
    ∃ τ ∈ Set.Icc 0 (arcsin η), t.err ≤ ‖1 - w τ ^ (t.internal - 1)‖ := by
  cases t with
  | leaf z => exact ht.elim
  | node m μ P ch =>
    obtain ⟨hμ, hP, hch⟩ := ht
    choose θs hlen hmem hdom using fun i => envelope hη0.le (ch i) (hch i)
    have hroot := root_step μ hμ P hP (fun i => (ch i).F) (fun i => (ch i).R)
      (fun i => ((θs i).map Real.cos).prod) (fun i => (θs i).sum) hdom
    set L := (List.ofFn θs).flatten with hL
    have hR : ∏ i, ((θs i).map Real.cos).prod = (L.map Real.cos).prod := by
      rw [hL, List.map_flatten, List.prod_flatten, List.map_ofFn, List.map_ofFn, List.prod_ofFn]
      rfl
    have hΘ : ∑ i, (θs i).sum = L.sum := by
      rw [hL, List.sum_flatten, List.map_ofFn, List.sum_ofFn]
      rfl
    have hn : (node m μ P ch).internal - 1 = L.length := by
      simp only [internal, hL, List.length_flatten, List.map_ofFn, List.sum_ofFn,
        Function.comp_def, hlen]
      omega
    rw [hR, hΘ] at hroot
    simp only [err]
    rw [show (node m μ P ch).internal - 1 = L.length from hn]
    have hmemL : ∀ θ ∈ L, θ ∈ Set.Icc 0 (arcsin η) := by
      intro x hx
      obtain ⟨l, hl, hxl⟩ := List.mem_flatten.1 hx
      obtain ⟨i, rfl⟩ := List.mem_ofFn.1 hl
      exact hmem i x hxl
    have hα0 : 0 < arcsin η := Real.arcsin_pos.2 hη0
    have hα : arcsin η ≤ π / 2 := Real.arcsin_le_pi_div_two η
    rcases Nat.eq_zero_or_pos L.length with h0 | hpos
    · refine ⟨0, ⟨le_rfl, hα0.le⟩, ?_⟩
      have hLnil : L = [] := List.eq_nil_of_length_eq_zero h0
      rw [hLnil] at hroot
      simp only [List.map_nil, List.prod_nil, List.sum_nil, Real.cos_zero, mul_one,
        min_eq_left Real.pi_pos.le] at hroot
      rw [h0, pow_zero, sub_self, norm_zero]
      have : ‖P (μ fun i => (ch i).F) - P (μ fun i => (ch i).R)‖ ^ 2 ≤ 0 := by linarith
      nlinarith [norm_nonneg (P (μ fun i => (ch i).F) - P (μ fun i => (ch i).R))]
    · obtain ⟨τ, hτ, hle⟩ := diagonal_capped L.length hpos (arcsin η) hα0 hα L.get
        (fun j => hmemL _ (List.get_mem L j))
      refine ⟨τ, hτ, ?_⟩
      have hprodL : ∏ j, Real.cos (L.get j) = (L.map Real.cos).prod := by
        rw [← List.prod_ofFn]
        congr 1
        apply List.ext_get (by simp)
        intro n h1 h2
        simp
      have hsumL : ∑ j, L.get j = L.sum := by
        rw [← List.sum_ofFn, List.ofFn_get]
      rw [hprodL, hsumL] at hle
      rw [Complex.normSq_eq_norm_sq] at hle
      have hsq := hroot.trans hle
      exact (abs_le_of_sq_le_sq' hsq (norm_nonneg _)).2

end PMT
