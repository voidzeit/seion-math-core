# Lemma 3 falsification campaign

Date: 2026-09-13. Branch `research/pmt-sharp-program`, on top of checkpoint
`d51dff6`. Status of every result here: `NUMERICAL_OBSERVATION`. The campaign
was designed to find a counterexample, not to confirm.

## Target

For a multilinear **non-root** vertex with internal children `c_1,…,c_m`:

```
s_i ≼ z_i  (all i)     ⟹     s_out ≼ w(θ) ∏ z_i   for some θ ∈ [0, arcsin η],
```

with `z = ρe^{iχ}` a chain datum (`ρ = ∏cos θ_j`, `χ = Σθ_j`) and two candidate
orders on vertex states `s = Gram(F,R)` (`a = ‖F‖`, `r = ‖R‖`, `c = ⟨F,R⟩`,
`ψ = ∠(F,R)`):

| order | definition |
|---|---|
| **O1** (proposed) | `a² + λ²r² − 2λar cos(min(ψ+φ,π)) ≤ 1 + λ²ρ² − 2λρ cos(min(χ+φ,π))` for all `λ ∈ [0,1]`, `φ ∈ [0,π]` |
| **O2** (dilation) | `Gram(F,R) ⪯ K(ρ,ψ') := [[1, ρcos ψ'],[ρcos ψ', ρ²]]` for some `ψ' ∈ [0, min(χ,π)]`; equivalently `(F,R)` is a contraction image of a unit chain pair |

`experiments` = `research/pmt_program/lemma3/`; outputs in `lemma3/outputs/`.
Real field; laws `(ℝ²)^m → ℝ⁴`; projector ranks 1–3; closure enforced along the
reduced trajectory (the larger class); law norms certified from above on grids
(`states.py::opnorm`, grid-spacing Lipschitz margin) before evaluation.

## Stage 1 — random sampling (`falsify_random.py`)

Children dominated in the order under test (O2: contraction images of chain
pairs, with identity/rank-deficient/near-singular contractions; O1: uniform
`(a,r,ψ)` filtered by O1). Laws: Gaussian, phase witness + noise, rank one,
Hilbert tensor embedding. Every flagged case is written with children chain data,
child states, law tensor, projector rank, `η`, the minimizing `θ` and `(λ,φ)`.

| order | m | η ∈ | cases per η | flagged | confirmed after replay |
|---|---|---|---|---|---|
| O1 | 1, 2 | 0.1, 0.3, 0.6, 0.9 | 20000 | 1 | 0 |
| O1 | 3 | same | 3000 | 0 | 0 |
| O2 | 1, 2 | same | 20000 | 79 | 0 |
| O2 | 3 | same | 3000 | 0 | 0 |

Total 344 000 cases. **All 80 flagged cases were artifacts of the 41-point θ
grid.** Replay (`replay_violations.py`) with the proof angle
`sin θ* = ‖Q μ(R)‖/∏ρ_i`, a 4001-point θ grid and a finer certified norm
removes every one (largest replayed value `2.2·10⁻¹⁶`). At `θ*` alone, the O2
violation over all O2 runs is `≤ 1.7·10⁻¹³`. The domination is **tight**, which
is why a coarse θ grid produces false alarms. The drivers were then patched to
always include `θ*`.

Lemma 2 (root reading `‖μ(F) − μ(R)‖ ≤ |1 − ∏z_i|`) was checked on the same
cases: 0 violations (largest `2.2·10⁻¹⁶`).

## Stage 2 — adversarial local optimization (`falsify_adversarial.py`)

Minimize the signed domination margin (negative = counterexample) over child
chain angles, child states inside the order's dominated set, the law and the
projector rank; Powell then Nelder–Mead, 4 restarts; final value with the
certified norm.

