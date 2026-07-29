[CmdletBinding()]
param()

$ErrorActionPreference = 'Stop'
$root = (Resolve-Path (Join-Path $PSScriptRoot '..')).Path
Set-Location $root
python -m seion_core.cli.main governance audit --strict --json
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
python scripts/release_bundle.py
exit $LASTEXITCODE
