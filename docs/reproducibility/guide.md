# Reproduction guide

```powershell
python -m pip install -e .
seion-core certify experiments/configs/finite_ternary_v1.yaml
.\scripts\run_fast.ps1
.\scripts\run_full_blackwell.ps1
.\scripts\build_all_artifacts.ps1
.\scripts\build_paper.ps1
.\scripts\release_bundle.ps1
```

Every run records Python, operating system, Git state, backend, dtype, seed, sample count, assumptions, tolerances, and SHA-256 hashes. Hardware acceleration is used when available but is not required for the finite tests.

