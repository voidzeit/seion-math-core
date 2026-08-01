# M4 — signed identity conventions

All constructions below are versioned convention `v5` (matches
`src/seion_core/research_v3/polynomial_forests.py`, unchanged this
session except where noted). "GJI" without further qualification is
never used per the mission's own instruction — every identity below is
tied to its exact source function.

| Name | Source function | Terms | Triangle bound |
|---|---|---|---|
| Binary associator (insertion-difference) | `ternary_associator` | 2 | 2 |
| Anchored binary associator | `anchored_binary_associator` | 2 | 2 |
| Binary Jacobiator (3-term cyclic) | `binary_jacobiator` | 3 | 3 |
| Filippov fundamental identity | `filippov_fundamental_identity` | 4 | 4 |
| Declared 6-term GJI variant | `ternary_declared_gji` | 6 | 6 |

Triangle bound = $\sum_\alpha |c_\alpha|\,(k_\alpha-1)$ (natural units,
unit leaf norms, operator norm $M=1$) — the same quantity
`scripts/tree_constants_v3_pipeline.py::_block_g()` and
`scripts/signed_forest_adversarial_search_v5.py::triangle_coefficient`
both compute; verified they agree (same formula, cross-checked by
reading both implementations).

Two structurally different searches appear in this repository's history
for these identities and must not be conflated:

1. **Structured gated-rotation law** (`rotation_tensor`,
   `src/seion_core/research_v3/extremizers.py`) — used for the k=2/k=3
   exact closed forms in `research/math_closure/k2/`, `k3/`. Verified
   this session: under this specific law, the binary Jacobiator's
   triangle-inequality discrepancy is **exactly zero** for every
   $\eta\in[0,1]$ (a specific-construction fact, not evidence about the
   general extremal question below).
2. **Fully generic i.i.d. random tensors**
   (`scripts/signed_forest_adversarial_search_v5.py::random_normalized_law`)
   — the source of the `derivative_free_constant` values in
   `constants_table.csv`, a genuine (if not exhaustive) search over the
   admissible class of arbitrary bounded multilinear laws.
