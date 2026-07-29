[CmdletBinding()]
param()

$ErrorActionPreference = 'Stop'
$root = (Resolve-Path (Join-Path $PSScriptRoot '..')).Path
Set-Location $root
$started = Get-Date

& (Join-Path $PSScriptRoot 'run_fast.ps1')
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }

python -m seion_core.numerics.reproducibility
python -m pytest -q
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }

$device = 'cpu'
$cudaProbe = python -c "import torch; print('cuda' if torch.cuda.is_available() else 'cpu')"
if ($LASTEXITCODE -eq 0 -and $cudaProbe -match 'cuda') { $device = 'cuda' }
python -m seion_core.cli.main run-suite --profile full --device $device
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }

python scripts/run_precision_sweep.py
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
python scripts/run_multiscale_suite.py
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
python scripts/build_claims_report.py
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
python -m seion_core.cli.main governance audit --json
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }

$report = [ordered]@{
  profile = 'full'
  started = $started.ToUniversalTime().ToString('o')
  finished = (Get-Date).ToUniversalTime().ToString('o')
  exit_code = 0
  device = $device
  mandatory_gates = 'pytest, vertical certificate, inventories, precision, multiscale, claims'
}
$report | ConvertTo-Json -Depth 6 | Set-Content -Encoding UTF8 (Join-Path $root 'artifacts/index/full_execution.json')
exit 0
