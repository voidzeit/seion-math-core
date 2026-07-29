# SEION durable memory

`.ai/` is the canonical durable memory for the SEION repository. It records
decisions, current state, risks, tasks, handoffs, and the recovery contract. It
does not replace source code, theorem proofs, claim registries, or run
artifacts; it points to them and records their provenance.

The memory tiers are:

- **durable**: the tracked Markdown/YAML files in this directory;
- **evidence**: immutable or append-only records under `claims/` and
  `artifacts/`;
- **derived**: `.ai/machine/` and `.ai/packs/`, rebuildable from canonical
  sources;
- **runtime**: `.ai/runtime/`, disposable and never a source of truth.

Use `seion-core governance context` before work and the postflight contract
after work. Every state assertion must include an observation date, command or
artifact source, commit when available, and a limitation.
