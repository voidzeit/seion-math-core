$ErrorActionPreference = 'Stop'

$repoRoot = (Resolve-Path (Join-Path $PSScriptRoot '..')).Path
Push-Location $repoRoot
try {
    & python scripts/run_research_v2.py
    if ($LASTEXITCODE -ne 0) { throw "research_v2 runner failed with exit code $LASTEXITCODE" }

    & python scripts/build_research_v2_tables.py
    if ($LASTEXITCODE -ne 0) { throw "v2 table generation failed with exit code $LASTEXITCODE" }

    & python scripts/build_research_v2_figures.py
    if ($LASTEXITCODE -ne 0) { throw "v2 figure generation failed with exit code $LASTEXITCODE" }

    Push-Location papers/foundations_v2
    try {
        & latexmk -pdf -interaction=nonstopmode -halt-on-error -file-line-error -outdir=build main.tex
        if ($LASTEXITCODE -ne 0) { throw "foundations build failed with exit code $LASTEXITCODE" }
        & latexmk -pdf -jobname=draft_not_for_submission -interaction=nonstopmode -halt-on-error -file-line-error -outdir=build main.tex
        if ($LASTEXITCODE -ne 0) { throw "foundations draft build failed with exit code $LASTEXITCODE" }
    }
    finally { Pop-Location }

    Push-Location papers/software_v2
    try {
        & latexmk -pdf -interaction=nonstopmode -halt-on-error -file-line-error -outdir=build main.tex
        if ($LASTEXITCODE -ne 0) { throw "software companion build failed with exit code $LASTEXITCODE" }
    }
    finally { Pop-Location }

    $renderRoot = Join-Path $repoRoot 'artifacts/pdf/research_v2_pages'
    New-Item -ItemType Directory -Force -Path $renderRoot | Out-Null
    $pdftoppmCommand = Get-Command pdftoppm -ErrorAction Stop
    $pdftoppm = $pdftoppmCommand.Source
    if ($pdftoppmCommand.Extension -eq '.cmd') {
        $overrideDirectory = Split-Path -Parent $pdftoppm
        $dependenciesDirectory = Split-Path -Parent (Split-Path -Parent $overrideDirectory)
        $nativeExecutable = Join-Path $dependenciesDirectory 'native\poppler\Library\bin\pdftoppm.exe'
        if (Test-Path -LiteralPath $nativeExecutable) { $pdftoppm = $nativeExecutable }
    }
    $pdfs = @(
        (Join-Path $repoRoot 'papers/foundations_v2/build/main.pdf'),
        (Join-Path $repoRoot 'papers/foundations_v2/build/draft_not_for_submission.pdf'),
        (Join-Path $repoRoot 'papers/software_v2/build/main.pdf')
    ) + @(Get-ChildItem (Join-Path $repoRoot 'papers/foundations_v2/figures') -Filter '*.pdf' | Select-Object -ExpandProperty FullName)
    foreach ($pdf in $pdfs) {
        if (-not (Test-Path -LiteralPath $pdf)) { throw "Missing PDF for render: $pdf" }
        $base = [IO.Path]::GetFileNameWithoutExtension($pdf)
        & $pdftoppm -png -r 120 $pdf (Join-Path $renderRoot $base)
        if ($LASTEXITCODE -ne 0) { throw "PDF render failed for $pdf with exit code $LASTEXITCODE" }
    }

    & python scripts/research_v2_audit.py
    $auditExit = $LASTEXITCODE
    if ($auditExit -ne 0) {
        Write-Warning "v2 build completed, but the strict research gate remains fail-closed (exit $auditExit)."
    }
    exit $auditExit
}
finally { Pop-Location }
