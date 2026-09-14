# Induced affine connection: curvature, torsion, and associator

## Contract

Let `V` be a finite-dimensional real or complex vector space and let
`star: V x V -> V` be a bilinear product. On the affine space `A(V)`, with
the standard flat derivative `D`, define

```text
nabla_X Y = D_X Y + X star Y.
```

For constant vector fields the Lie bracket vanishes, so the curvature of this
connection is the commutator of left multiplications:

```text
R_affine(x,y) = [L_x,L_y],   L_x(z) = x star z.
```

With

```text
T(x,y) = x star y - y star x
A(x,y,z) = (x star y) star z - x star (y star z)
A-(x,y,z) = A(x,y,z) - A(y,x,z),
```

the exact finite-dimensional identity is

```text
R_affine(x,y)z = T(x,y) star z - A-(x,y,z).
```

This is an algebraic identity. It does not require a metric, positivity,
projectors, or a physical interpretation.

## Coordinate contract

For `e_j star e_k = K[i,j,k] e_i`, the module uses the explicit index order

```text
Gamma[i,j,k] = K[i,j,k]
T[m,j,k] = K[m,j,k] - K[m,k,j]
R[i,l,j,k] = K[m,k,l] K[i,j,m] - K[m,j,l] K[i,k,m].
```

Thus `R[i,l,j,k]` is the coefficient of `e_i` in
`R_affine(e_j,e_k)e_l`. The implementation also exposes the component
residual for `R = T star - A-`.

## Convention boundary

`seion_core.geometry.induced_curvature.curvature_operator` intentionally keeps
the older algebraic convention

```text
R_standard(x,y) = [L_x,L_y] - L_[x,y].
```

It is not the raw curvature of `D + star` on an affine space. The two APIs are
kept separate so that the subtraction of `L_[x,y]` is never introduced or
removed silently.

## Metric and ternary extensions

For a metric matrix `G(x)`, metric compatibility is checked as

```text
partial_i G - L_i^* G - G L_i = 0,
```

where `*` is transpose over the reals and conjugate transpose for a Hermitian
form. Curvature integrability is checked by `R_jk^* G + G R_jk = 0`.

Given a ternary law `mu_3`, `anchored_bilinear_law` contracts its third input
with an anchor `u` and returns the binary product `star_u(x,y)=mu_3(x,y,u)`.
The binary identity then applies without conflating it with a four-input
ternary associator.

## Verification

The executable contract is implemented in
`src/seion_core/geometry/affine_connection.py` and exercised by
`tests/unit/test_affine_connection.py` for random dense products, a
non-commutative associative matrix algebra, variable one-dimensional metric
compatibility, anchored ternary laws, malformed dimensions, and a commuting
but non-associative curved example.
