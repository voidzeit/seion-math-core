# PMT-A — the canonical admissible class

Status: **FROZEN DEFINITION** (2026-09-13). Supersedes, for every sharp-constant
statement in `research/pmt_program/`, the scattered class declarations in
`CANONICAL_FORMALIZATION.md` §§1–6, `CANONICAL_W3_PROOF.md` ("Convention A",
class `free`) and `k4_exploration/CHAIN_GRAM_REPORT.md` §1. It does not rewrite
those historical files; it fixes one reference point that all new claims cite as
`PMT-A` (or `PMT-A[C]`, see A9).

Every sharp constant `C_T^P(η)` in Papers I–III means `C_T^{P}(η; PMT-A)` unless
the claim explicitly names another class.

---

## A0. Combinatorial data

`T` is a finite ordered rooted tree. `V_int(T)` are the internal vertices,
`L(T)` the leaves, `k = k(T) := |V_int(T)| ≥ 1`, root `r ∈ V_int(T)`.
Every internal `v` has ordered children `c_1(v),…,c_{m_v}(v)` with **arity
`m_v ≥ 1`**, and at least one leaf lies below every internal vertex.

*Remark.* `m_v = 1` (unary internal vertex) is allowed. It changes no constant:
a unary law `A` is the bilinear law `(x,ℓ) ↦ ⟨ℓ,e⟩A x` with one extra unit leaf,
and conversely freezing leaf slots (A5) turns any law into a law of lower arity.
The **internal skeleton** `sk(T)` is the rooted tree on `V_int(T)` obtained by
deleting leaves. All constants below depend on `T` only through `sk(T)`
(Lemma A5.2).

## A1. Spaces

Every vertex `w` carries a **finite-dimensional real Hilbert space** `H_w`.
Dimensions are arbitrary and may vary by vertex; they are *not* fixed in advance
(the supremum in A7 ranges over all dimensions).

## A2. Laws

Each internal `v` carries a multilinear map
`μ_v : H_{c_1(v)} × ⋯ × H_{c_{m_v}(v)} → H_v`
with the **multilinear operator norm**
`‖μ_v‖ := sup{‖μ_v(x_1,…,x_m)‖ : ‖x_i‖ ≤ 1}`
(supremum over products of unit balls — not a matricization or Hilbert–Schmidt
norm). **Laws are independently selectable at every vertex** (no weight
sharing, no symmetry, no associativity).

## A3. Projectors

Each internal `v` carries an **orthogonal** projector `P_v = P_v^2 = P_v^*` on
`H_v`, of arbitrary rank `0 ≤ rank P_v ≤ dim H_v`. `Q_v := I − P_v`.
Leaves carry the identity: `P̂_ℓ := I`, `P̂_v := P_v` for internal `v`.
Oblique projectors are excluded (they break `D ⊥ R`, the mechanism behind every
sharpening).

## A4. Evaluations and errors

Leaf data `z_ℓ ∈ H_ℓ` (ambient, unreduced). Ambient `F_ℓ = R_ℓ = z_ℓ`;
`F_v = μ_v(F_{c_1},…,F_{c_m})`, `R_v = P_v μ_v(R_{c_1},…,R_{c_m})`.
Errors: `E^amb_T = ‖F_r − R_r‖`, **`E^P_T = ‖P_r F_r − R_r‖`**,
`E^N_T = ‖Q_r F_r‖`, with `(E^amb)^2 = (E^P)^2 + (E^N)^2`.
The **root projects** (historical "Convention A").

## A5. Budgets

Fix `M > 0` and `0 < ρ ≤ M`; `η := ρ/M ∈ (0,1]`. A realization is
**`(M,ρ)`-admissible** iff for every internal `v`:

* (norm) `‖μ_v‖ ≤ M`;
* (projected closure) `ρ_v^proj := ‖Q_v μ_v(P̂_{c_1}·,…,P̂_{c_m}·)‖ ≤ ρ`,
  the multilinear norm of `Q_v μ_v` restricted to `∏_i Ran P̂_{c_i}` —
  **the whole product of projected subspaces**, including arbitrary vectors in
  leaf slots (A3: `P̂_ℓ = I`), not merely the evaluated trajectory.

`ρ` is a **budget**: defects need not saturate it. The root closure defect is
constrained like any other, although `E^P_T` never depends on it.

