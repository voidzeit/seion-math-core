# Source-Resolved Error Calculus for Projected Multilinear Computational Graphs

This is the canonical theorem package for the frozen finite core. Historical
labels P5–P7C are implementation milestones, not separate mathematical
objects.

## Definition — source polynomial

For a finite multilinear DAG with labelled local source directions,

```text
P_G(t) = sum_{alpha != 0} A_{G,alpha} t^alpha.
```

The multi-index records source multiplicity. P6B computes this polynomial
exactly for finite declared graphs and supplies certified order truncations.

## Theorem package

1. **Exact DAG provenance.** Topological convolution reconstructs the finite
   source polynomial; recursive unrolling agrees coefficient-by-coefficient.
2. **First-order source recombination.** Same-source path operators aggregate
   before norm, giving `B_source <= B_path`.
3. **Signed compositional refinement.** For `F=sum_j c_j T_j`, coefficient-wise
   signed aggregation gives `B_actual <= B_signed <= B_treewise`.
4. **Defect instantiation.** Associator, the declared three-term Jacobiator,
   and the declared Filippov defect are instances of the same signed engine.
5. **Approximate-law budget.** Representation, closure, and their interaction
   are separately bounded under the declared homogeneous hypotheses.
6. **Certified norm interfaces.** Certificate selection uses only individually
   sound upper enclosures.

The statements are finite-dimensional and conditional on their declared
hypotheses. They do not assert global sharpness, universal Jacobi/Filippov
identity satisfaction, or theorem-level novelty.
