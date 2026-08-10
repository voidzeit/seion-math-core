# Projected graphs v5 truth ledger

## Baseline

The finite v4 core is frozen at scientific commit
`1f4984ec8e741049789e0035c7a3ba84c86d3f29`. The operational branch later
contains governance-only postflight commit `f88f75bdf3f44407392d6c55dd2affb37d3185ab`.
V5 does not modify `research_projected_trees_v4`, Gate 13.5, Gate 14, KGR, or
historical artifacts.

## V5 theorem target

For the general real binary k=2 chain with independent node laws, define

```text
C_2^P(eta) = sup E_proj / (rho M L),   eta=rho/M.
```

The universal projected-root theorem gives `C_2^P(eta) <= 1`.

## Closed result: independent-law saturation

For every `0 < eta <= 1`, the explicit two-dimensional construction in
`src/seion_core/research_v5/k2_sharpness.py` has:

```text
||mu_inner|| = ||mu_outer|| = M
rho_inner = eta*M
rho_outer = 0
E_proj = eta*M^2 = rho*M.
```

Therefore:

```text
C_2^P(eta) = 1
```

for this declared general class with independent node laws. This does not
contradict the earlier `E_proj=eta^2` result: that result is for the narrower
repeated gated-planar law family, not the general independent-law class.

## Closed result: declared general k=2 class

The same witness is also admissible in the broader declared finite-dimensional
binary class with arbitrary bounded bilinear laws, whether shared or
independent. Combined with the universal upper bound, the new exact statement
is:

```text
C_{2,A}^P(eta) = 1,  0 < eta <= 1.
```

The proof and deterministic evaluator are in
`research/math_closure/k2/class_A_exact_constant.tex` and
`research/math_closure/k2/class_A_exact_constant.py`. Higher-arity variants,
infinite-dimensional attainment, and the broader gated-planar repeated-law
subclass remain outside this closure.

## Remaining open questions

- broader gated-planar repeated-law k=2 sharpness;
- higher-arity k=2 sharpness;
- universal dimension/rank reduction;
- k=3 topology-specific global constants;
- globally tight multilinear spectral norms;
- theorem-level novelty.

## Equality/slack conclusion

The simultaneous equality conditions are compatible for independent node laws,
as witnessed by the exact construction. The explicitly declared same-map class
is also sharp by the repeated-law witness; the remaining boundary is the
broader gated-planar repeated-law subclass.

## V5-A: independent-law k=3 lower witnesses

The chain and branching constructions in
`src/seion_core/research_v5/k3_independent_candidates.py` are certified lower
witnesses, not global sharpness results. With a defect budget `rho=eta*M`,
they choose

```text
q = min(rho, M/sqrt(2))
E_proj = 2*M*q*sqrt(M^2-q^2)
```

For `0 < eta <= 1/sqrt(2)`, the realized defect equals the budget and the
normalized lower bound is `2*sqrt(1-eta^2)`. For larger eta, the witness uses
the budget maximum of its family and reports the realized defect separately.
The global independent-law constants for `k=3` remain `OPEN`.

## V5-B: scalar extremal reduction and asymptotic sharpness

The V5-A family reduces to the exact scalar problem

```text
maximize 2*M*q*sqrt(M^2-q^2)
subject to 0 <= q <= rho=eta*M.
```

The exact scalar optimizer is `q*=min(rho,M/sqrt(2))`, yielding the
normalized lower curve

```text
L3(eta) = 2*sqrt(1-eta^2),  0 < eta <= 1/sqrt(2)
L3(eta) = 1/eta,              1/sqrt(2) < eta <= 1.
```

This is a certified lower bound for the declared V5-A witness family. It is
not a fixed-eta global upper bound. The proposed matching upper envelope is
recorded only conditionally on proving a universal scalar reduction of the
form `E_proj <= 2*A*B`, `A^2+B^2 <= M^2`, and `A <= rho`.

Combining `L3(eta) <= C_3,ind^P(eta) <= 2` gives the proved asymptotic result

```text
lim_{eta downarrow 0} C_3,ind^P(eta) = 2.
```

The fixed-eta k=3 constant remains `OPEN`.

## V5-B: repeated-law k=2 status

