# Schema migration log

Frozen under `governance/EVIDENCE_CONTRACT_V1.md` (SEION V5 Phase 2). Any
change to a file hashed in `SCHEMA_FREEZE_MANIFEST.json` must be recorded
here in the same commit, with the manifest regenerated via
`python scripts/freeze_schema_manifest.py`. `tests/governance/test_evidence_contract.py`
fails closed if the two drift apart without a matching entry here.

## v1 — 2026-07-30 — initial freeze

Froze the 9 pre-existing `schemas/*.json` files as-is (no content change)
plus the new `scientific_instance.schema.json` (scientific_instance_id /
execution_id / optimizer_restart_id / seed / precision / hardware /
code_commit / script_hash / config_hash / model_state_hash /
checkpoint_lineage / input_hashes / output_hashes / eval_mode /
is_resumed / restore_rng, per mission section 2). No existing claim
status vocabulary (`ALLOWED_CLAIM_STATUSES` in
`src/seion_core/certification/claims.py`) was changed — see
`governance/EVIDENCE_CONTRACT_V1.md` §3 for why that is deliberately
deferred rather than silently rewritten.
