# PMTFormal — machine-checked Theorem R (normalised, single-space form)

Lean 4 `v4.33.1`, Mathlib `v4.33.1` (pinned in `lakefile.toml` and `lean-toolchain`).

**Status (2026-09-14).** The upper bound, the universal sharp witness (with full PMT-A
admissibility) and the equality of suprema are formalised end to end, with no `sorry` and only
the standard axioms. The upper-bound core uses a **new proof**, the lifted-angle proof in
`../lifted_angle/LIFTED_ANGLE_PROOF.md`. It is **not** a formalisation of the dilation/Riesz
argument in `review/theorem_R_v2/THEOREM_R_v2.md` §§2–4; that text is frozen and still unreviewed.

## What the formal statement says

| Lean declaration | Content | Paper counterpart (v2) |
|---|---|---|
| `PMT.theorem_R_upper` | every PMT-A tree over any real inner product space `G`: `err ≤ ‖1 − w(τ)^(k−1)‖` for some `τ ∈ [0, arcsin η]` | Theorem 7.1 |
| `PMT.theorem_R_lower` | every shape, every `τ ∈ [0, arcsin η]`: a PMT-A tree in `ℂ` with that shape and `err = ‖1 − w(τ)^(k−1)‖` | Theorem 8.1 + Corollary 8.2, **including admissibility** |
| `PMT.theorem_R_sSup` | `sSup` of `err` over PMT-A realisations of a shape = `sSup_{τ∈[0, arcsin η]} ‖1 − w(τ)^(k−1)‖` | Theorem R (`C^P_T = C_k`, normalised) |

Supporting declarations:

| Lean declaration | Content |
|---|---|
| `PMT.phi`, `PMT.phi_triangle` | lifted angle `phi f g = ∠((f,√(1−‖f‖²)), (g,√(1−‖g‖²)))`; triangle inequality |
| `PMT.normSq_sub_le` | (N−): `phi f g ≤ S ≤ π`, `t ≥ 0` ⟹ `‖f − t g‖² ≤ 1 + t² − 2t cos S` |
| `PMT.phi_le_of_contr` | contraction monotonicity of `phi` (two spaces) |
| `PMT.phi_multilinear_le` | **tensor angle lemma, multilinear form**: `‖μ‖ ≤ 1`, inputs in the unit ball ⟹ `phi (μ x) (μ y) ≤ ∑ phi (xᵢ) (yᵢ)` |
| `PMT.phi_proj` | `phi g (P g / cos θ) ≤ θ`, `sin θ = ‖g − P g‖` |
| `PMT.node_step` | **Lemma 3**: dominated children + trajectory closure ⟹ node dominated by `(cos θ ∏ρᵢ, θ + ∑χᵢ)`, `θ ∈ [0, arcsin η]` |
| `PMT.root_step` | root reading |
| `PMT.envelope` | multiplicative envelope: one angle per internal node |
| `PMT.upper_bound` | upper bound under trajectory closure (weaker than PMT-A) |
| `PMT.wit_admFull`, `PMT.witRoot_admFull`, `PMT.witRoot_err` | witness: norms, projectors, full closure, exact error |
| `PMT.cos_sum_le_prod_cos`, `PMT.prod_cos_le_cos_mean_pow`, `PMT.diagonal_capped`, `PMT.diagonal_lemma` | Lemmas 6.1–6.3 (Diagonal Lemma) |
| `PMT.rootError_eq`, `PMT.rootError_equal_angles` | earlier skeleton-level witness evaluation (kept) |

## Heterogeneous Theorem R (`PMTFormal/Heterogeneous/`, 2026-09-14)

Each internal node `v` has its own defect `e_v` (paper: `η_v = ρ_v / M_v`). For a defect list `η`,

`gBox η = sup { |1 − ∏ w(θ_i)| : θ_i ∈ [0, arcsin η_i] }`   (a maximum when all `η_i ≥ 0`).

