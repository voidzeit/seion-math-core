# P5 — DAG-native scalar certificate

Implemented in `src/seion_core/research_v4/dag_certificate.py`.

The implementation accepts a finite acyclic dependency graph with local source
magnitudes and nonnegative gains. It computes:

1. forward node bounds in topological order;
2. reverse source weights from the root;
3. source-resolved contributions without tree-unrolling;
4. an exact agreement check between forward and source-summed values.

For the diamond graph

```text
u -> v1 -> root
 \-> v2 -> root
```

with local sources `(0.1, 0.2, 0.3, 0.4)` and gains `(2, 3, 4, 5)`, the
certificate returns:

```text
B_root = 5.0
w_u = 23.0
sum(source_contributions) = 5.0
complexity = O(|V|+|E|)
```

The projected-root mode excludes the root local source exactly and retains
upstream sources.

Status: `PROVED_UNDER_ASSUMPTIONS` for the declared scalar recurrence;
vector/tensor correlation-aware and signed cancellation-aware DAG certificates
remain open.
