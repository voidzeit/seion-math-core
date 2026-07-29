# Known blockers

| ID | Blocker | Impact | Evidence | Resolution condition |
|---|---|---|---|---|
| B-0001 | The current paper's theorem program is too modest for a competitive research paper. | Research-paper release is blocked. | `paper/quality/paper_quality_report.*`, `claims/theorem_registry.yaml` | A nontrivial central theorem is proved with complete assumptions and counterexamples. |
| B-0002 | Historical run indexes contain repeated executions of identical configurations. | Naive aggregate statistics are invalid. | `artifacts/index/run_index.csv` | Use `seion-core governance dedupe-runs` and report unique-instance counts. |
| B-0003 | Several figures are diagnostic or illustrative rather than dense multi-seed experiments. | Quantitative visual claims are limited. | `paper/generated/figures/`, `claims/claims_registry.yaml` | Rebuild figures from registered multi-seed runs with uncertainty and provenance. |
| B-0004 | Author ORCID and contact metadata are not available in the repository. | Submission metadata is incomplete. | `paper/metadata.tex`, `CITATION.cff` | Add verified author metadata explicitly. |

These blockers are not silently downgraded by successful software tests.

## V3 strict-gate blockers

| ID | Blocker | Impact | Evidence | Resolution condition |
|---|---|---|---|---|
| B-0005 | Fixed-eta sharpness is open for several nodewise, associator, FI/GJI, and signed-forest constants. | Sharp/optimal theorem language is blocked. | `claims/theorem_registry_v3.yaml`, `artifacts/index/optimality_gaps_v3.csv` | Supply matching constructions or downgrade every affected claim. |
| B-0006 | The bounded prior-art review does not establish theorem-level novelty. | Submission-grade novelty claims are blocked. | `claims/prior_art_registry_v3.yaml`, `docs/prior_art_v3.md` | Independent comprehensive review establishes a genuine difference, or the work remains a draft. |
| B-0007 | Not every declared small case has an independent global-optimality certificate. | Global optimum claims are blocked outside certified rows. | `artifacts/research_v3/block_A_exact_atlas.parquet` | Validate solver/relaxation status independently for every claimed optimum. |
| B-0008 | The extended schedule is resource-gated: 4/460,800 optimizer trajectories and 0/8,400 extended performance cells are complete. | The extended matrix cannot support release claims. | `artifacts/research_v3/extended_progress_v3.json` | Resume to completion under an authorized compute budget with all failures retained. |
| B-0009 | Three of four automated adversarial reviews recommend major revision; there are zero independent human reviews. | Preprint/submission approval is blocked. | `artifacts/reviews_v3/review_summary_v3.json` | Obtain four independent human reviews at least acceptable as preprint and address their findings. |
| B-0010 | A pre-existing user-owned `.obsidian/workspace.json` edit is intentionally preserved. | The literal clean-worktree gate remains false even after SEION deliverables are committed. | `git status --porcelain` | The user decides how to handle that unrelated file; automation must not discard it. |