| File | Lean declaration | Content |
|---|---|---|
| `BoxConstant.lean` | `PMT.box`, `PMT.gBox`, `PMT.le_gBox` | box and box constant (PMT-free) |
| | `PMT.box_capped` | root reduction inside the box by uniform angle scaling `π/Θ` (no Diagonal Lemma) |
| `Upper.lean` | `PMT.HPMTree`, `PMT.DShape`, `HPMTree.AdmFull`, `HPMTree.RootAdmFull` | nodewise-defect trees and admissibility |
| | `PMT.envelopeH` | heterogeneous envelope: `θ_u ≤ arcsin e_u` per node |
| | **`PMT.heterogeneous_upper`** (H1) | `err ≤ ‖1 − ∏ w(θ_u)‖` for some `θ ∈ box(childDefects)`, any `G` |
| | `PMT.heterogeneous_le_gBox` | `err ≤ gBox(childDefects)` |
| `Witness.lean` | `PMT.AShape`, `AShape.exists_fill`, `PMT.witH`, `PMT.witRootH` | per-node-angle witness in `ℂ` |
| | **`PMT.heterogeneous_witness`** (H4) | every box point is realised exactly by an admissible tree |
| `Sharp.lean` | **`PMT.heterogeneous_lower`**, **`PMT.heterogeneous_sSup`** | `sup_{A(T,η)} err = gBox(childDefects T)` |
| | `PMT.heterogeneous_sharp` | complex realisations are extremal over all `G` |
| | **`PMT.uniform_gBox_eq`**, `PMT.heterogeneous_uniform_recovery` | equal defects recover Theorem R's constant |
| `Permutation.lean` | **`PMT.gBox_perm`**, **`PMT.heterogeneous_placement_independent`** (H2) | the constant depends only on the multiset of non-root defects |
| `Attainment.lean` | `PMT.theorem_R_max_attained`, `PMT.gBox_attained`, `PMT.heterogeneous_max_attained` | the suprema are maxima, attained by trees |
| `Scaled.lean` | `PMT.SPMTree`, `SPMTree.normalize`, `SPMTree.err_eq` | scaled data `(M_v > 0, ρ_v)`, `Λ_T = ∏M_v ∏‖z_ℓ‖` |
| | `PMT.heterogeneous_scaled_upper`, `PMT.heterogeneous_scaled_sSup` | `err ≤ Λ_T gBox(ρ/M)`; `sup err/Λ_T = gBox(ρ/M)` |
| `ScaledZero.lean` | `SPMTree.AdmFull0`, `SPMTree.err_zero_of_hasZeroM`, `PMT.heterogeneous_scaled_upper_nonneg` | degenerate case `M_v = 0`: `err = 0`; scaled bound for all `M_v ≥ 0` |
| `SpecLemmas.lean` | `PMT.opNorm_le_iff_unit_ball`, `PMT.HPMTree.closure_iff_unit_ball` | Lean norm and closure conditions ⇔ the unit-ball forms of A2 and A5 |
| `Baseline.lean` | `PMT.gBox_le_sum` | additive baseline `gBox η ≤ Σ η_u` |
| `CommonSpace.lean` | `PMT.Emb`, `PMT.MSTree`, `MSTree.lift`, **`PMT.heterogeneous_multispace_upper`**, **`PMT.heterogeneous_multispace_sSup`** | **common-ambient-space reduction**: an arbitrary real inner product space at every vertex |
| `Monotone.lean` | `PMT.gBox_mono`, `PMT.gBox_le_replicate`, `PMT.gBox_le_uniform_fallback` | `gBox` is monotone in each defect; uniform fallback at the largest defect |
| `Trajectory.lean` | `SPMTree.AdmTC`, **`PMT.heterogeneous_scaled_upper_of_admTC`**, `PMT.heterogeneous_scaled_upper_of_admTC_nonneg` | a posteriori certificate: scaled bound with closure only along the realised reduced trajectory (global `‖μ_v‖ ≤ M_v` still required; one ambient space) |
| `CappedDiagonalFull.lean` | **`PMT.capped_equal_angle`**, **`PMT.gBox_eq_capped`**, `PMT.gBox_eq_capped_max`, `PMT.prod_cos_le_waterfill`, `PMT.log_cos_tangent` | **H3 proved**: `gBox(η) = max_τ ‖1 − ∏ w(min(arcsin η_i, τ))‖` (water-filling) |
| `Amplitude.lean` | `PMT.ATree.err_le_ebound`, `PMT.ATree.norm_F_ge` | a posteriori amplitude bound for arbitrary local deviations (max form) |
| `AmplitudeSlots.lean` | **`PMT.KTree.err_le_sbound`**, `PMT.norm_sub_le_slots`, `PMT.slot_const_general`, `PMT.slot_args_eq_update`, **`PMT.ATree.err_le_abound`**, `PMT.sum_slot_prod_eq` | slotwise bound `e_v ≤ d_v + Σ K_i e_i`; compact bound `A_v = d_v + M_v(∏(r_i + A_i) − ∏ r_i)` |
| `CappedDiagonal.lean` | `PMT.CappedEqualAngle` (a `Prop`), `PMT.sSup_capped_le_gBox`, `PMT.cappedEqualAngle_replicate` | **H3, kept separate and open.** Only the easy half and the equal-defect case are proved. No other module imports it; it is not an axiom. |

