# Memory ownership matrix

| Surface | Canonical owner | Agent write mode | Evidence required |
|---|---|---|---|
| Implementation behavior | `src/` and tests | additive code/test change | executed tests |
| Mathematical claim status | `claims/claims_registry.yaml` | explicit registry edit | proof or scoped experiment |
| Theorem dependencies | `claims/theorem_registry.yaml` and generated matrix | registry + generator | proof/counterexample links |
| Experiment design | `experiments/` | registered config/matrix edit | declared hypotheses and controls |
| Run facts | `artifacts/runs/` | runner only | manifest, metrics, certificate, hashes |
| Aggregate indexes | `artifacts/index/` | generator only | source artifacts and command |
| Current project state | `.ai/CURRENT_STATE.md` | postflight/review | command, commit, limitation |
| Decisions | `.ai/DECISIONS.md` | append/supersede | reason and evidence |
| Tasks and blockers | `.ai/TASKS.md`, `.ai/KNOWN_BLOCKERS.md` | explicit planning update | owner/status/resolution condition |
| Paper prose | `paper/` | research-editor workflow | claim mapping and citations |
| Governance policy | `governance/` | explicit policy change | decision record and tests |
