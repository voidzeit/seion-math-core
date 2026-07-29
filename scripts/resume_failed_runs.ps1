[CmdletBinding()]
param()

$ErrorActionPreference = 'Stop'
$root = (Resolve-Path (Join-Path $PSScriptRoot '..')).Path
Set-Location $root
python -m seion_core.cli.main compare --json
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
python -m seion_core.cli.main run-suite --profile full --device auto
exit $LASTEXITCODE

