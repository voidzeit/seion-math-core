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
| V3 canonical | `.\scripts\run_tree_constants_v3_full.ps1` | `artifacts/research_v3/full_execution_manifest.json` | observed/verified | Exit is nonzero when publication correctly fails closed. |
| V3 tests/CUDA | `python -m pytest -q` | `artifacts/qa_v3/pytest_v3.xml` | verified | Current result: 69 passed, including CUDA parity. |
| V3 exact enumeration | `python scripts/tree_constants_v3_pipeline.py enumerate` | `artifacts/index/tree_instances_v3.parquet` | verified | 81,445 occurrences; 80,870 unique hashes. |
| V3 base matrix | `python scripts/tree_constants_v3_pipeline.py full` | `artifacts/index/scientific_instances_full_v3.parquet` | observed/verified | 15,493 unique A--I instances; no duplicate scientific hashes. |
| V3 PDF QA | `python scripts/tree_constants_v3_audit.py render` | `artifacts/qa_v3/pdf_manifest_v3.json` | observed/verified | 37 pages rendered; final visual signoff is separate. |
| V3 technical audit | `python scripts/tree_constants_v3_audit.py audit` | `artifacts/research_v3/audit_v3.json` | verified | Tests, hashes, runs, DAG, data, LaTeX, and PDFs pass. |
| V3 release gate | `python scripts/tree_constants_v3_audit.py report` | `artifacts/research_v3/release_gate_v3.json` | fail-closed | Current result: 9/15, `FAIL_CLOSED_NOVELTY`. |
