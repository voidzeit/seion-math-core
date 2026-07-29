# Risk register

| ID | Risk | Likelihood | Impact | Control |
|---|---|---:|---:|---|
| R-0001 | Numerical evidence is described as proof. | medium | high | claim-language lint; authority/epistemic separation. |
| R-0002 | Duplicate runs inflate apparent sample size. | high | high | deterministic run deduplication and unique-seed reporting. |
| R-0003 | Generated paper output is edited manually and loses provenance. | medium | high | regenerate tables/figures from artifacts; hash release outputs. |
| R-0004 | Existing dirty artifacts are attributed to a later session. | medium | medium | record baseline commit/worktree state in `.ai/CURRENT_STATE.md`. |
| R-0005 | External applications expand the mathematical scope without proof. | medium | high | scope contract and research/software split. |
