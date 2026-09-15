# Applications boundary — heterogeneous Theorem R

```
STATUS:  FROZEN 2026-09-15 (application contract; changes only by explicit revision entry)
RULE:    no application claim may exceed what is proved; every claim names its level (A/B/C)
PAIR:    STYLE_CONTRACT.md governs the paper; this file governs applications, products and talks
LEAN:    research/pmt_program/lean (Lean 4.33.1, Mathlib), 8729 jobs, 52 #print axioms = standard only
```

## Purpose

This document defines the allowed interpretation of the heterogeneous Theorem R in engineering,
tensor computation, machine learning and HPC applications. It exists to keep application claims
from exceeding what is mathematically proved.

## 1. Core certified statement

Let `T` be an admissible projected multilinear tree (class PMT-A with nodewise budgets). Assume:

- **Local operator bounds:** `‖μ_v‖ ≤ M_v`.
- **Local projection defects:** `‖(I − P_v) μ_v(x)‖ ≤ ρ_v ∏_i ‖x_i‖`.
- **Normalized defects:** `η_v = ρ_v / M_v`.

Then the projected root error satisfies

`E_T^P ≤ Λ_T · gBox(η)`,  with  `Λ_T = (∏_v M_v)(∏_ℓ ‖z_ℓ‖)`  and

`gBox(η) = max_{0 ≤ θ_v ≤ arcsin η_v, v ≠ r} |1 − ∏_{v ≠ r} cos θ_v · e^{iθ_v}|`.

Over the admissible class, `sup E_T^P / Λ_T = gBox(η)`. The supremum is taken over realizations
with `M_v > 0` and nonzero leaves (`Λ_T > 0`), and with root defect `≥ 0`. The constant is sharp,
depends only on the multiset of normalized non-root defects, and is attained by a two-dimensional
realization.

Lean: `heterogeneous_scaled_upper_nonneg`, `heterogeneous_scaled_sSup`,
`heterogeneous_multispace_upper`, `heterogeneous_multispace_sSup`, `gBox_attained`,
`heterogeneous_placement_independent`.

## 2. What is already guaranteed (Level A)

### 2.1 Orthogonal truncation and projection trees

The theorem applies directly when the computation is `R_v = P_v μ_v(R_children)`, with `P_v` an
orthogonal projector and the local hypotheses verified. Natural candidates:

- hierarchical tensor contractions;
- Tensor Train style truncations;
- Hierarchical Tucker style truncations;
- tree tensor networks;
- reduced-basis computations;
- hierarchical low-rank approximation.

Applying it to a particular algorithm requires an explicit mapping from that algorithm to the PMT
definitions (Level B, §13).

### 2.2 Heterogeneous local tolerances

Different nodes may use different defects `η_1, …, η_n`. The global sharp constant is
`gBox(η_1, …, η_n)`, and no uniform local tolerance is required.

### 2.3 Certified fallbacks and monotonicity

For nonnegative defects: `gBox(η) ≤ Σ_i η_i ≤ n · max_i η_i`. Hence `E_T^P ≤ Λ_T Σ_i η_i`
(Lean: `gBox_le_sum`).

- **Monotonicity:** `η ≤ ξ` coordinatewise implies `gBox(η) ≤ gBox(ξ)` (Lean: `gBox_mono`).
- **Uniform fallback:** if every `η_i ≤ c` with `c > 0`, then
  `gBox(η) ≤ sup_{τ ∈ [0, arcsin c]} |1 − w(τ)^n|`, which is the uniform Theorem R constant at the
  largest defect (Lean: `gBox_le_uniform_fallback`).

### 2.4 Placement independence

For a fixed multiset of normalized non-root defects, the class-wide sharp constant is invariant
under permutation of the defects and under the combinatorial arrangement of the tree. This does
**not** imply that:

- the observed error of a particular computation is tree-independent;
- changing the tree preserves the local `M_v`, `ρ_v`, `η_v`;
- all contraction orders have equal computational cost;
- some tree position is "less sensitive". Differences between nodes enter only through `M_v`,
  `ρ_v(r_v)`, costs, or a posteriori amplitude information.

## 3. A posteriori trajectory certification (Level A, machine-checked)

For a concrete execution, the upper bound needs the projection defect only along the realized
reduced trajectory:

`‖(I − P_v) μ_v(R_children)‖ ≤ ρ_v ∏_i ‖R_i‖`.

This is weaker than requiring the inequality for every admissible input tuple. No closure is
required at the root.

Lean: `heterogeneous_scaled_upper_of_admTC` (`M_v > 0`) and
`heterogeneous_scaled_upper_of_admTC_nonneg` (`M_v ≥ 0`), with admissibility `SPMTree.RootAdmTC`
and `SPMTree.RootAdmTC0`.

