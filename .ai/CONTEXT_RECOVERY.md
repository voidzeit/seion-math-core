# Context recovery contract

When a session is interrupted, recover in this order:

1. `AGENTS.md` and `governance/PROJECT_MANIFEST.yaml` for scope;
2. `.ai/CURRENT_STATE.md`, `.ai/TASKS.md`, and `.ai/KNOWN_BLOCKERS.md` for
   durable state;
3. `.ai/DECISIONS.md` and `.ai/RISK_REGISTER.md` for constraints;
4. `claims/claims_registry.yaml` and `claims/theorem_registry.yaml` for
   epistemic status;
5. `artifacts/index/governance_audit.json`, if present, for the last structural
   audit;
6. the latest relevant run's `summary.md`, `final_metrics.json`, and
   `artifact_hashes.json`.

Runtime prompts, terminal scrollback, and generated context packs are not
canonical memory. If a fact cannot be recovered from these sources, mark it
unknown and create a blocker rather than guessing.