**Lemma A5.1 (scaling).** `E^P_T/(ρ M^{k−1} L_T)`, with `L_T := ∏_ℓ ‖z_ℓ‖`, is
invariant under `μ_v ↦ λμ_v`, `z_ℓ ↦ ν_ℓ z_ℓ`. Hence w.l.o.g. `M = 1`,
`ρ = η`, `‖z_ℓ‖ = 1`.

**Lemma A5.2 (leaf freezing).** Fixing the leaf arguments of `μ_v` at their
(unit) values yields a law on the internal-child slots with norm `≤ ‖μ_v‖` and
projected closure defect `≤ ρ_v^proj`; evaluations are unchanged. Conversely a
law on internal slots extends to any number of extra leaf slots via unit
coordinate gates `⟨ℓ,e⟩` without changing norm, defect or evaluation. So
`C_T^P(η) = C_{sk(T)}^P(η)`, where in the skeleton a vertex with no internal
child carries a fixed vector `f_v = μ_v(leaves)` with `‖f_v‖ ≤ 1`,
`‖Q_v f_v‖ ≤ η`, and every such vector is realizable.

## A6. Non-degeneracy

All leaves nonzero (a zero leaf gives `E^P_T = 0`).

## A7. The extremal constant

`C_T^P(η) := sup E^P_T / (ρ M^{k−1} L_T)` over all non-degenerate
`(M, ηM)`-admissible realizations of PMT-A on `T`, all dimensions, all ranks.
`C_T^P(η)` is a supremum over the whole class; statements for fixed dimensions
or ranks are different (with all `P_v = I`, `E^P_T = 0`).

Absolute form: `G_T(η) := η C_T^P(η) = sup E^P_T` at `M = L_T = 1`.

## A8. What is *not* in PMT-A (each is a different problem)

| excluded variant | why separate |
|---|---|
| same-law / weight-shared laws | tagging constructions needed; M21–M23 |
| fixed dimensions or ranks | quantifier change (A7) |
| ambient closure `ρ^amb` | strictly stronger hypothesis |
| trajectory-only closure (`‖Q_vμ_v(R_{c_1},…)‖ ≤ ρ∏‖R_{c_i}‖`) | weaker hypothesis, larger class. Correction (2026-09-13): every *upper* bound in this program (canonical §9, `W_3`, Theorem C, MIXED, BBR, STAR) uses closure only along the reduced trajectory, so those constants are unchanged in this class. Witnesses must still satisfy full PMT-A closure. |
| oblique projectors | OP6 |
| unreduced (non-projecting) root | historical Convention B; M24–M25 |
| DAGs (shared subexpressions) | Paper II |
| infinite dimensions / growing trees | OP7–OP8 |

## A9. The complex variant `PMT-A[C]`

Same as PMT-A with complex Hilbert spaces and **complex-multilinear** laws.
Status of transfer (see `K4_TOPOLOGY.md` §6):

* every *upper* bound proved in this program for PMT-A holds verbatim for
  PMT-A[C] (all reductions pass to real planes with `Re⟨·,·⟩`);
* *lower* bounds transfer only when the witness uses complex-linear maps and
  coordinate gates: `k ≤ 3` (all skeletons), chains of every length, and a
  bilinear root fed by two chains (MIXED);
* the real "phase" witnesses for internal vertices with ≥2 internal children
  use the multiplication of `ℝ² ≅ ℂ`, whose complexification has norm `√2`.
  A second-order expansion of the norm constraint shows that no
  complex-bilinear map of norm 1 can both *retain* the reduced value and
  *transport* two orthogonal first-order errors coherently at a non-root
  vertex. At `k = 4` this costs nothing at first order (BBR does not need
  retention; `K4_TOPOLOGY.md` §6), but for skeletons where stages follow such a
  vertex (first at `k = 5`) `C_T^P(η; PMT-A[C]) < C_T^P(η; PMT-A)` is a live
  possibility: the first candidate for genuine field dependence.

Consequently PMT-A is fixed over `ℝ`. Any statement over `ℂ` must be labelled
`PMT-A[C]` and must justify its lower bound separately.

## A10. Citation rule

A sharp-constant claim is admissible in Papers I–III only if it states:
(i) the class (`PMT-A` or `PMT-A[C]`), (ii) the skeleton or family of
skeletons, (iii) the `η`-range, (iv) the upper-bound proof, and (v) an explicit
admissible witness with norms and closure defects checked analytically.
