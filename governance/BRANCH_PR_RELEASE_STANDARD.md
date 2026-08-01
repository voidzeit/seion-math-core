# Branch, PR, and release standard

- Canonical implementation branch: `program/seion-canonical-repository-v4`.
- Feature branches use `program/` or `codex/`; no history rewrites.
- A PR must include scope, claim/evidence impact, tests, artifacts, blockers, and rollback.
- Releases are fail-closed: `math`, `software`, `dataset`, and `extended` gates are reported independently.
- Automation may prepare a candidate but cannot self-approve a mathematical or human-review gate.
