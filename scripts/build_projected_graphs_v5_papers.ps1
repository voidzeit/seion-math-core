$ErrorActionPreference = 'Stop'

$repoRoot = Split-Path -Parent $PSScriptRoot
$sourceDir = Join-Path $repoRoot 'papers/projected_graphs_v5'
$outputDir = Join-Path $repoRoot 'output/pdf'
New-Item -ItemType Directory -Force -Path $outputDir | Out-Null

function Resolve-PopplerExecutable([string]$name) {
    $direct = Get-Command "$name.exe" -ErrorAction SilentlyContinue |
        Where-Object { $_.Source -notlike '*.cmd' } |
        Select-Object -First 1
    if ($direct) { return $direct.Source }
    $runtimeRoot = Join-Path $env:USERPROFILE '.cache/codex-runtimes'
    $candidate = Get-ChildItem $runtimeRoot -Recurse -Filter "$name.exe" -ErrorAction SilentlyContinue |
        Where-Object { $_.FullName -match 'poppler[\\/]Library[\\/]bin' } |
        Select-Object -First 1
    if ($candidate) { return $candidate.FullName }
    throw "Unable to resolve Poppler executable $name.exe"
}

$pdfinfoExe = Resolve-PopplerExecutable 'pdfinfo'

$papers = @(
    @{ Source = 'projected_multilinear_trees_v5.tex'; Job = 'projected_multilinear_trees_v5' },
    @{ Source = 'source_resolved_error_calculus_v5.tex'; Job = 'source_resolved_error_calculus_v5' },
    @{ Source = 'software_reproducibility_v5.tex'; Job = 'software_reproducibility_v5' }
)

Push-Location $sourceDir
try {
    foreach ($paper in $papers) {
        & latexmk -pdf -interaction=nonstopmode -halt-on-error -file-line-error `
            "-outdir=$outputDir" "-jobname=$($paper.Job)" $paper.Source
        if ($LASTEXITCODE -ne 0) {
            throw "PDF build failed for $($paper.Source) with exit code $LASTEXITCODE"
        }
    }
}
finally {
    Pop-Location
}

$manifest = @{
    schema = 'projected-graphs-v5-paper-package-v1'
    generated_utc = (Get-Date).ToUniversalTime().ToString('o')
    source_directory = 'papers/projected_graphs_v5'
    output_directory = 'output/pdf'
    papers = @($papers | ForEach-Object {
        $pdf = Join-Path $outputDir "$($_.Job).pdf"
        $info = & $pdfinfoExe $pdf | Out-String
        [ordered]@{
            source = $_.Source
            output = "output/pdf/$($_.Job).pdf"
            sha256 = (Get-FileHash -Algorithm SHA256 $pdf).Hash.ToLowerInvariant()
            pdfinfo = $info.Trim()
        }
    })
    validation = @(
        'latexmk -pdf -interaction=nonstopmode -halt-on-error -file-line-error',
        'pdfinfo',
        'pdftoppm visual rendering'
    )
    limitations = @(
        'Theorem-level novelty and independent human review remain pending.',
        'Global repeated-law and k=3 sharpness remain open.',
        'This package does not modify Gate 13.5, Gate 14, KGR, or historical artifacts.'
    )
}
$manifest | ConvertTo-Json -Depth 8 | Set-Content -Encoding UTF8 (Join-Path $outputDir 'projected_graphs_v5_paper_manifest.json')
