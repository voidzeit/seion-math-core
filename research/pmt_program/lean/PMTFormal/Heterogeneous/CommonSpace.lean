/-
Common-ambient-space reduction (A1 of `ADMISSIBLE_CLASS_PMT_A.md`).

Every vertex carries its own real inner product space. All of them embed isometrically into one
common space (built recursively as `PiLp 2` over `Option (Fin m)`: slot `none` holds the vertex space,
slot `some i` the common space of the `i`-th subtree). Laws and projectors are transported by
`μ' = ι ∘ μ ∘ (π, …, π)` and `P' = ι P π`, where `(ι, π)` is an isometry with its adjoint left
inverse. Norm bounds, orthogonality, closure, evaluations, errors and `Λ_T` are preserved, so the
single-space theorems apply verbatim.

Statements:
* `PMT.Emb`                                 isometric embedding with adjoint left inverse
* `PMT.HSpace`, `PMT.MSTree`                trees with a (bundled) space at every vertex
* `PMT.MSTree.lift`                         the transported single-space tree
* `PMT.MSTree.lift_err`, `lift_Λ`, `lift_dshape`, `lift_rootAdmFull0`
* `PMT.heterogeneous_multispace_upper`      `E_T^P ≤ Λ_T · gBox(ρ/M)` with per-vertex spaces, `M_v ≥ 0`
* `PMT.heterogeneous_multispace_sSup`       `sup E_T^P / Λ_T = gBox(ρ/M)` over per-vertex-space trees
-/
import PMTFormal.Heterogeneous.ScaledZero

open Real
open scoped RealInnerProductSpace

namespace PMT

universe u

/-! ### Isometric embeddings with adjoint left inverse -/

/-- `ι : E → G` with `π ι = id` and `⟪ι a, v⟫ = ⟪a, π v⟫`. -/
structure Emb (E G : Type*) [NormedAddCommGroup E] [InnerProductSpace ℝ E]
    [NormedAddCommGroup G] [InnerProductSpace ℝ G] where
  inj : E →L[ℝ] G
  proj : G →L[ℝ] E
  left_inv : ∀ a, proj (inj a) = a
  adj : ∀ a v, ⟪inj a, v⟫ = ⟪a, proj v⟫

namespace Emb

variable {E G : Type*} [NormedAddCommGroup E] [InnerProductSpace ℝ E]
  [NormedAddCommGroup G] [InnerProductSpace ℝ G]

theorem norm_ι (e : Emb E G) (a : E) : ‖e.inj a‖ = ‖a‖ := by
  have h : ‖e.inj a‖ ^ 2 = ‖a‖ ^ 2 := by
    rw [← real_inner_self_eq_norm_sq, ← real_inner_self_eq_norm_sq, e.adj, e.left_inv]
  exact (pow_left_inj₀ (norm_nonneg _) (norm_nonneg _) two_ne_zero).1 h

theorem norm_π_le (e : Emb E G) (v : G) : ‖e.proj v‖ ≤ ‖v‖ := by
  have h1 : ‖e.proj v‖ ^ 2 = ⟪e.inj (e.proj v), v⟫ := by
    rw [e.adj, real_inner_self_eq_norm_sq]
  have h2 : ‖e.proj v‖ ^ 2 ≤ ‖e.proj v‖ * ‖v‖ := by
    rw [h1]
    exact (real_inner_le_norm _ _).trans (by rw [e.norm_ι])
  by_contra hc
  push Not at hc
  nlinarith [norm_nonneg v]

theorem adj' (e : Emb E G) (u : G) (b : E) : ⟪u, e.inj b⟫ = ⟪e.proj u, b⟫ := by
  rw [real_inner_comm, e.adj, real_inner_comm]

/-- The identity embedding. -/
def id : Emb E E where
  inj := ContinuousLinearMap.id ℝ E
  proj := ContinuousLinearMap.id ℝ E
  left_inv _ := rfl
  adj _ _ := rfl

/-- Composition of embeddings. -/
def comp {K : Type*} [NormedAddCommGroup K] [InnerProductSpace ℝ K]
    (e₁ : Emb E G) (e₂ : Emb G K) : Emb E K where
  inj := e₂.inj ∘L e₁.inj
  proj := e₁.proj ∘L e₂.proj
  left_inv a := by simp [e₂.left_inv, e₁.left_inv]
  adj a v := by simp only [ContinuousLinearMap.comp_apply, e₂.adj, e₁.adj]