Boundaries of this statement:

- **Operator norm.** `‖μ_v‖ ≤ M_v` is still required **globally**, not only on the trajectory. The
  exact multilinear operator norm of a tensor is hard to compute in general, so an application must
  use a certified upper bound (for example, a Frobenius norm of the node's coefficient tensor) and
  state which one.
- **Space.** The trajectory version is formalized in one ambient space. The per-vertex-space
  reduction (`CommonSpace.lean`) is formalized for full closure only.
- **Measurement.** For SVD truncation the natural measured quantity is the Hilbert (Frobenius) norm
  of the discarded part of the node tensor, `‖(I − P_v) A_v‖ = √(Σ_{j > r_v} σ_j²)`. This equality
  holds when `P_v` is the orthogonal projector `U_r U_r^* ⊗ I` on the corresponding
  matricization; the discarded **spectral** norm `σ_{r+1}` is not the PMT defect. The trajectory
  defect is `ρ_v = ‖(I − P_v) μ_v(R_children)‖ / ∏‖R_i‖`.
- **Exact arithmetic.** The theorem assumes exact projectors and exact singular values. A
  floating-point certificate is valid only modulo that assumption until an approximate-projector
  theorem exists (§10, Level C).

## 4. Certified adaptive tensor compression (Level B)

For each node `v`, a local rank `r_v` determines `η_v(r_v)` and a cost `c_v(r_v)`. The certified
allocation problem is

`min_{r} Σ_v c_v(r_v)`  subject to  `Λ_T · gBox(η_1(r_1), …, η_n(r_n)) ≤ ε`.

The result is **the cheapest configuration among those admitted by the certificate**. It must not
be described as the globally cheapest configuration with respect to the actual, unknown error
unless that stronger optimality is established independently.

## 5. Allocation strategy

Ranks and precision options are discrete, costs are not smooth, and `gBox` is not differentiable
where the active face of the box changes. KKT or Lagrangian stationarity conditions are therefore
not the primary allocator.

- **Stage A — additive certificate.** Minimize `Σ_v c_v(r_v)` subject to
  `Λ_T Σ_v η_v(r_v) ≤ ε`. This is separable, and with discrete choices it is a knapsack solvable
  exactly by dynamic programming.
- **Stage B — branch-and-bound.** Explore configurations the additive constraint rejects. Use the
  monotonicity of `gBox` for pruning.
- **Stage C — sharp refinement.** Accept a configuration if `Λ_T · U(η) ≤ ε`, where `U` is a
  **certified upper enclosure** of `gBox(η)` (for example `Σ η`, the uniform fallback, or a
  rigorously bounded numerical maximization).

Two rules for evaluating `gBox`:

- The capped equal-angle curve is only a **lower** bound for `gBox` while H3 is open. It must never
  be used to accept a configuration.
- Because `gBox ≤ Σ η`, the sharp condition can only enlarge the feasible set. For small defects
  the gain is second order (`gBox = Σ η + O(η²)`). The practical advantage appears at moderate
  defects or with many nodes.

## 6. Principal limitation: amplitude deflation

`Λ_T = (∏_v M_v)(∏_ℓ ‖z_ℓ‖)` can greatly exceed `‖F_r‖`. The PMT-TN benchmark V1 (34,192 runs)
observed exactly this: the bound was sound and sharp but vacuous in practice. Sharpness over the
class does not imply tightness for a particular numerical instance.

- **Valid a posteriori relative form.** Since `‖P_r F_r‖ ≥ ‖R_r‖ − E`, whenever `E < ‖R_r‖` the
  relative projected error satisfies `‖P_r F_r − R_r‖ / ‖P_r F_r‖ ≤ E / (‖R_r‖ − E)`, where `E` is
  the certified bound. This uses only computed quantities.
- **Acceptance criterion.** A compression product must report whether its certificate is
  non-vacuous (for example `E / ‖R_r‖ < 1` and the relative bound above) on preregistered
  benchmarks.
- **Required theory.** An amplitude-aware theory that replaces worst-case amplitude propagation by
  trajectory measurements is a principal requirement (Level C).

## 7. Mixed precision and quantization (Level C)

The current theorem does not certify FP16, BF16, FP8, INT8, stochastic rounding or other
quantization. A generic quantizer is `x̃ = x + ξ`, not `x̃ = P x` with `P = P* = P²`.

There is also a structural obstruction. If `R_v = P_v μ_v(R_children) + ξ_v` with
`ξ_v ∉ Ran P_v`, the child output no longer satisfies the range hypothesis of its parent, and the
propagation chain breaks at the first node.

Plausible extensions, each requiring its own theorem:

1. perturbations constrained to the retained range, `ξ_v ∈ Ran P_v`;
2. robust closure hypotheses allowing child inputs within a controlled distance of the retained
   range.

## 8. Knowledge graph embeddings (Level B, then C)

Use requires a bridge `PMT representation error → score error`. Suppose it yields
`|f̃(x) − f(x)| ≤ ε_x`. For a positive `x⁺` and a competitor `x⁻` with gap
`Δ = f(x⁺) − f(x⁻)`, the order is preserved whenever

`Δ > ε_{x⁺} + ε_{x⁻}`   (with a common bound: `Δ > 2ε`).

- If `ε = Λ_T gBox(η)`, a sufficient condition is `2 Λ_T gBox(η) < Δ`. It is **not**
  `gBox < γ/2`: the training margin `γ` does not imply this gap for every evaluated pair.
- Filtered MRR and Hits@K require the condition against **all** relevant competing entities of the
  query, each with its own `ε`.
- A per-query certified inference check is permitted once the score bridge is proved:
  1. compute the scores;
  2. take the gap `Δ_q` to the nearest relevant competitor;
  3. certify `ε`;
  4. report "order preserved" if `Δ_q` exceeds the sum of the bounds.
- Empirical gaps must come from models evaluated without held-out leakage (repository blocker
  B-0014).

## 9. Gradient compression (Level C)

The theorem does not imply convergence of Adam, AdaGrad, SGD or any optimizer under compressed
gradients. Even with `‖g̃_t − g_t‖ ≤ ε_t`, convergence needs a separate inexact-gradient analysis:
smoothness, landscape conditions, step-size schedule, accumulated compression error, stochastic
noise and optimizer state.

"The compressed optimizer converges exactly as the full-precision optimizer" is not permitted.

## 10. Formal verification boundary

Lean verifies that the stated theorem follows from the formalized definitions and assumptions. It
does not prove that:

- a CUDA implementation realizes the formal `μ_v`;
- a floating-point SVD implements an exact orthogonal projector;
- numerical libraries satisfy exact real-arithmetic assumptions;
- application data satisfy the PMT hypotheses;
- the reported `M_v` bounds are correct.

Certification chain:
`formal theorem → verified mathematical model → validated numerical algorithm → implementation`.

A needed bridge for floating-point SVD is a robustness theorem for approximate projectors with
small `‖P̃² − P̃‖` and `‖P̃ − P̃*‖` (Level C).

## 11. Allowed application claims

Allowed:

- Theorem R provides the sharp class-wide error constant for admissible tree-structured
  multilinear computations with orthogonal projection defects.
- The theorem provides a mathematical basis for heterogeneous local tolerance allocation in tensor
  compression.
- A certified rank allocator can minimize computational cost subject to the global Theorem R error
  constraint, and returns the cheapest configuration found among those the certificate admits.
- The additive bound is a simple certified fallback; `gBox` can give a less conservative
  class-wide certificate.
- For a concrete execution with exact orthogonal truncations, measured trajectory defects and
  certified operator-norm bounds yield a machine-checked-theorem-backed error certificate.

## 12. Claims requiring additional results (not currently allowed)

- Theorem R certifies arbitrary FP8 or INT8 computations.
- Theorem R determines the maximum possible tensor compression ratio.
- Theorem R guarantees preservation of KGE rankings from the training margin alone.
- Theorem R guarantees unchanged optimizer convergence under gradient compression.
- Lean verification of Theorem R certifies a production CUDA implementation.
- The sharp class-wide bound is tight for a concrete instance.
- Specific memory, bandwidth or scale figures (for example "100M entities in 14 GB",
  "80% less bandwidth") before a preregistered benchmark measures them. For reference, a dense
  `10^8 × 512` FP32 embedding matrix alone is about 204.8 GB.
- Any example certificate printout that is not produced by an actual run. Illustrative outputs
  must be labelled as illustrative.

## 13. Application hierarchy

**Level A — directly supported**

- orthogonal projected multilinear trees;
- heterogeneous truncation tolerances;
- sharp class-wide error certification;
- additive and uniform fallbacks, monotonicity;
- tree and placement invariance of the sharp constant;
- a posteriori trajectory certification in one ambient space, exact arithmetic.

**Level B — requires an application bridge**

- TT/HT adaptive rank allocation (formal mapping of the algorithm to `μ_v`, `P_v`, `M_v`, `ρ_v`);
- tensor-network contraction planning;
- compressed KGE scoring (score-error bridge);
- reduced-order engineering models.

**Level C — requires new mathematical theory**

- arbitrary mixed precision and non-orthogonal quantization;
- gradient compression convergence;
- approximate projectors and floating-point robustness;
- robust off-range perturbations;
- amplitude-aware relative certification;
- trajectory certification with per-vertex spaces.

## 14. Product staging (SharpTensor)

| Version | Scope | Mathematical basis |
|---|---|---|
| 0.1 / 1.0 | Certified orthogonal low-rank truncation of tree tensor computations: topology compiler, truncation instrumentation (`M_v` bound, measured `ρ_v`, `η_v`), allocator (§5), executor, certificate | Level A (§1–§3) plus the Level B mapping per decomposition |
| KGE plugin | Per-query certified inference ordering (§8) | Score-error bridge theorem |
| 2.0 | Approximate projectors and floating-point robustness | New theorem (§10) |
| 3.0 | Mixed precision and quantization | New theorem (§7) |
| later | Gradient compression, distributed training | Inexact-optimization theory (§9) |

Rules for V1:

- **Exclusions.** V1 excludes quantization, FP8, approximate projectors and gradient compression;
  these live under `experimental/` with no certificate claim.
- **Certificate contents.** A V1 certificate must record: theorem name and Lean commit; tree hash;
  the `M_v` bound method; measured defects; the `gBox` upper enclosure method; `Λ_T`; the certified
  absolute error; the a posteriori relative bound (§6); and the assumptions (exact orthogonal
  projectors, exact arithmetic).
- **Benchmark acceptance.** V1 must show, on preregistered benchmarks: reduced memory, reduced FLOPs
  or latency, and a **non-vacuous** certificate.

## Canonical application objective

**Minimize memory, FLOPs or rank subject to a rigorous global error certificate.** The current
theorem supplies the sharp worst-case propagation component of that system. It does not by itself
solve the application optimization problem.

## Revision 2026-09-15b (in force)

These revisions update the frozen text above. They are recorded here rather than rewriting the
original sections.

1. **H3 is a theorem.** `PMT.capped_equal_angle`, `PMT.gBox_eq_capped` and `PMT.gBox_eq_capped_max`:
   `gBox(η) = max_{τ ∈ [0, π/2]} |1 − ∏ w(min(arcsin η_i, τ))|`, attained on the water-filling curve.
   - The capped curve is therefore **exact**, not a lower bound.
   - §5 changes: a certified 1-D enclosure of `gBox` replaces multidimensional branch-and-bound.
   - The "open H3" limitations in §5, §13 and R1 are withdrawn.
2. **Instance-sensitive a posteriori certificates (Level A, machine-checked):**
   - `PMT.ATree.err_le_abound` (compact amplitude bound);
   - `PMT.KTree.err_le_sbound` with `PMT.slot_const_general` and `PMT.slot_args_eq_update`
     (slotwise bound).

   They do **not** require orthogonal projectors or range conditions. They propagate any measured local
   deviation `d_v = ‖μ_v(R_children) − R_v‖`. They are not sharp and are not part of Theorem R.
3. **§7 (mixed precision) reworded.** Theorem R still does not certify quantization. A quantized or
   floating-point computation *is* covered by the slotwise and amplitude certificates **provided each
   local deviation `d_v` is itself rigorously bounded**. The open problem moves from "propagation" to
   "certifying `d_v` for the numerical kernel" (Level C).
4. **Measured status of SharpTensor 0.1** (BENCHMARK_REPORT_v1): certificates sound in all runs; B3
   (HT arithmetic) non-vacuous at 3.2× compression with bound/actual ≈ 2.4; the TRL4 criterion is
   **not met** because B2 (MPO→MPS) admits no certified compression at δ = 0.01. Allowed:
   "prototype with preregistered benchmarks; certified non-vacuous compression demonstrated on HT
   arithmetic". Not allowed: "TRL4", or any memory or FLOPs claim beyond the report.
5. **Torch backend:** CPU-validated only. CUDA is blocked (B-0012); kernel roundoff is not certified.

## Revision log

| Date | Change |
|---|---|
| 2026-09-15 | Frozen from author draft, with these additions and corrections. §1: hypotheses of the `sup` statement and Lean names. §2.3: `gBox_mono`, `gBox_le_uniform_fallback`. §2.4: no "less sensitive position" reading. §3: marked machine-checked (`heterogeneous_scaled_upper_of_admTC[_nonneg]`); global operator-norm requirement; single ambient space; Frobenius vs spectral residual; exact-arithmetic caveat. §5: discrete allocator replaces KKT; certified upper enclosure; capped curve is lower bound; second-order gain. §6: a posteriori relative bound and non-vacuity criterion. §8: per-pair `ε_{x⁺} + ε_{x⁻}`, filtered ranking, leakage caveat. §12: unmeasured product figures and illustrative printouts. §14: SharpTensor staging. |