The broader explicitly declared same-map class is now sharp:

```text
C_2,same-law^P(eta) = 1.
```

The same bilinear law `mu(x,y)=M*x1*y0*e0+rho*x0*y0*e1` is used at both
internal nodes and attains `E_proj=rho*M` for every `0<eta<=1`. The earlier
gated-planar repeated-law family remains narrower, with exact projected error
`eta^2` and normalized value `eta`. Sharpness for that restricted subclass
remains open.

## Theorem-closure campaign (2026-08-08): k=2 iff characterization and k=3 upper envelope

Two new theorem-level results close the campaign's two highest-priority
open targets to the extent tractable in a single pass:

1. **k=2 saturation is now characterized, not just witnessed.** For the
   binary k=2 chain (any dimension, any projector rank, laws independent or
   repeated), `E_proj=rho*M*L_T` holds iff three explicit local conditions
   (EQ1: outer-law operator-norm saturation, EQ2: closure-map saturation,
   EQ3: root-projection alignment) hold simultaneously. Proved by an
   elementary chain-of-inequalities argument. Both prior witnesses verified
   as instances; a third, independently constructed witness (not matching
   either prior form) predicted and verified to saturate.
   `research/math_closure/k2/saturation_iff_theorem.tex`.
2. **The k=3 upper bound is now tightened unconditionally.** The
   `CONDITIONAL_ON_UNPROVED_SCALAR_REDUCTION` bookkeeping entry above is
   superseded by a proved envelope `U_3(eta)` (chain and branching, any
   dimension/rank), strictly below the trivial bound `2` for every `eta>0`.
   `research/math_closure/k3/general_upper_envelope.tex`.

Fixed-eta k=3 sharpness remains open; the certified gap narrowed but did
not close. See `V5B_EXTREMAL_STATUS.md`'s "Superseded" section for the
exact numbers.

**M10 (same-day follow-up, then revised after review found two errors):
no single configuration attains U_3(eta).** Deriving the equality
conditions of M9 uncovered a genuine structural obstruction, but the
first write-up had two bugs an external review caught: (1) it claimed
`S1 perp S2` from a lemma step that doesn't actually survive an arbitrary
projection -- repaired with a projector-independent self-adjointness
argument giving the weaker, sufficient fact "`S2` is never a nonzero
multiple of `S1`"; (2) it concluded the strict supremum inequality
`C_3,ind^P(eta) < U_3(eta)` from mere non-attainment, which is an invalid
inference (a supremum can be approached without being attained). The
corrected result is `PROVED_NON_ATTAINMENT` only: no single admissible
configuration reaches `U_3(eta)` exactly. Whether the *supremum* itself
is strictly below `U_3(eta)`, or merely unreachable pointwise while still
equal to it in the limit, is now tracked as a separate, explicitly open
question (`OPEN_V5_K3_STRICT_SUPREMUM_GAP`) requiring either a
compactness argument or an explicit quantitative gap -- neither
completed. A separate gradient-based numerical search attempt failed to
even recover the known `L_3(eta)` witness and was discarded as
methodologically unreliable, not as evidence.
`research/math_closure/k3/m10_non_sharpness_of_m9.tex`.

## Conjectural direction

The finite-tree independent-law statement
`C_{T,ind}^P(eta)=k(T)-1` for sufficiently free laws is recorded as an open
conjecture only. No theorem or numerical construction in this repository
establishes it beyond the exact k=2 independent-law class.

## Current-status correction for historical repeated-law wording

Some earlier baseline paragraphs above intentionally preserve their original
2026-08-08 wording and say that repeated-law compatibility was unresolved.
That statement is historical provenance and is superseded by the theorem-
closure entries above: M8 gives the necessary-and-sufficient EQ1--EQ3
characterization for independent or repeated laws, and V5-B supplies an
explicit repeated same-map witness with
`C_2,same-law^P(eta)=1`.

The remaining gated-planar item is narrower and should not be called general
repeated-law sharpness: it asks whether a broader gated-planar repeated-law
subclass contains an ambient-bound saturator at fixed eta. The declared
gated-planar rotation construction itself is closed exactly by
`E_proj(eta)=eta^2`, with normalized value `eta`, hence it saturates only at
`eta=1`. The authoritative current records are
`claims/theorem_registry_v5.yaml`, `research/math_closure/k2/classification_theorem.tex`,
and `research/projected_trees_v5/V5_STATUS.json`.

