# P7A — First-order signed source / associator certificate

## Scope

Represent a signed forest, such as the two bracketings of an associator, by
first-order source operators `A_{alpha,s}` and signed coefficients `c_alpha`.
For each source `s`, aggregate the signed operators before taking a norm:

```text
A_signed,s = sum_alpha c_alpha A_{alpha,s}.
```

For source vectors `epsilon_s`, define

```text
B_signed = sum_s ||A_signed,s|| ||epsilon_s||.
```

The treewise triangle certificate is

```text
B_treewise = sum_alpha |c_alpha| sum_s
              ||A_{alpha,s}|| ||epsilon_s||.
```

## Theorem (P7A)

Under the finite-dimensional first-order source-linear model,

```text
B_signed <= B_treewise.
```

Thus a signed source certificate is sound and is never weaker than applying
the triangle inequality to each signed tree before source aggregation.

## Proof

For every source `s`, the operator triangle inequality gives

```text
||sum_alpha c_alpha A_{alpha,s}||
    <= sum_alpha |c_alpha| ||A_{alpha,s}||.
```

Multiplying by `||epsilon_s||`, summing over sources, and exchanging the two
finite sums yields the stated inequality.

## Strict cancellation witness

Take two terms with the same source operator `A`, coefficients `+1` and `-1`.
Then `A_signed=0`, so `B_signed=0`, while `B_treewise=2||A|| ||epsilon||`.
This is the minimal associator-style cancellation witness and is covered by
the P7A tests.

## Boundary

P7A is a first-order signed-source theorem. It does not establish the exact
nonlinear associator constant, Jacobiator/Filippov bounds, or a universal
optimal cancellation certificate. It preserves the historical status of those
questions as open.
