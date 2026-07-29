.PHONY: install test fast full artifacts paper release

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

release:
	powershell -ExecutionPolicy Bypass -File scripts/release_bundle.ps1

