/-
Lifted angle: the order O2 of Theorem R v2 in metric form.

For `f` in the closed unit ball of a real inner product space `G`, the hemisphere lift is
`lift f = (f, √(1 - ‖f‖²)) ∈ G × ℝ` (L² product), a unit vector. The lifted angle
`phi f g := angle (lift f) (lift g)` is the spherical distance of the lifts, so it satisfies the
triangle inequality. Its cosine is `⟪f, g⟫ + √(1-‖f‖²) √(1-‖g‖²)`.

Statements:
* `PMT.phi_triangle`      triangle inequality
* `PMT.cos_phi`           cosine formula on the unit ball
* `PMT.normSq_sub_le`     (N−): `phi f g ≤ S ≤ π`, `t ≥ 0` ⟹ `‖f - t g‖² ≤ 1 + t² - 2 t cos S`
* `PMT.phi_le_of_contr`   contraction monotonicity (the order-one case of the tensor angle lemma)
-/
import Mathlib

open Real InnerProductGeometry
open scoped RealInnerProductSpace

namespace PMT

variable {G : Type*} [NormedAddCommGroup G] [InnerProductSpace ℝ G]

/-- Hemisphere lift of `f` into `G × ℝ` with the L² norm. -/
noncomputable def lift (f : G) : WithLp 2 (G × ℝ) := WithLp.toLp 2 (f, √(1 - ‖f‖ ^ 2))

/-- The lifted angle `phi f g`. -/
noncomputable def phi (f g : G) : ℝ := angle (lift f) (lift g)

/-- The cosine of the lifted angle, as an explicit expression. -/
noncomputable def cphi (f g : G) : ℝ := ⟪f, g⟫ + √(1 - ‖f‖ ^ 2) * √(1 - ‖g‖ ^ 2)

theorem phi_triangle (f g h : G) : phi f h ≤ phi f g + phi g h :=
  angle_le_angle_add_angle _ _ _

theorem phi_nonneg (f g : G) : 0 ≤ phi f g := angle_nonneg _ _

theorem phi_le_pi (f g : G) : phi f g ≤ π := angle_le_pi _ _

theorem inner_lift (f g : G) : ⟪lift f, lift g⟫ = cphi f g := by
  simp only [lift, WithLp.prod_inner_apply, cphi]
  simp [mul_comm]

theorem norm_lift {f : G} (hf : ‖f‖ ≤ 1) : ‖lift f‖ = 1 := by
  have h1 : 0 ≤ 1 - ‖f‖ ^ 2 := by nlinarith [norm_nonneg f]
  have hsq : ‖lift f‖ ^ 2 = 1 := by
    rw [← real_inner_self_eq_norm_sq, inner_lift, cphi, real_inner_self_eq_norm_sq,
      ← sq, Real.sq_sqrt h1]
    ring
  have hn := norm_nonneg (lift f)
  nlinarith [hsq]

theorem cos_phi {f g : G} (hf : ‖f‖ ≤ 1) (hg : ‖g‖ ≤ 1) : Real.cos (phi f g) = cphi f g := by
  rw [phi, cos_angle, inner_lift, norm_lift hf, norm_lift hg]
  simp

theorem cphi_le_one {f g : G} (hf : ‖f‖ ≤ 1) (hg : ‖g‖ ≤ 1) : cphi f g ≤ 1 := by
  rw [← cos_phi hf hg]; exact Real.cos_le_one _

theorem phi_eq_arccos {f g : G} (hf : ‖f‖ ≤ 1) (hg : ‖g‖ ≤ 1) :
    phi f g = Real.arccos (cphi f g) := by
  rw [← cos_phi hf hg, Real.arccos_cos (phi_nonneg f g) (phi_le_pi f g)]

theorem phi_self {f : G} (hf : ‖f‖ ≤ 1) : phi f f = 0 := by
  have h : lift f ≠ 0 := by
    intro h0
    have := norm_lift hf
    rw [h0, norm_zero] at this
    exact zero_ne_one this
  exact angle_self h

/-- `phi f g ≤ S` (for `S ∈ [0, π]`) iff `cos S ≤ cphi f g`. -/
theorem phi_le_iff {f g : G} (hf : ‖f‖ ≤ 1) (hg : ‖g‖ ≤ 1) {S : ℝ} (hS0 : 0 ≤ S) (hSπ : S ≤ π) :
    phi f g ≤ S ↔ Real.cos S ≤ cphi f g := by
  rw [← cos_phi hf hg]
  constructor
  · intro h
    exact Real.cos_le_cos_of_nonneg_of_le_pi (phi_nonneg f g) hSπ h
  · intro h
    by_contra hlt
    push Not at hlt
    have := Real.cos_lt_cos_of_nonneg_of_le_pi hS0 (phi_le_pi f g) hlt
    linarith

