[CmdletBinding()]
param(
    [ValidateRange(0, 1000000)]
    [int]$MaxTrajectories = 4,
    [ValidateRange(0, 100000)]
    [int]$AdamSteps = 30,
    [ValidateRange(0, 100000)]
    [int]$LbfgsSteps = 8
)

$ErrorActionPreference = "Stop"
$RepoRoot = Split-Path -Parent $PSScriptRoot
Push-Location $RepoRoot
try {
    python scripts/tree_constants_v3_extended.py plan
    if ($LASTEXITCODE -ne 0) { throw "Extended schedule generation failed." }
    python scripts/tree_constants_v3_extended.py run --max-trajectories $MaxTrajectories --adam-steps $AdamSteps --lbfgs-steps $LbfgsSteps
    if ($LASTEXITCODE -ne 0) { throw "Extended chunk failed." }
}
finally {
    Pop-Location
}
