# P7B — Nonlinear signed source-polynomial certificate

## Scope

P7B accepts a finite signed compositional expression

```text
F = sum_j c_j T_j
```

where each `T_j` has an exact P6B source polynomial

```text
P_j(t) = sum_alpha A_{j,alpha} t^alpha.
```

For an associator, the terms are the two bracketings with coefficients `+1`
and `-1`; the implementation is generic so Jacobiator and Filippov instances
can reuse it later.

## Theorem (P7B)

Aggregate coefficients by the complete source multi-index before taking norms:

```text
A_F,alpha = sum_j c_j A_{j,alpha}.
```

For source amplitudes `t`, define

```text
B_signed = sum_alpha ||A_F,alpha|| prod_s |t_s|^(alpha_s).
```

Then the direct signed expression and its certificate satisfy

```text
||sum_j c_j P_j(t)|| <= B_signed <= B_treewise,
```

where

```text
B_treewise = sum_j |c_j| sum_alpha
              ||A_{j,alpha}|| prod_s |t_s|^(alpha_s).
```

The first inequality is the triangle inequality over aggregated monomials.
The second follows coefficient-wise from

```text
||sum_j c_j A_{j,alpha}||
    <= sum_j |c_j| ||A_{j,alpha}||.
```

This preserves cancellation at every retained order, including repeated-source
terms such as `alpha_s=2` and mixed terms such as `alpha_s=alpha_t=1`.

## Truncated certificate

For order `p`, split the aggregated polynomial:

```text
P_F = P_F^(<=p) + R_F^(>p).
```

The implementation reports

```text
truncated_signed_bound = sum_{|alpha|<=p} ||A_F,alpha|| |t^alpha|
remainder_bound         = sum_{|alpha|>p}  ||A_F,alpha|| |t^alpha|
total_certified_bound   = truncated_signed_bound + remainder_bound.
```

The omitted part is never discarded. For a finite exact P6B polynomial, the
sum is finite and the total equals the exact signed bound up to roundoff.

## Strict higher-order cancellation

The tests include:

- first-order cancellation, recovering P7A;
- pure second-order cancellation with `alpha_s=2`;
- mixed second-order cancellation with `alpha_s=alpha_t=1`;
- partial cancellation with a positive signed bound;
- independent sources that remain distinct;
- projected-root polynomials and complex coefficients;
- direct evaluation satisfying `B_actual <= B_signed <= B_treewise`.

## Boundary

P7B certifies signed cancellation for finite source polynomials already
constructed by P6B. It does not yet instantiate Jacobiator or Filippov defects
(P7C), provide a universal nonlinear associator sharp constant, or improve
multilinear operator norms (P8).
