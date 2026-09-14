# Post-hoc check — per-node angle expression as a heterogeneous bound

**Status:** `POST_HOC_EXPLORATORY` (not preregistered, `NUMERICAL_OBSERVATION`). Written 2026-09-13 after the V1
results. Reproduce with `python posthoc_heterogeneous_angle.py`. Output:
`artifacts/pmt_tn_benchmark/2026-09-13-v1/posthoc/heterogeneous_angle_check.json`, with input hashes.

## Question

A natural heterogeneous refinement of Theorem R replaces the uniform leakage `η = max_v η_v` by per-node angles
`sin θ_v = η_v` (uniform `M̂`). There are two candidate forms:

```
corner :  |1 − ∏_{v≠r} cos θ_v e^{iθ_v}|
boxmax :  max_{0 ≤ t_v ≤ θ_v} |1 − ∏_{v≠r} cos t_v e^{i t_v}|        (≤ G_k(max_v η_v))
```

Every V1 run stored `corner` as `per_node_angle_expression_exploratory`. The question is whether
`E_obs ≤ expr · M̂^k · L` holds.

## Result: corner form

| campaign | runs | runs with `E_obs` above the corner form | max `E_obs / corner bound` |
|---|---|---|---|
| F1 | 4 224 | 0 | 0.283 |
| F2 | 23 040 | 0 | 0.035 |
| F3 | 2 880 | 0 | 0.634 |
| F4 | 1 152 | 0 | 0.0059 |
| F6 | 400 | 0 | 1 + 4e-16 |
| **F7** | 1 536 | **42** | **1.0124** |
| F7R | 960 | 0 | 0.9994 |

**The corner form is not a valid bound.** All 42 violations are `coiso` F7 runs:

| configuration | violations |
|---|---|
| star, `k = 7` | 33 |
| star, `k = 5` | 5 |
| balanced, `k = 7` | 2 |
| random, `k = 7` | 2 |

The runs combine nodes with `η_v ≈ 1` (so `cos θ_v ≈ 0`) and nodes with `η_v = 0`.
`|1 − ∏ w(θ_v)|` is not monotone in the angles once `Σθ_v > π`. This is the same phenomenon that forces the case
split in the Diagonal Lemma.

## Result: box-max form (frozen instances only)

Only the best restart of each F7 configuration was frozen, so the box-max form could be evaluated on just 2 of the
42 violating runs. In those two the corner excess is marginal (~1e-7). The largest excess, 1.0124, occurred in
restarts that were not frozen.

| instance | `k` | `Σθ/π` | `E/(M̂^k L)` | corner | box max | `G_k(η_max)` |
|---|---|---|---|---|---|---|
| `instance_000551` | 7 | 1.94 | 1.0000 | 0.99999991 | 1.4949 | 1.5096 |
| `instance_000563` | 7 | 1.72 | 1.0000 | 0.99999999 | 1.4731 | 1.5096 |

## Reading

* A heterogeneous certificate must be stated as the **box maximum**, not the corner evaluation.
* The box maximum is automatically `≤ G_k(η_max)`. It improves on Theorem R only when the `η_v` are spread out.
* Two questions remain open:
  * whether the Theorem R proof (multiplicative envelope before the Diagonal Lemma) already implies the box-max
    form node-wise;
  * whether the box-max form holds on all 42 corner violations.
* A clean test needs an F7 rerun that freezes every restart, with the box maximum computed by global optimisation.
