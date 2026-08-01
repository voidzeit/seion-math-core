# M1 — independent implementation comparison

Driver: `scripts/math_closure_m1_gji_symbolic.py`. Both methods operate on
the literal `Tree` objects returned by
`ternary_declared_gji()` in `src/seion_core/research_v3/polynomial_forests.py`
(not a hand-transcribed copy), eliminating transcription risk.

## Method A — tensor-symbolic (sympy)

Represents `mu` as a fully free rank-4 symbolic tensor (one `sympy.Symbol`
per entry) and every leaf as a fully free symbolic vector. Evaluates the
tree recursively via direct index-sum substitution (an explicit triple
loop per contraction, not `sympy.tensor`/`Indexed`), then
`sympy.expand()`s each output component. Zero iff every component
simplifies to the literal integer `0`.

## Method B — monomial-dictionary (no sympy polynomial engine)

An independent code path that never calls into sympy's `expand`/
`simplify`. Manually enumerates every `(output-index, inner-mu-entry,
outer-mu-entry, leaf-component)` assignment as a dictionary key (role of
each `mu` application — `"outer"`/`"inner"` — tagged once from the tree's
own structure at expansion time, **not** re-derived later from index
values, which would be unsound: index values are small integers 0..n-1
and coincide by chance without indicating shared structural role — an
earlier draft of this script had exactly that bug and was caught by
cross-checking against Method A on a concrete numeric instance before
trusting either). Signed integer coefficients are summed per canonical
key; the polynomial is zero iff the resulting dictionary is empty.

## Cross-check against the repo's own evaluator

Before trusting either symbolic method, both were validated against
`seion_core.research_v3.exact_evaluation.evaluate_ambient_numpy` (the
repo's own reference evaluator) on concrete random floating-point data,
term-by-term, for all 6 terms of the forest — exact match confirmed
(see session transcript / reproducible via
`scripts/math_closure_m1_gji_symbolic.py`). This is what surfaced that the
prior numerical finding was a genuine methodological artifact (rank-1
projector forcing collinear leaves) rather than evidence for a general
identity — Methods A and B, run on fully generic (non-collinear) symbolic
data, disagree with the "evaluates to ~0" claim, and an exact rational
counterexample confirms this decisively (`97/3` in both output
components, no floating point involved).

## Agreement

| Claim | Method A | Method B | Agree? |
|---|---|---|---|
| General identity ($n=2$) | nonzero | nonzero | yes |
| General identity ($n=3$) | nonzero | nonzero | yes |
| Collinear sub-identity ($n=2$) | zero | n/a (Method B targets the general claim only) | — |
| Collinear sub-identity ($n=3$) | zero | n/a | — |

Method B was not re-derived for the collinear specialization since
Method A's collinear proof is a direct symbolic substitution
($L_i \to c_i q$) into the same generic-tensor machinery already
independently cross-validated above, and the collinear result is also
proved by hand (see `exact_proof_or_counterexample.tex`) — a third,
fully independent, non-computational check.

## Mutation tests

Four mutations applied to the collinear construction (`flip_sign`,
`exchange_input`, `omit_term`, `change_slot`) — full results and the
explanation for the one non-rejecting mutation
(`exchange_input`, a genuine invariance of the collinear case, not a
verifier weakness) are in `mutation_test_report.json`.