## M17 contractive gated-planar repeated-law closure — 2026-08-09

The previously vague “broader gated-planar” item now has one explicit
canonical subclass: the repeated law
`mu_A(x,y)=A*x*<e0,y>` with a fixed gate, an active planar contraction, and
`||(I-P)A P||<=rho`. Its exact error is
`||P*A*(I-P)*A*e0||`, so the upper bound is `M*rho`; the off-diagonal
contraction `A=[[0,M],[rho,0]]` attains it. Thus this contractive subclass has
normalized constant `1`. Variable-gate, arbitrary-leaf, and non-planar shared
law variants remain separately open rather than being conflated with M17.

Likewise, the earlier scalar-reduction candidate for the k=3 envelope is only
historical. It is superseded by M9's unconditional envelope; the active open
item is the strict supremum-gap question recorded as
`OPEN_V5_K3_STRICT_SUPREMUM_GAP`, not the old unproved reduction itself.

M10b now closes the strict-gap question for each fixed finite dimension/rank
class by compactness: a class-dependent
`delta_{n,r}(eta)>0` exists for `0<eta<1`. The global question over unbounded
dimension/rank tuples remains open because no uniform lower bound on this
delta has been proved.

## Restricted topology-wide closure — 2026-08-08

The declared homogeneous gated-planar rotation family is now closed for every
finite ordered full-binary topology.  If `d(leaf)=0`,
`d((A,B))=1+d(A)`, `a(leaf)=1`, and
`a((A,B))=a(A)a(B)cos(d(B)theta)`, then
`E_proj=|a(T)cos(d(T)theta)-cos(theta)^k|` in the `M=L=1` normalization.
The exact proof and evaluator are registered as
`THM_V5_HOMOGENEOUS_GATED_ROTATION_ALL_BINARY_TOPOLOGIES`.

This result closes the previously untreated ordered topologies only inside
the declared shared gated-rotation law. It does not close independent-law
sharpness, arbitrary-law sharpness, or universal dimension/rank reduction.

The same induction extends to finite ordered rooted trees with variable
arity, using the arity-compatible law
`mu_m(x1,...,xm)=R_theta*x1*product_{j>=2}<e0,xj>`. The recursive formula is
identical with one gate factor for each secondary child; it is registered as
`THM_V5_HOMOGENEOUS_GATED_ROTATION_GENERAL_ARITY`. Mixed arity is therefore
closed only for this declared shared active rotation family, not for arbitrary
multilinear laws.

## M11 conditional quantitative gap — 2026-08-08

For the ordered `k=3` chain, exact operator-norm saturation of the first
propagated-defect direction at the second node yields the conditional bound
`G(eta)/eta` relative to `rho*M^2*L_T`, where
`G(eta)=eta*sqrt(4-3 eta^2)` for `eta<=sqrt(2/3)` and
`G(eta)=2/sqrt(3)` thereafter. This is a quantitative angle–magnitude gap
below the M9 envelope inside that conditional class. It does not imply a
global supremum gap, because near-extremizers need not satisfy exact
saturation. Evidence is registered as
`THM_V5_K3_M11_CONDITIONAL_QUANTITATIVE_GAP`.

## Fixed-tree support compression and global k=3 strict gap — 2026-08-09

Every fixed finite typed tree can be compressed to the projector-invariant
span generated by its leaf vectors and its ambient and recursively projected
raw node outputs. This preserves all named errors and cannot increase any law
or closure-residual cap. The dimension bound is
`2*(leaf_count_tau+2*node_count_tau)` per type; for a one-type binary `k=3`
chain or branching tree it is `20`, or `22` when proper-projector padding is
required.

This closes the dimension/rank-uniformity issue for the fixed `k=3` topologies:
the global supremum is a maximum over a finite union of compact parameter
spaces. Combined with M10 non-attainment, it proves
`C_3,ind^P(eta)<U_3(eta)` for `0<eta<1`. The gap is nonquantitative; the exact
constant, an explicit delta, the endpoint `eta=1`, and a bound uniform over
unbounded tree growth remain open.

