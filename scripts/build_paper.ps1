[CmdletBinding()]
param()

$ErrorActionPreference = 'Stop'
$root = (Resolve-Path (Join-Path $PSScriptRoot '..')).Path
Set-Location $root
& (Join-Path $PSScriptRoot 'build_all_artifacts.ps1')
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }

New-Item -ItemType Directory -Force -Path (Join-Path $root 'paper/build') | Out-Null
Push-Location (Join-Path $root 'paper')
latexmk -c -outdir=build main.tex
if ($LASTEXITCODE -ne 0) {
  Pop-Location
  exit $LASTEXITCODE
}
latexmk -pdf -interaction=nonstopmode -halt-on-error -file-line-error -outdir=build main.tex
$latexExit = $LASTEXITCODE
Pop-Location
if ($latexExit -ne 0) { exit $latexExit }
python scripts/inspect_paper.py
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
exit 0
