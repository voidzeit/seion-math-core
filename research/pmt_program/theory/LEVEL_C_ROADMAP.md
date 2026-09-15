# Level C roadmap — theory beyond Theorem R

```
STATUS:  2026-09-15. Research plan with precise target statements. Nothing below is claimed unless it
         is marked PROVED (Lean) and names its declaration.
BASE:    Theorem R (sharp, class-wide) + H3 (1-D gBox) + a posteriori certificates
         ATree.err_le_abound, KTree.err_le_sbound (instance-wise, any local deviation).
```

## C1. Amplitude-aware certification — PARTLY PROVED

**Proved (Lean):**

- compact bound `A_v = d_v + M_v(∏(‖R_i‖ + A_i) − ∏‖R_i‖)` (`PMT.ATree.err_le_abound`);
- slotwise bound `S_v = d_v + Σ_i K_i S_i` (`PMT.KTree.err_le_sbound`), with slot constants from
  `slot_const_general` or `slot_args_eq_update`;
- identity `Σ_i a_i ∏_{j<i}(r_j + a_j) ∏_{j>i} r_j = ∏(r + a) − ∏ r` (`PMT.sum_slot_prod_eq`).

**Measured** (BENCHMARK_REPORT_v1): slotwise bound/actual ≈ 2.4 on HT arithmetic, ≈ 80 on MPO→MPS,
≈ 1e4 on the matrix-product tree.

**Open targets:**

1. **Robust slot constants.** `K_i^rob = sup_{‖F_j − R_j‖ ≤ S_j, j<i} ‖x ↦ μ(F_{<i}, x, R_{>i})‖`.
   For bilinear laws, `K^rob ≤ K_op(R) + M·S_prev` (triangle inequality in the slot map). This is a
   lemma to formalize, and it would replace the product fallback for the second slot.
2. **Order optimisation** is already used in software (all permutations for arity ≤ 4). A Lean lemma
   `err_le_sbound` for permuted slot orders (via `domDomCongr`) would make the choice formal. The
   software currently relies on the fact that a permuted law is again a multilinear map, a paper-level
   argument.
3. **Chain environments** (MPO→MPS). Error at step `k` is propagated only by the *future* contractions
   restricted to the discarded direction. Target: `e_N ≤ Σ_k d_k · ‖E_{>k}‖`, with `E_{>k}` the
   right-environment operator norm computed in canonical form. This is the engineering blocker for TRL4.
4. **Sharp a posteriori theory.** Is there a Theorem R–type sharp constant when `‖R_v‖` are observed?
   Open; no conjecture yet.

## C2. Approximate projectors / floating point — REDUCED TO C2'

The slotwise certificate does not need `P_v` to be a projector: it propagates the measured
`d_v = ‖μ_v(R_children) − R_v‖`. What remains is to certify `d_v` under floating point:

**C2' target:** for a floating-point SVD truncation returning `R̃_v`, obtain a rigorous upper bound
`d̄_v ≥ ‖μ_v(R̃_children) − R̃_v‖`, computed from the backward error of the SVD, rounding bounds of the
contraction kernels, and the norms of the stored factors.

A sharp perturbative Theorem R (`E ≤ Λ_T gBox + Φ(δ_idem, δ_sym)`) is a separate, optional target.

## C3. Mixed precision / quantisation — REDUCED TO LOCAL BOUNDS

Quantize-after-compute, `R_v = Q(y_v)`, is covered by the slotwise certificate if
`‖y_v − Q(y_v)‖ ≤ q_v` is certified. For uniform quantisation with step `h` per entry and `n` entries,
`q_v ≤ (h/2)·√n` (deterministic rounding), or computed exactly from the stored codes. The range
obstruction of Theorem R disappears in this route.

Remaining work: rigorous bounds for kernels that compute *in* FP16/FP8 (not only quantizing their
outputs). Error analysis of GEMM and convolutions under IEEE arithmetic is a separate body of work.

## C4. KGE ranking bridge — TARGET STATEMENTS

- **Score-error lemma** (elementary; to formalize): for bilinear or trilinear scores
  `s(h, r, t) = β(h, r, t)` with `‖β‖ ≤ B`, representations with certified errors
  `‖h̃ − h‖ ≤ ε_h`, etc., give `|s̃ − s| ≤ B[(‖h‖ + ε_h)(‖r‖ + ε_r)(‖t‖ + ε_t) − ‖h‖‖r‖‖t‖]`. This is
  the compact bound again, applied to one node.
- **Ranking lemma:** `s(x⁺) − s(x⁻) > ε₊ + ε₋ ⇒ s̃(x⁺) > s̃(x⁻)`.
- **Filtered MRR / Hits@K:** preserved for a query if the gap to *every* relevant competitor exceeds
  the sum of the two bounds.
- **Evaluation protocol:** train-only negative filtering (repository blocker B-0014); no use of the
  training margin as a gap.

## C5. Gradient compression — OUT OF SCOPE UNTIL C1–C4

Even a certified `‖g̃_t − g_t‖ ≤ ε_t` requires an inexact-optimization theorem (smoothness, step sizes,
`Σ ε_t` control, optimizer state) before any convergence statement.

## C6. PMT-A[C] (complex field)

Upper bounds transfer, but lower bounds for skeletons with a vertex having ≥ 2 internal children are
not established over ℂ (blocker PMT-FIELD-C). Paper statements stay over ℝ.