| order | m | η | min margin over restarts |
|---|---|---|---|
| O1 | 1 | 0.3 / 0.9 | 0.107 / −8.9·10⁻¹⁶ |
| O1 | 2 | 0.3 / 0.9 | 0.328 / 3.8·10⁻⁴ |
| O1 | 3 | 0.3 / 0.9 | 0.805 / not completed |
| O2 | 1 | 0.3 / 0.9 | −2.2·10⁻¹⁶ / −8.9·10⁻¹⁶ |
| O2 | 2 | 0.3 / 0.9 | 0.0 / 5.0·10⁻⁷ |
| O2 | 3 | 0.3 / 0.9 | 0.0 / not completed |

O2 is driven exactly to its boundary (margin `0` to rounding) and never beyond.
The O1 optimizer, which must also keep the children O1-dominated through a
penalty, reaches the boundary only at `m = 1`; for `m ≥ 2` it is a weaker test.

## Stage 3 — near-global test of the analytic core (`tensor_angle_lp.py`)

In order O2, Lemma 3 reduces (see `THEOREM_R_DRAFT.md` §3) to the **tensor angle
inequality**

```
‖u_1⊗⋯⊗u_m − t·v_1⊗⋯⊗v_m‖_π ≤ |1 − t e^{i min(S,π)}|,   S = Σ∠(u_i,v_i).
```

For fixed data the real projective norm is the value of a linear program over
`m`-linear forms of norm `≤ 1`, solved by cutting planes (a separation oracle
maximizes the form's norm on a grid with local refinement).

| m | cases (random unequal angles, `t ∈ [0,2]`) | max (LP upper − bound) | max (admissible lower − bound) |
|---|---|---|---|
| 2 | 120 | 1.6·10⁻⁷ | −8.6·10⁻⁵ |
| 3 | 80 | 5.2·10⁻⁸ | −5.5·10⁻³ |
| 4 | 12 | 4.2·10⁻⁸ | −4.6·10⁻⁴ |

The LP upper estimate never exceeds the bound beyond discretization, and the
bound is attained (complex-multiplication form), i.e. the inequality is sharp.

## Stage 4 — end-to-end trees (`random_trees.py`)

3 000 random trees, `k = 2…6`, internal arities `≤ 3`, phase-witness laws with
noise `{0, 0.02, 0.1, 0.5}`, trajectory closure only, heuristic norm (alternating
maximization × 1.02). `max (E^P/η)/C_k(η) = 0.99940`; no tree above `C_k`.

## Relationship between the orders (`order_relation.py`)

40 000 samples: **O2 ⟹ O1** in every case (largest O1 violation of an O2 state
`5.8·10⁻¹⁴`), while 2 642 O1-dominated states (6.6%) are **not** O2-dominated
(violation up to 0.376). So O1 is strictly weaker. O2 is the stronger induction
hypothesis and the one that closes.

## Outcome

* **No counterexample** to Lemma 3 in either order.
* The binary outcome is **"order survives"**, and the surviving order O2 has an
  analytic proof draft of Lemma 3 for every arity, which with Theorem U gives
  Conjecture R: `THEOREM_R_DRAFT.md` (`ADVISORY_PROOF_DRAFT`, separate from this
  campaign).
* O1 is not refuted, but it is not needed and was probed less sharply for `m ≥ 2`.
* Not done: complex field; `m ≥ 4` beyond the 12 LP cases; exact (rational)
  certificates for the tensor angle inequality.
* Incomplete runs retained as such: the complex first-order field computation
  (`experiments/first_order_field.py`, C) hit its 3000 s timeout without output;
  the first launch of the two `m = 3, η = 0.9` adversarial runs exited without
  output and was relaunched (addendum).

## Addendum

The relaunched `m = 3, η = 0.9` adversarial runs (O1 and O2, 2 restarts) were
killed by their `timeout` (exit 124) before writing a result. The `m = 3,
η = 0.9` cell therefore has random-sampling coverage (3000 cases, 0 violations)
but **no adversarial coverage**. The m = 3 objective (256² norm grid per
evaluation, 33 parameters) is too slow for local optimization in this budget; a
gradient-based or GPU implementation is needed to close that cell.
