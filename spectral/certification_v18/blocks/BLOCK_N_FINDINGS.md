# Block N (cyclic law and GJI) — v18 findings

Raw (pre-averaging, `cp_raw`) vs symmetrized (`forward`) cyclic defect,
reported separately (n=16, rank=4, cp_rank=4, seed=0, 100 trials):
**raw_defect_mean = 4.60**, **symmetrized_defect_mean = 8.2e-33** (machine
precision zero). The ~31-order-of-magnitude gap is the headline finding:
near-zero cyclic defect after explicit cyclic averaging is exactly what
`forward()`'s construction guarantees for ANY CP parameters — it is a
`STRUCTURAL_IDENTITY_PASS`, never evidence that cyclic symmetry was
learned. The raw defect (large, nonzero) is the honest measure of how far
the underlying (unsymmetrized) law is from cyclic-symmetric before the
averaging is applied.

**GJI_v18** (one exact, versioned formula: full antisymmetrization of the
associator over all 6 permutations of 3 arguments, signed by permutation
parity) is implemented twice, independently (`itertools.permutations` +
parity vs. a manually-unrolled 6-term expression matching the legacy
script), and the two agree to **2.8e-16 relative difference** (machine
precision) across 100 random trials — confirms the formula is
unambiguous and correctly implemented both ways. A permutation mutation
test (deliberately flipping one term's sign) is confirmed detected (the
mutated and correct formulas disagree well above tolerance), so the
cross-check is not vacuous.

`gji_ratio` (||GJI||^2 / sum of the 6 individual associator norms^2): mean
0.43 over random trials, adversarial max **5.98** — notably, this ratio is
NOT bounded by 1 in general, meaning the normalization convention chosen
here does not itself yield a sharp constant; determining the supremum of
this ratio (if finite) is an open question this pass does not resolve
(would need either an analytic argument or a much larger adversarial/
interval search, tracked as follow-up).

## Gate status

`algebra_gate` contribution: `STRUCTURAL_IDENTITY_PASS` for the
symmetrized cyclic defect (never re-labeled as learned evidence);
`EXACT_CERTIFICATE`-tier for the GJI formula's internal consistency (two
independent implementations agree to machine precision, confirmed by a
passing mutation test); `EMPIRICAL_SCREENING_PASS` only for the GJI ratio
magnitude claim, with its supremum explicitly `OPEN`.
