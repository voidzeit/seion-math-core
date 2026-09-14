# Finite-dimensional extremal recursion

Status: §1 **ADVISORY_PROOF_DRAFT** (it is Theorem C in recursive form);
§§2–4 **CONJECTURE** with the partial proofs indicated. Class `PMT-A`.

Goal (program brief): a state `𝒮_k` carrying the norm/leakage/Gram information
and a map `𝒮_{k+1} = Φ_η(𝒮_k)` turning the case-by-case `k = 2,3,4,…` analysis
into one theory.

---

## 1. Chains: the recursion exists and is two-real-dimensional

After the isometric dilation (`CHAIN_ALL_K.md` §2.2) the ambient value is a unit
vector at every stage. The whole extremal information is

```
𝒮_j := z_j := ‖R'_j‖ · e^{iψ_j} ∈ D̄ ∩ {Im ≥ 0},    ψ_j := ∠(F'_j, R'_j) ∈ [0, π],
```

and one stage with local leakage angle `θ ∈ [0, arcsin η]` acts by

```
Φ_θ(z) = z · w(θ),      w(θ) := cos θ · e^{iθ} = (1 + e^{2iθ})/2      (angles capped at π).
```

`w(θ)` runs over the **Thales arc** `Γ_η := {w : |w − ½| = ½, 0 ≤ arg w ≤ arcsin η}`:
for a unit vector `y` at angle `θ` from `Ran P`, `Py` is the foot of the
perpendicular, which lies on the circle with diameter `[0, y]`. The terminal
functional is the distance to the ambient value, `|1 − z|`.

**Theorem R1 (chain recursion).**
`W_0(z) = |1 − z|²`, `W_m(z) = max_{w ∈ Γ_η} W_{m−1}(z·w)`. Then
`G_{k,chain}(η)² = W_{k−1}(1)`, and the maximum is attained on the constant
orbit `w_1 = ⋯ = w_{k−1}`.

*Proof.* Upper bound: every admissible chain produces a dilated trajectory whose
`(‖R'_j‖, ψ_j)` is dominated by some orbit of `Φ` (`‖R'_j‖ = ∏cos θ_i` exactly,
`ψ_j ≤ Σθ_i`), and `|1 − r e^{iψ}|` increases in `ψ ∈ [0,π]`. Lower bound: the
planar rotation witness realizes every orbit. Equal factors: log-concavity of
`cos` (§2.4 of `CHAIN_ALL_K.md`). `□`

So the chain problem is: *maximize the distance from 1 of a product of `k−1`
points of the Thales arc `Γ_η`*. Everything in Theorem C — `W_3`, the
`k = 4` formula, `a_k = (k−1)(k−2)(k+6)/24`, the critical leakages `s_c(k)`,
`G^max_k → 2` — is read off from `|1 − w(θ)^{k−1}|`.

## 2. Trees: the multiplicative state (Conjecture R)

The witness of Theorem U (`K4_TOPOLOGY.md` §2) composes states by complex
multiplication over the tree:

```
z_v = w(θ_v) · ∏_{c internal child of v} z_c        (non-root v),
E^P_T = |1 − ∏_{c internal child of r} z_c| = |1 − ∏_{v ≠ r} w(θ_v)|.
```

The error depends on the tree only through the multiset of leakage angles, and
by log-concavity the optimum is again `|1 − w(θ)^{k−1}|`.

**Conjecture R (topology independence, PMT-A).** For every finite ordered tree
`T` with `k` internal vertices and every `η ∈ (0,1]`,

```
C^P_T(η) = C^P_{k,chain}(η) = max_{0 ≤ θ ≤ arcsin η} |1 − (cos θ e^{iθ})^{k−1}| / η.
```

