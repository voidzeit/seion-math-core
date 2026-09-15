# Certified Adaptive Tensor Compression (CATC) — SharpTensor 0.1 specification

```
STATUS:   SPECIFICATION v1, 2026-09-15 (implemented in research/pmt_program/sharptensor, CPU)
CONTRACT: ../paper/APPLICATIONS_BOUNDARY.md (Levels A/B/C); this document is Level B (application bridge)
LEAN:     research/pmt_program/lean — 8732 jobs, 66 #print axioms within [propext, Classical.choice, Quot.sound]
RESULTS:  benchmarks/results/BENCHMARK_REPORT_v1.md (preregistered; TRL4 criterion not met)
```

## 1. Algorithm class

**Contract-then-truncate tree computations.** Every internal node computes

`y_v = μ_v(R_{c_1}, …, R_{c_m})`,  `R_v = P_v y_v`,

with `μ_v` multilinear and `P_v` an exact orthogonal projector chosen from the data (trajectory form).
The root is not truncated. Covered instances:

- evaluation and contraction of tree tensor networks with intermediate rank truncation;
- HT/TT arithmetic (sums, operator application) with rounding;
- MPO→MPS application with bond truncation.

**Excluded:** TT-SVD or HT-SVD of a given dense tensor. It is not a tree of multilinear laws, and
classical quasi-optimality bounds apply to it (Oseledets; Grasedyck). SharpTensor may use HSVD only to
*construct inputs*.

## 2. Map 1 — node → (μ_v, P_v, M_v, ρ_v, K_v)

Values are held in canonical factored form `R = Q S` with `Q` an isometry (explicit, or implicit as
nested cores), so every norm and singular value of `y_v` is computed from a small local matrix.

| model | `μ_v` | `P_v` | `M_v` bound (method) | slot operator norms `K_op` |
|---|---|---|---|---|
| matrix-product tree | `(XY + sYX)/(1+|s|)` | `U_r U_rᵀ` (left) | `1` (analytic, Frobenius submultiplicativity) | `‖R_other‖₂` (analytic `‖XA‖_F ≤ ‖X‖_F‖A‖₂`) |
| MPO→MPS chain | contraction `L·W_k` over one bond | top-`r` singular subspace | `1` (analytic, Cauchy–Schwarz) | `‖mat(W_k)‖₂` for the environment slot |
| HT arithmetic | `(U_l ⊗ U_r) B_v` | `U_r U_rᵀ` on the node matrix | `‖B_v‖₂` (spectral norm of the transfer matrix) | exact `‖x ↦ (x ⊗ R_other) B_v‖` via the isometric reduction |
| generic core `C_v` | `C_v · (x_1 ⊗ ⋯ ⊗ x_m)` | any exact orthogonal projector | `‖mat(C_v) : ⊗H_i → H_v‖₂` (default); `‖C_v‖_F` fallback; `1` for pure `x ⊗ y` | spectral norm of the contracted slot matrix |

`M_v` must be a *global* bound (`‖μ_v‖ ≤ M_v`). The multilinear norm itself is not computed.

## 3. Map 2 — discarded singular values → defects

For node `v` with local singular values `σ_1 ≥ σ_2 ≥ …` and kept rank `r_v`:

- absolute residual: `d_v = √(Σ_{j>r_v} σ_j²)` (Frobenius; the spectral `σ_{r+1}` is **not** the PMT defect);
- relative trajectory defect: `ρ_v = d_v / ∏_i ‖R_{c_i}‖` (`ρ_v = 0` if a child is zero, which forces `d_v = 0`);
- normalized defect: `η_v = ρ_v / M_v`.

Both `d_v` and `∏_i ‖R_{c_i}‖` are stored in the certificate.

## 4. Map 3 — ranks → (memory, FLOPs, η)

- **Memory:** bytes of the stored canonical factors (cores and remainders), measured from the actual arrays.
- **FLOPs:** counted by instrumentation. A product `a×b` by `b×c` counts `abc`; QR of `m×n` counts
  `2·max·min²`; SVD counts `4·max·min²`. These are counts, not hardware counters. Wall-clock time is
  also recorded.
- **η(r):** estimated from a full-rank pilot (§6). Actual `η` is measured after execution.

## 5. Certificates (all computed after execution; the minimum is reported)

| certificate | formula | Lean | requires |
|---|---|---|---|
| Theorem R trajectory | `E_R = Λ_T · U_gBox(η)`, `Λ_T = ∏ M_v ∏ ‖z_ℓ‖` | `heterogeneous_scaled_upper_of_admTC_nonneg`, `gBox_eq_capped`, `gBox_le_sum` | exact leaves, exact orthogonal `P_v`, untruncated root |
| compact amplitude | `A_v = d_v + M_v(∏(‖R_i‖ + A_i) − ∏ ‖R_i‖)`, `A_ℓ = dev_ℓ` | `ATree.err_le_abound`, `sum_slot_prod_eq` | any local deviation `d_v` |
| slotwise | `S_v = d_v + min_order Σ_k K_k S_{order[k]}` | `KTree.err_le_sbound`, `slot_const_general`, `slot_args_eq_update` | any local deviation; `K_k = min(K_gen, K_op if the prefix is exact)` |

