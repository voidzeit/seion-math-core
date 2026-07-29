[CmdletBinding()]
param()

$ErrorActionPreference = "Stop"
$RepoRoot = Split-Path -Parent $PSScriptRoot
Push-Location $RepoRoot
try {
    python scripts/tree_constants_v3_audit.py report
    $GateExit = $LASTEXITCODE
    if ($GateExit -eq 0) {
        Write-Host "V3 strict gate passed."
        exit 0
    }
    if ($GateExit -eq 2) {
        Write-Host "V3 strict gate correctly failed closed. See artifacts/research_v3/release_gate_v3.md."
        exit 2
    }
    throw "V3 release audit failed operationally with exit code $GateExit."
}
finally {
    Pop-Location
}
