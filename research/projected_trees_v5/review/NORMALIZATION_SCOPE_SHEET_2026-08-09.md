# Projected Graphs V5 — normalization and scope sheet

This sheet is a compact pre-review reference. It is intentionally descriptive,
not a theorem approval. A reviewer should compare each row with the cited
proof dossier and record corrections in the external-review form.

## Common setup and normalization

| Symbol/term | Declared meaning | Review check |
|---|---|---|
| `T` | One finite ordered rooted typed tree; `k(T)` is its number of internal vertices | No growing-tree or infinite-arity limit is implicit in a fixed-tree statement |
| `V_tau`, `W_tau` | Finite-dimensional real or complex Hilbert spaces | Verify field changes do not alter witness or equality arguments |
| `Q_tau`, `P_tau` | `Q_tau: W_tau -> V_tau` is an isometry; `P_tau=Q_tau Q_tau^*` is the orthogonal projector | Check every use of contractivity and `P(I-P)=0` |
| `F`, `R` | Ambient and recursively projected evaluations; leaves agree: `F_l=R_l=Q_l z_l` | No separate leaf truncation error is allowed in this convention |
| `E^P` | Root projected error `||P F-R||`; it equals reduced error `||Q^*F-Q^*R||` | Do not replace it with ambient error `E^A=||F-R||` |
| `L_T` | Product of reduced leaf norms, `prod_l ||z_l||` | Unit-leaf witnesses have `L_T=1` |
| `M` | Common upper bound for every internal law operator norm `M_v` | A witness may have smaller norm, but equality claims must check saturation |
| `rho` | Common upper bound for every local projected-input closure map `r_v=(I-P_v)mu_v(P_child .)` | It is not an arbitrary ambient residual evaluated on unprojected inputs |
| `eta` | Defect ratio `eta=rho/M`, with `0<eta<=1` | Check whether a statement uses a cap `<=rho` or exact defect `=rho` |
| `C_T^P(eta)` | Supremum of `E^P/(rho M^(k(T)-1)L_T)` over the explicitly declared admissible class | The supremum may be unattained; an explicit witness proves only a lower bound unless matched by an upper bound |

The authoritative definitions are in
`papers/projected_graphs_v5/projected_multilinear_trees_v5.tex`, sections
“Typed projected trees”, “Universal coefficients”, and “Fixed-eta sharpness”.

## Theorem-by-theorem scope map

| Result | Exact class and conclusion | Explicit exclusions | Primary dossier |
|---|---|---|---|
| Universal projected-root theorem | Any finite typed tree; multilinear laws; orthogonal projectors; `M_v<=M`, `rho_v<=rho`; `E^P<= (k-1) rho M^(k-1) L_T` | Does not assert sharpness, dimension-free equality, same-law equality, or growing-tree uniformity | `papers/projected_graphs_v5/projected_multilinear_trees_v5.tex`; theorem registry `THM_V3_PROJECTED_ROOT_K_MINUS_ONE` |
| M8 | Binary `k=2` chain; arbitrary finite dimension/rank; independent or repeated bilinear laws; equality iff EQ1–EQ3 | Does not classify further restricted gated-planar subclasses; does not address `k>=3` | `research/math_closure/k2/saturation_iff_theorem.tex` |
| M13 | Independent-law ordered binary `k=3` chain; arbitrary finite dimension/rank; upper envelope `W_3(eta)` | Envelope is not by itself a sharpness theorem; it does not close branching or shared-law classes | `research/math_closure/k3/m13_unconditional_chain_envelope.tex` |
| M14 | Independent-law ordered binary `k=3` chain; arbitrary dimension/rank for upper bound; dimension-two rank-one real witness for attainment; `C=W_3` | Not same-law, not gated-planar, not arbitrary topology | `research/math_closure/k3/m14_exact_chain_constant.tex` |
| M15 | Independent-law ordered binary `k=3` branching tree; arbitrary dimension/rank for upper bound; dimension-two rank-one real witness for attainment; `C=W_3` | Not same-law and not a consequence of the chain equality obstruction | `research/math_closure/k3/m15_exact_branching_constant.tex` |
| M16 | Corollary for the binary `k=3` class with independently selectable node laws; chain and branching | “Independent law” means no law-sharing constraint; it does not mean stochastic independence | `research/math_closure/k3/m16_general_binary_class_corollary.tex` |
| M18 | One fixed finite ordered full-binary topology; independent laws; real-plane witness; `lim_{eta->0} C=k-1` | No fixed-eta equality; no variable arity; no growing-tree limit | `research/math_closure/k3/m18_binary_tree_asymptotic_sharpness.tex` |
| M19 | One fixed finite ordered rooted topology, every internal arity at least two; independent multilinear laws; real-plane witness; `lim_{eta->0} C=k-1` | No fixed-eta equality and no uniformity as `k` or arity grows | `research/math_closure/k3/m19_finite_arity_asymptotic_sharpness.tex` |
| M20 | Every fixed finite ordered arity profile with exactly three internal vertices; independent bounded multilinear laws; frozen unit projected leaf slots; exact `C=W_3` | Does not close fixed-eta `k>=4`; the effective-law reduction is not a same-law theorem | `research/math_closure/k3/m20_k3_arbitrary_arity_exact_constant.tex` |
| M21 | Binary `k=3`; one repeated bilinear law; finite rank coordinate projector; arbitrary unit projected leaves including orthogonal tags; exact `C=W_3` | Tags and finite rank are part of the class; no rank-one/common-leaf conclusion | `research/math_closure/k3/m21_same_law_tagged_exact_constant.tex` |
| M22 | Binary `k=3` chain; one repeated gated-planar rotation; common `e0`; rank-one `P`; `sqrt(2/3)<=eta<=1`; exact high-eta value | Low-eta and branching same-law values remain open | `research/math_closure/k3/m22_same_law_rank_one_high_eta.tex` |
| M23 | Binary `k=3` chain; one repeated real bilinear law; common `e0`; rank-one `P`; exact reduction to a contraction-operator supremum | The reduced low-eta supremum is not evaluated; no branching claim | `research/math_closure/k3/m23_rank_one_same_law_chain_operator_reduction.tex` |

## Mandatory reviewer confirmations

The reviewer should mark each item only after inspecting the proof, not merely
the tests:

- [ ] The definition of `E^P` is used consistently at the root.
- [ ] `rho` always bounds the projected-input closure map, not an ambient
      residual on arbitrary inputs.
- [ ] Every use of `C_T^P(eta)` specifies the topology, law-sharing class,
      field, rank/projector assumptions, and whether the claim is a supremum,
      bound, exact value, or asymptotic limit.
- [ ] M14/M15 witnesses satisfy the declared operator and closure budgets and
      really use independently selectable laws.
- [ ] M20 freezing additional unit projected leaves preserves both budgets and
      does not silently change the admissible class.
- [ ] M21 tags are not conflated with the rank-one/common-leaf class of M22/M23.
- [ ] The negative statements about novelty, low-eta M23, `k>=4`, and growing
      trees are preserved as open rather than inferred closed.

## Authority status

This sheet is an internal review aid. It does not change theorem statuses,
novelty statuses, or approval fields. The repository continues to record
`NOVELTY_NOT_ESTABLISHED` and `PENDING_HUMAN_REVIEW`.
