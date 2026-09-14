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
* **Not formalised: two elementary reductions, argued on paper.**
  1. **Scaling (N1).** General `M`, `ρ` and leaf norms reduce to `M = 1`, `ρ = η` and unit leaves
     by `μ_v ↦ μ_v/M`, `z_ℓ ↦ z_ℓ/‖z_ℓ‖`.
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
