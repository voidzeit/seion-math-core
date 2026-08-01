$ErrorActionPreference = 'Stop'
python -m seion_core.cli.main governance audit --json
python -m seion_core.cli.main governance dedupe-runs
git status --short
