# SEION Math Core agent contract

This file is the entry point for every coding, research, and release session in
this repository. Read it before changing code, claims, artifacts, or paper
sources.

## Scope

SEION Math Core is the finite-dimensional mathematical and computational core
of the Kernel-Integrated Laws program. The other repositories that may have
inspired its workflow are external references, not dependencies and not edit
targets. All governance, memory, development, evidence, and publication work
for this task stays in this repository.

## Required reading order

1. `AGENTS.md`
2. `.ai/MEMORY_MANIFEST.yaml`
3. `.ai/CURRENT_STATE.md`, `.ai/TASKS.md`, and `.ai/KNOWN_BLOCKERS.md`
4. the relevant file in `governance/`
5. the relevant claim, theorem, experiment, and artifact registries
6. source code and tests

Use `seion-core governance context --task "..."` to compile a bounded context
pack before a large change.

## Source-of-truth policy

Truth is scoped by domain rather than inferred from prose:

- executable behavior: `src/` and executed tests;
- mathematical status: `claims/claims_registry.yaml`,
  `claims/theorem_registry.yaml`, proof files, and counterexample records;
- executed numerical facts: a run's `run_manifest.json`, `final_metrics.json`,
  `certificate.json`, and `artifact_hashes.json`;
- experiment design: `experiments/` and its registered matrix;
- durable project state and decisions: `.ai/`;
- generated paper figures/tables: derived outputs with provenance, never manual
  authorities.

When sources disagree, record the conflict in `.ai/KNOWN_BLOCKERS.md` or
`.ai/DECISIONS.md`; do not silently rewrite history.

## Epistemic rules

- A numerical residual is an observation, not a proof.
- A theorem with hypotheses is conditional on those hypotheses.
- A symbolic or exhaustive finite check does not establish a continuum or
  universal statement.
- `declared`, `observed`, `verified`, and `approved` are governance authority
  levels; they do not replace the mathematical claim statuses.
- AI-generated suggestions remain advisory until a deterministic gate or human
  review accepts them. The agent cannot approve an official theorem, compliance
  result, or release by itself.
- Preserve failed runs and negative controls. Do not delete evidence or turn a
  historical pass into a current pass without a new executed command.

## Development lifecycle

Use the stages in `governance/DEVELOPMENT_LIFECYCLE.yaml`:

`intake -> context -> plan -> change -> verify -> evidence -> postflight -> release`

At postflight, record the command, environment, branch, commit, date, result,
changed files, and limitations. Run:

```powershell
python -m seion_core.cli.main governance audit --json
python -m seion_core.cli.main governance dedupe-runs
```

before claiming reproducibility or release readiness.

## Research/software split

The research paper and reproducibility/software companion have separate claim
budgets. The mathematical paper may cite the software, but repository
architecture and run orchestration are not mathematical novelty. See
`governance/RESEARCH_SOFTWARE_SPLIT.yaml`.

## Safe change rules

- Preserve unrelated dirty worktree changes.
- Prefer additive, reviewable edits and deterministic generators.
- Never use destructive Git history rewrites.
- Do not add credentials, secrets, or external-repository mutations.
- Update registries and provenance when adding a claim, theorem, experiment,
  figure, or table.
- Run the smallest relevant tests first, then the declared quality gates.
