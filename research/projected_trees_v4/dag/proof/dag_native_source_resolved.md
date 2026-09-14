# DAG-native source-resolved scalar certificate

Let `G=(V,E)` be a finite DAG with nonnegative gain `h_(v,u)` on each
dependency `u -> v`, and nonnegative local source `lambda_v`. Assume

```text
B_v <= lambda_v + sum_(u -> v) h_(v,u) B_u.
```

Compute the forward bounds in topological order. Define reverse weights by

```text
w_root = 1
w_u = sum_(v : u -> v) h_(v,u) w_v.
```

Reverse induction gives the source-resolved certificate

```text
B_root <= sum_u lambda_u w_u.
```

The scalar recurrence is evaluated in `O(|V|+|E|)` time without duplicating
shared sources through tree unrolling. For a projected-root output, set the
root local source to zero because `P(I-P)=0`; upstream sources remain.

## Boundary

This is a scalar certificate theorem. It does not yet provide a
correlation-aware vector/tensor certificate, signed cancellation, or a
sharpness theorem for the underlying multilinear problem.