Scope notes for the heterogeneous statements:

* The root defect `e_r` enters admissibility (full closure at the root) but not the constant; the
  sharp statements assume `e_r ≥ 0` (otherwise the class is empty).
* Non-root defects are unrestricted reals. A negative defect empties both the class and the box,
  and `arcsin` saturates above `1`.
* `M_v = 0` is handled separately in `ScaledZero.lean` (upper bound only; the sharp sSup statement
  uses `M_v > 0`).
* One-space-per-node → one ambient space is machine-checked in `CommonSpace.lean` (2026-09-14).
  The paper-class ↔ Lean audit is `SPEC_AUDIT.md`.
* H1 and H4 do **not** use the Diagonal Lemma or H3. The Diagonal Lemma is used only in
  `uniform_gBox_eq`.

## Modelling choices and the exact gap to the paper statement

The formal objects are in `PMTFormal/Tree.lean` and `PMTFormal/WitnessAdm.lean`.

* **Trees.** `PMTree G` is `leaf z` or `node m μ P ch`, with
  `μ : ContinuousMultilinearMap ℝ (Fin m → G) G`, `P : G →L[ℝ] G` and `ch : Fin m → PMTree G`.
  Arity `m = 0` is allowed, which is harmless and more general.
* **Evaluations.** `F`, `R` and `err = ‖P_r(μ_r F_c) − P_r(μ_r R_c)‖ = ‖P_r F_r − R_r‖`.
* **PMT-A admissibility** (`AdmFull`, `RootAdmFull`):
  * `‖μ_v‖ ≤ 1`;
  * `P_v` idempotent and symmetric;
  * closure `‖μ_v x − P_v μ_v x‖ ≤ η ∏‖xᵢ‖` for all inputs whose internal-child slots satisfy
    `P_c xᵢ = xᵢ` (leaf slots arbitrary);
  * leaves `‖z‖ ≤ 1`.
* **Not formalised for `PMTree`: two elementary reductions, argued on paper.**
  1. **Scaling (N1).** General `M`, `ρ` and leaf norms reduce to `M = 1`, `ρ = η` and unit leaves
     by `μ_v ↦ μ_v/M`, `z_ℓ ↦ z_ℓ/‖z_ℓ‖`. For nodewise `M_v > 0` this reduction is now
     machine-checked in `Heterogeneous/Scaled.lean`.
  2. **One space per node → one ambient space.** Embed every `H_w` isometrically into a common
     space `G` and set `μ'_v = ι_v ∘ μ_v ∘ (π_c)`, `P'_v = ι_v P_v π_v`. Operator norms,
     projectors, full closure and both evaluations transfer, and the error is unchanged.
* **Supremum.** The sharp constant is stated as an equality of `sSup`s over realisations in `ℂ`.
  `theorem_R_upper` shows that no other space gives a larger error.
* **Review target.** What remains for human review is the **specification**: these definitions
  and the two reductions. The proof itself is machine-checked.

## Build

```bash
lake exe cache get
```

```bash
lake build
```

```bash
lake env lean AxiomsCheck.lean
```

A successful build with no `sorry`, and `#print axioms` showing only
`[propext, Classical.choice, Quot.sound]`, is the check. The record is in `BUILD_LOG.md`.
