# Local governance and memory system

SEION uses a repository-local control plane. The reference repositories that
informed the design are not dependencies and are not edited.

## Four layers

1. `AGENTS.md` is the session contract.
2. `.ai/` is durable project memory and recovery state.
3. `governance/` contains versioned authority, lifecycle, action, memory, and
   research/software contracts.
4. `src/seion_core/governance/` and the CLI enforce deterministic structural
   checks, context compilation, action gates, and run deduplication.

Run:

```powershell
python -m seion_core.cli.main governance context --task "prepare projector evidence review"
python -m seion_core.cli.main governance audit --strict
python -m seion_core.cli.main governance dedupe-runs
```

The audit is deliberately conservative. It reports missing evidence and
inconsistent release flags; it does not manufacture a clean state by deleting
old runs or rewriting the claim registry.

## Recovery and handoff

Use `.ai/CONTEXT_RECOVERY.md` after interruption. A postflight entry must state
what was actually executed, the exact commit and branch, changed files, and
limitations. Terminal context and generated packs are disposable.

## Research/software boundary

See `governance/RESEARCH_SOFTWARE_SPLIT.yaml`. A successful run proves that an
implementation executed under recorded conditions. It does not prove a new
mathematical theorem or establish novelty.
