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

## Remaining open questions

- repeated-law/shared-map k=2 sharpness;
- higher-arity k=2 sharpness;
- universal dimension/rank reduction;
- k=3 topology-specific global constants;
- globally tight multilinear spectral norms;
- theorem-level novelty.

## Equality/slack conclusion

The simultaneous equality conditions are compatible for independent node laws,
as witnessed by the exact construction. The additional same-law constraint is
not resolved: the repeated-law equality system remains `OPEN`.