/-- **(N−).** If `phi f g ≤ S ≤ π` and `t ≥ 0` then `‖f - t g‖² ≤ 1 + t² - 2 t cos S`. -/
theorem normSq_sub_le {f g : G} (hf : ‖f‖ ≤ 1) (hg : ‖g‖ ≤ 1) {S : ℝ} (hS0 : 0 ≤ S)
    (hSπ : S ≤ π) (hphi : phi f g ≤ S) {t : ℝ} (ht : 0 ≤ t) :
    ‖f - t • g‖ ^ 2 ≤ 1 + t ^ 2 - 2 * t * Real.cos S := by
  have hc := (phi_le_iff hf hg hS0 hSπ).1 hphi
  have ha : 0 ≤ 1 - ‖f‖ ^ 2 := by nlinarith [norm_nonneg f]
  have hb : 0 ≤ 1 - ‖g‖ ^ 2 := by nlinarith [norm_nonneg g]
  set a := √(1 - ‖f‖ ^ 2) with ha_def
  set b := √(1 - ‖g‖ ^ 2) with hb_def
  have ha2 : a ^ 2 = 1 - ‖f‖ ^ 2 := Real.sq_sqrt ha
  have hb2 : b ^ 2 = 1 - ‖g‖ ^ 2 := Real.sq_sqrt hb
  rw [cphi] at hc
  rw [norm_sub_sq_real, real_inner_smul_right, norm_smul, Real.norm_eq_abs, abs_of_nonneg ht]
  nlinarith [sq_nonneg (a - t * b), mul_le_mul_of_nonneg_left hc (by positivity : (0 : ℝ) ≤ 2 * t)]

omit [NormedAddCommGroup G] [InnerProductSpace ℝ G] in
theorem norm_smul_add_smul_sq {H : Type*} [NormedAddCommGroup H] [InnerProductSpace ℝ H]
    (u v : H) (s t : ℝ) :
    ‖s • u + t • v‖ ^ 2 = s ^ 2 * ‖u‖ ^ 2 + 2 * s * t * ⟪u, v⟫ + t ^ 2 * ‖v‖ ^ 2 := by
  rw [norm_add_sq_real, norm_smul, norm_smul, real_inner_smul_left, real_inner_smul_right,
    Real.norm_eq_abs, Real.norm_eq_abs, mul_pow, mul_pow, sq_abs, sq_abs]
  ring

