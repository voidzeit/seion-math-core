# Decisions

## D-0001 — Keep governance local to SEION Math Core

- **Date:** 2026-07-29
- **Decision:** The other repositories supplied workflow patterns only. No
  governance or integration files are written to them.
- **Reason:** SEION must remain self-contained and reproducible.
- **Evidence:** user scope clarification; `AGENTS.md`.
- **Status:** accepted

## D-0002 — Separate mathematical and software evidence

- **Date:** 2026-07-29
- **Decision:** Mathematical claims live in claims/theorem registries and proof
  files; software/reproducibility claims live in run manifests, schemas, and
  release records.
- **Reason:** A polished runner or artifact ledger cannot substitute for a
  mathematical theorem.
- **Evidence:** `governance/RESEARCH_SOFTWARE_SPLIT.yaml`.
- **Status:** accepted

## D-0003 — Preserve historical runs and deduplicate derived views

- **Date:** 2026-07-29
- **Decision:** Existing run indexes are not rewritten in place. A deterministic
  deduplicated index and audit report are generated alongside them.
- **Reason:** Repeated executions are useful operational history but are not
  independent scientific instances.
- **Evidence:** `artifacts/index/run_index.csv`; `governance/MEMORY_CONTRACT.yaml`.
- **Status:** accepted

## D-0004 — Keep v2 fail-closed until novelty and metadata gates pass

- **Date:** 2026-07-29
- **Decision:** The v2 foundations manuscript is delivered as a rigorously
  scoped draft/not-for-submission artifact, while the software companion is
  the reproducibility output. The strict research audit must remain false
  until a genuinely new theorem and verified author metadata exist.
- **Reason:** Exact invariant restriction, operadic identity inheritance, and
  the spectral gap estimate are standard consequences; a complete numerical
  matrix cannot substitute for theorem-level novelty.
- **Evidence:** `claims/theorem_registry_v2.yaml`,
  `claims/claim_evidence_matrix_v2.csv`,
  `papers/foundations_v2/RESEARCH_BLOCKED.md`,
  `artifacts/research_audit/v2_state.json`.
- **Status:** accepted
