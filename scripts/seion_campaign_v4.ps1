param([switch]$SkipHeavy)
$ErrorActionPreference = 'Continue'
$results = @()
function Stage($name, $script, [switch]$Optional) {
  $code = 0
  try { & $script; $code = $LASTEXITCODE } catch { Write-Warning "Stage $name exception: $($_.Exception.Message)"; $code = 1 }
  $results += [pscustomobject]@{stage=$name; exit_code=$code; optional=[bool]$Optional}
  if ($code -ne 0 -and -not $Optional) { Write-Warning "Stage $name failed with $code; evidence is preserved" }
}
Stage 'doctor' { python -c "import sys; print(sys.version)" }
Stage 'memory_graph' { python scripts/build_v4_foundation.py }
Stage 'static_quality' { python scripts/audit_v4.py } -Optional
Stage 'tests' { python -m pytest -q }
Stage 'exact' { & "$PSScriptRoot/run_exact.ps1" } -Optional
Stage 'base' { & "$PSScriptRoot/run_tree_constants_v3_full.ps1" } -Optional
Stage 'full_gpu' { & "$PSScriptRoot/run_full_blackwell.ps1" } -Optional
if (-not $SkipHeavy) { Stage 'extended_resource_gate' { & "$PSScriptRoot/run_extended_blackwell.ps1" } -Optional }
Stage 'table_validation' { python scripts/audit_v4.py } -Optional
Stage 'docs' { python scripts/build_docs_v4.py }
Stage 'papers' { python scripts/prepare_papers_v4.py } -Optional
Stage 'packaging' { python scripts/package_v4.py } -Optional
$results | ConvertTo-Json -Depth 4 | Set-Content artifacts/health/campaign_v4.json
if (($results | Where-Object {$_.exit_code -ne 0 -and -not $_.optional}).Count -gt 0) { exit 2 } else { exit 0 }
