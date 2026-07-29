# Memory governance

Durable memory is a controlled interface between sessions, not a transcript.

## Write rules

- Write only durable conclusions, decisions, blockers, and exact recovery
  instructions.
- Every current-state assertion names when it was observed, how it was checked,
  and what it does not establish.
- Append corrections and mark superseded records; do not erase history.
- Generated context packs and runtime scratch are disposable.
- Claims and theorem status remain in `claims/`; `.ai/` records navigation and
  project state, not mathematical authority.

## Health rule

Memory is healthy only when the manifest, ownership matrix, recovery contract,
and required registries exist and the governance audit can reconstruct the
project state without terminal history.