/-- Coordinate embedding into a finite `L²` product. -/
noncomputable def pi {ι : Type*} [Fintype ι] [DecidableEq ι] (K : ι → Type*)
    [∀ i, NormedAddCommGroup (K i)] [∀ i, InnerProductSpace ℝ (K i)] (j : ι) :
    Emb (K j) (PiLp 2 K) where
  inj := LinearMap.mkContinuous
    { toFun := fun a => PiLp.single 2 j a
      map_add' := fun a b => PiLp.single_add 2 j
      map_smul' := fun c a => by
        ext k
        by_cases hk : k = j
        · subst hk; simp
        · simp [Pi.single_eq_of_ne hk] }
    1 (fun a => by simp)
  proj := PiLp.proj 2 K j
  left_inv a := by simp
  adj a v := by
    simp only [LinearMap.mkContinuous_apply, LinearMap.coe_mk, AddHom.coe_mk, PiLp.proj_apply]
    rw [PiLp.inner_apply, Finset.sum_eq_single j]
    · simp
    · intro b _ hb
      simp [hb]
    · intro h
      exact absurd (Finset.mem_univ j) h

/-- First-factor embedding into an `L²` product. -/
noncomputable def fst (A B : Type*) [NormedAddCommGroup A] [InnerProductSpace ℝ A]
    [NormedAddCommGroup B] [InnerProductSpace ℝ B] : Emb A (WithLp 2 (A × B)) where
  inj := (WithLp.prodContinuousLinearEquiv 2 ℝ A B).symm.toContinuousLinearMap ∘L
    ContinuousLinearMap.inl ℝ A B
  proj := WithLp.fstL 2 ℝ A B
  left_inv a := by simp
  adj a v := by
    rw [WithLp.prod_inner_apply]
    simp

/-- Second-factor embedding into an `L²` product. -/
noncomputable def snd (A B : Type*) [NormedAddCommGroup A] [InnerProductSpace ℝ A]
    [NormedAddCommGroup B] [InnerProductSpace ℝ B] : Emb B (WithLp 2 (A × B)) where
  inj := (WithLp.prodContinuousLinearEquiv 2 ℝ A B).symm.toContinuousLinearMap ∘L
    ContinuousLinearMap.inr ℝ A B
  proj := WithLp.sndL 2 ℝ A B
  left_inv a := by simp
  adj a v := by
    rw [WithLp.prod_inner_apply]
    simp

end Emb

/-! ### Embedded nodes -/

section EmbeddedNode

variable {H G : Type*} [NormedAddCommGroup H] [InnerProductSpace ℝ H]
  [NormedAddCommGroup G] [InnerProductSpace ℝ G]
  {m : ℕ} {K : Fin m → Type*} [∀ i, NormedAddCommGroup (K i)] [∀ i, InnerProductSpace ℝ (K i)]

/-- `ι ∘ μ ∘ (π₁, …, π_m)`. -/
noncomputable def embLaw (e : Emb H G) (μ : ContinuousMultilinearMap ℝ K H)
    (ps : ∀ i, G →L[ℝ] K i) : ContinuousMultilinearMap ℝ (fun _ : Fin m => G) G :=
  e.inj.compContinuousMultilinearMap (μ.compContinuousLinearMap ps)

theorem embLaw_apply (e : Emb H G) (μ : ContinuousMultilinearMap ℝ K H)
    (ps : ∀ i, G →L[ℝ] K i) (x : Fin m → G) :
    embLaw e μ ps x = e.inj (μ (fun i => ps i (x i))) := rfl

theorem norm_embLaw_le (e : Emb H G) (μ : ContinuousMultilinearMap ℝ K H)
    (ps : ∀ i, G →L[ℝ] K i) (hπ : ∀ i v, ‖ps i v‖ ≤ ‖v‖) {M : ℝ} (hM0 : 0 ≤ M)
    (hμ : ‖μ‖ ≤ M) : ‖embLaw e μ ps‖ ≤ M := by
  refine ContinuousMultilinearMap.opNorm_le_bound hM0 fun x => ?_
  rw [embLaw_apply, e.norm_ι]
  calc ‖μ (fun i => ps i (x i))‖ ≤ ‖μ‖ * ∏ i, ‖ps i (x i)‖ := μ.le_opNorm _
    _ ≤ M * ∏ i, ‖x i‖ := mul_le_mul hμ
        (Finset.prod_le_prod (fun i _ => norm_nonneg _) (fun i _ => hπ i (x i)))
        (Finset.prod_nonneg fun i _ => norm_nonneg _) hM0