## Finite source-resolved error calculus — 2026-08-09

The formerly separate P6A/P6B/P7B implementation milestones are now
consolidated as one finite theorem package. For every finite typed multilinear
DAG with finitely many labelled sources, the node error is an exact finite
multi-index polynomial. Topological convolution agrees with recursive
unrolling; repeated source use is represented by multiplicity; same-source
first-order paths are aggregated before taking norms; finite truncations carry
an omitted-term norm certificate; and signed coefficient aggregation gives
`B_actual <= B_signed <= B_treewise`.

The canonical proof, executable witness, and focused test are
`research/math_closure/dag/source_resolved_error_calculus.tex`,
`research/math_closure/dag/source_resolved_error_calculus.py`, and
`tests/math_closure/test_source_resolved_error_calculus.py`. This closes the
finite theorem-consolidation gap, not the separate open problems of scalable
implicit-DAG compression, infinite-series tails, universal signed-forest
sharp constants, or novelty.

## Endpoint extension at eta=1 — 2026-08-09

The M10 equality obstruction also applies at the endpoint. The M9 optimizer is
then the interior point `q*=M/sqrt(2)`, and both propagated contributions are
nonzero. Therefore no individual configuration attains `U_3(1)=sqrt(2)`.
Finite support compression and compactness now give the strict global result
`C_3,ind^P(1)<sqrt(2)` for the binary chain and branching classes. The exact
endpoint constant and a quantitative gap remain open.

## M13 unconditional chain envelope — 2026-08-09

For the independent-law ordered binary chain with three internal nodes, the
M11 angle--magnitude estimate can be made unconditional. The second-node
cross-term is controlled by the Gram matrix
`K=(N/M)^*Q(N/M)`, which satisfies `0<=K<=I`; its diagonal constraints give
`|<x,Qy>| <= s sqrt(1-s^2)` without assuming saturation at the first node.
Consequently the normalized chain constant obeys
`C_3,ind,chain^P(eta) <= W_3(eta)`, with
`W_3(eta)=sqrt(4-3 eta^2)` for `0<eta<=sqrt(2/3)` and
`W_3(eta)=2/(sqrt(3) eta)` for `sqrt(2/3)<=eta<=1`.
The explicit difference `U_3(eta)-W_3(eta)` is positive on the full interval
`0<eta<=1`. This closes an unconditional quantitative gap for the chain only;
it does not provide a branching analogue, prove sharpness of `W_3`, or compute
the exact chain constant.

The proof, executable check, and focused test are
`research/math_closure/k3/m13_unconditional_chain_envelope.tex`,
`research/math_closure/k3/m13_unconditional_chain_envelope.py`, and
`tests/math_closure/test_m13_unconditional_chain_envelope.py`.

## M14 exact independent-law chain constant — 2026-08-09

The M13 chain envelope is attained, not merely an upper bound. For every
`0<eta<=1`,
`C_3,ind,chain^P(eta)=W_3(eta)`, with the same piecewise formula as M13.
The witness is explicit in dimension two with `P=span(e0)`: the first node
creates `t e1 + sqrt(1-t^2)e0`, the second node is an orthogonal two-plane
rotation whose projected leakage is `t`, and the root maps the exact error
sum isometrically into the projected root line. Here
`t=min(eta,sqrt(2/3))`, so the boundary regime and the interior scalar
optimizer are both attained. All three laws have operator norm one and their
closure residuals are at most `eta`.

The canonical proof, executable witness, and focused test are
`research/math_closure/k3/m14_exact_chain_constant.tex`,
`research/math_closure/k3/m14_exact_chain_constant.py`, and
`tests/math_closure/test_m14_exact_chain_constant.py`. This closes the exact
fixed-eta chain constant only; the branching constant and broader arity
profiles are recorded separately below.

## M15 exact independent-law branching constant — 2026-08-09

The branching root has two bilinear error terms with orthogonal first factors.
Scalarization and nuclear/operator-norm duality bound their joint contribution
by the same `W_3(eta)` envelope as M13. A polar-factor root law in dimension
two attains the nuclear norm, with child defects
`t=min(eta,sqrt(2/3))` and zero root residual. Therefore
`C_3,ind,branch^P(eta)=W_3(eta)` for every `0<eta<=1`.

