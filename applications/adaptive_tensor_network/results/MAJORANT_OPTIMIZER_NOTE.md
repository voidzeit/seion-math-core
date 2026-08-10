# Exact optimization of the fitted pathwise majorant

The adaptive application now includes `pathwise_majorant_optimal_allocation`.
For fixed fitted singular spectra and fixed empirical path factors, its
objective is the finite separable sum

\[
  \mathcal B(r)=\sum_{v\ne r_\mathrm{root}}
  h_v\sqrt{\frac{1}{N}\sum_{j\ge r_v}s_{v,j}^2}.
\]

The implementation solves the integer rank-allocation problem exactly by
dynamic programming. The root is fixed at rank one because the network's
reduced forward pass does not project the root. This is an exact optimization
of the declared fitted-data majorant, not an exact optimization of held-out
root error and not a universal allocator-optimality theorem. The empirical
path factors remain a diagnostic estimate; replacing them with validated
operator-norm enclosures is required for a formal application certificate.

The preregistered Level 1 records are preserved unchanged. The new policy is
an additive follow-up method and must receive its own preregistered comparison
before any performance claim is made.