/-- **Contraction monotonicity.** Let `f, g ∈ G` and `x, y ∈ H` with `‖x‖, ‖y‖ ≤ 1` and
`‖s f + t g‖ ≤ ‖s x + t y‖` for all real `s, t`. Then `‖f‖, ‖g‖ ≤ 1` and `phi f g ≤ phi x y`. -/
theorem phi_le_of_contr {H : Type*} [NormedAddCommGroup H] [InnerProductSpace ℝ H]
    {f g : G} {x y : H} (hx : ‖x‖ ≤ 1) (hy : ‖y‖ ≤ 1)
    (h : ∀ s t : ℝ, ‖s • f + t • g‖ ≤ ‖s • x + t • y‖) :
    ‖f‖ ≤ 1 ∧ ‖g‖ ≤ 1 ∧ phi f g ≤ phi x y := by
  -- quadratic-form inequality
  have hq : ∀ s t : ℝ, ‖s • f + t • g‖ ^ 2 ≤ ‖s • x + t • y‖ ^ 2 := fun s t =>
    pow_le_pow_left₀ (norm_nonneg _) (h s t) 2
  have expand : ∀ (u v : G) (s t : ℝ),
      ‖s • u + t • v‖ ^ 2 = s ^ 2 * ‖u‖ ^ 2 + 2 * s * t * ⟪u, v⟫ + t ^ 2 * ‖v‖ ^ 2 :=
    norm_smul_add_smul_sq
  have expandH : ∀ (u v : H) (s t : ℝ),
      ‖s • u + t • v‖ ^ 2 = s ^ 2 * ‖u‖ ^ 2 + 2 * s * t * ⟪u, v⟫ + t ^ 2 * ‖v‖ ^ 2 :=
    norm_smul_add_smul_sq
  have hf1 : ‖f‖ ≤ 1 := by
    have := hq 1 0
    simp only [one_smul, zero_smul, add_zero] at this
    nlinarith [norm_nonneg f, norm_nonneg x]
  have hg1 : ‖g‖ ≤ 1 := by
    have := hq 0 1
    simp only [one_smul, zero_smul, zero_add] at this
    nlinarith [norm_nonneg g, norm_nonneg y]
  refine ⟨hf1, hg1, ?_⟩
  rw [phi_eq_arccos hf1 hg1, phi_eq_arccos hx hy]
  apply Real.arccos_le_arccos
  -- goal: cphi x y ≤ cphi f g
  set α := ‖x‖ ^ 2 - ‖f‖ ^ 2
  set β := ‖y‖ ^ 2 - ‖g‖ ^ 2
  set γ := ⟪x, y⟫ - ⟪f, g⟫
  have hQ : ∀ s t : ℝ, 0 ≤ s ^ 2 * α + t ^ 2 * β + 2 * s * t * γ := by
    intro s t
    have := hq s t
    rw [expand, expandH] at this
    simp only [α, β, γ]
    nlinarith [this]
  have hα : 0 ≤ α := by have := hQ 1 0; simpa using this
  have hβ : 0 ≤ β := by have := hQ 0 1; simpa using this
  have hγ2 : γ ^ 2 ≤ α * β := by
    rcases lt_or_eq_of_le hβ with hβpos | hβ0
    · have := hQ β (-γ)
      nlinarith [this]
    · rcases lt_or_eq_of_le hα with hαpos | hα0
      · have := hQ (-γ) α
        nlinarith [this]
      · have := hQ γ (-1)
        rw [← hα0, ← hβ0] at this ⊢
        nlinarith [this, sq_nonneg γ]
  -- square roots
  have hx0 : 0 ≤ 1 - ‖x‖ ^ 2 := by nlinarith [norm_nonneg x]
  have hy0 : 0 ≤ 1 - ‖y‖ ^ 2 := by nlinarith [norm_nonneg y]
  have hf0 : 0 ≤ 1 - ‖f‖ ^ 2 := by nlinarith [norm_nonneg f]
  have hg0 : 0 ≤ 1 - ‖g‖ ^ 2 := by nlinarith [norm_nonneg g]
  set a := √(1 - ‖x‖ ^ 2)
  set b := √(1 - ‖y‖ ^ 2)
  set a' := √(1 - ‖f‖ ^ 2)
  set b' := √(1 - ‖g‖ ^ 2)
  have ha2 : a ^ 2 = 1 - ‖x‖ ^ 2 := Real.sq_sqrt hx0
  have hb2 : b ^ 2 = 1 - ‖y‖ ^ 2 := Real.sq_sqrt hy0
  have ha'2 : a' ^ 2 = a ^ 2 + α := by rw [Real.sq_sqrt hf0, ha2]; ring
  have hb'2 : b' ^ 2 = b ^ 2 + β := by rw [Real.sq_sqrt hg0, hb2]; ring
  have ha0 : 0 ≤ a := Real.sqrt_nonneg _
  have hb0 : 0 ≤ b := Real.sqrt_nonneg _
  have ha'0 : 0 ≤ a' := Real.sqrt_nonneg _
  have hb'0 : 0 ≤ b' := Real.sqrt_nonneg _
  -- key: a*b + γ ≤ a'*b'
  have key : a * b + γ ≤ a' * b' := by
    by_cases hneg : a * b + γ ≤ 0
    · nlinarith [mul_nonneg ha'0 hb'0]
    push Not at hneg
    have h2abγ : 2 * a * b * γ ≤ a ^ 2 * β + α * b ^ 2 := by
      by_cases hg : γ ≤ 0
      · nlinarith [mul_nonneg (mul_nonneg ha0 hb0) hα, mul_nonneg (sq_nonneg a) hβ,
          mul_nonneg hα (sq_nonneg b), mul_nonneg ha0 hb0]
      · push Not at hg
        have h1 : (2 * a * b * γ) ^ 2 ≤ (a ^ 2 * β + α * b ^ 2) ^ 2 := by
          nlinarith [mul_le_mul_of_nonneg_left hγ2 (by positivity : (0 : ℝ) ≤ 4 * a ^ 2 * b ^ 2),
            sq_nonneg (a ^ 2 * β - α * b ^ 2)]
        have hr : 0 ≤ a ^ 2 * β + α * b ^ 2 := by positivity
        exact (abs_le_of_sq_le_sq' h1 hr).2
    have hsq : (a * b + γ) ^ 2 ≤ (a' * b') ^ 2 := by
      rw [mul_pow, ha'2, hb'2]
      nlinarith [hγ2, h2abγ]
    exact (abs_le_of_sq_le_sq' hsq (mul_nonneg ha'0 hb'0)).2
  simp only [cphi]
  simp only [γ] at key
  linarith [key]

end PMT