- **`U_gBox`:** the certified 1-D enclosure (H3), with interval arithmetic and an audited rounding
  direction, intersected with `Σ η`.
- **Relative bound:** `E / (‖R_r‖ − E)`, or `VACUOUS` when `‖R_r‖ ≤ E`.
- **Slot order:** every permutation of a node's slots is an equivalent multilinear law, so the best
  telescoping order is used (all orders for arity ≤ 4).

**Certificate record (JSON):**

- theorem and Lean declaration names; tree hash;
- arithmetic model (float64 treated as exact);
- `M_v` and `K_op` methods and whether each is rigorous;
- `M`, absolute residuals, `ρ`, `η`, `Λ_T`;
- `gbox_lower`, `gbox_upper`;
- the three bounds, the best one, and relative bounds;
- measured error and soundness flag when a dense reference is available (benchmarks only).

`verify()` recomputes everything from the run record.

## 6. Planner

1. **Pilot** at full rank: singular values and child-norm products give `η_v(r)` and `c_v(r)`.
2. **Stage A (additive DP):** minimize `Σ c_v(r_v)` subject to `Λ_T Σ η_v(r_v) ≤ ε`; weights are
   rounded up (conservative knapsack).
3. **Stage B (sharp refinement):** greedy reductions while `Λ_T · gBox_float(η) ≤ ε`. Pruning by
   `gBox_mono`.
4. **A posteriori loop:** execute, certify; if the bound exceeds `ε`, raise the rank at the largest measured `η_v`.
5. **Certified search** (small models): greedy reductions from full rank, each accepted only after
   execution and certification with the best certificate.

The planner never certifies. The returned configuration is the cheapest *found* among those whose
executed certificate meets `ε`. It is not the true optimum and not optimal with respect to the actual
error.

## 7. Backends

- **numpy (reference):** `models.py`, with dense exact references for validation.
- **PyTorch:** `torch_backend.CertifiedMpoMpsApply`, a module that runs on any device, emits the same
  `Run` record and supports backward through `torch.linalg.svd`.
  - Validated on CPU against numpy (identical certificates).
  - **Not** validated on CUDA in this repository (blocker B-0012).
  - Kernel floating-point error is not certified (V1 experimental).

## 8. Validation (tests/research_sharptensor, 58 tests)

- **gBox evaluator:** closed form `C_3`; 40-digit brackets on edge cases (`η = 0`, `1`, `> 1`, near 1,
  `1e-12`); monotonicity; `≤ Σ η`; agreement with box multistart.
- **Synthetic trees:** arity 1–3, perturbed and exact nodes, approximate leaves, zero child, zero law,
  deep unary chain, orthogonal projections. `actual ≤ S ≤ A`.
- **Models:** soundness at several ranks; residual equals the dense `‖y − Py‖` with `P² = P = Pᵀ`;
  the MPO includes the identity; the HT sum representation is exact.
- **Planners** meet `ε`. **Torch CPU** matches numpy; backward runs.

## 9. Benchmark outcome (preregistered, v1)

| id | memory ratio | FLOPs ratio | non-vacuous | bound/actual (best) |
|---|---|---|---|---|
| B1a matrix-product tree | 1.27 (vs factored; worse than dense, post hoc) | 1.13 | yes | ~1e4 |
| B1b cancellation control | 1.01 | 1.01 | yes | 139 |
| B2 MPO→MPS | 1.00 at δ = 0.01 (1.02 at δ = 0.1) | 1.00 | yes | 79 (δ = 0.1) |
| B3 HT arithmetic | **3.20** | **2.01** | yes | **2.42** |

The TRL4 criterion (S1 ∧ S2 ∧ S3 for B1a, B2, B3) is **not met**.

## 10. Roadmap for this component

1. **Chain-aware slot constants** for MPO→MPS: environment-weighted `K_k` in canonical form. Needs a
   new preregistration.
2. **CUDA validation** once B-0012 is cleared; first a CPU/GPU agreement canary.
3. **V2:** approximate-projector and floating-point robustness. The `KTree` certificate already
   propagates any *certified* local deviation, so the remaining work is certifying `d_v` for
   floating-point kernels.
4. **V3:** quantization through certified local deviations (`KTree`), not through Theorem R.
5. KGE ranking plugin, after the score-error bridge (APPLICATIONS_BOUNDARY §8).
