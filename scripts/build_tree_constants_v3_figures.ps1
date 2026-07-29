[CmdletBinding()]
param()

$ErrorActionPreference = "Stop"
$RepoRoot = Split-Path -Parent $PSScriptRoot
Push-Location $RepoRoot
try {
    python scripts/figures_v3/build.py
    if ($LASTEXITCODE -ne 0) { throw "V3 figure generation failed." }
}
finally {
    Pop-Location
}
