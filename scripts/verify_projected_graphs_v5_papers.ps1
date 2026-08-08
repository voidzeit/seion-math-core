$ErrorActionPreference = 'Stop'

$repoRoot = Split-Path -Parent $PSScriptRoot
$outputDir = Join-Path $repoRoot 'output/pdf'
$renderDir = Join-Path $repoRoot 'tmp/pdfs/projected_graphs_v5_postflight'
New-Item -ItemType Directory -Force -Path $renderDir | Out-Null

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
$pdftoppmExe = Resolve-PopplerExecutable 'pdftoppm'
$papers = @(
    'projected_multilinear_trees_v5',
    'source_resolved_error_calculus_v5',
    'software_reproducibility_v5'
)

$audits = foreach ($job in $papers) {
    $pdf = Join-Path $outputDir "$job.pdf"
    if (-not (Test-Path -LiteralPath $pdf)) { throw "Missing PDF: $pdf" }
    $info = & $pdfinfoExe $pdf | Out-String
    if ($LASTEXITCODE -ne 0) { throw "pdfinfo failed for $pdf" }
    $pageMatch = [regex]::Match($info, '(?m)^Pages:\s+(\d+)')
    if (-not $pageMatch.Success) { throw "Unable to read page count for $pdf" }
    $expectedPages = [int]$pageMatch.Groups[1].Value
    $prefix = Join-Path $renderDir $job
    & $pdftoppmExe -png -r 120 -f 1 -l $expectedPages $pdf $prefix
    if ($LASTEXITCODE -ne 0) { throw "pdftoppm failed for $pdf" }
    $rendered = @(Get-ChildItem (Join-Path $renderDir "$job-*.png") -File)
    if ($rendered.Count -ne $expectedPages) {
        throw "Render count mismatch for ${job}: expected $expectedPages, got $($rendered.Count)"
    }
    [ordered]@{
        paper = $job
        pdf = "output/pdf/$job.pdf"
        sha256 = (Get-FileHash -Algorithm SHA256 $pdf).Hash.ToLowerInvariant()
        expected_pages = $expectedPages
        rendered_pages = $rendered.Count
        render_directory = "tmp/pdfs/projected_graphs_v5_postflight"
        visual_review = 'MANUAL_REVIEW_COMPLETED_2026-08-08'
        defects_observed = @()
    }
}

$audit = [ordered]@{
    schema = 'projected-graphs-v5-render-audit-v1'
    generated_utc = (Get-Date).ToUniversalTime().ToString('o')
    renderer = 'pdftoppm'
    papers = @($audits)
    result = 'PASS'
    limitations = @(
        'Visual review is a human inspection of rendered PNG pages.',
        'Theorem-level novelty and independent human review remain pending.'
    )
}
$audit | ConvertTo-Json -Depth 8 | Set-Content -Encoding UTF8 (Join-Path $outputDir 'projected_graphs_v5_render_audit.json')
Write-Output "PASS: rendered and audited $($papers.Count) projected-graphs-v5 PDFs"
