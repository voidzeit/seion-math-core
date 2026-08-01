# Originality assessment — table to be completed by a human specialist

**This table is empty on purpose.** It is the instrument for the assessment described in
`literature_audit.md`, which has **not** been carried out. Nothing in it may be filled in
by a search for matching wording, and nothing in it may be filled in by an automated tool.

## The question to answer

For each row, the question is **not**

> Is there a paper using this notation?

but

> **Does there already exist a theorem which, under equivalent hypotheses, implies this
> result?**

A result can be implied by a more general theorem stated in entirely different language.
That is the case the search must be designed to catch.

## Permitted verdicts

Exactly one per row:

| Verdict | Meaning |
| --- | --- |
| `new` | No located antecedent implies it under equivalent hypotheses |
| `new special case` | Implied by a known general theorem, but the specialisation is not in the literature and is not immediate |
| `new proof` | The statement is known; the argument here is different and independently interesting |
| `new application` | Statement and proof are known; the setting is new |
| `known equivalent formulation` | The same result in different language |
| `unresolved overlap` | An antecedent is close enough that the relationship could not be settled |

`unresolved overlap` is a legitimate outcome and is preferable to a guess.

---

## Table

| # | Result here | Statement | Closest antecedent located | Its hypotheses | Hypotheses here | Its conclusion | Conclusion here | Real difference | Verdict | Assessor | Date |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| O-1 | Exact local decomposition | `D_v = r_v(R_1,…,R_a) + Σ_{∅≠S⊆[a]} μ_v(y^S)` (doc 01, Thm. 5.1) | | | multilinear `μ_v`; orthogonal `P_v`; `R_i ∈ ran P_{τ(c_i)}` | | exact identity, no inequality | | | | |
| O-2 | Orthogonal splitting at the root | `(E^amb)² = (E^proj)² + (E^⊥)²`, `E^red = E^proj` (doc 01, Prop. 6.1) | | | `P = QQ*` orthogonal; `R ∈ ran P` | | two exact identities | | | | |
| O-3 | Uniform ambient coefficient | `E^amb ≤ kρM^{k−1}L_T` (doc 01, Thm. 9.1) | | | `‖μ_v‖ ≤ M`, `‖r_v‖ ≤ ρ` at every vertex; `k ≥ 1` | | upper bound | | | | |
| O-4 | **Projected coefficient `k−1`** | `E^proj = E^red ≤ (k−1)ρM^{k−1}L_T` (doc 01, Thm. 9.1) | | | as O-3 | | upper bound; optimality open | | | | |
| O-5 | State-resolved recursion | soundness of the `{R,∥,⊥}` recursion (doc 01, Thm. 7.1) | | | certified block norms assumed available | | valid upper bounds | | | | |
| O-6 | Optimal telescoping order | closed-form minimiser of `C(π)` (doc 01, Thm. 8.1) | | | `e_i, r_i, f_i, G_i ≥ 0`; the declared scalar family | | global minimum within that family | | | | |
| O-7 | Pathwise majorant | `B̂_ϱ = Σ_v λ_v Π_e h_e`, `B ≤ B̂` (doc 01, Cor. 10.2) | | | affine scalar recurrence with `h ≥ 0` | | identity for the majorant | | | | |
| O-8 | Signed-combination bound | `E^proj_ℱ ≤ Σ_α \|c_α\| B^proj_{T_α}`; coefficient 2 for the ternary associator (doc 01, Cor. 11.1) | | | finite compatible combination | | upper bound | | | | |
| O-9 | Representation and projection | `‖F_μ − R_μ̂‖ ≤ kρM^{k−1}L + kδ(M+δ)^{k−1}L` (doc 01, Prop. 14.1) | | | closure bound on the **exact** maps only | | upper bound, two sources separated | | | | |
| O-10 | Composite kernels square-integrable | `‖κ_L‖_{L²(X⁶)} ≤ ‖κ‖²_{L²(X⁴)}` (doc 02, Lemma 2.4) | | | `κ ∈ L²(X⁴)`, `(X,ν)` σ-finite | | bound and a.e. convergence | | | | |
| O-11 | Associator determines the defect kernel | vanishing on products ⟺ `Φ_κ = 0` a.e. (doc 02, Prop. 3.4) | | | additionally `L²(X,ν)` separable | | equivalence | | | | |
| O-12 | Commutator defect and associator | `R_std(x,y)z = A(y,x,z) − A(x,y,z)` (doc 02, Thm. 4.1) | | | any bilinear operation; no algebra axioms | | exact identity | | | | |

### Rows expected to resolve to `known`

O-2 is the Pythagorean theorem for an orthogonal decomposition and O-12 is an elementary
expansion; both are almost certainly known in some form, and the honest outcome for them is
probably `known equivalent formulation`. They are listed because the assessment must cover
every statement, not only the ones one hopes are new. Similarly, doc 02's Propositions 6.1
and 6.2 and the Stiefel gradient are already cited as standard and are not listed here.

### The row that matters most

**O-4.** If the coefficient `k−1` follows from a known general theorem under equivalent
hypotheses, the contribution must be repositioned — as a specialisation, a new proof, or a
new application — and the abstract and introduction rewritten accordingly. That is a
reasonable outcome and would not make anything in the package incorrect.

---

## Minimum search coverage

| Area | Rationale |
| --- | --- |
| forward and backward error analysis | the estimates are of that form |
| composition and perturbation of multilinear maps | the direct subject |
| perturbation of computational trees and expression DAGs | the structural setting |
| structure-preserving and projection-based model reduction | the closest methodological precedent located so far |
| hierarchical tensor formats; tree tensor networks | tree topology plus truncation at every vertex |
| dynamical low-rank approximation; low-rank integrators | recursive projection onto a moving subspace |
| approximately multiplicative maps; stability of algebraic identities | approximate structure preservation |
| coloured and symmetric operads, quantitative statements within them | the typed composition grammar |
| abstract interpretation; layerwise certified bounds | vertexwise recursions over a computation graph |
| error analysis in tensor networks | contraction plus truncation |
| validated numerics for extremal constants | the enclosure methodology |

## Rules

1. Every row gets a verdict, including the ones expected to be `known`.
2. Every verdict is signed and dated by the person who reached it.
3. No verdict may be reached from a keyword search alone; the antecedent's hypotheses and
   conclusion must be read.
4. Absence of a match is recorded as `unresolved overlap`, never as `new`.
5. No numerical or ordinal novelty score is computed.
6. Until this table is complete, every manuscript keeps its statement that no claim of
   originality is made.
