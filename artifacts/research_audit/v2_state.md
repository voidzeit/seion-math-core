# Research v2 audit

Generated: `2026-07-29T16:20:43.936309+00:00`.

Strict gate: **FAIL-CLOSED**.

The v2 numerical and reproducibility checks are evaluated separately from the novelty gate. A complete run matrix does not turn standard consequences into a new theorem.

## Checks

- `all_registered_runs_complete`: `True`
- `five_seeds_for_principal_groups`: `True`
- `bound_rows_respect_bound`: `True`
- `cpu_gpu_parity_rows_complete`: `True`
- `cpu_gpu_error_below_tolerance`: `True`
- `required_vector_figures_present`: `True`
- `paper_pdfs_present`: `True`
- `rendered_pages_present`: `True`
- `claim_matrix_present`: `True`
- `dependency_matrix_present`: `True`
- `blocked_status_is_explicit`: `True`
- `legacy_history_not_modified_by_runner`: `True`

## Evidence

- Runs: `180` total, `180` complete, `0` bound violations.
- Unique scientific instances: `100`.
- Maximum bound tightness ratio: `0.7100467992738069`.
- Maximum recorded CPU/GPU discrepancy: `1.4210854715202004e-14`.
- Vector figure pairs: `9/9`.
- Rendered PNG pages/previews: `39`.

## Scientific blockers

- `V2-B-0001` — **Theorem-level novelty is not established** (claims/theorem_registry_v2.yaml and papers/foundations_v2/RESEARCH_BLOCKED.md).
- `V2-B-0002` — **Author email and ORCID remain unverified** (papers/foundations_v2/main.tex front matter).

The foundations PDF is therefore a draft/not-for-submission artifact; the software companion is the appropriate reproducibility deliverable until a genuinely new theorem and verified author metadata are supplied.
