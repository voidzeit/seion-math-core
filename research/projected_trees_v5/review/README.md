# Projected Graphs V5 — review hub

This directory is the canonical handoff surface for independent mathematical
and prior-art review. Nothing here constitutes approval. Current authority
remains `PENDING_HUMAN_REVIEW` and `NOVELTY_NOT_ESTABLISHED`.

## Start here

1. [External review request](EXTERNAL_REVIEW_REQUEST_TEMPLATE.md)
2. [Independent-review packet](REVIEW_PACKET_2026-08-08.md)
3. [Objective requirements audit](OBJECTIVE_REQUIREMENTS_AUDIT_2026-08-09.md)
4. [Internal theorem audit](INTERNAL_THEOREM_AUDIT_2026-08-09.md)
5. [Normalization and scope sheet](NORMALIZATION_SCOPE_SHEET_2026-08-09.md)
6. [Frozen review artifact manifest](REVIEW_ARTIFACT_MANIFEST_2026-08-09.md)
7. [Neutral external-reviewer shortlist](EXTERNAL_REVIEWER_SHORTLIST_2026-08-09.md)

## Mathematical sources

- Main paper: `papers/projected_graphs_v5/projected_multilinear_trees_v5.tex`
- Theorem registry: `claims/theorem_registry_v5.yaml`
- Novelty matrix: `research/projected_trees_v5/novelty/THEOREM_TO_THEOREM_MATRIX.md`
- Bounded novelty search: `research/projected_trees_v5/novelty/TARGETED_AUDIT_2026-08-08.md`
- M8 dossier: `research/math_closure/k2/saturation_iff_theorem.tex`
- M14--M20 dossiers: `research/math_closure/k3/m14_exact_chain_constant.tex` through
  `m20_k3_arbitrary_arity_exact_constant.tex`
- Optional M21--M23 dossiers: `m21_same_law_tagged_exact_constant.tex`,
  `m22_same_law_rank_one_high_eta.tex`, and
  `m23_rank_one_same_law_chain_operator_reduction.tex`

## Verification commands

```powershell
python -m pytest tests/math_closure -q
python -m pytest tests/math_closure/test_m20_k3_arbitrary_arity_exact_constant.py tests/math_closure/test_m21_same_law_tagged_exact_constant.py tests/math_closure/test_m23_rank_one_same_law_chain_operator_reduction.py -q
powershell -ExecutionPolicy Bypass -File scripts/verify_projected_graphs_v5_papers.ps1
powershell -ExecutionPolicy Bypass -File scripts/verify_projected_trees_v5_review_manifest.ps1
python -m seion_core.cli.main governance audit --json
python -m seion_core.cli.main governance dedupe-runs
```

Tests and scripts support the proofs; they do not replace proof review or
establish novelty. The applied tensor benchmark is deliberately separated from
the mathematical review because it has predictive evidence but no general
allocator-superiority result.

Applied status and the required next matched-error study are summarized in
`applications/adaptive_tensor_network/results/APPLIED_VALIDATION_STATUS_2026-08-09.md`.
