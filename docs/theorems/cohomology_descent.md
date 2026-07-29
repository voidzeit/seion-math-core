# Finite cohomology descent

## Statement — `THM_COHOMOLOGY_DESCENT_FINITE_V1` (`PROVED_UNDER_ASSUMPTIONS`)

Let `d:C^k -> C^{k+1}` be a finite cochain complex with `d^2=0`, and let `T:C^k -> C^k` satisfy `Td=dT` on the relevant degrees. Then `T` maps cycles to cycles and boundaries to boundaries, hence defines a map on `ker(d)/im(d_prev)`.

## Proof

If `d v=0`, then `d(Tv)=T(dv)=0`, so cycles are preserved. If `v=d u`, then `T v=T d u=d T u`, so boundaries are preserved. The quotient map is therefore well-defined. No claim about infinite-resolution limits follows.

