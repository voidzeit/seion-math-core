$ErrorActionPreference = 'Stop'

$repoRoot = (Resolve-Path (Join-Path $PSScriptRoot '..')).Path
$manuscripts = @(
    @{ Name = 'foundations'; Directory = (Join-Path $repoRoot 'papers\foundations') },
    @{ Name = 'software'; Directory = (Join-Path $repoRoot 'papers\software') }
)

$outputPdf = Join-Path $repoRoot 'output\pdf'
$renderRoot = Join-Path $repoRoot 'artifacts\companion_render'
New-Item -ItemType Directory -Force -Path $outputPdf | Out-Null
New-Item -ItemType Directory -Force -Path $renderRoot | Out-Null

$pdftoppmCommand = Get-Command pdftoppm -ErrorAction Stop
$pdftoppm = $pdftoppmCommand.Source
if ($pdftoppmCommand.Extension -eq '.cmd') {
    $overrideDirectory = Split-Path -Parent $pdftoppm
    $dependenciesDirectory = Split-Path -Parent (Split-Path -Parent $overrideDirectory)
    $nativeExecutable = Join-Path $dependenciesDirectory 'native\poppler\Library\bin\pdftoppm.exe'
    if (Test-Path -LiteralPath $nativeExecutable) {
        $pdftoppm = $nativeExecutable
    }
}

foreach ($manuscript in $manuscripts) {
    $directory = $manuscript.Directory
    $buildDirectory = Join-Path $directory 'build'
    New-Item -ItemType Directory -Force -Path $buildDirectory | Out-Null

    Push-Location $directory
    try {
        & latexmk -pdf -interaction=nonstopmode -halt-on-error -file-line-error -outdir=build main.tex
        if ($LASTEXITCODE -ne 0) {
            throw "latexmk failed for $($manuscript.Name) with exit code $LASTEXITCODE"
        }
    }
    finally {
        Pop-Location
    }

    $pdf = Join-Path $buildDirectory 'main.pdf'
    if (-not (Test-Path -LiteralPath $pdf)) {
        throw "Expected PDF was not generated: $pdf"
    }

    $stablePdf = Join-Path $outputPdf ("seion-$($manuscript.Name).pdf")
    Copy-Item -LiteralPath $pdf -Destination $stablePdf -Force

    $renderDirectory = Join-Path $renderRoot $manuscript.Name
    New-Item -ItemType Directory -Force -Path $renderDirectory | Out-Null
    Get-ChildItem -LiteralPath $renderDirectory -Filter 'page-*.png' -File -ErrorAction SilentlyContinue | Remove-Item -Force
    $prefix = Join-Path $renderDirectory 'page'
    & $pdftoppm -png -r 150 $pdf $prefix
    if ($LASTEXITCODE -ne 0) {
        throw "pdftoppm failed for $($manuscript.Name) with exit code $LASTEXITCODE"
    }

    [pscustomobject]@{
        manuscript = $manuscript.Name
        source = (Join-Path $directory 'main.tex')
        pdf = $stablePdf
        render_directory = $renderDirectory
        status = 'PASS_COMPILE_AND_RENDER'
    } | ConvertTo-Json -Depth 4
}
