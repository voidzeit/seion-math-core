# Hostile author-side audit of the Theorem R proof, v1

Date: 2026-09-13. Object: `REVIEW_PACKAGE_v1.md` and its source
`THEOREM_R_DRAFT.md @ f80f4e8`.

**This is not an independent review.** The auditor is the author of the draft.
The audit looks for hidden hypotheses, divisions by zero and boundary
failures, and records what it found and what it could not establish.

## 1. The four danger points

| # | step | package location | finding |
|---|---|---|---|
| 1 | (N−) ⟹ domination | Lemma B | Correct with the explicit hypothesis `S ∈ [0,π]`. The draft left the reduction of (N−) to `G_12 + μ ≥ cos S` implicit; the package now derives it, including `1 − G_11 = 0` or `1 − G_22 = 0`. Only the sign sector `ab ≤ 0` is used, and it is exactly what Theorem T supplies. |
| 2 | tensor angle induction | Theorem T | Correct. Three points were implicit in the draft: (a) `Π` must be 2-dimensional even when `u_1 = v_1` or `dim H_1 = 1` (handled by an isometric embedding); (b) the angle bound for `Rot ⊕ I` needs `⟨x, Rot x⟩ = ‖x‖² cos ψ_1` for `x ∈ Π`; (c) the inductive hypothesis is needed for all `αβ ≤ 0`, not only one ratio. All three are written out. |
| 3 | child substitution / closure normalization | Lemma C | Correct. The normalization divides by `ρ = ∏ρ_i` and uses `‖R_{c_i}‖ ≤ ρ_i`. The draft said "if `ρ = 0` the claim is trivial"; the package proves `R_v = 0` in that case (Lemma C(iv)) and gives the explicit domination `K(0,0)` in Lemma D. Only closure along the trajectory `R̂_i` is used. |
| 4 | angle count at the root | Lemma F | Correct: exactly one `θ_u` per non-root internal vertex, by disjointness of the root's subtrees (a tree property; it would fail for DAGs). The monotone replacement `S ≤ Θ` needs `ρ ≥ 0` and `min(·,π)` on both sides; both are stated. |

## 2. Edge-case checklist

| edge case | where handled | status |
|---|---|---|
| degenerate dimensions (`dim H = 1`, collinear `u_i = v_i`) | Theorem T reductions; Lemma A (2-dim `X`, extension by 0) | handled |
| `R_v = 0` | Lemma D case `ρ = 0`; step 6 (`R̃ = 0`) | handled |
| `ρ_i = 0` (a leakage angle `π/2`, needs `η = 1`) | Lemma C(iv), Lemma D, Lemma G | handled |
| angles `ψ = 0` and `ψ = π` | Lemma A (singular `K`), Lemma B (`S = 0`), Theorem T (`S ≥ π` trivial) | handled |
| `η = 1` | Lemma G (`θ_j = π/2`, `ρ = 0`, left side `1 = |1 − w(π/2)^n|²`) | handled |
| arbitrary arity, including `m = 0` | Lemma D (`m = 0` branch), Theorem T (all `m`), N2 | handled |
| projector rank `0` or full | nothing divides by `‖P_v g‖`; `θ_v = arcsin‖Q_vg‖` ranges over `[0, arcsin η]`; `R̃ = 0` branch covers rank 0 | handled |
| angle sums `> π` | `min(·,π)` in the domination, Lemma E and Lemma F; Lemma G case `Θ > π` | handled |
| equality / saturation | Theorem U attains the bound; Theorem T is sharp for `S ≤ π` | consistent |
| mixed leaf and internal children | N2 (leaf freezing preserves norm and gives (TC)) | handled |
| `k = 1` | Theorem R proof (`E^P_T = 0`) | handled |
| unit-leaf normalization with zero leaves | excluded by PMT-A (`z_ℓ ≠ 0`) | by definition |

## 3. Numerical edge-case run (`edge_cases.py`)

6 000 vertex cases, each evaluated at the **proof angle**
`sin θ* = ‖Q μ(R)‖/∏ρ_i` (O2 domination) and at the root bound:

| family | count |
|---|---|
| `m = 0 / 1 / 2 / 3` | 1570 / 1478 / 1506 / 1446 |
| projector rank 0 | 1412 |
| projector full rank | 1527 |
| `η = 1` | 1993 |
| `ρ_in = 0` | 417 |
| `Σχ_i ≥ π` | 1517 |
| child contractions | identity, zero, rank one, orthogonal |

Results: largest O2 violation `4.4·10⁻¹⁶`, largest root-bound violation
`2.2·10⁻¹⁶`, `θ*` never outside `[0, arcsin η]`, **0 violations**
(`outputs/edge_cases.json`).

## 4. Findings summary

* **No mathematical error found.**
* **Presentation gaps in the source draft, all made explicit in the package:**
  1. the quadratic-form derivation in Lemma B;
  2. the 2-dimensional embedding in Theorem T;
  3. the rotation angle identity;
  4. the `ρ = 0` branch;
  5. the `R̃ = 0` branch;
  6. the `θ_j = π/2` and `Θ > π` cases of the scalar step.
* **Draft claims deliberately removed from the package's theorem:**
  1. the complex-field upper bound (plausible by realification, but not
     reviewed here);
  2. the DAG extension, which Lemma F's disjointness shows does not follow
     verbatim.

## 5. What this audit cannot establish

* Independence: the same person wrote and audited the proof.
* Novelty: a literature comparison (projective tensor norms, scaled relative
  graphs, contractive dilations) has not been done.
* That PMT-A is the right class for the intended applications.

## 6. Requested reviewer profiles

* **Functional analysis / tensor norms / operator theory:** Theorem T, Lemma B,
  and the dilation steps in Lemma D.
* **Numerical analysis / tensor approximation:** the class PMT-A, leaf freezing
  (N2), the closure hypothesis and its interpretation, and Lemma F.
