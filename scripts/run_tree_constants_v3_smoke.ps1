[CmdletBinding()]
param()

$ErrorActionPreference = "Stop"
$RepoRoot = Split-Path -Parent $PSScriptRoot
Push-Location $RepoRoot
try {
    python scripts/tree_constants_v3_pipeline.py budget
    if ($LASTEXITCODE -ne 0) { throw "Budget/calibration stage failed." }
    python scripts/tree_constants_v3_pipeline.py smoke
    if ($LASTEXITCODE -ne 0) { throw "Smoke stage failed." }
}
finally {
    Pop-Location
}
