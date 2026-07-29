# Known blockers

| ID | Blocker | Impact | Evidence | Resolution condition |
|---|---|---|---|---|
| B-0001 | The current paper's theorem program is too modest for a competitive research paper. | Research-paper release is blocked. | `paper/quality/paper_quality_report.*`, `claims/theorem_registry.yaml` | A nontrivial central theorem is proved with complete assumptions and counterexamples. |
| B-0002 | Historical run indexes contain repeated executions of identical configurations. | Naive aggregate statistics are invalid. | `artifacts/index/run_index.csv` | Use `seion-core governance dedupe-runs` and report unique-instance counts. |
| B-0003 | Several figures are diagnostic or illustrative rather than dense multi-seed experiments. | Quantitative visual claims are limited. | `paper/generated/figures/`, `claims/claims_registry.yaml` | Rebuild figures from registered multi-seed runs with uncertainty and provenance. |
| B-0004 | Author ORCID and contact metadata are not available in the repository. | Submission metadata is incomplete. | `paper/metadata.tex`, `CITATION.cff` | Add verified author metadata explicitly. |

These blockers are not silently downgraded by successful software tests.