Consequences if true: `a_T = (k−1)(k−2)(k+6)/24` for every `T` (open problem
OP3 of the canonical formalization would have the answer "`a_T` depends only on
`k`"), and the critical leakage and saturated absolute error are depth-only
invariants.

**Proved cases.** `≥` for all `T` (Theorem U). `=` for: `k ≤ 3` (`W_3`); all
four `k = 4` skeletons; chains of every length (Theorem C); a bilinear root fed
by two chains of arbitrary lengths (the MIXED argument).

**Mechanisms that realize `Φ` in the proofs.**

| vertex type | how the multiplicative domination is proved |
|---|---|
| linear stage | isometric dilation keeps the budget, angles add, norms multiply (exact) |
| bilinear/multilinear **root** | projective-norm duality; for real `2×2`, `‖K‖_*² = ‖K‖_F² + 2|det K| = |1 − z_az_b|²` |
| bilinear vertex followed by the root, singleton children | complex coordinates on input planes + **Gram repair** (Lemma G): the bidisc norm permits only *extra alignment* of `F_v` with `R_v`, which is removed without decreasing the objective |
| ternary root, singleton children | bilinear reduction onto two legs + repair + rotation by the third angle |

## 3. What a general induction needs

For a vertex with ≥ 2 internal children that is **not** followed directly by the
root, the output pair `(F_v, R_v)` is not of chain type: its Gram matrix can be
more aligned than any `Φ`-orbit allows, and `F_v` need not be dilatable to a unit
vector along an isometry. A complete theory needs a *domination order* on
states:

```
(F, R, P) ≼ z   :⟺   for every admissible continuation, the final error from (F,R) ≤ that from the chain state z.
```

**Conjecture R′ (alignment monotonicity).** At fixed `‖F‖, ‖R‖, ‖QF‖` and fixed
downstream data, the supremum of the final error over all admissible
continuations is non-increasing in `Re⟨F, R⟩`.

R′ plus the Gram repair would prove Conjecture R for all trees whose multilinear
vertices have singleton children; general children additionally need the
residual-case bounds of `K4_TOPOLOGY.md` §3.3–3.4 with `r_a ≤ ∏cos θ` replacing
`r_a = cos α` (they do not transfer verbatim: after two linear stages
`r_a = cos²θ > cos 2θ`).

**A concrete test of R′.** The chain Gram SDP accepts an arbitrary initial state
list: replace `GP_0 = [1]`, `GQ_0 = [0]` by the `P/Q` Gram of `(R_v, e_v)`
produced by a bilinear vertex, and maximize over that vertex's parameters. This
reduces every "multilinear vertex followed by a chain" skeleton at `k = 5`
(e.g. `1,2 → 3 → 4 → r`) to an outer optimization over an inner *exact
upper-bound* SDP. First runs (real field, `η ∈ {0.3, 0.5, 0.6}`) find no value
above `G_{5,chain}` beyond solver tolerance (`K4_TOPOLOGY.md` §4); a global
version (many starts, all `k = 5` skeletons with a multilinear non-root vertex)
is the next step.

## 4. The dual recursion

The exact certificates (`EXACT_CERTIFICATES.md` §2) are a **backward** LMI
recursion

```
Z3_j ⪰ T_P (Z3_{j+1}[PP] + η² Z4_{j+1}) T_Pᵀ,   Z3_j + emb(Z4_j) ⪰ T_Q Z3_{j+1}[QQ] T_Qᵀ,
terminal data aaᵀ,  bound V = Z3_1[0,0] + η² Z4_1[0,0].
```

Its matrices grow linearly with `j`, while the primal state of §1 is
two-dimensional. Question D: do optimal certificates have rank bounded
independently of `j` (a quadratic value function of `(F, R)` only)? If so, a
parametric certificate in `t = sin θ` would certify Theorem C for all `η` at once
and would be the right dual object for trees.

## 5. Field

Over `ℂ` the chain recursion is unchanged. At a non-root bilinear vertex the
retention obstruction (`K4_TOPOLOGY.md` §6) shows that `Φ` cannot be realized
with complex-bilinear laws, so the reachable state set may be strictly smaller.
The first skeleton where this could change the constant at first order is
`1,2 → 3 → 4 → r` (`k = 5`).

## 6. DAGs (for Paper II)

In a DAG a value may feed several slots. The same witness multiplies states
once per slot, so `z_r = w(θ)^{K(G)}` with `K(G)` the slot-path multiplicity of
`CANONICAL_FORMALIZATION.md` Def. 24.2, giving the lower bound
`C^P_G(η) ≥ max_θ |1 − w(θ)^{K(G)}|/η` → `K(G)` as `η ↓ 0`, consistent with the
canonical `lim = K(G)`. **Conjecture R-DAG:** equality. (Requires that the DAG
class allows one vertex in several slots of a multilinear law; to be frozen in
Paper II's class definition.)