Together M14 and M15 close the independent-law fixed-eta constants for both
binary `k=3` topologies. M20 below extends this closure to every finite
three-internal-vertex arity profile. Same-law/gated subclasses and fixed-eta
independent-law trees with `k>=4` remain open.

Evidence: `research/math_closure/k3/m15_exact_branching_constant.tex`,
`research/math_closure/k3/m15_exact_branching_constant.py`, and
`tests/math_closure/test_m15_exact_branching_constant.py`.

## M16 arbitrary-node-law binary class corollary — 2026-08-09

The phrase `independent-law` in M14/M15 means that each node law is freely
selectable subject only to the common norm and defect budgets; it imposes no
law-sharing constraint. Consequently M14 and M15 also close the full declared
binary `k=3` class with arbitrary node laws and no sharing constraint:

```text
C_{3,A,chain}^P(eta) = C_{3,A,branch}^P(eta) = W_3(eta).
```

This is a scope corollary, not a claim about repeated same-law subclasses or
higher-arity trees. Its deterministic scope-check is recorded in
`research/math_closure/k3/m16_general_binary_class_corollary.py`.

## M20 exact independent-law k=3 constant for every finite arity profile — 2026-08-09

M20 closes the remaining finite-arity extension at `k=3`. For any finite
ordered rooted tree with exactly three internal vertices and every internal
arity at least two, freezing each leaf at its unit projected value leaves an
effective linear law at a node with one internal child and an effective
bilinear law at a node with two. The effective norm and closure-defect caps
are no larger than the original multilinear caps.

There are only two possible three-vertex internal-child skeletons: a chain or
a branching root. M13--M15 therefore give the upper bound `W_3(eta)`. In the
other direction, the dimension-two M14/M15 witnesses embed into every finite
arity profile by inserting unit `e0` gates in the extra leaf slots. Hence

```text
C_{T,ind}^P(eta) = W_3(eta),  0 < eta <= 1,
```

for every such `T`, with `W_3=sqrt(4-3 eta^2)` below `sqrt(2/3)` and
`W_3=2/(sqrt(3) eta)` above. The executable atlas checks 12,691 ordered
profiles through maximum arity eight; the theorem itself is for arbitrary
finite arity. Same-law/gated variants, fixed-eta independent-law trees with
`k>=4`, growing-tree uniformity, novelty, and independent human review remain
open.

Evidence: `research/math_closure/k3/m20_k3_arbitrary_arity_exact_constant.tex`,
`research/math_closure/k3/m20_k3_arbitrary_arity_exact_constant.py`, and
`tests/math_closure/test_m20_k3_arbitrary_arity_exact_constant.py`.

## M21 tagged same-law exact constants for binary k=3 — 2026-08-09

M21 separates law sharing from the additional rank-one/common-leaf restriction.
In the explicitly declared finite-dimensional real class with one repeated
bilinear law, one fixed coordinate projector, and arbitrary unit projected
leaf vectors, orthogonal tags select blocks of a single direct-sum law. The
chain construction simulates the three M14 laws; the branching construction
simulates the two M15 child laws and the polar-factor root. Orthogonality of
the block supports preserves operator norm one, while the projected normal
outputs have norm at most `eta`.

Consequently, for both binary k=3 topologies,

```text
C_{3,tag-same}^P(eta) = W_3(eta),  0 < eta <= 1.
```

This closes law sharing as an obstruction when finite projected tags are
admissible. Rank-one/common-leaf same-law restrictions, gated and variable-
gate subclasses, fixed-eta independent-law trees with `k>=4`, growing-tree
uniformity, novelty, and independent human review remain open.

Evidence: `research/math_closure/k3/m21_same_law_tagged_exact_constant.tex`,
`research/math_closure/k3/m21_same_law_tagged_exact_constant.py`, and
`tests/math_closure/test_m21_same_law_tagged_exact_constant.py`.

## M22 rank-one/common-leaf same-law chain at high eta — 2026-08-09

