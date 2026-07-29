# Finite ternary vertical slice

`finite_ternary_v1.yaml` uses a block-supported ternary tensor with a known rank-two invariant subspace. The certificate compares the known projector with random, PCA, and an empirical closure-minimizing Stiefel search. It also evaluates the five-input associator, cyclic defect, a CP approximation, and a complex128 repeat.

The expected known-projector closure leakage is zero up to numerical roundoff. The optimizer comparison is empirical and seed-dependent.

