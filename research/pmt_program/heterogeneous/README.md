# Heterogeneous Theorem R tools

This directory implements the computational part of the proposed nodewise
extension of Theorem R.

For normalized defects `eta_i`, set `alpha_i = asin(eta_i)` and define

```text
G_box(alpha) = max_{0 <= theta_i <= alpha_i}
               |1 - product_i cos(theta_i) exp(i theta_i)|.
```

The code reports three different objects:

1. `exploratory_box_lower`: a value attained by a numerical optimizer. This
   is a lower bound on the scalar maximum, not a proof of global optimality.
2. `exploratory_box_upper`: the uniform Theorem R envelope using the largest
   cap. Since the heterogeneous box is contained in the uniform box, this is
   an upper bound for the scalar problem.
3. `interval_upper_bound`: a branch-and-bound interval enclosure for the
   scalar box. It is tighter than the uniform envelope in many cases, but is
   still numerical interval evidence rather than a formal theorem.
4. `uniform_safe_bound`: a conservative full PMT certificate obtained by
   replacing all nodewise operator and defect bounds by common worst-case
   values. This is the only value used by the discrete allocator to declare a
   plan feasible.

The capped-equal-angle curve

```text
theta_i(tau) = min(alpha_i, tau)
```

is implemented as a candidate, not as a theorem. The current post-hoc
experiments already show why evaluating only the corner `theta_i=alpha_i` is
incorrect: the scalar objective is not coordinatewise monotone after phase
wrap-around.

Example:

```python
from research.pmt_program.heterogeneous import make_certificate

report = make_certificate(
    operator_norms=[1.0, 1.0, 1.0, 1.0, 1.0],
    defects=[0.05, 0.10, 0.30, 0.50],
    leaf_product=1.0,
)
print(report.exploratory_bound)
print(report.uniform_safe_bound)
```

The same report can be reproduced from the command line:

```powershell
py -3.12 -m research.pmt_program.heterogeneous example.json --maxiter 300
```

The JSON output is intended to be auditable: it includes the local normalized
defects, angular caps, the exploratory optimizer point, the scalar envelope,
and the conservative full-tree bound.

The mathematical tasks still open are the heterogeneous upper-bound proof,
the global capped-equal-angle theorem, and sharpness for arbitrary defect
vectors and tree placements.  These must not be inferred from floating-point
optimization.

For a deterministic numerical stress test of the capped-angle hypothesis:

```powershell
py -3.12 -m research.pmt_program.heterogeneous.adversarial_scan --maxiter 80
```

The scan labels its output `NUMERICAL_OBSERVATION`; a zero discrepancy is not
a proof, while a positive discrepancy is a counterexample candidate.