theorem isOrthProj_emb (e : Emb H G) {P : H →L[ℝ] H} (hP : IsOrthProj P) :
    IsOrthProj (e.inj ∘L P ∘L e.proj) where
  idem u := by simp only [ContinuousLinearMap.comp_apply, e.left_inv, hP.idem]
  symm u v := by
    simp only [ContinuousLinearMap.comp_apply]
    rw [e.adj, hP.symm, e.adj']

theorem closure_emb (e : Emb H G) (μ : ContinuousMultilinearMap ℝ K H) (ps : ∀ i, G →L[ℝ] K i)
    (hπ : ∀ i v, ‖ps i v‖ ≤ ‖v‖) {P : H →L[ℝ] H} {ρ : ℝ} (hρ : 0 ≤ ρ)
    (S : ∀ i, K i → Prop) (S' : Fin m → G → Prop) (hS : ∀ i v, S' i v → S i (ps i v))
    (hcl : ∀ y : ∀ i, K i, (∀ i, S i (y i)) → ‖μ y - P (μ y)‖ ≤ ρ * ∏ i, ‖y i‖)
    (x : Fin m → G) (hx : ∀ i, S' i (x i)) :
    ‖embLaw e μ ps x - (e.inj ∘L P ∘L e.proj) (embLaw e μ ps x)‖ ≤ ρ * ∏ i, ‖x i‖ := by
  simp only [embLaw_apply, ContinuousLinearMap.comp_apply, e.left_inv]
  rw [← map_sub, e.norm_ι]
  calc _ ≤ ρ * ∏ i, ‖ps i (x i)‖ := hcl _ (fun i => hS i _ (hx i))
    _ ≤ ρ * ∏ i, ‖x i‖ := mul_le_mul_of_nonneg_left
        (Finset.prod_le_prod (fun i _ => norm_nonneg _) (fun i _ => hπ i (x i))) hρ

end EmbeddedNode

/-! ### Transport of single-space trees along an embedding -/

namespace SPMTree

variable {E G : Type*} [NormedAddCommGroup E] [InnerProductSpace ℝ E]
  [NormedAddCommGroup G] [InnerProductSpace ℝ G]

/-- Transport along an embedding. -/
noncomputable def transport (e : Emb E G) : SPMTree E → SPMTree G
  | leaf z => leaf (e.inj z)
  | node m M ρ μ P ch =>
      node m M ρ (embLaw e μ (fun _ => e.proj)) (e.inj ∘L P ∘L e.proj) (fun i => transport e (ch i))

theorem transport_eval (e : Emb E G) (t : SPMTree E) :
    (t.transport e).F = e.inj t.F ∧ (t.transport e).R = e.inj t.R := by
  induction t with
  | leaf z => exact ⟨rfl, rfl⟩
  | node m M ρ μ P ch ih =>
    constructor
    · simp only [transport, F, embLaw_apply, fun i => (ih i).1, e.left_inv]
    · simp only [transport, R, embLaw_apply, fun i => (ih i).2, e.left_inv,
        ContinuousLinearMap.comp_apply]

theorem transport_err (e : Emb E G) (t : SPMTree E) : (t.transport e).err = t.err := by
  cases t with
  | leaf z => rfl
  | node m M ρ μ P ch =>
    simp only [transport, err, embLaw_apply, fun i => (transport_eval e (ch i)).1,
      fun i => (transport_eval e (ch i)).2, e.left_inv, ContinuousLinearMap.comp_apply]
    rw [← map_sub, e.norm_ι]

theorem transport_Λ (e : Emb E G) (t : SPMTree E) : (t.transport e).Λ = t.Λ := by
  induction t with
  | leaf z => exact e.norm_ι z
  | node m M ρ μ P ch ih => simp only [transport, Λ, ih]

theorem transport_dshape (e : Emb E G) (t : SPMTree E) : (t.transport e).dshape = t.dshape := by
  induction t with
  | leaf z => rfl
  | node m M ρ μ P ch ih => simp only [transport, dshape, ih]

theorem transport_inRan (e : Emb E G) (t : SPMTree E) (v : G) (h : (t.transport e).InRan v) :
    t.InRan (e.proj v) := by
  cases t with
  | leaf z => trivial
  | node m M ρ μ P ch =>
    have h' : e.inj (P (e.proj v)) = v := h
    show P (e.proj v) = e.proj v
    have := congrArg e.proj h'
    rwa [e.left_inv] at this

theorem transport_admFull0 (e : Emb E G) (t : SPMTree E) (ht : t.AdmFull0) :
    (t.transport e).AdmFull0 := by
  induction t with
  | leaf z => trivial
  | node m M ρ μ P ch ih =>
    obtain ⟨hM, hρ, hμ, hP, hcl, hch⟩ := ht
    exact ⟨hM, hρ, norm_embLaw_le e μ _ (fun _ v => e.norm_π_le v) hM hμ, isOrthProj_emb e hP,
      closure_emb e μ _ (fun _ v => e.norm_π_le v) hρ (fun i v => (ch i).InRan v)
        (fun i v => ((ch i).transport e).InRan v) (fun i v hv => transport_inRan e (ch i) v hv) hcl,
      fun i => ih i (hch i)⟩

end SPMTree

/-! ### Trees with a space at every vertex -/

/-- A bundled real inner product space. -/
structure HSpace where
  carrier : Type u
  [str : NormedAddCommGroup carrier]
  [ips : InnerProductSpace ℝ carrier]

attribute [instance] HSpace.str HSpace.ips

/-- Scaled projected multilinear trees with a space at every vertex (indexed by the vertex space). -/
inductive MSTree : HSpace.{u} → Type (u + 1)
  | leaf {H : HSpace.{u}} (z : H.carrier) : MSTree H
  | node {H : HSpace.{u}} (m : ℕ) (M ρ : ℝ) (Hs : Fin m → HSpace.{u})
      (μ : ContinuousMultilinearMap ℝ (fun i => (Hs i).carrier) H.carrier)
      (P : H.carrier →L[ℝ] H.carrier) (ch : ∀ i, MSTree (Hs i)) : MSTree H

namespace MSTree

def F : {H : HSpace.{u}} → MSTree H → H.carrier
  | _, leaf z => z
  | _, node _ _ _ _ μ _ ch => μ (fun i => (ch i).F)

def R : {H : HSpace.{u}} → MSTree H → H.carrier
  | _, leaf z => z
  | _, node _ _ _ _ μ P ch => P (μ (fun i => (ch i).R))

def err : {H : HSpace.{u}} → MSTree H → ℝ
  | _, leaf _ => 0
  | _, node _ _ _ _ μ P ch => ‖P (μ (fun i => (ch i).F)) - P (μ (fun i => (ch i).R))‖

def InRan : {H : HSpace.{u}} → MSTree H → H.carrier → Prop
  | _, leaf _, _ => True
  | _, node _ _ _ _ _ P _, v => P v = v

def Λ : {H : HSpace.{u}} → MSTree H → ℝ
  | _, leaf z => ‖z‖
  | _, node _ M _ _ _ _ ch => M * ∏ i, (ch i).Λ

noncomputable def dshape : {H : HSpace.{u}} → MSTree H → DShape
  | _, leaf _ => .leaf
  | _, node m M ρ _ _ _ ch => .node m (ρ / M) (fun i => (ch i).dshape)

/-- Scaled heterogeneous PMT-A admissibility with per-vertex spaces (`M_v ≥ 0`). -/
def AdmFull0 : {H : HSpace.{u}} → MSTree H → Prop
  | _, leaf _ => True
  | _, node _ M ρ Hs μ P ch => 0 ≤ M ∧ 0 ≤ ρ ∧ ‖μ‖ ≤ M ∧ IsOrthProj P ∧
      (∀ x : ∀ i, (Hs i).carrier, (∀ i, (ch i).InRan (x i)) → ‖μ x - P (μ x)‖ ≤ ρ * ∏ i, ‖x i‖) ∧
      ∀ i, (ch i).AdmFull0

def RootAdmFull0 : {H : HSpace.{u}} → MSTree H → Prop
  | _, leaf _ => False
  | _, node m M ρ Hs μ P ch => (node m M ρ Hs μ P ch).AdmFull0

/-- The common space at a node: vertex space ⊕ (⊕ child common spaces), in `L²`. -/
noncomputable def nodeSpace (H : HSpace.{u}) {m : ℕ} (cs : Fin m → HSpace.{u}) : HSpace.{u} :=
  ⟨WithLp 2 (H.carrier × PiLp 2 (fun i => (cs i).carrier))⟩

/-- The common space of a tree. -/
noncomputable def cspace : {H : HSpace.{u}} → MSTree H → HSpace.{u}
  | H, leaf _ => H
  | H, node _ _ _ _ _ _ ch => nodeSpace H (fun i => cspace (ch i))

/-- Embedding of the vertex space into the node space. -/
noncomputable def vertexEmb (H : HSpace.{u}) {m : ℕ} (cs : Fin m → HSpace.{u}) :
    Emb H.carrier (nodeSpace H cs).carrier :=
  Emb.fst H.carrier (PiLp 2 (fun i => (cs i).carrier))

/-- Embedding of the `i`-th child common space into the node space. -/
noncomputable def slotEmb (H : HSpace.{u}) {m : ℕ} (cs : Fin m → HSpace.{u}) (i : Fin m) :
    Emb (cs i).carrier (nodeSpace H cs).carrier :=
  (Emb.pi (fun i => (cs i).carrier) i).comp (Emb.snd H.carrier (PiLp 2 (fun i => (cs i).carrier)))

/-- The embedding of the root space into the common space. -/
noncomputable def rootEmb : {H : HSpace.{u}} → (t : MSTree H) → Emb H.carrier (cspace t).carrier
  | _, leaf _ => Emb.id
  | H, node _ _ _ _ _ _ ch => vertexEmb H (fun i => cspace (ch i))

/-- The node of the transported tree, given transported children. -/
noncomputable def liftNode {H : HSpace.{u}} {m : ℕ} (M ρ : ℝ) {Hs : Fin m → HSpace.{u}}
    (μ : ContinuousMultilinearMap ℝ (fun i => (Hs i).carrier) H.carrier)
    (P : H.carrier →L[ℝ] H.carrier) (cs : Fin m → HSpace.{u})
    (re : ∀ i, Emb (Hs i).carrier (cs i).carrier) (lc : ∀ i, SPMTree (cs i).carrier) :
    SPMTree (nodeSpace H cs).carrier :=
  .node m M ρ (embLaw (vertexEmb H cs) μ (fun i => (re i).proj ∘L (slotEmb H cs i).proj))
    ((vertexEmb H cs).inj ∘L P ∘L (vertexEmb H cs).proj)
    (fun i => (lc i).transport (slotEmb H cs i))

/-- The transported single-space tree. -/
noncomputable def lift : {H : HSpace.{u}} → (t : MSTree H) → SPMTree (cspace t).carrier
  | _, leaf z => .leaf z
  | _, node _ M ρ _ μ P ch =>
      liftNode M ρ μ P (fun i => cspace (ch i)) (fun i => rootEmb (ch i)) (fun i => lift (ch i))

section LiftNode

variable {H : HSpace.{u}} {m : ℕ} (M ρ : ℝ) {Hs : Fin m → HSpace.{u}}
    (μ : ContinuousMultilinearMap ℝ (fun i => (Hs i).carrier) H.carrier)
    (P : H.carrier →L[ℝ] H.carrier) (cs : Fin m → HSpace.{u})
    (re : ∀ i, Emb (Hs i).carrier (cs i).carrier) (lc : ∀ i, SPMTree (cs i).carrier)
    (F R : ∀ i, (Hs i).carrier)

theorem liftNode_eval (hF : ∀ i, (lc i).F = (re i).inj (F i))
    (hR : ∀ i, (lc i).R = (re i).inj (R i)) :
    (liftNode M ρ μ P cs re lc).F = (vertexEmb H cs).inj (μ F) ∧
      (liftNode M ρ μ P cs re lc).R = (vertexEmb H cs).inj (P (μ R)) := by
  have key : ∀ i, (re i).proj ((slotEmb H cs i).proj ((lc i).transport (slotEmb H cs i)).F) = F i ∧
      (re i).proj ((slotEmb H cs i).proj ((lc i).transport (slotEmb H cs i)).R) = R i := fun i => by
    rw [(SPMTree.transport_eval _ _).1, (SPMTree.transport_eval _ _).2, Emb.left_inv, Emb.left_inv,
      hF, hR, Emb.left_inv, Emb.left_inv]
    exact ⟨rfl, rfl⟩
  constructor
  · show (vertexEmb H cs).inj (μ fun i => (re i).proj ((slotEmb H cs i).proj
      ((lc i).transport (slotEmb H cs i)).F)) = _
    simp only [fun i => (key i).1]
  · show (vertexEmb H cs).inj (P ((vertexEmb H cs).proj ((vertexEmb H cs).inj
      (μ fun i => (re i).proj ((slotEmb H cs i).proj ((lc i).transport (slotEmb H cs i)).R))))) = _
    simp only [Emb.left_inv, fun i => (key i).2]

theorem liftNode_err (hF : ∀ i, (lc i).F = (re i).inj (F i))
    (hR : ∀ i, (lc i).R = (re i).inj (R i)) :
    (liftNode M ρ μ P cs re lc).err = ‖P (μ F) - P (μ R)‖ := by
  have h := liftNode_eval M ρ μ P cs re lc F R hF hR
  have e1 : (liftNode M ρ μ P cs re lc).err =
      ‖((vertexEmb H cs).inj ∘L P ∘L (vertexEmb H cs).proj) (liftNode M ρ μ P cs re lc).F -
        (liftNode M ρ μ P cs re lc).R‖ := rfl
  rw [e1, h.1, h.2, ContinuousLinearMap.comp_apply, ContinuousLinearMap.comp_apply, Emb.left_inv,
    ← map_sub, Emb.norm_ι]

theorem liftNode_Λ : (liftNode M ρ μ P cs re lc).Λ = M * ∏ i, (lc i).Λ := by
  show M * ∏ i, ((lc i).transport (slotEmb H cs i)).Λ = _
  simp only [SPMTree.transport_Λ]

theorem liftNode_dshape : (liftNode M ρ μ P cs re lc).dshape =
    .node m (ρ / M) (fun i => (lc i).dshape) := by
  show DShape.node m (ρ / M) (fun i => ((lc i).transport (slotEmb H cs i)).dshape) = _
  simp only [SPMTree.transport_dshape]

theorem liftNode_inRan (v : (nodeSpace H cs).carrier) (h : (liftNode M ρ μ P cs re lc).InRan v) :
    P ((vertexEmb H cs).proj v) = (vertexEmb H cs).proj v := by
  have h' : (vertexEmb H cs).inj (P ((vertexEmb H cs).proj v)) = v := h
  have h'' := congrArg (vertexEmb H cs).proj h'
  rwa [Emb.left_inv] at h''

theorem liftNode_admFull0 (hM : 0 ≤ M) (hρ : 0 ≤ ρ) (hμ : ‖μ‖ ≤ M) (hP : IsOrthProj P)
    (S : ∀ i, (Hs i).carrier → Prop)
    (hcl : ∀ y : ∀ i, (Hs i).carrier, (∀ i, S i (y i)) → ‖μ y - P (μ y)‖ ≤ ρ * ∏ i, ‖y i‖)
    (hS : ∀ i v, (lc i).InRan v → S i ((re i).proj v)) (hch : ∀ i, (lc i).AdmFull0) :
    (liftNode M ρ μ P cs re lc).AdmFull0 := by
  have hps : ∀ i (v : (nodeSpace H cs).carrier),
      ‖((re i).proj ∘L (slotEmb H cs i).proj) v‖ ≤ ‖v‖ := fun i v =>
    ((re i).norm_π_le _).trans (Emb.norm_π_le _ v)
  exact ⟨hM, hρ, norm_embLaw_le _ μ _ hps hM hμ, isOrthProj_emb _ hP,
    closure_emb _ μ _ hps hρ S (fun i v => ((lc i).transport (slotEmb H cs i)).InRan v)
      (fun i v hv => hS i _ (SPMTree.transport_inRan _ _ v hv)) hcl,
    fun i => SPMTree.transport_admFull0 _ _ (hch i)⟩

end LiftNode

theorem lift_eval {H : HSpace.{u}} (t : MSTree H) :
    (lift t).F = (rootEmb t).inj t.F ∧ (lift t).R = (rootEmb t).inj t.R := by
  induction t with
  | leaf z => exact ⟨rfl, rfl⟩
  | node m M ρ Hs μ P ch ih =>
    exact liftNode_eval M ρ μ P _ _ _ (fun i => (ch i).F) (fun i => (ch i).R)
      (fun i => (ih i).1) (fun i => (ih i).2)

theorem lift_err {H : HSpace.{u}} (t : MSTree H) : (lift t).err = t.err := by
  cases t with
  | leaf z => rfl
  | node m M ρ Hs μ P ch =>
    exact liftNode_err M ρ μ P _ _ _ (fun i => (ch i).F) (fun i => (ch i).R)
      (fun i => (lift_eval (ch i)).1) (fun i => (lift_eval (ch i)).2)

theorem lift_Λ {H : HSpace.{u}} (t : MSTree H) : (lift t).Λ = t.Λ := by
  induction t with
  | leaf z => rfl
  | node m M ρ Hs μ P ch ih =>
    exact (liftNode_Λ M ρ μ P _ _ _).trans (by simp only [ih]; rfl)

theorem lift_dshape {H : HSpace.{u}} (t : MSTree H) : (lift t).dshape = t.dshape := by
  induction t with
  | leaf z => rfl
  | node m M ρ Hs μ P ch ih =>
    exact (liftNode_dshape M ρ μ P _ _ _).trans (by simp only [ih]; rfl)

theorem lift_inRan {H : HSpace.{u}} (t : MSTree H) (v : (cspace t).carrier)
    (h : (lift t).InRan v) : t.InRan ((rootEmb t).proj v) := by
  cases t with
  | leaf z => trivial
  | node m M ρ Hs μ P ch => exact liftNode_inRan M ρ μ P _ _ _ v h

theorem lift_admFull0 {H : HSpace.{u}} (t : MSTree H) (ht : t.AdmFull0) : (lift t).AdmFull0 := by
  induction t with
  | leaf z => trivial
  | node m M ρ Hs μ P ch ih =>
    obtain ⟨hM, hρ, hμ, hP, hcl, hch⟩ := ht
    exact liftNode_admFull0 M ρ μ P _ _ _ hM hρ hμ hP (fun i v => (ch i).InRan v)
      hcl (fun i v hv => lift_inRan (ch i) v hv) (fun i => ih i (hch i))

theorem lift_rootAdmFull0 {H : HSpace.{u}} (t : MSTree H) (ht : t.RootAdmFull0) :
    (lift t).RootAdmFull0 := by
  cases t with
  | leaf z => exact ht.elim
  | node m M ρ Hs μ P ch => exact lift_admFull0 _ ht

/-- A zero operator-norm bound somewhere forces `Λ_T = 0`. -/
theorem Λ_eq_zero_of_hasZeroM {G : Type*} [NormedAddCommGroup G] [InnerProductSpace ℝ G] :
    ∀ t : SPMTree G, t.HasZeroM → t.Λ = 0
  | .leaf _, h => h.elim
  | .node _ _ _ _ _ ch, h => by
    rcases h with h0 | ⟨i, hi⟩
    · simp only [SPMTree.Λ, h0, zero_mul]
    · simp only [SPMTree.Λ]
      rw [Finset.prod_eq_zero (Finset.mem_univ i) (Λ_eq_zero_of_hasZeroM (ch i) hi), mul_zero]

/-- Single-space trees as per-vertex-space trees (all spaces equal). -/
def ofS {G : Type u} [NormedAddCommGroup G] [InnerProductSpace ℝ G] :
    SPMTree G → MSTree (HSpace.mk G)
  | .leaf z => leaf z
  | .node m M ρ μ P ch => node m M ρ (fun _ => HSpace.mk G) μ P (fun i => ofS (ch i))

section OfS

variable {G : Type u} [NormedAddCommGroup G] [InnerProductSpace ℝ G]

theorem ofS_eval (t : SPMTree G) : (ofS t).F = t.F ∧ (ofS t).R = t.R := by
  induction t with
  | leaf z => exact ⟨rfl, rfl⟩
  | node m M ρ μ P ch ih =>
    exact ⟨congrArg μ (funext fun i => (ih i).1),
      congrArg P (congrArg μ (funext fun i => (ih i).2))⟩

theorem ofS_err (t : SPMTree G) : (ofS t).err = t.err := by
  cases t with
  | leaf z => rfl
  | node m M ρ μ P ch =>
    show ‖P (μ fun i => (ofS (ch i)).F) - P (μ fun i => (ofS (ch i)).R)‖ = _
    rw [funext fun i => (ofS_eval (ch i)).1, funext fun i => (ofS_eval (ch i)).2]
    rfl

theorem ofS_Λ (t : SPMTree G) : (ofS t).Λ = t.Λ := by
  induction t with
  | leaf z => rfl
  | node m M ρ μ P ch ih =>
    show M * ∏ i, (ofS (ch i)).Λ = M * ∏ i, (ch i).Λ
    simp only [ih]

theorem ofS_dshape (t : SPMTree G) : (ofS t).dshape = t.dshape := by
  induction t with
  | leaf z => rfl
  | node m M ρ μ P ch ih =>
    show DShape.node m (ρ / M) (fun i => (ofS (ch i)).dshape) = _
    simp only [ih]
    rfl

theorem ofS_inRan (t : SPMTree G) (v : G) : (ofS t).InRan v ↔ t.InRan v := by
  cases t <;> rfl

theorem ofS_admFull0 (t : SPMTree G) (ht : t.AdmFull) : (ofS t).AdmFull0 := by
  induction t with
  | leaf z => trivial
  | node m M ρ μ P ch ih =>
    obtain ⟨hM, hρ, hμ, hP, hcl, hch⟩ := ht
    exact ⟨hM.le, hρ, hμ, hP, fun x hx => hcl x (fun i => (ofS_inRan (ch i) (x i)).1 (hx i)),
      fun i => ih i (hch i)⟩

end OfS

end MSTree

open MSTree

/-- **Heterogeneous Theorem R with a space at every vertex** (`M_v ≥ 0`). -/
theorem heterogeneous_multispace_upper {H : HSpace.{u}} (t : MSTree H) (ht : t.RootAdmFull0) :
    t.err ≤ t.Λ * gBox t.dshape.childDefects := by
  rw [← lift_err, ← lift_Λ, ← lift_dshape]
  exact heterogeneous_scaled_upper_nonneg _ (lift_rootAdmFull0 t ht)

/-- **Heterogeneous sharp constant with a space at every vertex.** The supremum ranges over all
per-vertex-space realisations (spaces in `Type`) with `Λ_T > 0`. -/
theorem heterogeneous_multispace_sSup {m : ℕ} {e : ℝ} (he : 0 ≤ e) (ch : Fin m → DShape) :
    sSup {x | ∃ (H : HSpace.{0}) (t : MSTree H), t.dshape = .node m e ch ∧ t.RootAdmFull0 ∧
      0 < t.Λ ∧ t.err / t.Λ = x} = gBox (DShape.node m e ch).childDefects := by
  apply csSup_eq_csSup_of_forall_exists_le
  · rintro x ⟨H, t, hT, hadm, hΛ, rfl⟩
    have hadm' := lift_rootAdmFull0 t hadm
    have hΛ' : 0 < (MSTree.lift t).Λ := by rwa [lift_Λ]
    have hstrict : (MSTree.lift t).RootAdmFull := by
      revert hadm' hΛ'
      generalize MSTree.lift t = s
      intro hadm' hΛ'
      cases s with
      | leaf z => exact hadm'.elim
      | node m' M' ρ' μ' P' ch' =>
        refine SPMTree.admFull_of_admFull0 _ hadm' fun hz => ?_
        rw [Λ_eq_zero_of_hasZeroM _ hz] at hΛ'
        exact lt_irrefl 0 hΛ'
    obtain ⟨θ, hθ, hle⟩ := heterogeneous_upper _ (SPMTree.normalize_rootAdmFull _ hstrict)
    rw [SPMTree.normalize_dshape, lift_dshape, hT] at hθ
    refine ⟨_, ⟨θ, hθ, rfl⟩, ?_⟩
    rw [← lift_err, ← lift_Λ, SPMTree.err_eq _ hstrict, mul_div_cancel_left₀ _ hΛ'.ne']
    exact hle
  · rintro y ⟨θ, hθ, rfl⟩
    obtain ⟨g, hg, hgi⟩ := forall₂_flatten_ofFn (fun i => (ch i).defects) θ hθ
    choose a ha1 ha2 ha3 using fun i => AShape.exists_fill (ch i) (g i) (hgi i)
    have hsΛ : (SPMTree.ofH (witRootH m e a)).Λ = 1 := witRootH_Λ m e a
    refine ⟨_, ⟨HSpace.mk ℂ, ofS (SPMTree.ofH (witRootH m e a)), ?_,
      ofS_admFull0 _ (SPMTree.ofH_admFull _ (witRootH_rootAdmFull he a ha3)), ?_, rfl⟩, ?_⟩
    · rw [ofS_dshape, SPMTree.ofH_dshape, witRootH_dshape]
      simp only [ha1]
    · rw [ofS_Λ, hsΛ]
      exact one_pos
    · rw [ofS_Λ, hsΛ, div_one, ofS_err, SPMTree.ofH_err, witRootH_err, hg]
      simp only [ha2, le_refl]

end PMT