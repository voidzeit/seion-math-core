# Exploratory majorant-optimizer probe

The additive probe used the two Level 1 synthetic topologies, ten seeds, six
budgets, the same fitting/evaluation split, and 240 paired records. It compared
the existing `pathwise_global` heuristic with the exact optimizer of the
fitted root-excluded pathwise majorant.

| Topology | Pairs | Mean true-error reduction | Candidate better fraction | Mean majorant reduction |
|---|---:|---:|---:|---:|
| chain depth 3 | 60 | 0.3400 | 0.6167 | 0.6443 |
| balanced binary, 4 leaves | 60 | 0.3560 | 0.6333 | 0.6465 |

The candidate never exceeded the fitted majorant of `pathwise_global` in any
pair (`majorant_exactly_no_worse_fraction = 1.0` in both topologies), as
expected from the exact dynamic-program objective. The true-error comparison
is exploratory only: the path factors are empirical directional-derivative
estimates, the candidate may leave unused budget after all non-root nodes reach
full rank, and no universal allocator-optimality or technology-superiority
claim is made.

Raw records and the exact command are retained in
`majorant_optimizer_probe_2026-08-09.json` and
`experiments/run_majorant_optimizer_probe.py`. The preregistered Level 1 raw
records were not modified.
