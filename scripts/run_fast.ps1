[CmdletBinding()]
param()

$ErrorActionPreference = 'Stop'
$root = (Resolve-Path (Join-Path $PSScriptRoot '..')).Path
Set-Location $root
$started = Get-Date

python -m pip install -e . --no-deps --disable-pip-version-check
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }

python -m pytest -q tests/unit tests/symbolic tests/numerical
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }

python -m seion_core.cli.main run-suite --profile fast --device cpu
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }

$report = [ordered]@{
  profile = 'fast'
  started = $started.ToUniversalTime().ToString('o')
  finished = (Get-Date).ToUniversalTime().ToString('o')
  exit_code = 0
  tests = 'unit, symbolic, numerical'
}
New-Item -ItemType Directory -Force -Path (Join-Path $root 'artifacts/index') | Out-Null
$report | ConvertTo-Json -Depth 6 | Set-Content -Encoding UTF8 (Join-Path $root 'artifacts/index/fast_execution.json')
python -m seion_core.cli.main governance audit --json
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
exit 0
