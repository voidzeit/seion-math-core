# Shared-DAG certificate probe — 2026-08-09

Status: exploratory and not preregistered. The raw output is
`dag_certificate_probe_2026-08-09.json`; the executable design is
`experiments/run_dag_certificate_probe.py` and the configuration is
`experiments/configs/dag_certificate_probe_2026-08-09.yaml`.

## Design

The probe uses a finite tensor-network diamond with four internal nodes. The
node `u` is evaluated once and feeds both `left` and `right`; the root is not
projected. Twenty random seeds, 100 normalized fitting samples, 300
normalized held-out samples, seven budgets, and three methods were evaluated:

- `global_certificate_optimal`: exact DP for the global bounded-domain
  certificate, using only the fitting projectors and the declared leaf norm
  domain;
- `rank_aware_certificate_optimal`: exhaustive small-DAG oracle for the
  rank-aware certificate, which also tracks projected value bounds;
- `uniform`: round-robin rank allocation under the same integer budget.

The Frobenius norm of each core is used as a valid, conservative multilinear
operator enclosure. The held-out batch is used only for evaluation.

## Result

There are 420 method records, or 140 matched seed/budget pairs.

| Quantity | Result |
|---|---:|
| Certificate holds on held-out sup error | 140/140 = 1.000 for both certificate allocators |
| Rank-independent allocator better than uniform, sup error | 15.7% |
| Rank-aware allocator better than uniform, sup error | 16.4% |
| Rank-independent allocator better than uniform, RMS error | 10.0% |
| Rank-aware allocator better than uniform, RMS error | 10.0% |
| Mean sup-error reduction, rank-independent vs uniform | -0.007571 |
| Mean sup-error reduction, rank-aware vs uniform | -0.007448 |

Both certificate allocators therefore lose on average in this finite probe;
the rank-aware coupling gives only a small change. This is a negative control
for any claim that a mathematically valid certificate implies universal
allocator superiority. The result supports sound domain certification and
shared-DAG accounting, but not an industrial or uniformly optimal policy.
