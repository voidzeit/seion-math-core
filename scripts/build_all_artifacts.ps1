[CmdletBinding()]
param()

$ErrorActionPreference = 'Stop'
$root = (Resolve-Path (Join-Path $PSScriptRoot '..')).Path
Set-Location $root
python scripts/build_artifacts.py
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
python scripts/verify_artifacts.py
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
python -m seion_core.cli.main governance dedupe-runs --json
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
python -m seion_core.cli.main governance audit --json
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
exit 0