M22 closes the high-defect regime even under the strict rank-one/common-leaf
restriction. Use one repeated gated rotation with leakage
`alpha=sqrt(2/3)`, common leaf `e0`, and `P=span(e0)`. The ambient three-step
rotation and the recursively projected chain differ by `2/sqrt(3)`. Since
`alpha<=eta` for `eta>=sqrt(2/3)`, this witness is admissible and its
normalized error is

```text
2/(sqrt(3) eta) = W_3(eta).
```

M14 supplies the matching upper bound from the larger independent-law class.
Thus the strict rank-one/common-leaf same-law chain is exact in this regime.
Its low-eta regime, rank-one/common-leaf branching, broader gated/shared-law
variants, novelty, and independent human review remain open.

Evidence: `research/math_closure/k3/m22_same_law_rank_one_high_eta.tex`,
`research/math_closure/k3/m22_same_law_rank_one_high_eta.py`, and
`tests/math_closure/test_m22_same_law_rank_one_high_eta.py`.

## M18 asymptotic sharpness for every finite binary topology — 2026-08-09

For every fixed finite ordered full-binary tree `T` with `k` internal vertices,
the independent-law class has asymptotic constant `k-1` as `eta` tends to zero.
The witness lives in `C ~= R^2`, uses `P(z)=Re(z)`, unit leaves, the law
`mu_theta(z,w)=exp(i theta) z w` at every non-root vertex, and a scalar
off-diagonal root law, with `theta=arcsin(eta)`. Shape-independence of complex
multiplication gives the exact projected error
`E_proj=|sin((k-1) arcsin(eta))|`; the universal projected-root bound supplies
the matching upper limit.

Thus the finite binary-tree asymptotic statement
`lim_{eta downarrow 0} C_{T,ind}^P(eta)=k(T)-1` is now proved under the declared
independent-law and finite-tree assumptions. This does not assert fixed-eta
equality and leaves higher arity, same-law/gated variants, growing-tree
uniformity, novelty, and independent human review open.

Evidence: `research/math_closure/k3/m18_binary_tree_asymptotic_sharpness.tex`,
`research/math_closure/k3/m18_binary_tree_asymptotic_sharpness.py`, and
`tests/math_closure/test_m18_binary_tree_asymptotic_sharpness.py`.

## M19 asymptotic sharpness for every finite arity-compatible tree — 2026-08-09

M19 removes the binary restriction from the finite-tree asymptotic result. Let
`T` be any fixed finite ordered rooted tree with every internal arity at least
two. On the real plane identified with `C`, use
`mu_{m,theta}(z_1,...,z_m)=exp(i theta) prod_j z_j` at each non-root node and
`mu_{star,d}(z_1,...,z_d)=Im(prod_j z_j) e0` at the root, with
`theta=arcsin(eta)`. Each law has norm one; non-root closure defect is `eta`
and the root defect is zero. The ambient phase counts internal vertices only,
so the exact witness error is
`E_proj=|sin((k(T)-1) arcsin(eta))|` for every arity profile.

Combined with the universal projected-root bound, this proves
`lim_{eta downarrow 0} C_{T,ind}^P(eta)=k(T)-1` for every fixed finite
arity-compatible topology. Fixed-eta equality, same-law/gated variants and
uniform growing-tree bounds remain open. Evidence:
`research/math_closure/k3/m19_finite_arity_asymptotic_sharpness.tex`,
`research/math_closure/k3/m19_finite_arity_asymptotic_sharpness.py`, and
`tests/math_closure/test_m19_finite_arity_asymptotic_sharpness.py`.

## M23 exact operator reduction for the remaining strict chain class — 2026-08-09

M23 removes the ambiguity in the low-eta rank-one/common-leaf same-law chain.
For a repeated bilinear law and common leaf `e0`, freeze the second input and
write `A(x)=mu(x,e0)`. With `P=span(e0)`, the exact projected error is

```text
|<e0,A^3 e0> - <e0,A e0>^3|.
```

Conversely every finite-dimensional contraction `A` is realized by the gated
repeated law `mu_A(x,y)=A x <e0,y>`, with the same operator and closure budgets.
Thus the class supremum is exactly the stated contraction-operator supremum.
This is a reduction theorem, not an evaluation: the low-eta value, branching,
and broader same-law/gated variants remain open.

