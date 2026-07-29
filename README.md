# SEION Math Core

SEION Math Core is a research repository for the defensible mathematical nucleus of the Kernel-Integrated Laws framework. It defines typed finite-dimensional n-ary laws, separates ternary composition conventions, measures associator and symmetry defects, studies structure-preserving projectors, and records finite cohomological/operator checks.

The repository is deliberately conservative. A numerical residual is an observation, not a proof. A theorem with hypotheses remains conditional. Continuous limits, physical interpretations, and application claims are separate open research tracks.

## First vertical slice

After installation, run:

```powershell
python -m pip install -e .
seion-core certify experiments/configs/finite_ternary_v1.yaml
```

The command emits a self-contained run directory under `artifacts/runs/` containing the configuration, manifest, metrics, certificate, summary, and hashes.

## Research commands

```powershell
.\scripts\run_fast.ps1
.\scripts\run_full_blackwell.ps1
.\scripts\build_all_artifacts.ps1
.\scripts\build_paper.ps1
.\scripts\release_bundle.ps1
```

The full local profile detects hardware and uses CUDA when available, but every mathematical gate has a CPU path.

## Epistemic status

Claims are registered in `claims/` with statuses such as `definition`, `proved_under_assumptions`, `symbolically_verified`, `numerically_verified`, `conjecture`, `open`, and `refuted`. Generated figures and paper tables point back to run identifiers and `final_metrics.json` files.

## Local governance, memory, and recovery

The repository contains a self-contained governance and memory system. Read
`AGENTS.md` first, then recover durable state from `.ai/`. Shared contracts live
in `governance/`; executable controls live in `src/seion_core/governance/`.

```powershell
python -m seion_core.cli.main governance context --task "review the projector evidence"
python -m seion_core.cli.main governance audit --strict
python -m seion_core.cli.main governance dedupe-runs --json
```

The audit preserves historical runs and generates a derived unique-instance
index at `artifacts/index/run_index_deduplicated.csv`. A green structural audit
is not mathematical proof or release approval. The mathematical research paper
and the reproducibility/software companion are governed as separate workstreams
by `governance/RESEARCH_SOFTWARE_SPLIT.yaml`.

## Research v2 track

The structure-preserving-reduction track is isolated from the legacy 0.1
release. Rebuild its registered runs, tables, vector figures, both manuscripts,
rendered pages, and fail-closed audit with:

```powershell
powershell -ExecutionPolicy Bypass -File scripts/build_research_v2.ps1
```

The v2 foundations draft is intentionally not submission-ready: its standard
exact-reduction and spectral results are not claimed as novel, and the audit
records the remaining novelty and author-metadata blockers in
`papers/foundations_v2/RESEARCH_BLOCKED.md`.

## Research v3: nodewise tree constants

The v3 track studies finite typed multilinear composition trees only. Its
canonical command executes the 15-stage base workflow, rebuilds both papers,
renders every PDF page, audits all evidence, and exits nonzero when any strict
publication gate remains unresolved:

    .\scripts\run_tree_constants_v3_full.ps1

Exit code 2 means the technical workflow completed but publication remains
fail-closed; it is not an operational crash. The resource-gated optimizer grid
is preserved as a complete resumable schedule:

    .\scripts\run_tree_constants_v3_extended.ps1 -MaxTrajectories 4
    .\scripts\resume_tree_constants_v3.ps1 -MaxTrajectories 4

See docs/reproducibility/tree_constants_v3.md for artifact locations,
epistemic statuses, exact commands, and hash verification.

## Scope

The core package does not contain KGE, LLM compression, BIM, cosmology, trading, or a universal physical theory. Those are explicitly non-goals for this repository.
