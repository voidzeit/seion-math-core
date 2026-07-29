[CmdletBinding()]
param()

$ErrorActionPreference = 'Stop'
$root = (Resolve-Path (Join-Path $PSScriptRoot '..')).Path
Set-Location $root
python -m seion_core.cli.main run-suite --profile extended --device cuda
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
python scripts/run_projector_sweep.py
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
exit 0