Evidence: `research/math_closure/k3/m23_rank_one_same_law_chain_operator_reduction.tex`,
`research/math_closure/k3/m23_rank_one_same_law_chain_operator_reduction.py`,
and `tests/math_closure/test_m23_rank_one_same_law_chain_operator_reduction.py`.

## Finite DAG bounded-domain certificate — 2026-08-09

For a finite multilinear DAG with declared operator bounds, rank-indexed normal
residual bounds, and bounded leaf domains, the topological value/error
recurrence certifies the root error. Shared subexpressions are cached once;
repeated input slots and downstream fan-out are charged by their multiplicity.
Reverse downstream gains make the rank-budget objective separable when the
operator and value enclosures are rank-independent, so the finite rank-table
allocation is solved exactly by dynamic programming.

This is a proved finite enclosure theorem under declared assumptions, not an
extremal constant or a claim that empirical enclosures are universal. Evidence:
`research/math_closure/dag/global_domain_certificate.tex`,
`src/seion_core/research_v5/dag_domain_certificate.py`, and
`tests/research_v5_test_dag_domain_certificate.py`.

## Rank-aware finite DAG certificate — 2026-08-09

The fixed-assignment refinement tracks exact-value bounds, recursively
projected-value bounds, and mixed factors `max(U_v,A_v)`. With declared
rank-dependent projected-operator bounds it certifies the multilinear
telescoping error on shared DAGs and repeated slots. Because descendant ranks
change ancestor value bounds, its allocation objective is coupled; the
repository's optimizer is therefore an exhaustive small-DAG oracle, not a
scalable allocator theorem. Evidence:
`research/math_closure/dag/global_domain_certificate.tex`,
`src/seion_core/research_v5/dag_domain_certificate.py`, and
`applications/adaptive_tensor_network/tests/test_dag_network.py`.

## Exact nonnegative DAG path constant — 2026-08-09

For the first-order nonnegative channel envelope produced by multilinear
telescoping, the exact root coefficient is the sum of local source bounds
weighted by all source-to-root path products. The identity remains valid with
shared subexpressions and parallel edges for repeated slots, and is attained by
setting every channel source to its bound. This is sharpness for the declared
channel model, not a claim that the full multilinear operator class jointly
attains every channel equality. Evidence:
`research/math_closure/dag/exact_path_constant.tex`,
`src/seion_core/research_v5/dag_path_constant.py`, and
`tests/research_v5_test_dag_path_constant.py`.

## Shared diamond DAG asymptotic sharpness — 2026-08-09

For the fixed independent-law shared diamond with one shared projected node,
two projected branches, and an unprojected root, the universal path bound is
`E <= 4 eta`. Planar complex multiplication with
`theta=arcsin(eta)` gives the exact witness error
`|exp(4 i theta)-cos(theta)^4|`, whose normalized ratio tends to `4`. Thus
the asymptotic constant for this declared DAG class is exactly `4`; fixed-eta
equality and arbitrary-DAG sharpness remain open. Evidence:
`research/math_closure/dag/diamond_asymptotic_sharpness.tex`,
`research/math_closure/dag/diamond_asymptotic_sharpness.py`, and
`tests/math_closure/test_diamond_asymptotic_sharpness.py`.

## Fixed-DAG independent-law asymptotic path sharpness — 2026-08-09

The diamond construction generalizes to every fixed finite ordered acyclic
DAG. If `K(G)` is the sum of directed slot-path multiplicities from all
projected internal nodes to the unprojected root, the universal recurrence
gives `E <= K(G) eta`. The complex product laws have exact witness error
`|exp(i K(G) theta)-cos(theta)^K(G)|`, with `theta=arcsin(eta)`, so the
normalized asymptotic constant is exactly `K(G)`. This closes asymptotic
sharpness for the declared independent-law fixed-DAG class, but not fixed-eta
equality, unbounded-DAG uniformity, or same-law/gated restrictions. Evidence:
`research/math_closure/dag/dag_asymptotic_sharpness.tex`,
`src/seion_core/research_v5/dag_asymptotic_sharpness.py`, and
`tests/research_v5_test_dag_asymptotic_sharpness.py`.
