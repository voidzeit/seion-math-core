# Specification audit — paper class ↔ Lean definitions

```
STATUS:   AGENT AUDIT 2026-09-14 (not an independent human review)
SCOPE:    heterogeneous Theorem R (Theorem 1.1 of STYLE_CONTRACT revision R1) and its uniform case
REFERENCE: ../ADMISSIBLE_CLASS_PMT_A.md (FROZEN 2026-09-13), items A0–A10
BUILD:    8727 jobs, no sorry/admit/axiom, 47 `#print axioms` = [propext, Classical.choice, Quot.sound]
```

Legend:
- **exact**: the Lean condition is the paper condition.
- **exact (Lean)**: the equivalence is itself machine-checked.
- **superset**: the Lean class is larger. This is harmless for upper bounds, and the extremizer lies in the paper class.
- **intentional**: a documented modelling choice.
- **gap**: not formalized.

## 1. Proposed heterogeneous class PMT-A^het (to be frozen by the author)

PMT-A^het is PMT-A (A0–A4, A6–A8) with A5 replaced by nodewise budgets.

- For every internal `v`, there are `M_v > 0` and `ρ_v ≥ 0` with
  - `‖μ_v‖ ≤ M_v`,
  - `‖Q_v μ_v(P̂_{c_1}·,…,P̂_{c_m}·)‖ ≤ ρ_v`.
- The normalized defect is `η_v := ρ_v / M_v`.
- The scale is `Λ_T := ∏_v M_v · ∏_ℓ ‖z_ℓ‖`.
- The constant is `sup E^P_T / Λ_T`, taken over non-degenerate realizations.
- The root budget is constrained like any other but does not enter the constant.

The uniform class PMT-A is the special case `M_v = M`, `ρ_v = ρ`. There,
`Λ_T = M^k L_T` and `sup E^P_T / Λ_T = η·C_T^P(η)`.

## 2. Row-by-row audit

| # | Paper (PMT-A / PMT-A^het) | Lean | Verdict |
|---|---|---|---|
| A0a | finite ordered rooted tree, internal/leaf vertices | `MSTree` / `SPMTree` / `HPMTree` inductives, children `Fin m → _` | exact (ordered) |
| A0b | arity `m_v ≥ 1`, a leaf below every internal vertex | arity `m = 0` allowed | **superset**. The extremizer is built on the given skeleton, so for PMT-A skeletons it lies in PMT-A. |
| A0c | `k ≥ 1`, root internal | `RootAdmFull*` is `False` on a leaf | exact |
| A1 | finite-dimensional real Hilbert space `H_w` per vertex | `MSTree`: an arbitrary real inner product space per vertex (`HSpace`), possibly infinite-dimensional or incomplete | **superset**. `heterogeneous_multispace_upper` covers per-vertex spaces. The extremizer uses `H_w = ℂ ≅ ℝ²` at every vertex, which is a finite-dimensional Hilbert space. |
| A1' | per-vertex spaces → common ambient space | `MSTree.lift`, `lift_err`, `lift_Λ`, `lift_dshape`, `lift_rootAdmFull0`: isometric embedding into `WithLp 2 (H_v × PiLp 2 (children))` | **exact (Lean)**. Closed 2026-09-14. |
| A2 | multilinear map, norm `sup{‖μ(x)‖ : ‖x_i‖ ≤ 1}` | `ContinuousMultilinearMap ℝ`, `opNorm` | **exact (Lean)**: `opNorm_le_iff_unit_ball` |
| A2' | laws independently selectable | no sharing constraint | exact |
| A3 | orthogonal projector `P = P² = P*`, any rank | `IsOrthProj P` (idempotent, symmetric) | exact (symmetric = self-adjoint for bounded operators) |
| A3' | leaves carry `P̂_ℓ = I` | `InRan (leaf) v := True` | exact |
| A4 | `F_v = μ_v(F_c)`, `R_v = P_v μ_v(R_c)`, `E^P = ‖P_r F_r − R_r‖` | `F`, `R`, `err = ‖P(μ F) − P(μ R)‖` | exact (`P_r R_r = R_r` is not needed: `R_r` is defined as `P_r μ_r(R_c)`) |
| A5-norm | `‖μ_v‖ ≤ M_v` | `‖μ‖ ≤ M` in `AdmFull0` / `AdmFull` | exact |
| A5-closure | `‖Q_v μ_v‖` restricted to `∏ Ran P̂_{c_i}` is `≤ ρ_v` (unit-ball sup) | `∀ x, (∀ i, InRan (ch i) (x i)) → ‖μ x − P μ x‖ ≤ ρ ∏‖x_i‖` | **exact (Lean)**: `HPMTree.closure_iff_unit_ball` |
| A5-range | `0 < ρ ≤ M` (uniform) | `ρ_v ≥ 0`, `M_v ≥ 0`, `η_v` may exceed 1 (`arcsin` saturates) | **superset** |
| A5-root | root closure constrained, not in the constant | root closure is part of `RootAdmFull*`; `gBox` uses `childDefects` only | intentional, and matches A5 |
| A5.1 | scaling reduction to `M = 1`, unit leaves | `SPMTree.normalize`, `err_eq` (`M_v > 0`); `ScaledZero` for `M_v = 0` | **exact (Lean)** |
| A5.2 | leaf freezing, constants depend only on `sk(T)` | not used; the constant is `gBox(childDefects)` and depends only on the internal defect multiset | stronger (placement independence, `gBox_perm`) |
| A6 | all leaves nonzero | `0 < Λ_T` in the `sSup` statements. For `AdmFull0` with `M_v ≥ 0`, `Λ > 0` forces all `M_v > 0` (Lean: `Λ_eq_zero_of_hasZeroM`) and all leaves nonzero (by the product form). The converse is immediate. | exact |
| A7 | `sup` over all dimensions and ranks | `heterogeneous_multispace_sSup`: `sup` over all per-vertex-space trees in `Type` with `Λ > 0` | **exact for the value**. The Lean class ⊇ the paper class; the upper bound holds on the larger class and the extremizer lies in the smaller one, so both suprema equal `gBox`. |
| A8 | excluded variants (weight sharing, fixed dims, trajectory-only closure, …) | the upper bound also holds under trajectory-only closure (`heterogeneous_upper_of_rootAdm`) | stronger upper bound; lower bound in full PMT-A |
| A9 | field ℝ; ℂ-statements must be labelled PMT-A[C] | `ℂ` is used only as the real inner product space ℝ² with ℝ-multilinear laws | exact. **Not** a PMT-A[C] statement. |
| A10 | class, skeleton, η-range, upper proof, explicit witness | `DShape`, arbitrary real defects, `heterogeneous_upper`, `witRootH` with `witRootH_rootAdmFull` | exact |
| extra | attainment ("attained") | `gBox_attained`, `theorem_R_max_attained`, `heterogeneous_max_attained` | exact (Lean) |
| extra | uniform case recovers `C_k` | `uniform_gBox_eq`, `heterogeneous_uniform_recovery` | exact (Lean), `0 < η` |
| extra | additive baseline `Σ η_u` | `gBox_le_sum` | exact (Lean) |
| extra | H3 (capped equal angles) | `CappedEqualAngle : List ℝ → Prop`; only the easy half and the equal-defect case are proved; nothing imports it | open, isolated |

## 3. Residual items for a human reviewer

1. **Degenerate arity.** A0 requires arity ≥ 1 and a leaf below every internal vertex; Lean
   allows arity 0. The paper theorem should quantify over PMT-A skeletons. The Lean result covers
   them because (i) upper bounds hold on the larger class and (ii) the extremizer has the given
   skeleton. Check that no paper sentence relies on arity-0 behaviour.
2. **Dimension quantifier.** A1 fixes finite-dimensional Hilbert spaces. Lean's upper bound covers
   all real inner product spaces, and its extremizer is 2-dimensional, so the paper's `sup`
   equals the Lean `sup`. A reviewer should confirm the two-line argument in the A7 row.
3. **Universe.** `heterogeneous_multispace_sSup` ranges over spaces in `Type` (universe 0).
   `heterogeneous_multispace_upper` is universe-polymorphic. No mathematical content depends on
   this.
4. **Defect bookkeeping.** In `MSTree.dshape` and `SPMTree.dshape` the defect is `ρ/M`, and Lean
   defines `ρ/0 = 0`. This matters only when `M_v = 0`, where `err = 0` and `Λ_T = 0`, so the
   `sSup` statement (`Λ_T > 0`) never sees it.
5. **Error definition.** `err` uses the projected root error `E^P`. The ambient error `E^amb` and
   the `E^N` component are not formalized.
6. **Wording.** The formal-verification paragraph may now say that the heterogeneous theorem,
   the scaling reduction and the common-ambient-space reduction are formalized. Correspondence
   of definitions (this document) is an agent audit and still needs an attributable human review.

## 4. Build evidence

```bash
lake build
```

```bash
lake env lean AxiomsCheck.lean
```

Key elaborated statements are recorded in `BUILD_LOG.md`.
