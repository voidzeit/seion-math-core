# P7C — Generic signed compositional expressions

## Purpose

P7C is an instantiation layer over P6B and P7B. It does not introduce a new
error algebra. It accepts a finite expression

```text
F = sum_j c_j T_j
```

whose terms already have exact finite source polynomials, aligns their full
source multi-index supports, and delegates signed aggregation and truncation
to the P7B engine.

For every multi-index `alpha`, it computes

```text
A_F,alpha = sum_j c_j A_j,alpha.
```

The resulting defect certificate satisfies

```text
B_actual <= B_signed <= B_treewise.
```

No identity is assumed to vanish.

## Instantiations

### Associator regression

```text
T_left - T_right
```

is produced by `make_associator_expression` and reproduces P7B.

### Jacobiator

The declared convention is the standard three-term defect

```text
[x,[y,z]] + [y,[z,x]] + [z,[x,y]].
```

The factory returns `JACOBIATOR_CERTIFICATE`; it does not return “Jacobi
proved” and it does not assume the expression is zero.

### Filippov defect

The factory represents the declared defect convention

```text
T_fundamental - sum_i T_insertion_i
```

and returns `FILIPPOV_DEFECT_CERTIFICATE`. Arity and bracket construction stay
with the caller, so an unsupported convention cannot be silently relabelled.

## Acceptance evidence

The tests cover exact and partial cancellation, no cancellation, repeated
source `s^2`, mixed source `st`, complex data, projected roots, direct
reconstruction, conservative truncation, and a deliberately nonzero
Jacobiator control. The generic associator factory is a regression case, not a
parallel implementation.

## Boundary

The statuses certify the calculated defects under their stated conventions.
They do not establish that the underlying SEION bracket satisfies Jacobi or
Filippov identities universally, nor do they establish nonlinear sharpness.
