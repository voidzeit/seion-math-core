# P10 — Approximate-law error budget

For an exact law `mu` and an approximation `mu_hat` with

```text
||mu - mu_hat||_op <= delta,
||mu||_op <= M,
||closure||_op <= rho,
```

the implementation separates three certified contributions:

```text
closure_contribution
representation_contribution
interaction_contribution
```

For `k` internal nodes and leaf product `L`, with `c=k` for an ambient output
and `c=k-1` for a projected root,

```text
representation = k delta (M+delta)^(k-1) L
closure        = c rho M^(k-1) L
interaction    = c rho ((M+delta)^(k-1)-M^(k-1)) L
```

The reported total is their sum. The nodewise API is a conservative reduction
using maxima of declared nodewise bounds; it is sound but not claimed optimal.
This keeps closure leakage separate from representation perturbation and their
recursive interaction.
