# Epistemic policy

Every statement is labeled as a definition, proof, conditional proof, symbolic verification, numerical observation, empirical heuristic, conjecture, open problem, or refutation.

Numerical certificates record a convention, dtype, seed, samples, normalization, condition indicator, and artifact path. They do not upgrade a conjecture or a finite experiment into a theorem. A theorem with assumptions is never rendered as universal.

The paper language linter rejects proof verbs adjacent to claims registered as numerical or empirical.

Operational authority is tracked separately in `governance/AUTHORITY_LADDER.yaml`:
`declared` means registered, `observed` means executed with provenance,
`verified` means a deterministic or exact gate passed, and `approved` means an
explicit scoped release decision. None of these labels changes a claim's
mathematical status.
