# P1 — equality/slack audit

The projected-root proof contains one exact cancellation and several norm
inequalities.

| Step | Type | Equality requirement |
|---|---|---|
| `P(I-P)=0` | exact identity | none beyond orthogonal projection |
| projection contractivity | inequality | realized vector lies in `im(P)` or is zero |
| telescoping triangle inequality | inequality | all nonzero replacement terms are positively collinear |
| multilinear operator norm | inequality | realized tuple attains the operator norm |
| closure-map norm | inequality | projected tuple attains the closure norm |
| state induction | inequality | every ancestor composition/projection preserves the realized norm |
| source accumulation | inequality | all non-root sources and gains saturate compatibly |

Therefore the root source disappears exactly, but the universal coefficient
`k-1` is sharp only if all remaining equality conditions are compatible. That
compatibility is not established for the general fixed-eta class.

Result: `AUDITED_NOT_SHARP`.
