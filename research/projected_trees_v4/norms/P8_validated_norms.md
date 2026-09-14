# P8 — Validated multilinear norm enclosures

P8 implements a conservative hierarchy for the operator norm of a finite
multilinear tensor. Every returned object records a lower value, an upper
bound, method, certification flag, and gap.

Implemented certified paths:

1. exact rank-one formula when the decomposition is explicitly declared;
2. interval-evaluated Frobenius upper enclosure;
3. flattening induced-norm upper enclosure
   `sqrt(||A||_1 ||A||_inf)`;
4. CP structural upper bound;
5. Frobenius fallback.

Basis-vector evaluations provide attained lower values. They are not promoted
to global optima. Power iteration and alternating optimization are not used
by this module and cannot be labelled exact by the API.

The certificate selector chooses only the minimum among candidates whose
`certified` flag is true. Heuristic lower estimates may be retained as
metadata but are rejected from automatic upper-bound selection.

The general multilinear spectral norm remains open; P8 reduces dependence on
Frobenius where the declared enclosure is tighter but does not claim global
sharpness.
