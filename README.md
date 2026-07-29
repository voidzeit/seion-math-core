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

## Scope

The core package does not contain KGE, LLM compression, BIM, cosmology, trading, or a universal physical theory. Those are explicitly non-goals for this repository.

