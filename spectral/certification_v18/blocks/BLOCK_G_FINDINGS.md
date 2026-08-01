# Block G (n-ary closure) — v18 findings

Upgraded from the legacy's 8-16 random trials to: a 2000-sample empirical
distribution (mean/std/quantiles/worst), an exact zero-law sanity floor
(defect exactly 0), and adversarial gradient ascent search for the
worst-case defect over inputs constrained to the subspace (unit-norm
combinations of `U`'s columns). `test_adversarial_search_finds_at_least_as_bad_as_random_worst`
confirms the adversarial search is at least as strong as the best random
sample, i.e. it is not a strictly weaker check dressed up as one.

Exhaustive small-case / interval-arithmetic certified upper bounds (mission
section 2G) were not attempted this pass — the CP law's closure defect is a
degree-`2*arity` polynomial in the input coefficients, and a genuine SOS/
interval certified bound needs a dedicated small-arity symbolic pass;
tracked as follow-up, not silently claimed.

## Gate status

`algebra_gate` contribution: `STATISTICALLY_VALIDATED_PASS` for the
empirical (large-sample + adversarial) closure claim on the tested
configuration (n=16, rank=4, single seed); `PASS_CERTIFIED` (a validated
worst-case bound) is explicitly NOT claimed — no interval/SOS bound was
derived.
