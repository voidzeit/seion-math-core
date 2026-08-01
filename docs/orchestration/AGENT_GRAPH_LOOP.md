# Agent graph loop

Executes `governance/DEVELOPMENT_LIFECYCLE.yaml` (8 stages: `intake ->
context -> plan -> change -> verify -> evidence -> postflight -> release`)
and `governance/STATE_MACHINES.yaml`'s matching `development` state enum
as a real, code-checked graph, with `governance/agents/*.yaml` role
manifests bound to the stage(s) they act at. This is a **deterministic
gate/state-machine executor**, not an autonomous multi-agent dispatcher —
it never itself invokes an LLM or spawns a sub-agent. Any agent (Claude,
another coding tool, or a human) drives a task through the graph via the
CLI below; the executor's job is to make every transition, required
piece of evidence, and gate confirmation explicit and logged, never
silently assumed.

## Stages and bound roles

| Stage | State | Roles (`governance/agents/*.yaml`) |
|---|---|---|
| intake | `INTAKE` | *(none yet — task definition, no existing role fits)* |
| context | `CONTEXT` | graph-maintainer, memory-curator |
| plan | `PLANNED` | research-mathematician, prior-art-auditor |
| change | `IN_PROGRESS` | artifact-builder, development-reviewer |
| verify | `VERIFYING` | numerical-verifier, verification-runner, proof-auditor, security-auditor |
| evidence | `EVIDENCE` | experiment-runner |
| postflight | `POSTFLIGHT` | memory-curator |
| release | `RELEASE` | release-auditor, paper-editor, research-editor, visualization-auditor |

`COMPLETED`, `BLOCKED`, `SUPERSEDED` are terminal states with no outgoing
transitions.

## The one loop-back

`VERIFYING -> IN_PROGRESS` is the only legal backward edge: a failed
verify stage routes back to `change`, incrementing a counted retry
(`retry_counts["verify"]`). Once a configurable `max_retries` (default 5)
is exceeded, the session is forced to `BLOCKED` with an explicit
`blocked_reason` — logged to `.ai/evidence/ledger.jsonl` as
`kind=lifecycle_blocked`, never a silent infinite loop and never a
silently dropped cap.

## Gates are never assumed

Several stages declare a `gate` in `DEVELOPMENT_LIFECYCLE.yaml` (e.g.
context's "unresolved blockers are visible"). Advancing past a gated
stage requires an explicit `gate_confirmations[<stage_key>] = True` from
the caller — the executor will not infer this from the presence of
evidence alone, on either the passing or failing path.

## Required evidence

Each stage's `required` list (from `DEVELOPMENT_LIFECYCLE.yaml`) must be
satisfied by the `evidence` dict passed to `advance`/`start` — either as a
direct key, or (for file/path-looking required entries, e.g. context's
`.ai/CURRENT_STATE.md`) as an entry in `evidence["files_consulted"]`.
Missing items reject the transition with a specific, listed reason.

## Concurrency

`src/seion_core/orchestration/lease.py` provides liveness-aware resource
leases under `.ai/runtime/locks/` so two sessions cannot claim the same
resource concurrently: a lease held by a dead process on the same machine
is force-breakable regardless of its TTL; a lease on a different machine,
or a live process, is only breakable after its TTL expires. Not yet wired
into the CLI as a standalone verb — used internally where a caller wants
it, via `seion_core.orchestration.lease.acquire/release/status`.

## CLI

```bash
python -m seion_core.cli.main governance lifecycle start \
  --task "..." --workstream spectral --risk low \
  --evidence-json '{"task_id":"...","affected_workstream":"...","risk_level":"low","expected_outputs":"..."}'

python -m seion_core.cli.main governance lifecycle advance <session_id> \
  --to context --gate-confirm \
  --evidence-json '{"AGENTS.md":true,".ai/CURRENT_STATE.md":true,".ai/TASKS.md":true,"relevant registries":true}'

python -m seion_core.cli.main governance lifecycle verify-result <session_id> \
  --passed --gate-confirm --evidence-json '{"run_id_or_proof_location":"...","artifact_hashes":"...","provenance":"..."}'

python -m seion_core.cli.main governance lifecycle status <session_id>
python -m seion_core.cli.main governance lifecycle list
python -m seion_core.cli.main governance lifecycle roles verify
```

## State storage

Mirrors the canonical/machine split already used throughout `.ai/`:
`.ai/runtime/sessions/<id>.json` is the current-state snapshot (always
rebuildable), `.ai/runtime/sessions/<id>.history.jsonl` is the append-only
transition log (never rewritten). Both are disposable runtime state
(`.ai/runtime/*` is gitignored), not canonical memory. Every
start/advance/block also appends one entry to the canonical
`.ai/evidence/ledger.jsonl` via the existing
`src/seion_core/governance/events.py:append_event` (extended with an
optional `session_id` field, not a schema break).

## Tests

`tests/governance/test_lifecycle.py`, `test_roles.py`, `test_lease.py` —
run with `python -m pytest tests/governance -q`.
