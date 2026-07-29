[CmdletBinding()]
param()

$ErrorActionPreference = "Stop"
$RepoRoot = Split-Path -Parent $PSScriptRoot
Push-Location $RepoRoot
try {
    python scripts/tree_constants_v3_pipeline.py budget
    if ($LASTEXITCODE -ne 0) { throw "Budget stage failed." }
    python scripts/tree_constants_v3_pipeline.py enumerate
    if ($LASTEXITCODE -ne 0) { throw "Tree enumeration failed." }
    python scripts/tree_constants_v3_pipeline.py exact
    if ($LASTEXITCODE -ne 0) { throw "Exact certification stage failed." }
}
finally {
    Pop-Location
}
