# P6B — Exact higher-order source polynomial on finite multilinear DAGs

## Formal representation

Each local source `s` is represented by a fixed vector `epsilon_s` and a
formal scalar amplitude `t_s`. A provenance monomial is indexed by a
multi-index

```text
alpha = (alpha_s)_{s in S},       |alpha| = sum_s alpha_s.
```

Its evaluated vector coefficient is denoted `A_{v,alpha}[epsilon^alpha]`;
the implementation stores the already-evaluated vector coefficient for the
declared source directions and retains `alpha` exactly.

## Theorem (P6B, finite exact form)

For a finite acyclic graph of finite-dimensional multilinear laws, with
labelled local source vectors and recursively projected baseline states, the
error at every node admits a finite expansion

```text
Delta_v(t) = sum_{alpha != 0} C_{v,alpha} t^alpha.
```

The coefficients are computed in topological order. If the ordered inputs of
`v` have baseline states `R_i` and source polynomials `D_i`, form the finite
Cartesian expansion of

```text
mu_v(R_1 + D_1(t), ..., R_a + D_a(t)).
```

When terms from different slots have indices `alpha` and `beta`, their
provenance is merged by addition:

```text
alpha + beta.
```

This is a multi-index sum, not set union, so repeated use of the same source
correctly creates `alpha_s=2,3,...`. The constant term is removed from the
error and replaced by the local closure residual `(I-P_v)mu_v(R_1,...,R_a)`;
explicit local sources are added as degree-one terms. At a projected output,
the root projector is applied to every retained coefficient, annihilating the
root-local normal residual.

## Tree reduction

If every DAG node has at most one consumer and no source is reused in two
slots, each multi-index records the subset of erroneous child slots. The P6B
convolution therefore reduces to the existing tree subset expansion. P6B is a
strict generalization because a shared source can have multiplicity greater
than one.

## Exact reference check

The implementation has two paths:

1. a cached topological evaluator that computes every DAG node once;
2. a deliberately slow recursive evaluator that unrolls shared dependencies.

For small graphs, coefficients and baseline states must agree coefficient by
coefficient in FP64. This is a validation oracle, not the scalable algorithm.

## Certified order truncation

For any order `p`, including `p=1,2,3`, define

```text
Delta = Delta^(<=p) + R^(>p).
```

For supplied amplitudes, the implementation returns the finite omitted-term
bound

```text
||R^(>p)|| <= sum_{|alpha|>p}
               ||C_alpha|| prod_s |t_s|^(alpha_s).
```

This is a certified triangle bound over all omitted terms. No term is silently
dropped. The current result is exact for finite declared DAGs; scalable tail
envelopes for an implicitly infinite or parametrically generated expansion
remain future work.

## Boundary

P6B does not yet provide a nonlinear signed associator theorem. That is P7B.
It also does not claim a universal sharp constant, validated multilinear
operator norms, or a continuum/infinite-composition result.
