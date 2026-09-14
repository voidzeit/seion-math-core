# P6A — First-order source-aware vector DAG certificate

## Scope

P6A is a theorem for the first-order source-linearized error layer of a
finite-dimensional, finite acyclic computational graph. It does not include
higher-order multilinear interactions between source errors; those remain the
P6B track.

Let `G=(V,E)` be a typed DAG with root `r`. For each edge `u -> v`, let
`H_{v,u}` be the linearized operator from the error space of `u` to that of
`v`. Let `L_{v,s}` be the local linearized operator by which source error
`epsilon_s` enters node `v`. The first-order coefficient operators are defined
in topological order by

```text
A_{v,s} = L_{v,s} + sum_{u -> v} H_{v,u} A_{u,s}.
```

For a projected observable at the root, the root-local source term is omitted
(`L_{r,s}=0` for the observable certificate), matching the exact
`P_r(I-P_r)=0` cancellation in the projected-tree theory.

## Theorem (P6A)

For every source `s`, the first-order error at node `v` is exactly

```text
Delta_v^(1) = sum_s A_{v,s} epsilon_s.
```

Consequently, at the root,

```text
||Delta_r^(1)|| <= B_source
                         := sum_s ||A_{r,s}|| ||epsilon_s||.
```

Define the pathwise scalar recurrence

```text
p_{v,s} = ||L_{v,s}|| + sum_{u -> v} ||H_{v,u}|| p_{u,s}.
```

Then

```text
||A_{r,s}|| <= p_{r,s}
```

for every source, and therefore

```text
B_source <= B_path
          := sum_s p_{r,s} ||epsilon_s||.
```

The coefficient maps and both bounds are computed by forward dynamic
programming in `O(|V|+|E|)` graph traversals, with matrix multiplication cost
accounted for separately.

## Proof sketch

The coefficient identity follows by induction on a topological ordering. At a
source entry it is the local operator `L_{v,s}`. At an internal node, linearity
of the first-order recurrence distributes each incoming coefficient over its
edge operator, giving the displayed recurrence. The norm inequality follows
from `||sum_i X_i|| <= sum_i ||X_i||` and submultiplicativity. The source-aware
certificate performs the sum of operators for a shared source before taking a
norm; the pathwise certificate takes the norm at every path merge. Thus its
dominance is a direct triangle-inequality consequence, not an empirical claim.

## Strictness witness

In the diamond graph `u -> a`, `u -> b`, `(a,b) -> r`, choose scalar operators
`H_{a,u}=1`, `H_{b,u}=-1`, and `H_{r,a}=H_{r,b}=1`. The two paths carry the
same source with opposite signs. Their aggregated root coefficient is zero,
so `B_source=0`, while `B_path=2 ||epsilon_u||` (equal to `4` for
`epsilon_u=2`). This is a strict source-correlation/cancellation improvement.

## Boundary

P6A is not a theorem about the full nonlinear multilinear error polynomial.
It does not certify higher-order source products, arbitrary nonlinear gates,
or a universal sharp constant. Those are deliberately left open for P6B and
later cancellation-aware work.
