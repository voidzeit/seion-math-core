.PHONY: install test fast full artifacts paper companions research-v2 release governance context dedupe

install:
	python -m pip install -e .

test:
	python -m pytest

fast:
	powershell -ExecutionPolicy Bypass -File scripts/run_fast.ps1

full:
	powershell -ExecutionPolicy Bypass -File scripts/run_full_blackwell.ps1

artifacts:
	powershell -ExecutionPolicy Bypass -File scripts/build_all_artifacts.ps1

paper:
	powershell -ExecutionPolicy Bypass -File scripts/build_paper.ps1

companions:
	powershell -ExecutionPolicy Bypass -File scripts/build_companions.ps1

research-v2:
	powershell -ExecutionPolicy Bypass -File scripts/build_research_v2.ps1

release:
	powershell -ExecutionPolicy Bypass -File scripts/release_bundle.ps1

governance:
	powershell -ExecutionPolicy Bypass -File scripts/governance_audit.ps1

context:
	python -m seion_core.cli.main governance context --task "repository recovery"

dedupe:
	python -m seion_core.cli.main governance dedupe-runs --json
