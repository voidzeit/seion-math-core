# Finite sharpness registry

The registry stores evidence as bands

```text
L_T(eta) <= C_T^P(eta) <= U_T(eta).
```

New constructions may increase `L`; new theorems may decrease `U`. A merge
rejects a looser upper bound, inconsistent cells, or a lower bound above the
upper bound. The status is derived from the band:

- `EXACTLY_DETERMINED_POSITIVE` only when the gap closes;
- `EXACTLY_ZERO_BY_THEOREM` when the upper bound is zero;
- `POSITIVE_LOWER_BOUND_WITH_NONZERO_GAP` otherwise;
- `NO_POSITIVE_LOWER_BOUND_OBTAINED` for a trivial lower bound.

The current restricted gated-planar records are lower constructions paired
with the universal upper bound. They do not establish global fixed-eta
sharpness, dimension reduction, or extremizer universality.
