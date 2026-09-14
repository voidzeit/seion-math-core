# Changelog: Theorem R v1 → v2

v1 is frozen in `../theorem_R_v1/` (source commit `f80f4e8`, manifest
`FREEZE_v1.json`). v2 is a from-scratch rewrite into one canonical source,
`THEOREM_R_v2.md`.

## Mathematics: unchanged

No lemma of v1 was found false. The upper-bound argument (O2, tensor angle
inequality, Lemma 3, root reading, scalar step) is the same. The lower-bound
construction is the same complex-multiplication family.

## Changes

1. **Terminology.** `k` is the number of internal nodes, not depth. Wording that
   called it depth in older program notes is not carried over.
2. **One canonical source**, in dependency order: Definitions → O2 → Tensor
   angle lemma → Lemma 3 → Multiplicative envelope → Diagonal Lemma → Upper
   bound → Universal sharp witness → Theorem R.
3. **Diagonal Lemma split into three lemmas.**
   * Lemma 6.1 (subadditivity) carries the explicit hypothesis
     `Σθ_j ≤ π/2`.
   * Lemma 6.2 is Jensen for `log cos`.
   * Lemma 6.3 is stated as an equality of maxima, with the case split at
     `Θ = π` kept.
   * v1 Lemma G proved `R ≥ cos Θ` for `Θ ≤ π` in one step; v2 separates
     `Θ ≤ π/2` (Lemma 6.1) from `Θ ∈ (π/2, π]` (trivial).
   * The counterexample showing the split is necessary for `Θ > π` is recorded
     (`outputs/diagonal_lemma_check.json`).
4. **Witnesses separated and named.**
   * `UNIVERSAL_SHARP_WITNESS` (Theorem 8.1) is written as a standalone theorem
     for an arbitrary tree, with the explicit induction for `F_v = e^{iΦ_v}` and
     `R_v = A_v`.
   * Root variant `P_r = I` with plain complex multiplication (defect 0). v1
     used a real reader `Re(λ·)` at the root; both are valid.
   * `ASYMPTOTIC_WITNESS` (§8.3) is the historical `|sin((k−1)θ)|` family, with
     its leaf-closure defect and the correction noted, and the exact identity
     `|1 − w^n|² = sin²(nθ) + (cos^nθ − cos nθ)²` showing it is dominated.
5. **Multiplicative envelope** (§5) made explicit: every non-root internal node
   contributes exactly one factor, `k − 1` in total. It is not called a monoid
   isomorphism.
6. **`∏ρ_i = 0`** handled as a separate case in Lemma 4.2 (no hidden division),
   with the explicit formula `sin θ_v = ‖Q_vμ_v(R_c)‖/∏ρ_i` otherwise.
7. **`η = 0`** stated as outside PMT-A.
8. **Degenerate-case index** (§10). New controls: `edge_cases_v2.py` (8000 cases,
   tiny `η`, explicit `‖F‖ < 1`), `sharp_witness_check.py` (4000 random trees,
   exact attainment), `diagonal_lemma_check.py`, `asymptotic_vs_sharp.py`.
9. **Formalization targets** (§12): only the Diagonal Lemma and the witness
   evaluation are proposed for Lean; statements listed, unchecked (no toolchain).
10. **Reviewer questions** (§13) for a functional-analysis referee.

## Correction to an external suggestion recorded here

A proposed simplification claimed `R = ∏cos θ_j ≥ cos Θ` for all `Θ` when
`θ_j ∈ [0, π/2]`. It is false (`n = 4`, `θ_j = π/2 − ε`). v2 keeps the case
split.
