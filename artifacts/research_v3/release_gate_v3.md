# V3 strict release gate

- Result: **FAIL_CLOSED_NOVELTY**
- Passed gates: 9/15
- Failed gates: 6/15

## Gate matrix

| Gate | Result | Requirement |
|---:|:---:|---|
| 1 | PASS | projected-root k-1 proved or refuted |
| 2 | FAIL | every sharpness claim has a matching construction |
| 3 | PASS | near-optimal claims have certified declared gaps |
| 4 | FAIL | prior art establishes theorem-level novelty |
| 5 | FAIL | all declared small-case global optima independently certified |
| 6 | PASS | multiple optimizer families executed |
| 7 | PASS | exact tree enumeration complete |
| 8 | FAIL | all mandatory base and extended matrix blocks complete |
| 9 | PASS | no unexplained theorem-bound violation |
| 10 | PASS | run artifacts carry immutable commit and input hashes |
| 11 | FAIL | worktree clean for final rerun |
| 12 | PASS | CPU/GPU float64 parity passes |
| 13 | PASS | every figure is registered and hash-valid |
| 14 | FAIL | four reviewers are at least acceptable as preprint |
| 15 | PASS | latexmk and page-by-page visual inspection pass |

Automation cannot convert this result into human publication approval.
