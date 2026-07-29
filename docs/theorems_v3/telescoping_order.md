# Optimal telescoping order

For one multilinear replacement step, let (e_i\ge0) bound the error in slot
(i), (r_i\ge0) the recursively projected child magnitude, (f_i\ge0) the
ambient child magnitude, and (G_i\ge0) a slot/output-specific gain.  Put
(w_i=G_ie_i).  For an order (pi), define

\[
C(\pi)=\sum_t w_{\pi_t}
  \prod_{s<t}r_{\pi_s}\prod_{s>t}f_{\pi_s}.
\]

Consider adjacent slots (i,j).  All prefix and suffix factors are common, so
(i) before (j) is no worse exactly when

\[
w_i f_j+r_iw_j\le w_jf_i+r_jw_i
\iff
w_i(f_j-r_j)\le w_j(f_i-r_i).
\]

Let (d_i=f_i-r_i).  A globally optimal order is obtained as follows:

1. slots with (d_i>0), sorted by (w_i/d_i) increasingly;
2. slots with (d_i=0,w_i>0);
3. slots with (d_i<0), again sorted by (w_i/d_i) increasingly.

Slots with (d_i=w_i=0) are indifferent and receive a deterministic position.
The cross-sign order follows directly from the exchange inequality: positive
(d) precedes negative (d), with the nonzero zero-denominator class between.
Within either nonzero sign class, division by (d_id_j>0) yields increasing
(w_i/d_i).  Repeatedly exchanging adjacent inversions cannot increase the
cost and terminates at the stated order, proving global optimality for this
scalar certificate.

This theorem optimizes the declared telescoping upper bound; it does not claim
that the resulting bound is the exact error of a fixed law.  Deterministic
tests compare the sorted order with all permutations for random positive,
zero, and negative denominators through arity seven.
