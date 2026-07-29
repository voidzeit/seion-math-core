[CmdletBinding()]
param()

$ErrorActionPreference = "Stop"
$RepoRoot = Split-Path -Parent $PSScriptRoot
Push-Location (Join-Path $RepoRoot "papers/tree_stability_v3")
try {
    latexmk -pdf -interaction=nonstopmode -halt-on-error -file-line-error -outdir=build main.tex
    if ($LASTEXITCODE -ne 0) { throw "Mathematical paper compilation failed." }
}
finally {
    Pop-Location
}
Push-Location (Join-Path $RepoRoot "papers/software_v3")
try {
    latexmk -pdf -interaction=nonstopmode -halt-on-error -file-line-error -outdir=build main.tex
    if ($LASTEXITCODE -ne 0) { throw "Software companion compilation failed." }
}
finally {
    Pop-Location
}
