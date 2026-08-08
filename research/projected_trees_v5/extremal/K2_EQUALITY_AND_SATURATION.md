# V5-A1 — k=2 equality and saturation result

For a binary chain with two internal nodes, the projected-root proof has one
propagated child-error contribution. Saturation of the universal coefficient
requires equality in:

1. the inner closure-map norm bound;
2. the outer multilinear operator-norm bound on the normal inner error and
   projected sibling leaf;
3. outer projection contractivity;
4. leaf/state norm induction;
5. the common normalization `rho=eta*M`.

These conditions are compatible when the two laws are independent. In a real
two-dimensional space with `P=diag(1,0)`, let `e0` be projected and `e1`
normal. Set `rho=eta*M` and define

```text
mu_inner(x,y) = M*x1*y1*e0 + rho*x0*y0*e1
mu_outer(x,y) = M*x1*y0*e0.
```

Both laws have operator norm `M`; the inner closure on projected inputs has
norm `rho`; the outer closure on projected inputs is zero. Unit leaves
`e0,e0,e0` give inner ambient state `rho*e1`, inner projected state zero, and
root projected error `M*rho`.

Thus the general independent-law k=2 constant is exactly one in the
normalization `E_proj/(rho*M*L)`. The result is a construction plus the
existing universal upper bound, so it is a theorem for that declared class.
It does not close repeated-law, higher-arity, or dimension-reduction problems.
