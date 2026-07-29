# Test and evidence matrix

| Gate | Command | Evidence output | Authority | Notes |
|---|---|---|---|---|
| Unit/symbolic/numerical | `python -m pytest -q` | pytest output | observed/verified | Must be executed for current status. |
| Claims lint | `python -m seion_core.cli.main audit` | `artifacts/index/claims_report.json` | verified | Registry status and language constraints. |
| Governance audit | `python -m seion_core.cli.main governance audit --strict` | `artifacts/index/governance_audit.json` | verified | Structural and provenance gate. |
| Run deduplication | `python -m seion_core.cli.main governance dedupe-runs` | `artifacts/index/run_index_deduplicated.csv` | observed | Derived view; historical index preserved. |
| Fast profile | `.\scripts\run_fast.ps1` | `artifacts/index/profile_fast.json` | observed | CPU-safe vertical slice. |
| Full profile | `.\scripts\run_full_blackwell.ps1` | profile/matrix artifacts | observed | Hardware fallback must be recorded. |
| Paper build | `.\scripts\build_paper.ps1` | `paper/build/main.pdf` | observed | Compile and log inspection. |
| Render inspection | `python scripts/inspect_paper.py` | `artifacts/paper_render/render_report.json` | observed | Automated gate plus manual review. |
| Release | `.\scripts\release_bundle.ps1` | `artifacts/release/` | approved only after review | Never infer approval from automation. |
