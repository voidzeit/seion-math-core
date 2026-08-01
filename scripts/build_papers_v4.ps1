$ErrorActionPreference = 'Stop'
foreach ($spec in @(@{Path='papers/tree_stability_v4'; Main='main.tex'}, @{Path='papers/software_v4'; Main='main.tex'}, @{Path='papers/supplement_v4'; Main='main.tex'})) {
  $dir = Join-Path $PWD $spec.Path
  if (Get-Command latexmk -ErrorAction SilentlyContinue) {
    $build = Join-Path $dir 'build'
    New-Item -ItemType Directory -Force -Path $build | Out-Null
    Push-Location $dir
    latexmk -pdf -interaction=nonstopmode -halt-on-error -file-line-error "-outdir=build" $spec.Main
    $code = $LASTEXITCODE
    Pop-Location
    if ($code -ne 0) { exit $code }
  } else { Write-Warning "latexmk unavailable; source prepared but PDF build is blocked" }
}
